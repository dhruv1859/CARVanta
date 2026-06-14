"""
CARVanta – Real Biological Data Fetcher v1
=============================================
Fetches real gene expression and protein data from 5 public databases:
  1. TCGA  (GDC API)        → Tumor gene expression
  2. GTEx  (Portal API v2)  → Normal tissue expression
  3. Human Protein Atlas    → Protein-level validation
  4. UniProt (REST API)     → Membrane topology / subcellular location
  5. ClinicalTrials.gov     → CAR-T clinical trial data

All results are cached locally in data/cache/ to avoid repeated API calls.

CARVanta-Original: This multi-source integration pipeline is unique to CARVanta.

Usage:
    from data.real_data_fetcher import RealDataFetcher
    fetcher = RealDataFetcher()
    tcga = fetcher.fetch_tcga_expression("CD19")
    gtex = fetcher.fetch_gtex_expression("CD19")
"""

import os
import json
import time
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional


# ─── Cache directory ────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CACHE_DIR = os.path.join(_BASE_DIR, "data", "cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

# ─── API endpoints ──────────────────────────────────────────────────────────────
TCGA_GDC_BASE = "https://api.gdc.cancer.gov"
GTEX_API_BASE = "https://gtexportal.org/api/v2"
HPA_API_BASE = "https://www.proteinatlas.org"
UNIPROT_API_BASE = "https://rest.uniprot.org"
CLINICAL_TRIALS_BASE = "https://clinicaltrials.gov/api/v2"

# ─── Gene symbol → Ensembl ID mapping (curated for key CAR-T targets) ──────────
# This mapping is used for APIs that require Ensembl IDs (GTEx, HPA)
GENE_TO_ENSEMBL = {
    "CD19":     "ENSG00000177455",
    "BCMA":     "ENSG00000048462",   # TNFRSF17
    "CD22":     "ENSG00000012124",
    "GPRC5D":   "ENSG00000111291",
    "PSMA":     "ENSG00000086205",   # FOLH1
    "GD2":      "ENSG00000163521",   # B4GALNT1
    "GPC3":     "ENSG00000147257",
    "FOLR1":    "ENSG00000110195",
    "CLDN18":   "ENSG00000066405",
    "ROR1":     "ENSG00000185483",
    "DLL3":     "ENSG00000090932",
    "CD70":     "ENSG00000125726",
    "CD138":    "ENSG00000115884",   # SDC1
    "CAIX":     "ENSG00000107611",   # CA9
    "IL13RA2":  "ENSG00000123496",
    "HER2":     "ENSG00000141736",   # ERBB2
    "EGFR":     "ENSG00000146648",
    "MESOTHELIN":"ENSG00000100321",  # MSLN
    "CD20":     "ENSG00000156738",   # MS4A1
    "CD38":     "ENSG00000004468",
    "CD33":     "ENSG00000105383",
    "FLT3":     "ENSG00000122025",
    "CD123":    "ENSG00000185291",   # IL3RA
    "SLAMF7":   "ENSG00000026751",
    "EGFRVIII": "ENSG00000146648",   # Same gene, variant
    "B7H3":     "ENSG00000103855",   # CD276
    "MUC1":     "ENSG00000185499",
    "EPCAM":    "ENSG00000119888",
    "TP53":     "ENSG00000141510",
    "KRAS":     "ENSG00000133703",
    "BRAF":     "ENSG00000157764",
    "PTEN":     "ENSG00000171862",
    "MYC":      "ENSG00000136997",
}

# ─── TCGA project codes → cancer type mapping ──────────────────────────────────
TCGA_PROJECT_MAP = {
    "TCGA-BRCA": "Breast Cancer",
    "TCGA-LUAD": "Lung Adenocarcinoma",
    "TCGA-GBM":  "Glioblastoma",
    "TCGA-PRAD": "Prostate Cancer",
    "TCGA-COAD": "Colorectal Cancer",
    "TCGA-OV":   "Ovarian Cancer",
    "TCGA-LAML": "Leukemia",
    "TCGA-SKCM": "Melanoma",
    "TCGA-LIHC": "Liver Cancer",
    "TCGA-KIRC": "Renal Cancer",
    "TCGA-STAD": "Gastric Cancer",
    "TCGA-PAAD": "Pancreatic Cancer",
    "TCGA-DLBC": "Lymphoma",
    "TCGA-BLCA": "Bladder Cancer",
    "TCGA-HNSC": "Head & Neck Cancer",
    "TCGA-UCEC": "Endometrial Cancer",
    "TCGA-THCA": "Thyroid Cancer",
}

# ─── GTEx tissue mapping (54 tissues → organ systems) ───────────────────────────
GTEX_TISSUE_GROUPS = {
    "Brain": [
        "Brain_Amygdala", "Brain_Anterior_cingulate_cortex_BA24",
        "Brain_Caudate_basal_ganglia", "Brain_Cerebellar_Hemisphere",
        "Brain_Cerebellum", "Brain_Cortex", "Brain_Frontal_Cortex_BA9",
        "Brain_Hippocampus", "Brain_Hypothalamus",
        "Brain_Nucleus_accumbens_basal_ganglia",
        "Brain_Putamen_basal_ganglia",
        "Brain_Spinal_cord_cervical_c-1",
        "Brain_Substantia_nigra",
    ],
    "Heart": ["Heart_Atrial_Appendage", "Heart_Left_Ventricle"],
    "Lung": ["Lung"],
    "Liver": ["Liver"],
    "Kidney": ["Kidney_Cortex", "Kidney_Medulla"],
    "GI Tract": [
        "Colon_Sigmoid", "Colon_Transverse",
        "Esophagus_Gastroesophageal_Junction",
        "Esophagus_Mucosa", "Esophagus_Muscularis",
        "Small_Intestine_Terminal_Ileum", "Stomach",
    ],
    "Blood": ["Whole_Blood", "Cells_EBV-transformed_lymphocytes"],
    "Skin": ["Skin_Not_Sun_Exposed_Suprapubic", "Skin_Sun_Exposed_Lower_leg"],
    "Muscle": ["Muscle_Skeletal"],
    "Nerve": ["Nerve_Tibial"],
    "Adipose": ["Adipose_Subcutaneous", "Adipose_Visceral_Omentum"],
    "Breast": ["Breast_Mammary_Tissue"],
    "Reproductive": [
        "Ovary", "Uterus", "Vagina", "Prostate", "Testis",
        "Fallopian_Tube",
    ],
    "Endocrine": [
        "Adrenal_Gland", "Thyroid", "Pituitary", "Pancreas",
    ],
    "Immune": ["Spleen", "Minor_Salivary_Gland"],
    "Vascular": ["Artery_Aorta", "Artery_Coronary", "Artery_Tibial"],
    "Bladder": ["Bladder"],
}

# Critical organs for safety — expression here is a red flag
CRITICAL_ORGANS = ["Brain", "Heart", "Lung", "Liver", "Kidney"]


def _cache_key(prefix: str, gene: str) -> str:
    """Generate a cache filename for a given API + gene."""
    safe = hashlib.md5(f"{prefix}_{gene}".encode()).hexdigest()[:12]
    return os.path.join(_CACHE_DIR, f"{prefix}_{gene}_{safe}.json")


def _load_cache(path: str, max_age_days: int = 30) -> Optional[dict]:
    """Load cached data if it exists and is fresh enough."""
    if not os.path.exists(path):
        return None
    age = time.time() - os.path.getmtime(path)
    if age > max_age_days * 86400:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_cache(path: str, data: dict):
    """Save data to cache."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError:
        pass


def _http_get(url: str, timeout: int = 30) -> Optional[dict]:
    """Simple HTTP GET returning parsed JSON, or None on failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CARVanta/1.0 (Research Platform)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, TimeoutError, OSError):
        return None


def _http_post_json(url: str, payload: dict, timeout: int = 30) -> Optional[dict]:
    """HTTP POST with JSON body, returning parsed JSON."""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data,
            headers={
                "User-Agent": "CARVanta/1.0 (Research Platform)",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, TimeoutError, OSError):
        return None


class RealDataFetcher:
    """
    CARVanta Real Biological Data Fetcher.

    Integrates 5 public databases into a unified interface for
    fetching real gene expression, protein, and clinical trial data.
    """

    def __init__(self, cache_days: int = 30):
        self.cache_days = cache_days

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. TCGA (GDC API) — Tumor gene expression
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_tcga_expression(self, gene_symbol: str) -> dict:
        """
        Fetch tumor expression data from TCGA via cBioPortal API.

        cBioPortal hosts all TCGA pan-cancer atlas data with a free REST API.
        Returns median RNA-seq RSEM values per cancer type.
        """
        gene = gene_symbol.upper()
        cache_path = _cache_key("tcga", gene)
        cached = _load_cache(cache_path, self.cache_days)
        if cached:
            return cached

        result = {
            "gene": gene,
            "cancer_types": {},
            "overall_mean_tumor": 0.0,
            "max_expression_cancer": "",
            "max_expression_value": 0.0,
            "source": "TCGA-cBioPortal",
            "status": "pending",
        }

        # Resolve gene aliases
        CBIO_BASE = "https://www.cbioportal.org/api"
        gene_aliases = {
            "BCMA": "TNFRSF17", "GD2": "B4GALNT1", "PSMA": "FOLH1",
            "CD138": "SDC1", "CD20": "MS4A1", "CD123": "IL3RA",
            "CAIX": "CA9", "B7H3": "CD276", "MESOTHELIN": "MSLN",
            "CLDN18.2": "CLDN18", "EGFRVIII": "EGFR",
        }
        query_gene = gene_aliases.get(gene, gene)

        gene_url = f"{CBIO_BASE}/genes/{query_gene}"
        gene_data = _http_get(gene_url)

        if not gene_data or "entrezGeneId" not in gene_data:
            result["status"] = "gene_not_found"
            _save_cache(cache_path, result)
            return result

        entrez_id = gene_data["entrezGeneId"]

        # Query across 18 TCGA pan-cancer studies
        tcga_studies = {
            "brca_tcga_pan_can_atlas_2018": "Breast Cancer",
            "laml_tcga_pan_can_atlas_2018": "Leukemia",
            "dlbc_tcga_pan_can_atlas_2018": "Lymphoma",
            "gbm_tcga_pan_can_atlas_2018": "Glioblastoma",
            "luad_tcga_pan_can_atlas_2018": "Lung Adenocarcinoma",
            "skcm_tcga_pan_can_atlas_2018": "Melanoma",
            "prad_tcga_pan_can_atlas_2018": "Prostate Cancer",
            "ov_tcga_pan_can_atlas_2018": "Ovarian Cancer",
            "coad_tcga_pan_can_atlas_2018": "Colorectal Cancer",
            "lihc_tcga_pan_can_atlas_2018": "Liver Cancer",
            "kirc_tcga_pan_can_atlas_2018": "Renal Cancer",
            "stad_tcga_pan_can_atlas_2018": "Gastric Cancer",
            "paad_tcga_pan_can_atlas_2018": "Pancreatic Cancer",
            "blca_tcga_pan_can_atlas_2018": "Bladder Cancer",
            "hnsc_tcga_pan_can_atlas_2018": "Head & Neck Cancer",
            "ucec_tcga_pan_can_atlas_2018": "Endometrial Cancer",
            "thca_tcga_pan_can_atlas_2018": "Thyroid Cancer",
        }

        all_medians = []
        max_val = 0.0
        max_cancer = ""

        for study_id, cancer_name in tcga_studies.items():
            profile_id = study_id + "_rna_seq_v2_mrna"
            expr_url = (
                f"{CBIO_BASE}/molecular-profiles/{profile_id}/molecular-data?"
                f"entrezGeneId={entrez_id}&sampleListId={study_id}_all"
            )
            data = _http_get(expr_url, timeout=15)

            if data and isinstance(data, list) and len(data) > 0:
                values = [d["value"] for d in data if d.get("value") is not None]
                if values:
                    import statistics
                    med = round(statistics.median(values), 1)
                    mn = round(statistics.mean(values), 1)
                    result["cancer_types"][cancer_name] = {
                        "median_expression": med,
                        "mean_expression": mn,
                        "sample_count": len(values),
                    }
                    all_medians.append(med)
                    if med > max_val:
                        max_val = med
                        max_cancer = cancer_name

        if result["cancer_types"]:
            result["status"] = "fetched"
            result["overall_mean_tumor"] = round(
                sum(all_medians) / len(all_medians), 1
            ) if all_medians else 0.0
            result["max_expression_cancer"] = max_cancer
            result["max_expression_value"] = max_val
        else:
            result["status"] = "no_expression_data"

        _save_cache(cache_path, result)
        return result


    # ═══════════════════════════════════════════════════════════════════════════
    # 2. GTEx — Normal tissue expression (critical for safety)
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_gtex_expression(self, gene_symbol: str) -> dict:
        """
        Fetch normal tissue expression from GTEx for a gene.

        Returns dict with:
            - gene: str
            - tissues: {tissue_name: {median_tpm, n_samples}}
            - organ_summary: {organ: mean_tpm across sub-tissues}
            - critical_organ_flags: list of organs with high expression
            - overall_mean_normal: float
            - source: "GTEx"
        """
        gene = gene_symbol.upper()
        cache_path = _cache_key("gtex", gene)
        cached = _load_cache(cache_path, self.cache_days)
        if cached:
            return cached

        result = {
            "gene": gene,
            "tissues": {},
            "organ_summary": {},
            "critical_organ_flags": [],
            "overall_mean_normal": 0.0,
            "source": "GTEx",
            "status": "pending",
        }

        # ── Step 1: Resolve versioned gencode ID via gene symbol lookup ──
        # The expression API requires versioned IDs (e.g. ENSG00000177455.12)
        # Always try the symbol lookup first — it works for ALL genes.
        gencode_id = None

        symbol_url = (
            f"{GTEX_API_BASE}/reference/gene?"
            f"geneId={gene}&datasetId=gtex_v8"
        )
        gene_data = _http_get(symbol_url)
        if gene_data and "data" in gene_data and gene_data["data"]:
            gencode_id = gene_data["data"][0].get("gencodeId", "")

        # Fallback: use static mapping (unversioned — less reliable)
        if not gencode_id:
            gencode_id = GENE_TO_ENSEMBL.get(gene)

        if not gencode_id:
            result["status"] = "gene_not_found"

        # ── Step 2: Fetch expression using resolved gencode ID ────────
        if gencode_id:
            expr_url = (
                f"{GTEX_API_BASE}/expression/medianGeneExpression?"
                f"gencodeId={gencode_id}&datasetId=gtex_v8"
            )
            data = _http_get(expr_url)

            if data and "data" in data and len(data["data"]) > 0:
                result["status"] = "fetched"
                for entry in data["data"]:
                    tissue = entry.get("tissueSiteDetailId", "Unknown")
                    median_tpm = entry.get("median", 0.0)
                    n_samples = entry.get("nSamples", 0)
                    result["tissues"][tissue] = {
                        "median_tpm": round(median_tpm, 3),
                        "n_samples": n_samples,
                    }
            else:
                result["status"] = "no_expression_data"


        # Compute organ-level summary
        for organ, tissue_list in GTEX_TISSUE_GROUPS.items():
            tpms = []
            for tissue in tissue_list:
                if tissue in result["tissues"]:
                    tpms.append(result["tissues"][tissue]["median_tpm"])
            if tpms:
                organ_mean = round(sum(tpms) / len(tpms), 3)
                result["organ_summary"][organ] = organ_mean

                # Flag critical organs with significant expression
                if organ in CRITICAL_ORGANS and organ_mean > 5.0:
                    result["critical_organ_flags"].append({
                        "organ": organ,
                        "mean_tpm": organ_mean,
                        "risk": "HIGH" if organ_mean > 15 else "MODERATE",
                    })

        # Overall mean
        all_tpms = [
            t["median_tpm"] for t in result["tissues"].values()
        ]
        result["overall_mean_normal"] = round(
            sum(all_tpms) / len(all_tpms), 3
        ) if all_tpms else 0.0

        _save_cache(cache_path, result)
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. Human Protein Atlas — Protein-level validation
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_hpa_data(self, gene_symbol: str) -> dict:
        """
        Fetch protein expression and subcellular location from Human Protein Atlas.

        Returns dict with:
            - gene: str
            - subcellular_location: list of locations
            - is_membrane: bool
            - is_secreted: bool
            - protein_class: list
            - tissue_expression: {tissue: level}
            - cancer_expression: {cancer: level}
            - source: "HPA"
        """
        gene = gene_symbol.upper()
        cache_path = _cache_key("hpa", gene)
        cached = _load_cache(cache_path, self.cache_days)
        if cached:
            return cached

        result = {
            "gene": gene,
            "subcellular_location": [],
            "is_membrane": False,
            "is_secreted": False,
            "protein_class": [],
            "tissue_expression": {},
            "cancer_expression": {},
            "antibody_validated": False,
            "source": "HPA",
            "status": "pending",
        }

        # Try fetching by gene symbol search
        search_url = (
            f"{HPA_API_BASE}/api/search_download.php?"
            f"search={gene}&format=json"
            f"&columns=g,gs,scl,pc,rnats,rnaca,ab&compress=no"
        )
        data = _http_get(search_url, timeout=45)

        if data and isinstance(data, list) and len(data) > 0:
            result["status"] = "fetched"
            entry = data[0]

            # Subcellular location
            scl = entry.get("Subcellular location", "") or ""
            if scl:
                if isinstance(scl, list):
                    locations = [str(loc).strip() for loc in scl if loc]
                else:
                    locations = [loc.strip() for loc in str(scl).split(";") if loc.strip()]
                result["subcellular_location"] = locations
                scl_text = " ".join(locations).lower()
                membrane_keywords = [
                    "cell membrane", "plasma membrane", "membrane",
                    "cell surface", "extracellular",
                ]
                result["is_membrane"] = any(
                    kw in scl_text for kw in membrane_keywords
                )
                result["is_secreted"] = "secreted" in scl_text

            # Protein class
            pc = entry.get("Protein class", "") or ""
            if pc:
                if isinstance(pc, list):
                    result["protein_class"] = [str(c).strip() for c in pc if c]
                else:
                    result["protein_class"] = [
                        c.strip() for c in str(pc).split(",") if c.strip()
                    ]

            # RNA tissue expression
            rna_ts = entry.get("RNA tissue specific nTPM", "") or ""
            if rna_ts:
                if isinstance(rna_ts, dict):
                    for tissue, val in rna_ts.items():
                        try:
                            result["tissue_expression"][tissue] = float(val)
                        except (ValueError, TypeError):
                            pass
                elif isinstance(rna_ts, list):
                    pass  # Skip if list format
                else:
                    for pair in str(rna_ts).split(";"):
                        if ":" in pair:
                            tissue, val = pair.rsplit(":", 1)
                            try:
                                result["tissue_expression"][tissue.strip()] = float(val.strip())
                            except ValueError:
                                pass

            # RNA cancer expression
            rna_ca = entry.get("RNA cancer specific FPKM", "") or ""
            if rna_ca:
                if isinstance(rna_ca, dict):
                    for cancer, val in rna_ca.items():
                        try:
                            result["cancer_expression"][cancer] = float(val)
                        except (ValueError, TypeError):
                            pass
                elif isinstance(rna_ca, list):
                    pass  # Skip if list format
                else:
                    for pair in str(rna_ca).split(";"):
                        if ":" in pair:
                            cancer, val = pair.rsplit(":", 1)
                            try:
                                result["cancer_expression"][cancer.strip()] = float(val.strip())
                            except ValueError:
                                pass

            # Antibody validation
            ab = entry.get("Antibody", "") or ""
            if isinstance(ab, list):
                result["antibody_validated"] = len(ab) > 0
            else:
                result["antibody_validated"] = bool(str(ab).strip())

        else:
            # Try direct Ensembl approach
            ensembl_id = GENE_TO_ENSEMBL.get(gene)
            if ensembl_id:
                direct_url = f"{HPA_API_BASE}/{ensembl_id}.json"
                direct_data = _http_get(direct_url, timeout=45)
                if direct_data:
                    result["status"] = "fetched"
                    # Parse direct HPA JSON format
                    if "Subcellular location" in direct_data:
                        scl_data = direct_data["Subcellular location"]
                        if isinstance(scl_data, list):
                            result["subcellular_location"] = scl_data
                        elif isinstance(scl_data, str):
                            result["subcellular_location"] = [
                                s.strip() for s in scl_data.split(";")
                            ]
                        result["is_membrane"] = any(
                            "membrane" in loc.lower() or "surface" in loc.lower()
                            for loc in result["subcellular_location"]
                        )
                else:
                    result["status"] = "unavailable"
            else:
                result["status"] = "no_ensembl_id"

        _save_cache(cache_path, result)
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. UniProt — Membrane topology and surface accessibility
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_uniprot_data(self, gene_symbol: str) -> dict:
        """
        Fetch protein data from UniProt for membrane topology and function.

        Returns dict with:
            - gene: str
            - uniprot_id: str
            - protein_name: str
            - subcellular_location: list
            - is_membrane_protein: bool
            - is_single_pass: bool
            - topology: str (e.g., "Type I membrane protein")
            - function_description: str
            - source: "UniProt"
        """
        gene = gene_symbol.upper()
        cache_path = _cache_key("uniprot", gene)
        cached = _load_cache(cache_path, self.cache_days)
        if cached:
            return cached

        result = {
            "gene": gene,
            "uniprot_id": "",
            "protein_name": "",
            "subcellular_location": [],
            "is_membrane_protein": False,
            "is_single_pass": False,
            "topology": "",
            "function_description": "",
            "molecular_mass_kda": 0.0,
            "source": "UniProt",
            "status": "pending",
        }

        # Search UniProt for the gene in human
        search_url = (
            f"{UNIPROT_API_BASE}/uniprotkb/search?"
            f"query=gene_exact:{gene}+AND+organism_id:9606+AND+reviewed:true"
            f"&format=json&size=1"
            f"&fields=accession,protein_name,cc_subcellular_location,"
            f"cc_function,ft_transmem,ft_topo_dom,mass"
        )
        data = _http_get(search_url)

        if data and "results" in data and data["results"]:
            result["status"] = "fetched"
            entry = data["results"][0]

            result["uniprot_id"] = entry.get("primaryAccession", "")

            # Protein name
            pn = entry.get("proteinDescription", {})
            rec_name = pn.get("recommendedName", {})
            if rec_name:
                full_name = rec_name.get("fullName", {})
                result["protein_name"] = full_name.get("value", "")

            # Subcellular location
            comments = entry.get("comments", [])
            for comment in comments:
                if comment.get("commentType") == "SUBCELLULAR LOCATION":
                    locs = comment.get("subcellularLocations", [])
                    for loc in locs:
                        loc_val = loc.get("location", {}).get("value", "")
                        if loc_val:
                            result["subcellular_location"].append(loc_val)
                    # Check membrane topology
                    loc_text = " ".join(result["subcellular_location"]).lower()
                    result["is_membrane_protein"] = (
                        "membrane" in loc_text
                        or "cell surface" in loc_text
                    )

                elif comment.get("commentType") == "FUNCTION":
                    texts = comment.get("texts", [])
                    if texts:
                        result["function_description"] = texts[0].get("value", "")

            # Transmembrane regions
            features = entry.get("features", [])
            transmem_count = sum(
                1 for f in features if f.get("type") == "Transmembrane"
            )
            result["is_single_pass"] = transmem_count == 1
            if transmem_count > 0:
                result["is_membrane_protein"] = True
                if transmem_count == 1:
                    result["topology"] = "Single-pass type I membrane protein"
                else:
                    result["topology"] = f"Multi-pass membrane protein ({transmem_count} TM domains)"

            # Topological domains → determine extracellular portion
            topo_domains = [
                f for f in features if f.get("type") == "Topological domain"
            ]
            for td in topo_domains:
                desc = td.get("description", "").lower()
                if "extracellular" in desc:
                    result["topology"] = result["topology"] or "Has extracellular domain"

            # Mass
            mass_str = entry.get("sequence", {}).get("molWeight", 0)
            if mass_str:
                result["molecular_mass_kda"] = round(int(mass_str) / 1000, 1)

        else:
            result["status"] = "not_found"

        _save_cache(cache_path, result)
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. ClinicalTrials.gov — CAR-T clinical trial data
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_clinical_trials(self, gene_symbol: str) -> dict:
        """
        Fetch CAR-T related clinical trial data from ClinicalTrials.gov.

        Returns dict with:
            - gene: str
            - total_trials: int
            - car_t_trials: int
            - phase_distribution: {phase: count}
            - status_distribution: {status: count}
            - recent_trials: list of recent trial summaries
            - source: "ClinicalTrials.gov"
        """
        gene = gene_symbol.upper()
        cache_path = _cache_key("ctgov", gene)
        cached = _load_cache(cache_path, self.cache_days)
        if cached:
            return cached

        result = {
            "gene": gene,
            "total_trials": 0,
            "car_t_trials": 0,
            "phase_distribution": {},
            "status_distribution": {},
            "recent_trials": [],
            "source": "ClinicalTrials.gov",
            "status": "pending",
        }

        # Search for CAR-T trials specifically targeting this antigen
        # Must include BOTH gene name AND CAR-T terminology
        gene_aliases = {
            "BCMA": "BCMA OR TNFRSF17",
            "GD2": "GD2 OR B4GALNT1",
            "PSMA": "PSMA OR FOLH1",
            "CD138": "CD138 OR SDC1",
            "CD20": "CD20 OR MS4A1",
            "CD123": "CD123 OR IL3RA",
            "B7H3": "B7-H3 OR CD276",
            "CLDN18.2": "Claudin 18.2 OR CLDN18",
            "PDL1": "PD-L1 OR CD274",
            "PD1": "PD-1 OR PDCD1",
        }
        gene_term = gene_aliases.get(gene, gene)

        # Primary search: gene + CAR-T specific
        search_terms = f'({gene_term}) AND (CAR-T OR "CAR T" OR "chimeric antigen receptor" OR "CAR cell")'
        encoded = urllib.parse.quote(search_terms)
        url = (
            f"{CLINICAL_TRIALS_BASE}/studies?"
            f"query.term={encoded}"
            f"&pageSize=50&format=json"
        )
        data = _http_get(url, timeout=30)

        if data and "studies" in data:
            result["status"] = "fetched"
            studies = data["studies"]
            result["total_trials"] = len(studies)

            # Count CAR-T specific trials
            car_t_keywords = [
                "car-t", "car t", "chimeric antigen receptor",
                "cart cell", "car-modified",
            ]

            for study in studies:
                protocol = study.get("protocolSection", {})
                id_module = protocol.get("identificationModule", {})
                status_module = protocol.get("statusModule", {})
                design_module = protocol.get("designModule", {})

                title = (id_module.get("briefTitle", "") or "").lower()
                official_title = (id_module.get("officialTitle", "") or "").lower()
                combined = title + " " + official_title

                is_cart = any(kw in combined for kw in car_t_keywords)
                if is_cart:
                    result["car_t_trials"] += 1

                # Phase distribution
                phases = design_module.get("phases", [])
                for phase in phases:
                    result["phase_distribution"][phase] = (
                        result["phase_distribution"].get(phase, 0) + 1
                    )

                # Status distribution
                overall_status = status_module.get("overallStatus", "Unknown")
                result["status_distribution"][overall_status] = (
                    result["status_distribution"].get(overall_status, 0) + 1
                )

                # Save recent trial summaries (first 10)
                if len(result["recent_trials"]) < 10:
                    result["recent_trials"].append({
                        "nct_id": id_module.get("nctId", ""),
                        "title": id_module.get("briefTitle", ""),
                        "status": overall_status,
                        "phases": phases,
                    })
        else:
            result["status"] = "unavailable"

        _save_cache(cache_path, result)
        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # Unified fetch — all sources for one gene
    # ═══════════════════════════════════════════════════════════════════════════

    def fetch_all(self, gene_symbol: str) -> dict:
        """
        Fetch data from ALL 5 sources for a given gene.

        Returns a unified dict with keys: tcga, gtex, hpa, uniprot, clinical_trials
        """
        gene = gene_symbol.upper()
        return {
            "gene": gene,
            "tcga": self.fetch_tcga_expression(gene),
            "gtex": self.fetch_gtex_expression(gene),
            "hpa": self.fetch_hpa_data(gene),
            "uniprot": self.fetch_uniprot_data(gene),
            "clinical_trials": self.fetch_clinical_trials(gene),
        }

    def fetch_batch(self, gene_symbols: list, delay: float = 0.5) -> dict:
        """
        Fetch data for multiple genes with rate-limiting delay.

        Returns: {gene_symbol: fetch_all_result}
        """
        results = {}
        total = len(gene_symbols)
        for i, gene in enumerate(gene_symbols, 1):
            print(f"  [{i}/{total}] Fetching {gene}...")
            results[gene] = self.fetch_all(gene)
            if i < total:
                time.sleep(delay)  # Rate limiting
        return results


# ─── Module-level convenience ───────────────────────────────────────────────────
_fetcher = None


def get_fetcher() -> RealDataFetcher:
    """Get or create the singleton fetcher instance."""
    global _fetcher
    if _fetcher is None:
        _fetcher = RealDataFetcher()
    return _fetcher


if __name__ == "__main__":
    print("CARVanta Real Data Fetcher")
    print("=" * 50)

    fetcher = RealDataFetcher()

    # Test with CD19 (most well-known CAR-T target)
    print("\nFetching CD19 data from all 5 sources...")
    result = fetcher.fetch_all("CD19")

    for source, data in result.items():
        if source == "gene":
            continue
        status = data.get("status", "unknown") if isinstance(data, dict) else "N/A"
        print(f"  {source}: {status}")

    print("\nDone! Cache saved to data/cache/")
