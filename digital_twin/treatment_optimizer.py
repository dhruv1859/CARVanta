"""
CARVanta – Treatment Optimization Engine
==========================================
AI-driven treatment optimization for CAR-T cell therapy.
Provides personalized treatment recommendations by analyzing:
  - Patient characteristics and risk factors
  - Cancer biology and tumor microenvironment
  - CAR-T product suitability scoring
  - Lymphodepletion regimen selection
  - Dosing optimization
  - Combination therapy opportunities
  - Timing and sequencing recommendations
  - Real-world outcome predictions

Uses multi-criteria decision analysis (MCDA) weighted by evidence level.
"""

import math
import hashlib
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PatientProfile:
    """Complete patient profile for treatment optimization."""
    age: int = 55
    weight_kg: float = 70.0
    cancer_type: str = "DLBCL"
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    prior_lines: int = 2
    prior_car_t: bool = False
    ecog_status: int = 1
    comorbidities: List[str] = field(default_factory=list)
    # Lab values
    ldh: Optional[float] = None
    crp: Optional[float] = None
    ferritin: Optional[float] = None
    alc: Optional[float] = None
    platelet_count: Optional[float] = None
    # Genomic
    tp53_mutated: bool = False
    myc_rearranged: bool = False
    double_hit: bool = False


@dataclass
class TreatmentRecommendation:
    """A scored treatment recommendation."""
    product_name: str
    target_antigen: str
    suitability_score: float  # 0-1
    confidence: float  # 0-1
    predicted_orr: float  # overall response rate %
    predicted_cr: float  # complete response %
    predicted_pfs_months: float
    crs_risk: str  # low, moderate, high
    icans_risk: str  # low, moderate, high
    recommended_dose: str
    lymphodepletion: str
    rationale: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence_level: str = "moderate"


# ═══════════════════════════════════════════════════════════════════════════════
# FDA-Approved CAR-T Product Database
# ═══════════════════════════════════════════════════════════════════════════════

CART_PRODUCTS = {
    "axi-cel": {
        "name": "Axicabtagene ciloleucel (Yescarta)",
        "manufacturer": "Kite/Gilead",
        "target": "CD19",
        "costimulatory": "CD28",
        "approved_indications": ["DLBCL", "PMBCL", "FL", "HGBCL"],
        "approval_year": 2017,
        "dose_range": "1×10⁶–2×10⁶ CAR+ T cells/kg",
        "standard_dose": "2×10⁶/kg (max 2×10⁸)",
        "lymphodepletion": "Flu/Cy (30/500 mg/m²)",
        "pivotal_trial": "ZUMA-1",
        "historical_orr": 83,
        "historical_cr": 58,
        "median_pfs_months": 5.9,
        "grade3_crs_rate": 13,
        "grade3_icans_rate": 28,
        "median_onset_crs_days": 2,
        "bridging_allowed": True,
        "manufacturing_time_days": 17,
        "age_range": {"min": 18, "max": 999},
    },
    "tisa-cel": {
        "name": "Tisagenlecleucel (Kymriah)",
        "manufacturer": "Novartis",
        "target": "CD19",
        "costimulatory": "4-1BB",
        "approved_indications": ["ALL", "DLBCL", "FL"],
        "approval_year": 2017,
        "dose_range": "0.2–5×10⁶ CAR+ T cells/kg (peds), 0.6–6×10⁸ (adults)",
        "standard_dose": "0.6–6×10⁸ total (adults)",
        "lymphodepletion": "Flu/Cy (30/500 mg/m²) or Benda",
        "pivotal_trial": "JULIET / ELIANA",
        "historical_orr": 52,
        "historical_cr": 40,
        "median_pfs_months": 2.9,
        "grade3_crs_rate": 22,
        "grade3_icans_rate": 12,
        "median_onset_crs_days": 3,
        "bridging_allowed": True,
        "manufacturing_time_days": 22,
        "age_range": {"min": 0, "max": 999},
    },
    "liso-cel": {
        "name": "Lisocabtagene maraleucel (Breyanzi)",
        "manufacturer": "BMS/Juno",
        "target": "CD19",
        "costimulatory": "4-1BB",
        "approved_indications": ["DLBCL", "HGBCL", "PMBCL", "FL3B", "MCL"],
        "approval_year": 2021,
        "dose_range": "50–110×10⁶ CAR+ T cells",
        "standard_dose": "100×10⁶ total (fixed)",
        "lymphodepletion": "Flu/Cy (30/300 mg/m²)",
        "pivotal_trial": "TRANSCEND",
        "historical_orr": 73,
        "historical_cr": 53,
        "median_pfs_months": 6.8,
        "grade3_crs_rate": 2,
        "grade3_icans_rate": 10,
        "median_onset_crs_days": 5,
        "bridging_allowed": True,
        "manufacturing_time_days": 24,
        "age_range": {"min": 18, "max": 999},
    },
    "brexu-cel": {
        "name": "Brexucabtagene autoleucel (Tecartus)",
        "manufacturer": "Kite/Gilead",
        "target": "CD19",
        "costimulatory": "CD28",
        "approved_indications": ["MCL", "ALL"],
        "approval_year": 2020,
        "dose_range": "2×10⁶ CAR+ T cells/kg",
        "standard_dose": "2×10⁶/kg (max 2×10⁸)",
        "lymphodepletion": "Flu/Cy (30/500 mg/m²)",
        "pivotal_trial": "ZUMA-2",
        "historical_orr": 91,
        "historical_cr": 68,
        "median_pfs_months": 14.6,
        "grade3_crs_rate": 15,
        "grade3_icans_rate": 31,
        "median_onset_crs_days": 2,
        "bridging_allowed": False,
        "manufacturing_time_days": 16,
        "age_range": {"min": 18, "max": 999},
    },
    "ide-cel": {
        "name": "Idecabtagene vicleucel (Abecma)",
        "manufacturer": "BMS/bluebird",
        "target": "BCMA",
        "costimulatory": "4-1BB",
        "approved_indications": ["Multiple Myeloma"],
        "approval_year": 2021,
        "dose_range": "300–460×10⁶ CAR+ T cells",
        "standard_dose": "450×10⁶ total",
        "lymphodepletion": "Flu/Cy (30/300 mg/m²)",
        "pivotal_trial": "KarMMa",
        "historical_orr": 73,
        "historical_cr": 33,
        "median_pfs_months": 8.8,
        "grade3_crs_rate": 5,
        "grade3_icans_rate": 3,
        "median_onset_crs_days": 1,
        "bridging_allowed": True,
        "manufacturing_time_days": 28,
        "age_range": {"min": 18, "max": 999},
    },
    "cilta-cel": {
        "name": "Ciltacabtagene autoleucel (Carvykti)",
        "manufacturer": "J&J/Legend",
        "target": "BCMA",
        "costimulatory": "4-1BB",
        "approved_indications": ["Multiple Myeloma"],
        "approval_year": 2022,
        "dose_range": "0.5–1.0×10⁶ CAR+ T cells/kg",
        "standard_dose": "0.75×10⁶/kg",
        "lymphodepletion": "Flu/Cy (30/300 mg/m²)",
        "pivotal_trial": "CARTITUDE-1",
        "historical_orr": 98,
        "historical_cr": 83,
        "median_pfs_months": 27.7,
        "grade3_crs_rate": 4,
        "grade3_icans_rate": 2,
        "median_onset_crs_days": 7,
        "bridging_allowed": True,
        "manufacturing_time_days": 32,
        "age_range": {"min": 18, "max": 999},
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Lymphodepletion Regimens
# ═══════════════════════════════════════════════════════════════════════════════

LYMPHODEPLETION_REGIMENS = {
    "flu_cy_standard": {
        "name": "Fludarabine/Cyclophosphamide (Standard)",
        "drugs": "Flu 30mg/m² × 3d + Cy 500mg/m² × 3d",
        "schedule": "Day -5 to Day -3",
        "efficacy_score": 1.0,
        "toxicity_score": 0.4,
        "indications": ["DLBCL", "ALL", "MCL", "FL", "Multiple Myeloma"],
        "contraindications": ["severe_renal", "severe_hepatic"],
    },
    "flu_cy_reduced": {
        "name": "Fludarabine/Cyclophosphamide (Reduced)",
        "drugs": "Flu 25mg/m² × 3d + Cy 250mg/m² × 3d",
        "schedule": "Day -5 to Day -3",
        "efficacy_score": 0.85,
        "toxicity_score": 0.25,
        "indications": ["DLBCL", "ALL", "MCL", "FL"],
        "contraindications": [],
    },
    "bendamustine": {
        "name": "Bendamustine",
        "drugs": "Bendamustine 90mg/m² × 2d",
        "schedule": "Day -5 to Day -4",
        "efficacy_score": 0.80,
        "toxicity_score": 0.3,
        "indications": ["DLBCL", "FL", "CLL"],
        "contraindications": [],
    },
    "flu_only": {
        "name": "Fludarabine Only",
        "drugs": "Flu 25mg/m² × 5d",
        "schedule": "Day -6 to Day -2",
        "efficacy_score": 0.65,
        "toxicity_score": 0.15,
        "indications": ["ALL"],
        "contraindications": [],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Treatment Optimization Engine
# ═══════════════════════════════════════════════════════════════════════════════

def optimize_treatment(patient: PatientProfile) -> Dict[str, Any]:
    """
    Generate a complete treatment optimization report.
    Uses multi-criteria decision analysis (MCDA) to rank products
    and recommend optimal treatment parameters.
    """
    # Step 1: Filter eligible products
    eligible = _get_eligible_products(patient)
    if not eligible:
        return {"error": "No eligible CAR-T products found for this patient profile"}

    # Step 2: Score each product
    recommendations = []
    for product_key, product in eligible.items():
        rec = _score_product(patient, product_key, product)
        recommendations.append(rec)

    # Step 3: Rank by suitability
    recommendations.sort(key=lambda r: r.suitability_score, reverse=True)

    # Step 4: Select optimal lymphodepletion
    best_product = recommendations[0]
    lympho_rec = _recommend_lymphodepletion(patient, best_product)

    # Step 5: Generate timing recommendation
    timing = _recommend_timing(patient)

    # Step 6: Identify combination opportunities
    combos = _identify_combinations(patient, best_product)

    # Step 7: Risk-benefit summary
    risk_benefit = _risk_benefit_analysis(patient, recommendations[0])

    return {
        "patient_summary": _patient_summary(patient),
        "recommendations": [
            {
                "rank": i + 1,
                "product": r.product_name,
                "target": r.target_antigen,
                "suitability_score": round(r.suitability_score, 3),
                "confidence": round(r.confidence, 3),
                "predicted_orr": round(r.predicted_orr, 1),
                "predicted_cr": round(r.predicted_cr, 1),
                "predicted_pfs_months": round(r.predicted_pfs_months, 1),
                "crs_risk": r.crs_risk,
                "icans_risk": r.icans_risk,
                "recommended_dose": r.recommended_dose,
                "lymphodepletion": r.lymphodepletion,
                "rationale": r.rationale,
                "warnings": r.warnings,
                "evidence_level": r.evidence_level,
            }
            for i, r in enumerate(recommendations)
        ],
        "optimal_lymphodepletion": lympho_rec,
        "timing_recommendation": timing,
        "combination_opportunities": combos,
        "risk_benefit_analysis": risk_benefit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_eligible_products(patient: PatientProfile) -> Dict[str, Any]:
    """Filter products based on approved indications and age."""
    eligible = {}
    cancer = patient.cancer_type.upper()

    for key, product in CART_PRODUCTS.items():
        indications = [ind.upper() for ind in product["approved_indications"]]
        age_range = product["age_range"]

        # Check indication match (fuzzy)
        indication_match = any(
            cancer in ind or ind in cancer
            for ind in indications
        )

        # Check age
        age_ok = age_range["min"] <= patient.age <= age_range["max"]

        if indication_match and age_ok:
            eligible[key] = product

    # If no exact match, include CD19-targeting products for all B-cell malignancies
    if not eligible:
        b_cell_keywords = ["B-CELL", "LYMPHOMA", "LEUKEMIA", "ALL", "DLBCL"]
        if any(kw in cancer for kw in b_cell_keywords):
            for key, product in CART_PRODUCTS.items():
                if product["target"] == "CD19":
                    eligible[key] = product

    return eligible


def _score_product(
    patient: PatientProfile,
    product_key: str,
    product: Dict,
) -> TreatmentRecommendation:
    """Score a product for a specific patient using MCDA."""
    rationale = []
    warnings = []

    # Base efficacy from historical data
    base_orr = product["historical_orr"]
    base_cr = product["historical_cr"]
    base_pfs = product["median_pfs_months"]

    # ── Patient-specific adjustments ──────────────────────────────────────

    # Age adjustment
    age_factor = 1.0
    if patient.age > 65:
        age_factor = 0.85
        rationale.append(f"Age {patient.age}: Modest efficacy reduction expected in elderly")
    elif patient.age < 18:
        age_factor = 1.1
        rationale.append(f"Age {patient.age}: Pediatric patients often show better responses")
    elif patient.age < 40:
        age_factor = 1.05

    # Prior lines
    prior_factor = 1.0
    if patient.prior_lines >= 4:
        prior_factor = 0.75
        warnings.append("≥4 prior lines: Significantly reduced T-cell fitness expected")
    elif patient.prior_lines >= 3:
        prior_factor = 0.85
        rationale.append("3 prior lines: Moderate impact on T-cell quality")
    elif patient.prior_lines <= 1:
        prior_factor = 1.1
        rationale.append("Early line: Better T-cell fitness expected")

    # Prior CAR-T
    if patient.prior_car_t:
        prior_factor *= 0.7
        warnings.append("Prior CAR-T: Significant reduction in expected efficacy")

    # ECOG performance status
    ecog_factor = 1.0
    if patient.ecog_status >= 2:
        ecog_factor = 0.8
        warnings.append(f"ECOG {patient.ecog_status}: Higher treatment-related mortality risk")
    elif patient.ecog_status == 0:
        ecog_factor = 1.05

    # Tumor burden
    burden_factor = 1.0
    if patient.tumor_burden_mm > 100:
        burden_factor = 0.85
        warnings.append("High tumor burden: Increased CRS risk and potential for incomplete response")
    elif patient.tumor_burden_mm > 70:
        burden_factor = 0.92
    elif patient.tumor_burden_mm < 30:
        burden_factor = 1.08
        rationale.append("Low tumor burden: Favorable for complete response")

    # LDH (tumor marker)
    ldh_factor = 1.0
    if patient.ldh and patient.ldh > 400:
        ldh_factor = 0.82
        warnings.append(f"Elevated LDH ({patient.ldh}): Aggressive disease biology")
    elif patient.ldh and patient.ldh > 250:
        ldh_factor = 0.92

    # Genomic risk factors
    genomic_factor = 1.0
    if patient.double_hit:
        genomic_factor = 0.65
        warnings.append("Double-hit lymphoma: High-risk biology, reduced long-term efficacy")
    elif patient.tp53_mutated:
        genomic_factor = 0.75
        warnings.append("TP53 mutation: Adverse prognostic factor")
    elif patient.myc_rearranged:
        genomic_factor = 0.8
        warnings.append("MYC rearrangement: Increased proliferative potential")

    # Costimulatory domain advantage
    costim_factor = 1.0
    if product["costimulatory"] == "4-1BB":
        costim_factor = 1.02  # Slightly better persistence
        rationale.append("4-1BB costimulation: Better long-term T-cell persistence")
    elif product["costimulatory"] == "CD28":
        rationale.append("CD28 costimulation: Faster initial expansion")

    # ── Calculate adjusted outcomes ──────────────────────────────────────
    total_factor = (
        age_factor * prior_factor * ecog_factor *
        burden_factor * ldh_factor * genomic_factor * costim_factor
    )

    adjusted_orr = min(100, base_orr * total_factor)
    adjusted_cr = min(adjusted_orr, base_cr * total_factor)
    adjusted_pfs = base_pfs * total_factor

    # ── CRS Risk Assessment ──────────────────────────────────────────────
    crs_base = product["grade3_crs_rate"]
    crs_adjusted = crs_base
    if patient.tumor_burden_mm > 80:
        crs_adjusted *= 1.4
    if patient.ldh and patient.ldh > 400:
        crs_adjusted *= 1.3
    if patient.prior_car_t:
        crs_adjusted *= 0.7  # Reduced CRS on retreatment

    crs_risk = "low" if crs_adjusted < 10 else "moderate" if crs_adjusted < 25 else "high"

    # ICANS risk
    icans_base = product["grade3_icans_rate"]
    icans_adjusted = icans_base
    if patient.age > 60:
        icans_adjusted *= 1.3
    icans_risk = "low" if icans_adjusted < 10 else "moderate" if icans_adjusted < 25 else "high"

    # ── Suitability Score (0-1) ──────────────────────────────────────────
    efficacy_weight = 0.40
    safety_weight = 0.25
    evidence_weight = 0.20
    practical_weight = 0.15

    efficacy_score = adjusted_orr / 100
    safety_score = 1.0 - (crs_adjusted + icans_adjusted) / 200
    evidence_score = 0.9 if product["pivotal_trial"] else 0.5
    practical_score = 1.0 - (product["manufacturing_time_days"] / 60)

    suitability = (
        efficacy_weight * efficacy_score +
        safety_weight * safety_score +
        evidence_weight * evidence_score +
        practical_weight * practical_score
    )

    # Confidence based on data quality
    confidence = 0.85 if total_factor > 0.8 else 0.7 if total_factor > 0.6 else 0.55

    # Add product-specific rationale
    rationale.insert(0, f"{product['name']}: {product['pivotal_trial']} trial data")
    rationale.append(f"Manufacturing: ~{product['manufacturing_time_days']} days")

    return TreatmentRecommendation(
        product_name=product["name"],
        target_antigen=product["target"],
        suitability_score=suitability,
        confidence=confidence,
        predicted_orr=adjusted_orr,
        predicted_cr=adjusted_cr,
        predicted_pfs_months=adjusted_pfs,
        crs_risk=crs_risk,
        icans_risk=icans_risk,
        recommended_dose=product["standard_dose"],
        lymphodepletion=product["lymphodepletion"],
        rationale=rationale,
        warnings=warnings,
        evidence_level="high" if product["approval_year"] <= 2020 else "moderate",
    )


def _recommend_lymphodepletion(
    patient: PatientProfile,
    recommendation: TreatmentRecommendation,
) -> Dict[str, Any]:
    """Select optimal lymphodepletion regimen."""
    scored_regimens = []

    for key, regimen in LYMPHODEPLETION_REGIMENS.items():
        # Check contraindications
        has_contraindication = any(
            c in [ci.lower() for ci in patient.comorbidities]
            for c in regimen["contraindications"]
        )
        if has_contraindication:
            continue

        # Check indication
        cancer_match = any(
            patient.cancer_type.upper() in ind.upper() or ind.upper() in patient.cancer_type.upper()
            for ind in regimen["indications"]
        )

        # Score
        score = regimen["efficacy_score"]
        if not cancer_match:
            score *= 0.7

        # Adjust for patient factors
        if patient.age > 70 or patient.ecog_status >= 2:
            # Prefer less toxic regimens
            score -= regimen["toxicity_score"] * 0.3

        if patient.platelet_count and patient.platelet_count < 50000:
            score -= regimen["toxicity_score"] * 0.4

        scored_regimens.append({
            "key": key,
            "name": regimen["name"],
            "drugs": regimen["drugs"],
            "schedule": regimen["schedule"],
            "score": round(max(0, score), 3),
            "toxicity": regimen["toxicity_score"],
        })

    scored_regimens.sort(key=lambda r: r["score"], reverse=True)

    return {
        "recommended": scored_regimens[0] if scored_regimens else None,
        "alternatives": scored_regimens[1:3],
        "rationale": _lympho_rationale(patient, scored_regimens[0] if scored_regimens else None),
    }


def _lympho_rationale(patient: PatientProfile, regimen: Optional[Dict]) -> str:
    """Generate rationale for lymphodepletion choice."""
    if not regimen:
        return "No suitable regimen identified. Manual review required."

    parts = [f"Selected {regimen['name']} (score: {regimen['score']})."]
    if patient.age > 70:
        parts.append("Lower toxicity preferred for elderly patient.")
    if patient.ecog_status >= 2:
        parts.append("Reduced intensity due to performance status.")
    return " ".join(parts)


def _recommend_timing(patient: PatientProfile) -> Dict[str, Any]:
    """Recommend treatment timing and sequencing."""
    urgency = "standard"
    rationale = []

    if patient.tumor_burden_mm > 100:
        urgency = "urgent"
        rationale.append("High tumor burden requires expedited treatment")
    elif patient.ldh and patient.ldh > 500:
        urgency = "urgent"
        rationale.append("Very elevated LDH indicates aggressive disease kinetics")

    if patient.ecog_status >= 2:
        rationale.append("Declining performance status — early treatment window closing")
        if urgency == "standard":
            urgency = "priority"

    bridging_recommended = patient.tumor_burden_mm > 60 or (patient.ldh and patient.ldh > 350)

    return {
        "urgency": urgency,
        "recommended_timeline": "2-3 weeks" if urgency == "urgent" else "4-6 weeks",
        "bridging_therapy_recommended": bridging_recommended,
        "bridging_options": (
            ["R-GemOx", "Polatuzumab + BR", "Radiation for bulky sites"]
            if bridging_recommended else []
        ),
        "monitoring_schedule": {
            "pre_infusion": ["CBC", "CMP", "LDH", "Ferritin", "CRP", "IL-6"],
            "post_infusion_daily": ["Temp", "BP", "SpO2", "Neuro assessment"],
            "post_infusion_labs": ["CBC q2d", "CRP daily", "Ferritin q2d", "IL-6 if CRS"],
        },
        "rationale": rationale,
    }


def _identify_combinations(
    patient: PatientProfile,
    recommendation: TreatmentRecommendation,
) -> List[Dict[str, Any]]:
    """Identify combination therapy opportunities."""
    combos = []

    # Checkpoint inhibitor combination
    if patient.prior_lines >= 3:
        combos.append({
            "combination": "CAR-T + PD-1 inhibitor (pembrolizumab)",
            "timing": "Post-CAR-T (Day +30 if suboptimal response)",
            "rationale": "Overcome T-cell exhaustion in heavily pretreated patients",
            "evidence_level": "emerging (Phase I/II)",
            "risk": "Increased immune-related adverse events",
        })

    # Bispecific antibody bridge
    if patient.tumor_burden_mm > 80:
        combos.append({
            "combination": "Bispecific antibody bridging (glofitamab/epcoritamab)",
            "timing": "Pre-CAR-T bridging (2-4 weeks before apheresis)",
            "rationale": "Tumor debulking to reduce CRS risk",
            "evidence_level": "moderate",
            "risk": "CRS from bispecific may complicate subsequent CAR-T CRS management",
        })

    # PI3K inhibitor for persistence
    if recommendation.target_antigen == "CD19":
        combos.append({
            "combination": "Ibrutinib concurrent",
            "timing": "Start Day -3 through Day +90",
            "rationale": "Enhanced CAR-T expansion and persistence in B-cell malignancies",
            "evidence_level": "Phase II (ZUMA-8-like)",
            "risk": "Bleeding risk, atrial fibrillation",
        })

    # Lenalidomide maintenance
    if "myeloma" in patient.cancer_type.lower():
        combos.append({
            "combination": "Lenalidomide maintenance",
            "timing": "Post-CAR-T (Day +90-100 if response maintained)",
            "rationale": "Enhance immune surveillance and prevent relapse",
            "evidence_level": "Phase I/II",
            "risk": "Cytopenia, second primary malignancy",
        })

    return combos


def _risk_benefit_analysis(
    patient: PatientProfile,
    recommendation: TreatmentRecommendation,
) -> Dict[str, Any]:
    """Generate comprehensive risk-benefit analysis."""
    benefits = []
    risks = []

    # Benefits
    if recommendation.predicted_orr > 70:
        benefits.append({"factor": "High response rate", "value": f"{recommendation.predicted_orr:.0f}% ORR",
                        "weight": "high"})
    if recommendation.predicted_cr > 40:
        benefits.append({"factor": "Meaningful CR rate", "value": f"{recommendation.predicted_cr:.0f}% CR",
                        "weight": "high"})
    if recommendation.predicted_pfs_months > 6:
        benefits.append({"factor": "Durable responses", "value": f"{recommendation.predicted_pfs_months:.1f} mo PFS",
                        "weight": "moderate"})

    benefits.append({"factor": "Potential for cure", "value": "Long-term disease-free survival possible",
                    "weight": "high"})

    # Risks
    if recommendation.crs_risk == "high":
        risks.append({"factor": "CRS risk", "value": "High-grade CRS likely", "weight": "high",
                      "mitigation": "Prophylactic tocilizumab, ICU standby"})
    elif recommendation.crs_risk == "moderate":
        risks.append({"factor": "CRS risk", "value": "Moderate CRS expected", "weight": "moderate",
                      "mitigation": "Tocilizumab on hand, close monitoring"})

    if recommendation.icans_risk in ("high", "moderate"):
        risks.append({"factor": "Neurotoxicity", "value": f"{recommendation.icans_risk} ICANS risk", "weight": "moderate",
                      "mitigation": "ICE assessment q8h, dexamethasone protocol"})

    risks.append({"factor": "Cytopenias", "value": "Prolonged pancytopenia expected",
                 "weight": "moderate", "mitigation": "Growth factor support, transfusion protocol"})

    if patient.age > 65:
        risks.append({"factor": "Age-related toxicity", "value": "Higher TRM in elderly",
                     "weight": "moderate", "mitigation": "Reduced-intensity lymphodepletion consideration"})

    # Overall benefit-risk ratio
    benefit_score = sum(1.0 if b["weight"] == "high" else 0.5 for b in benefits)
    risk_score = sum(1.0 if r["weight"] == "high" else 0.5 for r in risks)
    ratio = benefit_score / max(risk_score, 0.1)

    return {
        "benefits": benefits,
        "risks": risks,
        "benefit_score": round(benefit_score, 1),
        "risk_score": round(risk_score, 1),
        "benefit_risk_ratio": round(ratio, 2),
        "recommendation": (
            "Strongly favorable" if ratio > 2.5 else
            "Favorable" if ratio > 1.5 else
            "Balanced — discuss with patient" if ratio > 0.8 else
            "Unfavorable — consider alternatives"
        ),
    }


def _patient_summary(patient: PatientProfile) -> Dict[str, Any]:
    """Generate a structured patient summary."""
    risk_factors = []
    if patient.age > 65:
        risk_factors.append("Advanced age")
    if patient.prior_lines >= 3:
        risk_factors.append(f"{patient.prior_lines} prior lines of therapy")
    if patient.prior_car_t:
        risk_factors.append("Prior CAR-T exposure")
    if patient.ecog_status >= 2:
        risk_factors.append(f"ECOG {patient.ecog_status}")
    if patient.tumor_burden_mm > 80:
        risk_factors.append("High tumor burden")
    if patient.double_hit:
        risk_factors.append("Double-hit biology")
    if patient.tp53_mutated:
        risk_factors.append("TP53 mutated")

    return {
        "demographics": f"{patient.age}yo, {patient.weight_kg}kg",
        "diagnosis": f"{patient.cancer_type} Stage {patient.cancer_stage}",
        "prior_treatment": f"{patient.prior_lines} prior lines" + (" (includes prior CAR-T)" if patient.prior_car_t else ""),
        "performance_status": f"ECOG {patient.ecog_status}",
        "tumor_burden": f"{patient.tumor_burden_mm}mm",
        "risk_factors": risk_factors,
        "risk_category": (
            "high" if len(risk_factors) >= 3 else
            "intermediate" if len(risk_factors) >= 1 else
            "standard"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Comparison Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def compare_treatments(patient: PatientProfile, product_keys: List[str]) -> Dict[str, Any]:
    """Head-to-head comparison of specific products for a patient."""
    comparisons = []

    for key in product_keys:
        if key not in CART_PRODUCTS:
            continue
        rec = _score_product(patient, key, CART_PRODUCTS[key])
        comparisons.append({
            "product_key": key,
            "product_name": rec.product_name,
            "suitability": round(rec.suitability_score, 3),
            "predicted_orr": round(rec.predicted_orr, 1),
            "predicted_cr": round(rec.predicted_cr, 1),
            "pfs_months": round(rec.predicted_pfs_months, 1),
            "crs_risk": rec.crs_risk,
            "icans_risk": rec.icans_risk,
            "warnings_count": len(rec.warnings),
        })

    comparisons.sort(key=lambda c: c["suitability"], reverse=True)

    return {
        "patient": _patient_summary(patient),
        "comparisons": comparisons,
        "winner": comparisons[0]["product_key"] if comparisons else None,
    }


def get_all_products_detail() -> List[Dict[str, Any]]:
    """Return detailed info on all CAR-T products."""
    return [
        {
            "key": key,
            "name": prod["name"],
            "manufacturer": prod["manufacturer"],
            "target": prod["target"],
            "costimulatory": prod["costimulatory"],
            "indications": prod["approved_indications"],
            "approval_year": prod["approval_year"],
            "dose": prod["standard_dose"],
            "lymphodepletion": prod["lymphodepletion"],
            "trial": prod["pivotal_trial"],
            "orr": prod["historical_orr"],
            "cr": prod["historical_cr"],
            "pfs": prod["median_pfs_months"],
            "crs_rate": prod["grade3_crs_rate"],
            "icans_rate": prod["grade3_icans_rate"],
            "manufacturing_days": prod["manufacturing_time_days"],
        }
        for key, prod in CART_PRODUCTS.items()
    ]
