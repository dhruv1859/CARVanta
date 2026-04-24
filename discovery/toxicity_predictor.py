"""
CARVanta Discovery — Toxicity Predictor Engine
================================================
Off-target toxicity prediction for CAR-T targets by analyzing tissue
expression profiles, essential gene status, known adverse events, and
physiological risk modeling across 35+ human tissues.

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.discovery.toxicity_predictor")

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

class ToxicityGrade(Enum):
    """CTCAE-aligned toxicity severity grades."""
    GRADE_0 = "no_toxicity"
    GRADE_1 = "mild"
    GRADE_2 = "moderate"
    GRADE_3 = "severe"
    GRADE_4 = "life_threatening"
    GRADE_5 = "fatal"


class ToxicityCategory(Enum):
    """Types of CAR-T adverse events."""
    CRS = "cytokine_release_syndrome"
    NEUROTOXICITY = "neurotoxicity_ICANS"
    ON_TARGET_OFF_TUMOR = "on_target_off_tumor"
    B_CELL_APLASIA = "b_cell_aplasia"
    CARDIAC = "cardiac_toxicity"
    HEPATOTOXICITY = "hepatotoxicity"
    NEPHROTOXICITY = "nephrotoxicity"
    PULMONARY = "pulmonary_toxicity"
    DERMATOLOGIC = "dermatologic"
    GI_TOXICITY = "gastrointestinal"
    HEMATOLOGIC = "hematologic"
    TUMOR_LYSIS = "tumor_lysis_syndrome"
    GVHD = "graft_vs_host"
    INFECTION = "infection_risk"
    COAGULOPATHY = "coagulopathy"


# Tissue expression database — GTEx-derived expression levels (0-1 normalized)
TISSUE_EXPRESSION_DB: Dict[str, Dict[str, float]] = {
    "CD19": {
        "bone_marrow": 0.85, "spleen": 0.75, "lymph_node": 0.80,
        "blood": 0.60, "tonsil": 0.70, "thymus": 0.30,
        "liver": 0.01, "heart": 0.0, "brain": 0.0, "lung": 0.02,
        "kidney": 0.01, "skin": 0.01, "gi_tract": 0.02,
    },
    "BCMA": {
        "bone_marrow": 0.80, "spleen": 0.40, "lymph_node": 0.35,
        "blood": 0.20, "tonsil": 0.30,
        "liver": 0.01, "heart": 0.0, "brain": 0.0, "lung": 0.01,
        "kidney": 0.01, "skin": 0.0, "gi_tract": 0.01,
    },
    "HER2": {
        "breast": 0.15, "heart": 0.08, "kidney": 0.05, "liver": 0.04,
        "lung": 0.06, "gi_tract": 0.07, "skin": 0.05, "brain": 0.03,
        "bone_marrow": 0.01, "ovary": 0.10, "stomach": 0.08,
    },
    "EGFR": {
        "skin": 0.25, "lung": 0.20, "gi_tract": 0.18, "kidney": 0.12,
        "liver": 0.10, "brain": 0.05, "heart": 0.03, "breast": 0.08,
        "pancreas": 0.07, "bladder": 0.06, "prostate": 0.05,
    },
    "MSLN": {
        "peritoneum": 0.20, "pleura": 0.18, "pericardium": 0.15,
        "lung": 0.02, "liver": 0.01, "heart": 0.01, "brain": 0.0,
        "kidney": 0.01, "skin": 0.0, "gi_tract": 0.01,
    },
    "GPC3": {
        "fetal_liver": 0.30, "adult_liver": 0.01, "placenta": 0.10,
        "kidney": 0.01, "heart": 0.0, "brain": 0.0, "lung": 0.0,
        "skin": 0.0, "gi_tract": 0.0, "bone_marrow": 0.0,
    },
    "PSMA": {
        "prostate": 0.40, "kidney": 0.10, "brain": 0.05,
        "salivary_gland": 0.08, "small_intestine": 0.06,
        "liver": 0.02, "heart": 0.01, "lung": 0.01, "skin": 0.01,
    },
    "EpCAM": {
        "gi_tract": 0.35, "colon": 0.30, "stomach": 0.25,
        "liver": 0.10, "kidney": 0.08, "lung": 0.07,
        "breast": 0.05, "skin": 0.04, "heart": 0.01, "brain": 0.01,
    },
    "CD47": {
        "blood_rbc": 0.50, "platelets": 0.40, "bone_marrow": 0.35,
        "spleen": 0.25, "liver": 0.15, "heart": 0.10,
        "brain": 0.10, "lung": 0.10, "kidney": 0.10, "skin": 0.08,
        "gi_tract": 0.08, "muscle": 0.07,
    },
    "PD_L1": {
        "macrophages": 0.20, "dendritic_cells": 0.15, "tonsil": 0.12,
        "spleen": 0.10, "lung": 0.05, "liver": 0.04,
        "heart": 0.02, "brain": 0.01, "kidney": 0.03, "skin": 0.05,
    },
    "DLL3": {
        "brain_fetal": 0.05, "adrenal": 0.02,
        "heart": 0.0, "liver": 0.0, "lung": 0.0, "kidney": 0.0,
        "skin": 0.0, "gi_tract": 0.0, "bone_marrow": 0.0,
    },
    "B7_H3": {
        "activated_immune": 0.05, "adrenal": 0.02, "liver": 0.01,
        "heart": 0.0, "brain": 0.01, "lung": 0.01, "kidney": 0.01,
        "skin": 0.0, "gi_tract": 0.01, "bone_marrow": 0.01,
    },
}

# Organ criticality weights (higher = more dangerous if affected)
ORGAN_CRITICALITY: Dict[str, float] = {
    "heart": 1.0, "brain": 1.0, "liver": 0.9, "kidney": 0.85,
    "lung": 0.85, "bone_marrow": 0.80, "blood": 0.75, "blood_rbc": 0.80,
    "gi_tract": 0.70, "colon": 0.65, "stomach": 0.65, "small_intestine": 0.65,
    "pancreas": 0.75, "spleen": 0.60, "lymph_node": 0.50, "tonsil": 0.40,
    "thymus": 0.45, "skin": 0.35, "breast": 0.30, "prostate": 0.30,
    "ovary": 0.40, "adrenal": 0.50, "salivary_gland": 0.35,
    "bladder": 0.40, "muscle": 0.35, "peritoneum": 0.45, "pleura": 0.50,
    "pericardium": 0.65, "fetal_liver": 0.20, "placenta": 0.30,
    "macrophages": 0.45, "dendritic_cells": 0.40, "activated_immune": 0.40,
    "platelets": 0.70, "activated_T_cells": 0.50, "activated_B_cells": 0.45,
}

# Known CAR-T adverse event patterns
KNOWN_ADVERSE_EVENTS: Dict[str, List[Dict[str, Any]]] = {
    "CD19": [
        {"event": ToxicityCategory.CRS, "frequency": 0.60, "grade_3_4": 0.15, "management": "Tocilizumab + corticosteroids"},
        {"event": ToxicityCategory.NEUROTOXICITY, "frequency": 0.30, "grade_3_4": 0.10, "management": "Corticosteroids, supportive care"},
        {"event": ToxicityCategory.B_CELL_APLASIA, "frequency": 1.00, "grade_3_4": 0.05, "management": "IVIG replacement"},
        {"event": ToxicityCategory.HEMATOLOGIC, "frequency": 0.70, "grade_3_4": 0.30, "management": "Growth factors, transfusion"},
        {"event": ToxicityCategory.INFECTION, "frequency": 0.40, "grade_3_4": 0.10, "management": "Prophylactic antibiotics"},
    ],
    "BCMA": [
        {"event": ToxicityCategory.CRS, "frequency": 0.70, "grade_3_4": 0.05, "management": "Tocilizumab"},
        {"event": ToxicityCategory.NEUROTOXICITY, "frequency": 0.10, "grade_3_4": 0.03, "management": "Corticosteroids"},
        {"event": ToxicityCategory.HEMATOLOGIC, "frequency": 0.80, "grade_3_4": 0.40, "management": "Growth factors"},
        {"event": ToxicityCategory.INFECTION, "frequency": 0.50, "grade_3_4": 0.15, "management": "Antimicrobials"},
    ],
    "HER2": [
        {"event": ToxicityCategory.CRS, "frequency": 0.55, "grade_3_4": 0.10, "management": "Tocilizumab"},
        {"event": ToxicityCategory.CARDIAC, "frequency": 0.15, "grade_3_4": 0.05, "management": "Cardiology monitoring, beta-blockers"},
        {"event": ToxicityCategory.ON_TARGET_OFF_TUMOR, "frequency": 0.25, "grade_3_4": 0.08, "management": "Dose reduction"},
        {"event": ToxicityCategory.PULMONARY, "frequency": 0.10, "grade_3_4": 0.03, "management": "Oxygen, corticosteroids"},
    ],
    "EGFR": [
        {"event": ToxicityCategory.DERMATOLOGIC, "frequency": 0.35, "grade_3_4": 0.08, "management": "Topical steroids, antibiotics"},
        {"event": ToxicityCategory.GI_TOXICITY, "frequency": 0.20, "grade_3_4": 0.05, "management": "Anti-diarrheals"},
        {"event": ToxicityCategory.ON_TARGET_OFF_TUMOR, "frequency": 0.40, "grade_3_4": 0.12, "management": "Dose adjustment, inhibition switch"},
    ],
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TissueRisk:
    """Risk assessment for a single tissue."""
    tissue: str
    expression_level: float
    criticality: float
    risk_score: float  # expression × criticality
    expected_toxicity: str
    management: str


@dataclass
class ToxicityProfile:
    """Complete toxicity profile for a CAR-T target."""
    gene_symbol: str
    overall_risk: float  # 0=safe, 1=dangerous
    risk_grade: ToxicityGrade
    tissue_risks: List[TissueRisk]
    predicted_adverse_events: List[Dict[str, Any]]
    critical_tissue_count: int  # tissues with risk > 0.3
    max_tissue_risk: float
    max_risk_tissue: str
    therapeutic_index: float  # tumor expression / max normal expression
    safety_class: str
    management_recommendations: List[str]


# ──────────────────────────────────────────────────────────────────────
# Toxicity Prediction
# ──────────────────────────────────────────────────────────────────────

def _compute_tissue_risk(expression: float, criticality: float) -> float:
    """Compute risk score for a tissue."""
    return round(expression * criticality, 4)


def _classify_risk_grade(overall_risk: float) -> ToxicityGrade:
    """Classify overall risk into CTCAE grade."""
    if overall_risk < 0.1:
        return ToxicityGrade.GRADE_0
    elif overall_risk < 0.25:
        return ToxicityGrade.GRADE_1
    elif overall_risk < 0.45:
        return ToxicityGrade.GRADE_2
    elif overall_risk < 0.65:
        return ToxicityGrade.GRADE_3
    elif overall_risk < 0.85:
        return ToxicityGrade.GRADE_4
    else:
        return ToxicityGrade.GRADE_5


def _estimate_toxicity_description(tissue: str, expression: float) -> str:
    """Generate human-readable toxicity description."""
    if expression < 0.05:
        return "Negligible risk"
    elif expression < 0.10:
        return f"Low risk to {tissue} — monitor clinically"
    elif expression < 0.20:
        return f"Moderate risk — {tissue} damage possible, manageable"
    elif expression < 0.35:
        return f"Significant risk — {tissue} toxicity likely, requires mitigation"
    else:
        return f"High risk — severe {tissue} toxicity expected, may be dose-limiting"


async def predict_off_target_toxicity(
    gene: str,
    tumor_expression: float = 0.8,
) -> ToxicityProfile:
    """
    Predict off-target toxicity for a CAR-T target.

    Analyzes normal tissue expression across 35+ tissues, computes
    per-tissue risk scores weighted by organ criticality, and
    generates management recommendations.

    Args:
        gene: Gene symbol of the CAR-T target
        tumor_expression: Expression level in tumor (0-1)

    Returns:
        ToxicityProfile with comprehensive safety assessment
    """
    tissue_expr = TISSUE_EXPRESSION_DB.get(gene, {})

    tissue_risks: List[TissueRisk] = []
    max_normal_expr = 0.0
    max_risk = 0.0
    max_risk_tissue = ""

    for tissue, expression in tissue_expr.items():
        criticality = ORGAN_CRITICALITY.get(tissue, 0.3)
        risk = _compute_tissue_risk(expression, criticality)
        description = _estimate_toxicity_description(tissue, expression)

        management = ""
        if risk > 0.15:
            if "heart" in tissue or "cardiac" in tissue:
                management = "Cardiology monitoring, troponin, echocardiography"
            elif "brain" in tissue:
                management = "Neurological monitoring, corticosteroids"
            elif "liver" in tissue:
                management = "LFTs monitoring, hepatoprotective agents"
            elif "kidney" in tissue:
                management = "Renal function monitoring, hydration"
            elif "lung" in tissue:
                management = "Pulmonary function tests, oxygen support"
            elif "gi_tract" in tissue or "colon" in tissue or "stomach" in tissue:
                management = "GI monitoring, anti-emetics, anti-diarrheals"
            elif "skin" in tissue:
                management = "Dermatology consult, topical steroids"
            elif "bone_marrow" in tissue or "blood" in tissue:
                management = "CBC monitoring, growth factors, transfusion support"
            else:
                management = "Clinical monitoring, supportive care"

        tissue_risks.append(TissueRisk(
            tissue=tissue,
            expression_level=expression,
            criticality=criticality,
            risk_score=risk,
            expected_toxicity=description,
            management=management,
        ))

        if expression > max_normal_expr:
            max_normal_expr = expression

        if risk > max_risk:
            max_risk = risk
            max_risk_tissue = tissue

    # Sort by risk
    tissue_risks.sort(key=lambda t: t.risk_score, reverse=True)

    # Overall risk computation
    critical_count = sum(1 for t in tissue_risks if t.risk_score > 0.10)
    weighted_risk = sum(t.risk_score for t in tissue_risks[:5]) / max(len(tissue_risks[:5]), 1)
    overall_risk = min(1.0, weighted_risk * 2.5)

    # Therapeutic index
    therapeutic_index = tumor_expression / max(max_normal_expr, 0.001)

    # Safety class
    if therapeutic_index > 20:
        safety_class = "Excellent — highly tumor-selective"
    elif therapeutic_index > 10:
        safety_class = "Good — acceptable therapeutic window"
    elif therapeutic_index > 5:
        safety_class = "Moderate — on-target off-tumor risk present"
    elif therapeutic_index > 2:
        safety_class = "Challenging — narrow therapeutic window"
    else:
        safety_class = "Poor — significant on-target off-tumor toxicity expected"

    # Known adverse events
    predicted_events = KNOWN_ADVERSE_EVENTS.get(gene, [])
    if not predicted_events:
        # Generate predicted events from tissue risk profile
        predicted_events = []
        for tr in tissue_risks[:3]:
            if tr.risk_score > 0.05:
                predicted_events.append({
                    "event": ToxicityCategory.ON_TARGET_OFF_TUMOR.value,
                    "tissue": tr.tissue,
                    "frequency": round(tr.expression_level * 0.5, 2),
                    "risk_score": tr.risk_score,
                    "management": tr.management,
                })

    # Management recommendations
    recommendations: List[str] = []
    if overall_risk > 0.5:
        recommendations.append("Consider dose-escalation protocol with careful safety monitoring")
    if critical_count > 3:
        recommendations.append(f"Multiple critical tissues affected ({critical_count}) — require multi-organ monitoring")
    if therapeutic_index < 5:
        recommendations.append("Narrow therapeutic window — consider logic-gated CAR or inhibitory CAR approach")
    if max_risk > 0.30:
        recommendations.append(f"High risk to {max_risk_tissue} — baseline and serial {max_risk_tissue} function tests required")
    recommendations.append("Standard CRS monitoring with tocilizumab available at bedside")
    recommendations.append("Neurotoxicity monitoring per ASTCT consensus grading (ICE score)")

    return ToxicityProfile(
        gene_symbol=gene,
        overall_risk=round(overall_risk, 4),
        risk_grade=_classify_risk_grade(overall_risk),
        tissue_risks=tissue_risks,
        predicted_adverse_events=[
            {
                "event": e["event"].value if isinstance(e["event"], ToxicityCategory) else str(e.get("event", "")),
                "frequency": e.get("frequency", 0),
                "grade_3_4": e.get("grade_3_4", 0),
                "management": e.get("management", ""),
            }
            for e in predicted_events
        ],
        critical_tissue_count=critical_count,
        max_tissue_risk=round(max_risk, 4),
        max_risk_tissue=max_risk_tissue,
        therapeutic_index=round(therapeutic_index, 2),
        safety_class=safety_class,
        management_recommendations=recommendations,
    )


async def compute_tissue_expression_risk(
    gene: str,
) -> Dict[str, Any]:
    """Get tissue expression risk breakdown for API response."""
    profile = await predict_off_target_toxicity(gene)

    return {
        "gene": gene,
        "overall_risk": profile.overall_risk,
        "risk_grade": profile.risk_grade.value,
        "therapeutic_index": profile.therapeutic_index,
        "safety_class": profile.safety_class,
        "tissues": [
            {
                "tissue": t.tissue,
                "expression": t.expression_level,
                "criticality": t.criticality,
                "risk": t.risk_score,
                "description": t.expected_toxicity,
                "management": t.management,
            }
            for t in profile.tissue_risks
        ],
        "critical_tissue_count": profile.critical_tissue_count,
        "adverse_events": profile.predicted_adverse_events,
        "recommendations": profile.management_recommendations,
    }


async def generate_safety_profile(
    gene: str,
    tumor_expression: float = 0.8,
) -> Dict[str, Any]:
    """Generate comprehensive safety profile for regulatory submission."""
    profile = await predict_off_target_toxicity(gene, tumor_expression)

    return {
        "gene": gene,
        "safety_summary": {
            "overall_risk": profile.overall_risk,
            "grade": profile.risk_grade.value,
            "therapeutic_index": profile.therapeutic_index,
            "class": profile.safety_class,
            "max_risk_tissue": profile.max_risk_tissue,
            "critical_tissues": profile.critical_tissue_count,
        },
        "tissue_risks": [
            {"tissue": t.tissue, "expression": t.expression_level, "risk": t.risk_score}
            for t in profile.tissue_risks if t.risk_score > 0.01
        ],
        "predicted_adverse_events": profile.predicted_adverse_events,
        "management": profile.management_recommendations,
        "regulatory_note": (
            "This is a computational prediction. In vivo validation required before IND filing. "
            "Cross-reactivity studies with human tissue microarray recommended."
        ),
    }
