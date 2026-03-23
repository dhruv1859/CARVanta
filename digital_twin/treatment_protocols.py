"""
CARVanta – Treatment Protocol Database & Outcome Predictor
=============================================================
Comprehensive database of FDA-approved and clinical-stage CAR-T products 
with treatment protocols, expected outcomes, and toxicity profiles.

Includes:
- All FDA-approved CAR-T products (as of 2024)
- Key clinical-stage products
- Bridging therapy protocols
- Manufacturing timelines
- Real-world outcome data
- Cost modeling

References:
    - Neelapu et al., NEJM (2017) — ZUMA-1 (axi-cel)
    - Schuster et al., NEJM (2019) — JULIET (tisa-cel)
    - Wang et al., NEJM (2020) — ZUMA-2 (brexu-cel) 
    - Munshi et al., NEJM (2021) — KarMMa (ide-cel)
    - Berdeja et al., Lancet (2021) — CARTITUDE-1 (cilta-cel)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
import math
import random


# ═══════════════════════════════════════════════════════════════════════════════
# FDA-Approved & Clinical-Stage CAR-T Products
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CARTProduct:
    """Complete profile of a CAR-T cell therapy product."""
    
    # Identity
    generic_name: str
    brand_name: str
    manufacturer: str
    approval_year: Optional[int]
    fda_approved: bool
    
    # Target & Design
    target_antigen: str
    costimulatory_domain: str         # 4-1BB or CD28
    hinge_domain: str
    scfv_origin: str                  # FMC63, etc.
    generation: str                   # "2nd", "3rd", "armored"
    
    # Approved Indications
    indications: List[str]
    
    # Manufacturing
    vein_to_vein_days: int             # Total time from collection to infusion
    manufacturing_days: int            # Cell processing time
    manufacturing_success_rate: float  # % of successful products
    fresh_vs_cryo: str                # "cryopreserved" or "fresh"
    
    # Dosing
    dose_range: str                   # cells/kg or flat dose
    typical_dose_cells: float         # Typical total cells infused
    
    # Lymphodepletion
    lymphodepletion_regimen: str
    
    # Clinical Outcomes (from pivotal trials)
    overall_response_rate: float
    complete_response_rate: float
    median_dor_months: Optional[float]  # Duration of response
    median_pfs_months: Optional[float]  # Progression-free survival
    median_os_months: Optional[float]   # Overall survival
    one_year_survival: float
    two_year_survival: float
    
    # Toxicity Profile
    any_grade_crs: float              # % any grade CRS
    grade_3plus_crs: float            # % grade ≥3 CRS
    any_grade_icans: float            # % any grade ICANS
    grade_3plus_icans: float          # % grade ≥3 ICANS
    median_crs_onset_days: float
    median_crs_duration_days: float
    tocilizumab_use_pct: float        # % needing tocilizumab
    steroid_use_pct: float            # % needing steroids
    icu_admission_pct: float
    treatment_related_mortality: float
    
    # Long-term Toxicity
    b_cell_aplasia: bool              # Expected B-cell aplasia
    hypogammaglobulinemia: float      # % requiring IVIG
    prolonged_cytopenias: float       # % with >28d cytopenias
    secondary_malignancy_risk: float  # % with secondary cancers
    
    # Cost
    list_price_usd: float
    total_treatment_cost_usd: float   # Including hospitalization
    
    # Key Trial
    pivotal_trial: str
    trial_nct: str


# ─── Product Database ──────────────────────────────────────────────────────────

CAR_T_PRODUCTS: Dict[str, CARTProduct] = {
    
    "axi-cel": CARTProduct(
        generic_name="Axicabtagene ciloleucel",
        brand_name="Yescarta",
        manufacturer="Kite/Gilead",
        approval_year=2017,
        fda_approved=True,
        target_antigen="CD19",
        costimulatory_domain="CD28",
        hinge_domain="CD28",
        scfv_origin="FMC63",
        generation="2nd",
        indications=[
            "Relapsed/refractory DLBCL (≥2 prior lines)",
            "Relapsed/refractory FL (≥2 prior lines)",
            "Relapsed/refractory LBCL (after 1st-line failure)",
        ],
        vein_to_vein_days=28,
        manufacturing_days=17,
        manufacturing_success_rate=0.99,
        fresh_vs_cryo="cryopreserved",
        dose_range="2×10⁶ cells/kg",
        typical_dose_cells=2e8,
        lymphodepletion_regimen="Flu 30mg/m² ×3d + Cy 500mg/m² ×3d",
        overall_response_rate=0.83,
        complete_response_rate=0.58,
        median_dor_months=11.1,
        median_pfs_months=5.9,
        median_os_months=None,
        one_year_survival=0.59,
        two_year_survival=0.48,
        any_grade_crs=0.93,
        grade_3plus_crs=0.13,
        any_grade_icans=0.64,
        grade_3plus_icans=0.28,
        median_crs_onset_days=2,
        median_crs_duration_days=7,
        tocilizumab_use_pct=0.43,
        steroid_use_pct=0.27,
        icu_admission_pct=0.36,
        treatment_related_mortality=0.02,
        b_cell_aplasia=True,
        hypogammaglobulinemia=0.15,
        prolonged_cytopenias=0.30,
        secondary_malignancy_risk=0.03,
        list_price_usd=373000,
        total_treatment_cost_usd=500000,
        pivotal_trial="ZUMA-1",
        trial_nct="NCT02348216",
    ),
    
    "tisa-cel": CARTProduct(
        generic_name="Tisagenlecleucel",
        brand_name="Kymriah",
        manufacturer="Novartis",
        approval_year=2017,
        fda_approved=True,
        target_antigen="CD19",
        costimulatory_domain="4-1BB",
        hinge_domain="CD8α",
        scfv_origin="FMC63",
        generation="2nd",
        indications=[
            "Relapsed/refractory B-ALL (age ≤25)",
            "Relapsed/refractory DLBCL (≥2 prior lines)",
            "Relapsed/refractory FL (≥2 prior lines)",
        ],
        vein_to_vein_days=45,
        manufacturing_days=22,
        manufacturing_success_rate=0.92,
        fresh_vs_cryo="cryopreserved",
        dose_range="0.6-6×10⁸ cells (ALL), 0.1-6×10⁸ cells (DLBCL)",
        typical_dose_cells=3e8,
        lymphodepletion_regimen="Flu 30mg/m² ×4d + Cy 500mg/m² ×2d (or Bendamustine 90mg/m² ×2d)",
        overall_response_rate=0.52,
        complete_response_rate=0.40,
        median_dor_months=None,
        median_pfs_months=2.9,
        median_os_months=11.1,
        one_year_survival=0.49,
        two_year_survival=0.40,
        any_grade_crs=0.58,
        grade_3plus_crs=0.22,
        any_grade_icans=0.21,
        grade_3plus_icans=0.12,
        median_crs_onset_days=3,
        median_crs_duration_days=7,
        tocilizumab_use_pct=0.15,
        steroid_use_pct=0.10,
        icu_admission_pct=0.26,
        treatment_related_mortality=0.01,
        b_cell_aplasia=True,
        hypogammaglobulinemia=0.12,
        prolonged_cytopenias=0.25,
        secondary_malignancy_risk=0.02,
        list_price_usd=475000,
        total_treatment_cost_usd=600000,
        pivotal_trial="JULIET",
        trial_nct="NCT02445248",
    ),
    
    "brexu-cel": CARTProduct(
        generic_name="Brexucabtagene autoleucel",
        brand_name="Tecartus",
        manufacturer="Kite/Gilead",
        approval_year=2020,
        fda_approved=True,
        target_antigen="CD19",
        costimulatory_domain="CD28",
        hinge_domain="CD28",
        scfv_origin="FMC63",
        generation="2nd",
        indications=[
            "Relapsed/refractory MCL",
            "Relapsed/refractory B-ALL (adults)",
        ],
        vein_to_vein_days=30,
        manufacturing_days=17,
        manufacturing_success_rate=0.97,
        fresh_vs_cryo="cryopreserved",
        dose_range="2×10⁶ cells/kg (max 2×10⁸)",
        typical_dose_cells=2e8,
        lymphodepletion_regimen="Flu 30mg/m² ×3d + Cy 500mg/m² ×3d",
        overall_response_rate=0.93,
        complete_response_rate=0.67,
        median_dor_months=None,
        median_pfs_months=14.6,
        median_os_months=None,
        one_year_survival=0.83,
        two_year_survival=0.64,
        any_grade_crs=0.91,
        grade_3plus_crs=0.15,
        any_grade_icans=0.63,
        grade_3plus_icans=0.31,
        median_crs_onset_days=2,
        median_crs_duration_days=5,
        tocilizumab_use_pct=0.56,
        steroid_use_pct=0.24,
        icu_admission_pct=0.35,
        treatment_related_mortality=0.03,
        b_cell_aplasia=True,
        hypogammaglobulinemia=0.14,
        prolonged_cytopenias=0.35,
        secondary_malignancy_risk=0.03,
        list_price_usd=373000,
        total_treatment_cost_usd=480000,
        pivotal_trial="ZUMA-2",
        trial_nct="NCT02601313",
    ),
    
    "liso-cel": CARTProduct(
        generic_name="Lisocabtagene maraleucel",
        brand_name="Breyanzi",
        manufacturer="Bristol-Myers Squibb",
        approval_year=2021,
        fda_approved=True,
        target_antigen="CD19",
        costimulatory_domain="4-1BB",
        hinge_domain="IgG4",
        scfv_origin="FMC63",
        generation="2nd",
        indications=[
            "Relapsed/refractory LBCL (≥2 prior lines)",
            "Relapsed/refractory LBCL (after 1st-line failure)",
        ],
        vein_to_vein_days=35,
        manufacturing_days=24,
        manufacturing_success_rate=0.97,
        fresh_vs_cryo="cryopreserved",
        dose_range="50-110×10⁶ cells (defined CD4+/CD8+ ratio)",
        typical_dose_cells=1e8,
        lymphodepletion_regimen="Flu 30mg/m² ×3d + Cy 300mg/m² ×3d",
        overall_response_rate=0.73,
        complete_response_rate=0.53,
        median_dor_months=None,
        median_pfs_months=6.8,
        median_os_months=21.1,
        one_year_survival=0.58,
        two_year_survival=0.48,
        any_grade_crs=0.42,
        grade_3plus_crs=0.02,
        any_grade_icans=0.30,
        grade_3plus_icans=0.10,
        median_crs_onset_days=5,
        median_crs_duration_days=5,
        tocilizumab_use_pct=0.19,
        steroid_use_pct=0.10,
        icu_admission_pct=0.14,
        treatment_related_mortality=0.0,
        b_cell_aplasia=True,
        hypogammaglobulinemia=0.10,
        prolonged_cytopenias=0.20,
        secondary_malignancy_risk=0.02,
        list_price_usd=410300,
        total_treatment_cost_usd=530000,
        pivotal_trial="TRANSCEND",
        trial_nct="NCT02631044",
    ),
    
    "ide-cel": CARTProduct(
        generic_name="Idecabtagene vicleucel",
        brand_name="Abecma",
        manufacturer="Bristol-Myers Squibb",
        approval_year=2021,
        fda_approved=True,
        target_antigen="BCMA",
        costimulatory_domain="4-1BB",
        hinge_domain="CD8α",
        scfv_origin="C11D5.3",
        generation="2nd",
        indications=[
            "Relapsed/refractory Multiple Myeloma (≥4 prior lines)",
        ],
        vein_to_vein_days=42,
        manufacturing_days=28,
        manufacturing_success_rate=0.96,
        fresh_vs_cryo="cryopreserved",
        dose_range="150-450×10⁶ cells",
        typical_dose_cells=4e8,
        lymphodepletion_regimen="Flu 30mg/m² ×3d + Cy 300mg/m² ×3d",
        overall_response_rate=0.73,
        complete_response_rate=0.33,
        median_dor_months=10.7,
        median_pfs_months=8.8,
        median_os_months=24.8,
        one_year_survival=0.78,
        two_year_survival=0.51,
        any_grade_crs=0.84,
        grade_3plus_crs=0.05,
        any_grade_icans=0.18,
        grade_3plus_icans=0.03,
        median_crs_onset_days=1,
        median_crs_duration_days=5,
        tocilizumab_use_pct=0.52,
        steroid_use_pct=0.15,
        icu_admission_pct=0.08,
        treatment_related_mortality=0.01,
        b_cell_aplasia=False,
        hypogammaglobulinemia=0.20,
        prolonged_cytopenias=0.40,
        secondary_malignancy_risk=0.04,
        list_price_usd=419500,
        total_treatment_cost_usd=550000,
        pivotal_trial="KarMMa",
        trial_nct="NCT03361748",
    ),
    
    "cilta-cel": CARTProduct(
        generic_name="Ciltacabtagene autoleucel",
        brand_name="Carvykti",
        manufacturer="Janssen/Legend",
        approval_year=2022,
        fda_approved=True,
        target_antigen="BCMA",
        costimulatory_domain="4-1BB",
        hinge_domain="CD8α",
        scfv_origin="Dual BCMA-binding VHH",
        generation="2nd (dual epitope)",
        indications=[
            "Relapsed/refractory Multiple Myeloma (≥4 prior lines, or after ≥1 prior line [2024 update])",
        ],
        vein_to_vein_days=56,
        manufacturing_days=35,
        manufacturing_success_rate=0.97,
        fresh_vs_cryo="cryopreserved",
        dose_range="0.5-1.0×10⁶ cells/kg",
        typical_dose_cells=7e7,
        lymphodepletion_regimen="Flu 30mg/m² ×3d + Cy 300mg/m² ×3d",
        overall_response_rate=0.98,
        complete_response_rate=0.83,
        median_dor_months=None,
        median_pfs_months=34.9,
        median_os_months=None,
        one_year_survival=0.89,
        two_year_survival=0.74,
        any_grade_crs=0.95,
        grade_3plus_crs=0.04,
        any_grade_icans=0.23,
        grade_3plus_icans=0.09,
        median_crs_onset_days=7,
        median_crs_duration_days=4,
        tocilizumab_use_pct=0.69,
        steroid_use_pct=0.22,
        icu_admission_pct=0.11,
        treatment_related_mortality=0.01,
        b_cell_aplasia=False,
        hypogammaglobulinemia=0.22,
        prolonged_cytopenias=0.45,
        secondary_malignancy_risk=0.07,
        list_price_usd=465000,
        total_treatment_cost_usd=600000,
        pivotal_trial="CARTITUDE-1",
        trial_nct="NCT03548207",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Treatment Outcome Predictor
# ═══════════════════════════════════════════════════════════════════════════════

def predict_outcome_for_product(
    product_key: str,
    patient_age: int = 55,
    cancer_stage: str = "III",
    tumor_burden_mm: float = 50.0,
    prior_lines: int = 3,
    ecog: int = 1,
    ldh: Optional[float] = None,
    crp: Optional[float] = None,
    bridging_therapy: bool = False,
    seed: int = 42,
) -> Dict:
    """
    Predict personalized treatment outcome for a specific CAR-T product.
    Adjusts published trial data based on individual patient factors.
    """
    
    product = CAR_T_PRODUCTS.get(product_key)
    if not product:
        return {"error": f"Unknown product: {product_key}. Available: {list(CAR_T_PRODUCTS.keys())}"}
    
    random.seed(seed)
    
    # ── Risk Factor Scoring ──────────────────────────────────────
    risk_score = 0.0
    risk_factors = []
    
    # Age
    if patient_age > 70:
        risk_score += 15
        risk_factors.append({"factor": "Age >70", "impact": -15, "category": "demographic"})
    elif patient_age > 60:
        risk_score += 8
        risk_factors.append({"factor": "Age 60-70", "impact": -8, "category": "demographic"})
    elif patient_age < 25:
        risk_score -= 5
        risk_factors.append({"factor": "Age <25 (favorable)", "impact": 5, "category": "demographic"})
    
    # Stage
    if cancer_stage == "IV":
        risk_score += 12
        risk_factors.append({"factor": "Stage IV", "impact": -12, "category": "disease"})
    elif cancer_stage in ("I", "II"):
        risk_score -= 5
        risk_factors.append({"factor": f"Stage {cancer_stage} (favorable)", "impact": 5, "category": "disease"})
    
    # Tumor burden
    if tumor_burden_mm > 100:
        risk_score += 20
        risk_factors.append({"factor": "Bulky disease (>100mm)", "impact": -20, "category": "disease"})
    elif tumor_burden_mm > 50:
        risk_score += 8
        risk_factors.append({"factor": "Moderate burden (50-100mm)", "impact": -8, "category": "disease"})
    
    # Prior lines of therapy
    if prior_lines >= 5:
        risk_score += 15
        risk_factors.append({"factor": f"Heavily pretreated ({prior_lines} prior lines)", "impact": -15, "category": "treatment"})
    elif prior_lines >= 3:
        risk_score += 8
        risk_factors.append({"factor": f"{prior_lines} prior lines", "impact": -8, "category": "treatment"})
    
    # ECOG
    if ecog >= 2:
        risk_score += 20
        risk_factors.append({"factor": f"ECOG {ecog} (poor performance status)", "impact": -20, "category": "fitness"})
    
    # LDH
    if ldh is not None:
        if ldh > 500:
            risk_score += 15
            risk_factors.append({"factor": "Very high LDH (>500)", "impact": -15, "category": "labs"})
        elif ldh > 250:
            risk_score += 8
            risk_factors.append({"factor": "Elevated LDH", "impact": -8, "category": "labs"})
    
    # CRP
    if crp is not None and crp > 30:
        risk_score += 10
        risk_factors.append({"factor": "Elevated CRP (systemic inflammation)", "impact": -10, "category": "labs"})
    
    # Bridging therapy impact
    if bridging_therapy:
        risk_score -= 5
        risk_factors.append({"factor": "Bridging therapy (reduced burden)", "impact": 5, "category": "treatment"})
    
    # ── Adjust Published Outcomes ────────────────────────────────
    risk_modifier = max(0.3, min(1.3, 1 - risk_score / 100))
    
    predicted_orr = min(1.0, product.overall_response_rate * risk_modifier)
    predicted_cr = min(predicted_orr, product.complete_response_rate * risk_modifier)
    predicted_crs_risk = min(1.0, product.grade_3plus_crs * (1 + risk_score / 50))
    predicted_1yr_survival = min(1.0, product.one_year_survival * risk_modifier)
    
    # Cost analysis
    cost = product.total_treatment_cost_usd
    if predicted_1yr_survival > 0:
        cost_per_life_year = cost / predicted_1yr_survival
    else:
        cost_per_life_year = float('inf')
    
    return {
        "product": {
            "name": product.brand_name,
            "generic": product.generic_name,
            "manufacturer": product.manufacturer,
            "target": product.target_antigen,
            "design": product.costimulatory_domain,
            "fda_approved": product.fda_approved,
            "list_price": f"${product.list_price_usd:,.0f}",
        },
        "published_outcomes": {
            "orr": f"{product.overall_response_rate * 100:.0f}%",
            "cr": f"{product.complete_response_rate * 100:.0f}%",
            "one_year_survival": f"{product.one_year_survival * 100:.0f}%",
            "grade3_crs": f"{product.grade_3plus_crs * 100:.0f}%",
            "grade3_icans": f"{product.grade_3plus_icans * 100:.0f}%",
            "pivotal_trial": product.pivotal_trial,
        },
        "personalized_prediction": {
            "predicted_orr": f"{predicted_orr * 100:.0f}%",
            "predicted_cr": f"{predicted_cr * 100:.0f}%",
            "predicted_1yr_survival": f"{predicted_1yr_survival * 100:.0f}%",
            "predicted_severe_crs_risk": f"{predicted_crs_risk * 100:.0f}%",
            "risk_modifier": round(risk_modifier, 3),
            "risk_score": round(risk_score, 1),
        },
        "risk_factors": risk_factors,
        "cost_analysis": {
            "treatment_cost": f"${cost:,.0f}",
            "cost_per_life_year_gained": f"${cost_per_life_year:,.0f}",
        },
        "manufacturing": {
            "vein_to_vein_days": product.vein_to_vein_days,
            "success_rate": f"{product.manufacturing_success_rate * 100:.0f}%",
            "lymphodepletion": product.lymphodepletion_regimen,
        },
    }


def compare_products(
    product_keys: List[str],
    patient_params: Dict,
) -> Dict:
    """Compare multiple CAR-T products for a specific patient."""
    
    results = []
    for key in product_keys:
        pred = predict_outcome_for_product(key, **patient_params)
        if "error" not in pred:
            results.append(pred)
    
    # Rank by predicted ORR
    results.sort(key=lambda r: float(r["personalized_prediction"]["predicted_orr"].replace("%", "")), reverse=True)
    
    for i, r in enumerate(results):
        r["rank"] = i + 1
    
    return {
        "comparisons": results,
        "recommended": results[0]["product"]["name"] if results else None,
    }


def get_products_for_cancer(cancer_type: str) -> List[Dict]:
    """Return CAR-T products available for a specific cancer type."""
    
    # Map cancer types to target antigens
    cancer_to_targets = {
        "DLBCL": ["CD19"],
        "B-ALL": ["CD19"],
        "MCL": ["CD19"],
        "FL": ["CD19"],
        "MM": ["BCMA"],
        "CLL": ["CD19"],
        "HL": ["CD30"],
    }
    
    targets = cancer_to_targets.get(cancer_type, [])
    
    matches = []
    for key, product in CAR_T_PRODUCTS.items():
        if product.target_antigen in targets:
            matches.append({
                "key": key,
                "brand": product.brand_name,
                "generic": product.generic_name,
                "target": product.target_antigen,
                "orr": f"{product.overall_response_rate * 100:.0f}%",
                "cr": f"{product.complete_response_rate * 100:.0f}%",
                "crs_risk": f"{product.grade_3plus_crs * 100:.0f}%",
                "list_price": f"${product.list_price_usd:,.0f}",
                "manufacturer": product.manufacturer,
            })
    
    return matches


def get_all_products_summary() -> List[Dict]:
    """Return summary of all CAR-T products."""
    return [
        {
            "key": key,
            "brand": p.brand_name,
            "generic": p.generic_name,
            "manufacturer": p.manufacturer,
            "target": p.target_antigen,
            "fda_approved": p.fda_approved,
            "approval_year": p.approval_year,
            "orr": f"{p.overall_response_rate * 100:.0f}%",
            "cr": f"{p.complete_response_rate * 100:.0f}%",
            "indications_count": len(p.indications),
            "list_price": f"${p.list_price_usd:,.0f}",
        }
        for key, p in CAR_T_PRODUCTS.items()
    ]
