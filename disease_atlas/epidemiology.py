"""
CARVanta Disease Atlas — Global Epidemiology & Treatment Landscape
===================================================================
Comprehensive database of cancer epidemiology and treatment patterns
with focus on cell therapy-eligible hematologic malignancies.

Features:
- Incidence and prevalence by country, region, cancer type
- Age-standardized rates (ASR)
- Treatment line distribution and relapse rates
- CAR-T eligible patient estimation per market
- Survival data (OS, PFS) by disease and line of therapy
- Treatment landscape mapping (approved therapies per indication)
- Competitive intelligence (pipeline therapies)
- Global burden of disease metrics

Data: Based on GLOBOCAN 2022, SEER, Eurostat, IARC, and published
disease registries. Simplified for demonstration.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.disease_atlas.epidemiology")


# ──────────────────────────────────────────────────────────────────────
# Disease Database
# ──────────────────────────────────────────────────────────────────────

@dataclass
class DiseaseProfile:
    disease_id: str
    name: str
    icd10: str
    category: str  # "hematologic", "solid"
    subcategory: str
    global_incidence: int  # annual new cases
    global_prevalence: int
    median_age_diagnosis: int
    male_female_ratio: float
    five_year_survival: float
    cell_therapy_eligible_pct: float  # % of patients potentially eligible
    approved_cart_products: List[str] = field(default_factory=list)
    key_targets: List[str] = field(default_factory=list)
    regions: Dict[str, Dict[str, int]] = field(default_factory=dict)  # region -> {incidence, prevalence}

_DISEASES: Dict[str, DiseaseProfile] = {
    "dlbcl": DiseaseProfile(
        "dlbcl", "Diffuse Large B-Cell Lymphoma", "C83.3", "hematologic", "NHL",
        150000, 350000, 64, 1.2, 0.64, 0.25,
        ["Yescarta", "Kymriah", "Breyanzi", "Tecartus"],
        ["CD19", "CD20", "CD79b"],
        {"North America": {"incidence": 28000, "prevalence": 72000},
         "Europe": {"incidence": 35000, "prevalence": 85000},
         "Asia-Pacific": {"incidence": 55000, "prevalence": 120000},
         "Latin America": {"incidence": 15000, "prevalence": 35000},
         "MENA": {"incidence": 8000, "prevalence": 18000},
         "Africa": {"incidence": 9000, "prevalence": 20000}},
    ),
    "all": DiseaseProfile(
        "all", "Acute Lymphoblastic Leukemia", "C91.0", "hematologic", "Leukemia",
        75000, 110000, 15, 1.3, 0.90, 0.15,
        ["Kymriah", "Tecartus"],
        ["CD19", "CD22", "CD38"],
        {"North America": {"incidence": 6000, "prevalence": 12000},
         "Europe": {"incidence": 8500, "prevalence": 15000},
         "Asia-Pacific": {"incidence": 42000, "prevalence": 55000},
         "Latin America": {"incidence": 10000, "prevalence": 14000},
         "MENA": {"incidence": 5000, "prevalence": 7000},
         "Africa": {"incidence": 3500, "prevalence": 7000}},
    ),
    "multiple_myeloma": DiseaseProfile(
        "multiple_myeloma", "Multiple Myeloma", "C90.0", "hematologic", "Plasma Cell",
        176000, 480000, 69, 1.4, 0.55, 0.20,
        ["Abecma", "Carvykti"],
        ["BCMA", "GPRC5D", "FcRH5", "CD38"],
        {"North America": {"incidence": 35000, "prevalence": 115000},
         "Europe": {"incidence": 42000, "prevalence": 120000},
         "Asia-Pacific": {"incidence": 65000, "prevalence": 155000},
         "Latin America": {"incidence": 16000, "prevalence": 40000},
         "MENA": {"incidence": 9000, "prevalence": 25000},
         "Africa": {"incidence": 9000, "prevalence": 25000}},
    ),
    "fl": DiseaseProfile(
        "fl", "Follicular Lymphoma", "C82", "hematologic", "NHL",
        120000, 600000, 63, 0.9, 0.89, 0.10,
        ["Yescarta"],
        ["CD19", "CD20"],
        {"North America": {"incidence": 22000, "prevalence": 130000},
         "Europe": {"incidence": 30000, "prevalence": 150000},
         "Asia-Pacific": {"incidence": 40000, "prevalence": 200000},
         "Latin America": {"incidence": 12000, "prevalence": 55000},
         "MENA": {"incidence": 8000, "prevalence": 30000},
         "Africa": {"incidence": 8000, "prevalence": 35000}},
    ),
    "cll": DiseaseProfile(
        "cll", "Chronic Lymphocytic Leukemia", "C91.1", "hematologic", "Leukemia",
        190000, 900000, 72, 1.7, 0.87, 0.05,
        [],
        ["CD19", "CD20", "BTK"],
        {"North America": {"incidence": 21000, "prevalence": 180000},
         "Europe": {"incidence": 50000, "prevalence": 300000},
         "Asia-Pacific": {"incidence": 70000, "prevalence": 250000},
         "Latin America": {"incidence": 20000, "prevalence": 65000},
         "MENA": {"incidence": 15000, "prevalence": 50000},
         "Africa": {"incidence": 14000, "prevalence": 55000}},
    ),
    "mcl": DiseaseProfile(
        "mcl", "Mantle Cell Lymphoma", "C83.1", "hematologic", "NHL",
        25000, 55000, 68, 2.5, 0.60, 0.30,
        ["Tecartus"],
        ["CD19", "CD20"],
        {"North America": {"incidence": 5000, "prevalence": 12000},
         "Europe": {"incidence": 7000, "prevalence": 15000},
         "Asia-Pacific": {"incidence": 8000, "prevalence": 17000},
         "Latin America": {"incidence": 2500, "prevalence": 5000},
         "MENA": {"incidence": 1200, "prevalence": 3000},
         "Africa": {"incidence": 1300, "prevalence": 3000}},
    ),
}

# Treatment landscape data
_TREATMENT_LINES: Dict[str, List[Dict[str, Any]]] = {
    "dlbcl": [
        {"line": "1L", "regimen": "R-CHOP", "orr": 0.82, "cr_rate": 0.65, "median_pfs_months": 36, "standard": True},
        {"line": "2L", "regimen": "R-ICE / R-DHAP", "orr": 0.63, "cr_rate": 0.26, "median_pfs_months": 10},
        {"line": "2L", "regimen": "Polatuzumab + BR", "orr": 0.45, "cr_rate": 0.40, "median_pfs_months": 8},
        {"line": "3L+", "regimen": "Axi-cel (Yescarta)", "orr": 0.83, "cr_rate": 0.58, "median_pfs_months": 15, "cart": True},
        {"line": "3L+", "regimen": "Tisa-cel (Kymriah)", "orr": 0.52, "cr_rate": 0.40, "median_pfs_months": 6, "cart": True},
        {"line": "3L+", "regimen": "Liso-cel (Breyanzi)", "orr": 0.73, "cr_rate": 0.53, "median_pfs_months": 14, "cart": True},
        {"line": "3L+", "regimen": "Glofitamab", "orr": 0.56, "cr_rate": 0.39, "median_pfs_months": 5},
        {"line": "3L+", "regimen": "Loncastuximab tesirine", "orr": 0.48, "cr_rate": 0.24, "median_pfs_months": 5},
    ],
    "all": [
        {"line": "1L", "regimen": "Hyper-CVAD", "orr": 0.93, "cr_rate": 0.80, "median_pfs_months": 24, "standard": True},
        {"line": "2L+", "regimen": "Blinatumomab", "orr": 0.44, "cr_rate": 0.34, "median_pfs_months": 7},
        {"line": "2L+", "regimen": "Inotuzumab", "orr": 0.81, "cr_rate": 0.36, "median_pfs_months": 5},
        {"line": "2L+", "regimen": "Tisa-cel (Kymriah)", "orr": 0.81, "cr_rate": 0.60, "median_pfs_months": 18, "cart": True},
    ],
    "multiple_myeloma": [
        {"line": "1L", "regimen": "VRd (Bortezomib/Lenalidomide/Dex)", "orr": 0.93, "cr_rate": 0.42, "median_pfs_months": 36, "standard": True},
        {"line": "2L", "regimen": "Carfilzomib/Dex", "orr": 0.77, "cr_rate": 0.32, "median_pfs_months": 19},
        {"line": "3L", "regimen": "Daratumumab/Pomalidomide/Dex", "orr": 0.60, "cr_rate": 0.18, "median_pfs_months": 12},
        {"line": "4L+", "regimen": "Ide-cel (Abecma)", "orr": 0.73, "cr_rate": 0.33, "median_pfs_months": 9, "cart": True},
        {"line": "4L+", "regimen": "Cilta-cel (Carvykti)", "orr": 0.98, "cr_rate": 0.83, "median_pfs_months": 34, "cart": True},
        {"line": "4L+", "regimen": "Teclistamab", "orr": 0.63, "cr_rate": 0.39, "median_pfs_months": 11},
    ],
}

# Pipeline therapies
_PIPELINE: List[Dict[str, Any]] = [
    {"target": "CD19", "company": "Kite/Gilead", "product": "Axi-cel 2L", "phase": "Phase 3", "indication": "DLBCL 2L", "status": "Approved"},
    {"target": "BCMA", "company": "J&J/Legend", "product": "Cilta-cel 2L", "phase": "Phase 3", "indication": "MM earlier lines", "status": "Recruiting"},
    {"target": "GPRC5D", "company": "MSK/Eureka", "product": "GPRC5D CAR-T", "phase": "Phase 1/2", "indication": "Post-BCMA myeloma", "status": "Recruiting"},
    {"target": "CD22", "company": "NCI", "product": "CD22 CAR-T", "phase": "Phase 1", "indication": "CD19- relapsed ALL", "status": "Recruiting"},
    {"target": "CD19/CD22", "company": "NCI", "product": "Bispecific CAR-T", "phase": "Phase 1/2", "indication": "B-ALL", "status": "Recruiting"},
    {"target": "GPC3", "company": "Multiple", "product": "GPC3 CAR-T", "phase": "Phase 1", "indication": "HCC", "status": "Recruiting"},
    {"target": "Claudin 18.2", "company": "CARsgen", "product": "CT041", "phase": "Phase 2", "indication": "Gastric cancer", "status": "Active"},
    {"target": "DLL3", "company": "Regeneron", "product": "DLL3 CAR-T", "phase": "Phase 1", "indication": "SCLC", "status": "Recruiting"},
    {"target": "PSMA", "company": "UPenn", "product": "PSMA-TGFβDN CAR-T", "phase": "Phase 1", "indication": "Prostate cancer", "status": "Active"},
    {"target": "CD7", "company": "Gracell", "product": "GC027", "phase": "Phase 1", "indication": "T-ALL", "status": "Recruiting"},
    {"target": "NKG2D", "company": "Celyad", "product": "CYAD-01", "phase": "Phase 1", "indication": "AML", "status": "Active"},
    {"target": "Mesothelin", "company": "MSKCC", "product": "Meso CAR-T + ICB", "phase": "Phase 1/2", "indication": "Mesothelioma", "status": "Recruiting"},
]


# ──────────────────────────────────────────────────────────────────────
# Query Functions
# ──────────────────────────────────────────────────────────────────────

async def get_disease_profile(disease_id: str) -> Optional[Dict[str, Any]]:
    """Get comprehensive disease profile."""
    d = _DISEASES.get(disease_id)
    if not d:
        return None
    eligible = int(d.global_incidence * d.cell_therapy_eligible_pct)
    return {
        "disease_id": d.disease_id, "name": d.name, "icd10": d.icd10,
        "category": d.category, "subcategory": d.subcategory,
        "global_incidence": d.global_incidence,
        "global_prevalence": d.global_prevalence,
        "median_age": d.median_age_diagnosis,
        "male_female_ratio": d.male_female_ratio,
        "five_year_survival": d.five_year_survival,
        "cell_therapy_eligible_pct": d.cell_therapy_eligible_pct,
        "estimated_eligible_patients": eligible,
        "approved_cart": d.approved_cart_products,
        "key_targets": d.key_targets,
        "regions": d.regions,
    }


async def list_diseases(
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """List all diseases."""
    results = []
    for d in _DISEASES.values():
        if category and d.category != category:
            continue
        eligible = int(d.global_incidence * d.cell_therapy_eligible_pct)
        results.append({
            "disease_id": d.disease_id, "name": d.name, "category": d.category,
            "incidence": d.global_incidence, "prevalence": d.global_prevalence,
            "five_year_survival": d.five_year_survival,
            "eligible_patients": eligible,
            "approved_cart_count": len(d.approved_cart_products),
            "key_targets": d.key_targets[:3],
        })
    return {"total": len(results), "diseases": results}


async def get_treatment_landscape(disease_id: str) -> Dict[str, Any]:
    """Get treatment options by line of therapy."""
    lines = _TREATMENT_LINES.get(disease_id, [])
    disease = _DISEASES.get(disease_id)
    return {
        "disease_id": disease_id,
        "disease_name": disease.name if disease else disease_id,
        "treatment_lines": lines,
        "cart_options": [l for l in lines if l.get("cart")],
        "total_options": len(lines),
    }


async def get_regional_data(
    disease_id: str, region: Optional[str] = None,
) -> Dict[str, Any]:
    """Get regional epidemiology data."""
    d = _DISEASES.get(disease_id)
    if not d:
        return {"error": "Disease not found"}
    if region and region in d.regions:
        return {"disease": d.name, "region": region, "data": d.regions[region]}
    return {"disease": d.name, "regions": d.regions}


async def get_pipeline(
    target: Optional[str] = None,
    indication: Optional[str] = None,
) -> Dict[str, Any]:
    """Get cell therapy pipeline."""
    results = _PIPELINE
    if target:
        results = [p for p in results if target.lower() in p["target"].lower()]
    if indication:
        results = [p for p in results if indication.lower() in p["indication"].lower()]
    return {"total": len(results), "pipeline": results}


async def get_global_summary() -> Dict[str, Any]:
    """Get global disease atlas summary."""
    total_incidence = sum(d.global_incidence for d in _DISEASES.values())
    total_prevalence = sum(d.global_prevalence for d in _DISEASES.values())
    total_eligible = sum(int(d.global_incidence * d.cell_therapy_eligible_pct) for d in _DISEASES.values())
    all_targets = set()
    for d in _DISEASES.values():
        all_targets.update(d.key_targets)

    return {
        "diseases_tracked": len(_DISEASES),
        "total_annual_incidence": total_incidence,
        "total_prevalence": total_prevalence,
        "total_cart_eligible": total_eligible,
        "approved_cart_products": 6,
        "pipeline_entries": len(_PIPELINE),
        "unique_targets": len(all_targets),
        "regions": ["North America", "Europe", "Asia-Pacific", "Latin America", "MENA", "Africa"],
    }
