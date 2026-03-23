"""
CARVanta – Gene Notation Standards Module v1
===============================================
Maps antigen common names to standardized identifiers:
HUGO gene symbols, NCBI Gene IDs, UniProt accession numbers,
and Ensembl Gene IDs.

CARVanta-Original: Standardized gene nomenclature for interoperability.

Usage:
    from features.notation_standards import get_gene_identifiers
    ids = get_gene_identifiers("CD19")
"""


# ─── Gene identifier mapping ────────────────────────────────────────────────────
# Sources: HUGO Gene Nomenclature Committee, NCBI Gene, UniProt, Ensembl
GENE_IDENTIFIERS = {
    "CD19": {
        "hugo_symbol": "CD19",
        "hugo_name": "CD19 molecule",
        "ncbi_gene_id": 930,
        "uniprot_id": "P15391",
        "ensembl_gene_id": "ENSG00000177455",
        "chromosome": "16p11.2",
        "aliases": ["B4", "CVID3"],
    },
    "BCMA": {
        "hugo_symbol": "TNFRSF17",
        "hugo_name": "TNF receptor superfamily member 17",
        "ncbi_gene_id": 608,
        "uniprot_id": "Q02223",
        "ensembl_gene_id": "ENSG00000048462",
        "chromosome": "16p13.13",
        "aliases": ["BCM", "CD269", "TNFRSF13A"],
    },
    "CD22": {
        "hugo_symbol": "CD22",
        "hugo_name": "CD22 molecule",
        "ncbi_gene_id": 933,
        "uniprot_id": "P20273",
        "ensembl_gene_id": "ENSG00000012124",
        "chromosome": "19q13.12",
        "aliases": ["SIGLEC-2", "SIGLEC2"],
    },
    "HER2": {
        "hugo_symbol": "ERBB2",
        "hugo_name": "erb-b2 receptor tyrosine kinase 2",
        "ncbi_gene_id": 2064,
        "uniprot_id": "P04626",
        "ensembl_gene_id": "ENSG00000141736",
        "chromosome": "17q12",
        "aliases": ["HER2", "NEU", "NGL", "CD340"],
    },
    "EGFR": {
        "hugo_symbol": "EGFR",
        "hugo_name": "epidermal growth factor receptor",
        "ncbi_gene_id": 1956,
        "uniprot_id": "P00533",
        "ensembl_gene_id": "ENSG00000146648",
        "chromosome": "7p11.2",
        "aliases": ["ERBB", "ERBB1", "HER1"],
    },
    "CD20": {
        "hugo_symbol": "MS4A1",
        "hugo_name": "membrane spanning 4-domains A1",
        "ncbi_gene_id": 931,
        "uniprot_id": "P11836",
        "ensembl_gene_id": "ENSG00000156738",
        "chromosome": "11q12.2",
        "aliases": ["B1", "Bp35", "CD20", "LEU-16"],
    },
    "CD33": {
        "hugo_symbol": "CD33",
        "hugo_name": "CD33 molecule",
        "ncbi_gene_id": 945,
        "uniprot_id": "P20138",
        "ensembl_gene_id": "ENSG00000105383",
        "chromosome": "19q13.41",
        "aliases": ["SIGLEC-3", "SIGLEC3", "p67"],
    },
    "CD38": {
        "hugo_symbol": "CD38",
        "hugo_name": "CD38 molecule",
        "ncbi_gene_id": 952,
        "uniprot_id": "P28907",
        "ensembl_gene_id": "ENSG00000004468",
        "chromosome": "4p15.32",
        "aliases": ["ADPRC1", "T10"],
    },
    "PSMA": {
        "hugo_symbol": "FOLH1",
        "hugo_name": "folate hydrolase 1",
        "ncbi_gene_id": 2346,
        "uniprot_id": "Q04609",
        "ensembl_gene_id": "ENSG00000086205",
        "chromosome": "11p11.12",
        "aliases": ["FOLH", "GCPII", "GCP2", "NAALAD1", "PSM", "PSMA"],
    },
    "GD2": {
        "hugo_symbol": "B4GALNT1",
        "hugo_name": "beta-1,4-N-acetyl-galactosaminyltransferase 1",
        "ncbi_gene_id": 2583,
        "uniprot_id": "Q00973",
        "ensembl_gene_id": "ENSG00000135226",
        "chromosome": "12q13.3",
        "aliases": ["GALGT", "GalNAc-T", "GM2/GD2 synthase"],
    },
    "MESOTHELIN": {
        "hugo_symbol": "MSLN",
        "hugo_name": "mesothelin",
        "ncbi_gene_id": 10232,
        "uniprot_id": "Q13421",
        "ensembl_gene_id": "ENSG00000100326",
        "chromosome": "16p13.3",
        "aliases": ["MPF", "MSLN", "SMRP"],
    },
    "GPRC5D": {
        "hugo_symbol": "GPRC5D",
        "hugo_name": "G protein-coupled receptor class C group 5 member D",
        "ncbi_gene_id": 55507,
        "uniprot_id": "Q9NZD1",
        "ensembl_gene_id": "ENSG00000111291",
        "chromosome": "12p13.3",
        "aliases": [],
    },
    "CD70": {
        "hugo_symbol": "CD70",
        "hugo_name": "CD70 molecule",
        "ncbi_gene_id": 970,
        "uniprot_id": "P32970",
        "ensembl_gene_id": "ENSG00000125726",
        "chromosome": "19p13.3",
        "aliases": ["CD27L", "CD27LG", "TNFSF7"],
    },
    "ROR1": {
        "hugo_symbol": "ROR1",
        "hugo_name": "receptor tyrosine kinase like orphan receptor 1",
        "ncbi_gene_id": 4919,
        "uniprot_id": "Q01973",
        "ensembl_gene_id": "ENSG00000185483",
        "chromosome": "1p31.3",
        "aliases": ["NTRKR1"],
    },
    "DLL3": {
        "hugo_symbol": "DLL3",
        "hugo_name": "delta like canonical Notch ligand 3",
        "ncbi_gene_id": 10683,
        "uniprot_id": "Q9NYJ7",
        "ensembl_gene_id": "ENSG00000090932",
        "chromosome": "19q13.2",
        "aliases": ["SCDO1"],
    },
    "MUC1": {
        "hugo_symbol": "MUC1",
        "hugo_name": "mucin 1, cell surface associated",
        "ncbi_gene_id": 4582,
        "uniprot_id": "P15941",
        "ensembl_gene_id": "ENSG00000185499",
        "chromosome": "1q22",
        "aliases": ["PEM", "PEMT", "EMA", "CD227"],
    },
    "FLT3": {
        "hugo_symbol": "FLT3",
        "hugo_name": "fms related receptor tyrosine kinase 3",
        "ncbi_gene_id": 2322,
        "uniprot_id": "P36888",
        "ensembl_gene_id": "ENSG00000122025",
        "chromosome": "13q12.2",
        "aliases": ["CD135", "FLK2", "STK1"],
    },
    "GPC3": {
        "hugo_symbol": "GPC3",
        "hugo_name": "glypican 3",
        "ncbi_gene_id": 2719,
        "uniprot_id": "P51654",
        "ensembl_gene_id": "ENSG00000147257",
        "chromosome": "Xq26.2",
        "aliases": ["DGSX", "SDYS", "SGB", "SGBS"],
    },
    "FOLR1": {
        "hugo_symbol": "FOLR1",
        "hugo_name": "folate receptor alpha",
        "ncbi_gene_id": 2348,
        "uniprot_id": "P15328",
        "ensembl_gene_id": "ENSG00000110195",
        "chromosome": "11q13.4",
        "aliases": ["FBP", "FOLR", "MOv18"],
    },
    "CLDN18": {
        "hugo_symbol": "CLDN18",
        "hugo_name": "claudin 18",
        "ncbi_gene_id": 51208,
        "uniprot_id": "P56856",
        "ensembl_gene_id": "ENSG00000066405",
        "chromosome": "3q22.3",
        "aliases": ["SFTA5"],
    },
}


def get_gene_identifiers(antigen_name: str) -> dict:
    """
    Get standardized gene identifiers for an antigen.

    Returns HUGO symbol, NCBI Gene ID, UniProt ID, Ensembl ID.
    """
    antigen = antigen_name.upper()
    data = GENE_IDENTIFIERS.get(antigen, None)

    if data is None:
        # Try to find by alias
        for key, entry in GENE_IDENTIFIERS.items():
            if antigen in [a.upper() for a in entry.get("aliases", [])]:
                return {"antigen": antigen, "matched_to": key, **entry}

        return {
            "antigen": antigen,
            "has_identifiers": False,
            "hugo_symbol": antigen,
            "hugo_name": None,
            "ncbi_gene_id": None,
            "uniprot_id": None,
            "ensembl_gene_id": None,
            "external_links": {
                "ncbi_search": f"https://www.ncbi.nlm.nih.gov/gene/?term={antigen}",
                "uniprot_search": f"https://www.uniprot.org/uniprot/?query={antigen}+AND+organism_id:9606",
            },
        }

    return {
        "antigen": antigen,
        "has_identifiers": True,
        **data,
        "external_links": {
            "ncbi_gene": f"https://www.ncbi.nlm.nih.gov/gene/{data['ncbi_gene_id']}",
            "uniprot": f"https://www.uniprot.org/uniprot/{data['uniprot_id']}",
            "ensembl": f"https://www.ensembl.org/Homo_sapiens/Gene/Summary?g={data['ensembl_gene_id']}",
            "hugo": f"https://www.genenames.org/data/gene-symbol-report/#!/symbol/{data['hugo_symbol']}",
        },
    }


def get_all_gene_identifiers() -> dict:
    """Return all catalogued gene identifiers."""
    return {
        "total": len(GENE_IDENTIFIERS),
        "genes": {
            k: {
                "hugo_symbol": v["hugo_symbol"],
                "ncbi_gene_id": v["ncbi_gene_id"],
                "uniprot_id": v["uniprot_id"],
            }
            for k, v in GENE_IDENTIFIERS.items()
        },
    }
