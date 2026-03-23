"""
CARVanta – IP Landscape Module v1
====================================
Curated patent and intellectual property data for CAR-T target antigens.
Shows which antigens have existing patents that may affect development.

CARVanta-Original: Patent landscape intelligence.

Usage:
    from features.ip_landscape import get_patent_landscape
    result = get_patent_landscape("CD19")
"""


# ─── Curated patent data ────────────────────────────────────────────────────────
# Sources: USPTO, EPO, Google Patents (public summaries)
PATENT_DATA = {
    "CD19": {
        "total_patents": 85,
        "key_patents": [
            {
                "id": "US10,221,245",
                "title": "Anti-CD19 CAR constructs and methods",
                "assignee": "Novartis AG",
                "year": 2019,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Covers specific scFv-based CAR constructs targeting CD19 with 4-1BB co-stimulatory domain.",
            },
            {
                "id": "US10,357,514",
                "title": "CD19-directed CAR-T cell therapy (Kymriah)",
                "assignee": "Novartis AG / UPenn",
                "year": 2019,
                "status": "active",
                "type": "method_of_treatment",
                "summary": "Method patent covering tisagenlecleucel manufacturing and administration.",
            },
            {
                "id": "US9,855,298",
                "title": "Anti-CD19 CAR with CD28 co-stimulation",
                "assignee": "Kite Pharma (Gilead)",
                "year": 2018,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Covers axicabtagene ciloleucel (Yescarta) CAR construct with CD28 domain.",
            },
        ],
        "freedom_to_operate": "limited",
        "patent_cliff_year": 2035,
        "recommendation": "CD19 CAR-T space is heavily patented. Novel scFv or co-stimulatory designs may offer FTO.",
    },
    "BCMA": {
        "total_patents": 62,
        "key_patents": [
            {
                "id": "US10,294,304",
                "title": "BCMA-targeting CAR constructs",
                "assignee": "Celgene (BMS)",
                "year": 2019,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Covers idecabtagene vicleucel (Abecma) anti-BCMA CAR.",
            },
            {
                "id": "US11,124,577",
                "title": "Dual-targeting BCMA/CD38 CAR",
                "assignee": "Janssen (J&J)",
                "year": 2021,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Dual-antigen CAR construct for enhanced myeloma killing.",
            },
        ],
        "freedom_to_operate": "limited",
        "patent_cliff_year": 2037,
        "recommendation": "BCMA is the most competitive CAR-T target in myeloma. Consider bispecific or novel epitope approaches.",
    },
    "HER2": {
        "total_patents": 120,
        "key_patents": [
            {
                "id": "US6,165,464",
                "title": "Anti-HER2 antibody compositions (Herceptin)",
                "assignee": "Genentech (Roche)",
                "year": 2000,
                "status": "expired",
                "type": "composition_of_matter",
                "summary": "Original trastuzumab patent — now expired. CAR-T using this scFv has more FTO.",
            },
        ],
        "freedom_to_operate": "moderate",
        "patent_cliff_year": 2020,
        "recommendation": "Core Herceptin patents expired. HER2 CAR-T has moderate FTO but safety concerns (on-target/off-tumor) are the main barrier.",
    },
    "CD20": {
        "total_patents": 45,
        "key_patents": [
            {
                "id": "US5,736,137",
                "title": "Anti-CD20 antibody (Rituximab)",
                "assignee": "Genentech / Biogen IDEC",
                "year": 1998,
                "status": "expired",
                "type": "composition_of_matter",
                "summary": "Original rituximab patent — expired. CD20 CAR-T derivatives have good FTO.",
            },
        ],
        "freedom_to_operate": "good",
        "patent_cliff_year": 2015,
        "recommendation": "CD20 patent landscape is favorable for new CAR-T entrants. Core antibody patents expired.",
    },
    "EGFR": {
        "total_patents": 95,
        "key_patents": [
            {
                "id": "US7,060,808",
                "title": "EGFRvIII-specific CAR constructs",
                "assignee": "Duke University",
                "year": 2006,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Covers CAR constructs specifically targeting the EGFRvIII mutation variant.",
            },
        ],
        "freedom_to_operate": "moderate",
        "patent_cliff_year": 2026,
        "recommendation": "Wild-type EGFR CAR-T faces safety issues. EGFRvIII-specific approaches are patented but expiring soon.",
    },
    "PSMA": {
        "total_patents": 35,
        "key_patents": [
            {
                "id": "US10,640,569",
                "title": "PSMA-targeting CAR-T cells for prostate cancer",
                "assignee": "Memorial Sloan Kettering",
                "year": 2020,
                "status": "active",
                "type": "method_of_treatment",
                "summary": "Method patent for PSMA CAR-T in metastatic prostate cancer.",
            },
        ],
        "freedom_to_operate": "moderate",
        "patent_cliff_year": 2038,
        "recommendation": "PSMA CAR-T landscape is growing. Novel scFv designs or combination approaches may provide differentiation.",
    },
    "GD2": {
        "total_patents": 28,
        "key_patents": [
            {
                "id": "US9,745,368",
                "title": "GD2-targeting CAR with enhanced persistence",
                "assignee": "Baylor College of Medicine",
                "year": 2017,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "Enhanced GD2 CAR with IL-15 co-expression for pediatric neuroblastoma.",
            },
        ],
        "freedom_to_operate": "good",
        "patent_cliff_year": 2035,
        "recommendation": "GD2 CAR-T space is less crowded than CD19/BCMA. Academic institutions hold key patents.",
    },
    "CD38": {
        "total_patents": 40,
        "key_patents": [
            {
                "id": "US10,793,632",
                "title": "CD38-knockout CAR-T to prevent fratricide",
                "assignee": "Cellectis",
                "year": 2020,
                "status": "active",
                "type": "method_of_treatment",
                "summary": "Gene-edited CAR-T with CD38 knocked out to survive anti-CD38 antibody environment.",
            },
        ],
        "freedom_to_operate": "limited",
        "patent_cliff_year": 2038,
        "recommendation": "CD38 CAR-T requires gene editing to prevent fratricide. Key engineering patents are active.",
    },
    "MESOTHELIN": {
        "total_patents": 30,
        "key_patents": [
            {
                "id": "US9,394,368",
                "title": "Anti-mesothelin CAR constructs",
                "assignee": "University of Pennsylvania",
                "year": 2016,
                "status": "active",
                "type": "composition_of_matter",
                "summary": "CAR constructs using SS1 scFv targeting mesothelin in pancreatic/ovarian cancer.",
            },
        ],
        "freedom_to_operate": "moderate",
        "patent_cliff_year": 2034,
        "recommendation": "Mesothelin CAR-T is actively investigated for solid tumors. Novel targeting moieties may improve FTO.",
    },
}


def get_patent_landscape(antigen_name: str) -> dict:
    """
    Get patent landscape data for a given antigen.

    Returns patent count, key patents, freedom-to-operate assessment,
    and strategic recommendations.
    """
    antigen = antigen_name.upper()
    data = PATENT_DATA.get(antigen, None)

    if data is None:
        return {
            "antigen": antigen,
            "has_patents": False,
            "total_patents": 0,
            "key_patents": [],
            "freedom_to_operate": "uncharted",
            "patent_cliff_year": None,
            "recommendation": (
                f"No patent data catalogued for {antigen}. This may indicate "
                f"a novel target with open IP landscape — advantageous for new entrants."
            ),
        }

    return {
        "antigen": antigen,
        "has_patents": True,
        **data,
    }


def get_all_patent_summaries() -> dict:
    """Return a summary of all catalogued antigen patent landscapes."""
    summaries = {}
    for antigen, data in PATENT_DATA.items():
        summaries[antigen] = {
            "total_patents": data["total_patents"],
            "freedom_to_operate": data["freedom_to_operate"],
            "patent_cliff_year": data["patent_cliff_year"],
        }
    return {
        "total_antigens_catalogued": len(PATENT_DATA),
        "antigens": summaries,
    }
