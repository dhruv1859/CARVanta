"""
CARVanta – Live Gene Validator
===============================
Verifies antigen/gene symbols against real-world databases:
  - NCBI Entrez Gene API (https://eutils.ncbi.nlm.nih.gov)
  - UniProt REST API (https://rest.uniprot.org)

Returns verified gene information if found, enabling community
submissions of newly discovered antigens.

Usage:
    from features.gene_validator import validate_gene
    result = validate_gene("ALPP", timeout=15)
"""

import requests
import logging

logger = logging.getLogger(__name__)

# Timeout for each external API call (seconds)
DEFAULT_TIMEOUT = 15


def _search_ncbi(gene_symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict | None:
    """
    Search NCBI Entrez Gene database for a human gene symbol.

    Uses the E-utilities API:
    https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi

    Returns gene info dict or None if not found.
    """
    try:
        # Step 1: Search for the gene symbol in human genes
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "gene",
            "term": f"{gene_symbol}[sym] AND Homo sapiens[orgn]",
            "retmode": "json",
            "retmax": 1,
        }
        resp = requests.get(search_url, params=search_params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        id_list = data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return None

        gene_id = id_list[0]

        # Step 2: Fetch gene summary
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {
            "db": "gene",
            "id": gene_id,
            "retmode": "json",
        }
        resp2 = requests.get(summary_url, params=summary_params, timeout=timeout)
        resp2.raise_for_status()
        summary = resp2.json()

        gene_info = summary.get("result", {}).get(str(gene_id), {})
        if not gene_info or "name" not in gene_info:
            return None

        return {
            "source": "NCBI Gene",
            "gene_id": gene_id,
            "symbol": gene_info.get("name", gene_symbol).upper(),
            "full_name": gene_info.get("description", ""),
            "organism": gene_info.get("organism", {}).get("scientificname", "Homo sapiens"),
            "gene_type": gene_info.get("genetictype", ""),
            "chromosome": gene_info.get("chromosome", ""),
            "url": f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}",
        }

    except requests.exceptions.Timeout:
        logger.warning("NCBI API timed out for %s (timeout=%ds)", gene_symbol, timeout)
        return None
    except Exception as e:
        logger.warning("NCBI API error for %s: %s", gene_symbol, e)
        return None


def _search_uniprot(gene_symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict | None:
    """
    Search UniProt REST API for a human protein by gene name.

    Uses the new UniProt REST API:
    https://rest.uniprot.org/uniprotkb/search

    Returns protein info dict or None if not found.
    """
    try:
        url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": f"gene_exact:{gene_symbol} AND organism_id:9606 AND reviewed:true",
            "format": "json",
            "size": 1,
            "fields": "accession,gene_names,protein_name,organism_name,cc_subcellular_location",
        }
        resp = requests.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            # Try unreviewed (TrEMBL) entries too
            params["query"] = f"gene_exact:{gene_symbol} AND organism_id:9606"
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

        entry = results[0]
        accession = entry.get("primaryAccession", "")

        # Extract protein name
        protein_desc = entry.get("proteinDescription", {})
        rec_name = protein_desc.get("recommendedName", {})
        protein_name = rec_name.get("fullName", {}).get("value", "")
        if not protein_name:
            sub_names = protein_desc.get("submissionNames", [])
            if sub_names:
                protein_name = sub_names[0].get("fullName", {}).get("value", "")

        # Extract gene names
        gene_names = entry.get("genes", [])
        primary_gene = gene_names[0].get("geneName", {}).get("value", gene_symbol) if gene_names else gene_symbol

        # Extract subcellular location (important for CAR-T — surface vs intracellular)
        location_info = ""
        comments = entry.get("comments", [])
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                locs = comment.get("subcellularLocations", [])
                location_parts = [loc.get("location", {}).get("value", "") for loc in locs]
                location_info = "; ".join(filter(None, location_parts))
                break

        return {
            "source": "UniProt",
            "accession": accession,
            "symbol": primary_gene.upper(),
            "full_name": protein_name,
            "organism": "Homo sapiens",
            "subcellular_location": location_info,
            "url": f"https://www.uniprot.org/uniprotkb/{accession}",
        }

    except requests.exceptions.Timeout:
        logger.warning("UniProt API timed out for %s (timeout=%ds)", gene_symbol, timeout)
        return None
    except Exception as e:
        logger.warning("UniProt API error for %s: %s", gene_symbol, e)
        return None


def validate_gene(gene_symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Validate a gene symbol against NCBI Gene and UniProt databases.

    Searches both databases in parallel (with timeout per DB).
    Returns the best result with verification metadata.

    Parameters
    ----------
    gene_symbol : str
        Gene/antigen symbol to verify (e.g., "ALPP", "CRIB", "CD19")
    timeout : int
        Timeout in seconds for each database query (default: 15s)

    Returns
    -------
    dict with keys:
        - verified: bool — whether the gene was found in any database
        - gene_info: dict — gene details if verified
        - sources_checked: list — which databases were queried
        - sources_found: list — which databases confirmed the gene
    """
    import concurrent.futures

    gene = gene_symbol.strip().upper()
    result = {
        "verified": False,
        "gene_info": None,
        "sources_checked": [],
        "sources_found": [],
    }

    ncbi_result = None
    uniprot_result = None

    # Query both databases in parallel with timeout
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        ncbi_future = executor.submit(_search_ncbi, gene, timeout)
        uniprot_future = executor.submit(_search_uniprot, gene, timeout)

        try:
            ncbi_result = ncbi_future.result(timeout=timeout + 2)
            result["sources_checked"].append("NCBI Gene")
        except Exception:
            result["sources_checked"].append("NCBI Gene (timeout)")

        try:
            uniprot_result = uniprot_future.result(timeout=timeout + 2)
            result["sources_checked"].append("UniProt")
        except Exception:
            result["sources_checked"].append("UniProt (timeout)")

    # Merge results — prefer NCBI for gene info, UniProt for protein info
    if ncbi_result:
        result["verified"] = True
        result["sources_found"].append("NCBI Gene")
        result["gene_info"] = ncbi_result

    if uniprot_result:
        result["verified"] = True
        result["sources_found"].append("UniProt")
        if result["gene_info"] is None:
            result["gene_info"] = uniprot_result
        else:
            # Enrich NCBI result with UniProt protein info
            result["gene_info"]["protein_name"] = uniprot_result.get("full_name", "")
            result["gene_info"]["uniprot_accession"] = uniprot_result.get("accession", "")
            result["gene_info"]["subcellular_location"] = uniprot_result.get("subcellular_location", "")
            result["gene_info"]["uniprot_url"] = uniprot_result.get("url", "")

    return result
