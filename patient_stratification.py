"""
CARVanta – Biomarker Stratification Engine v1
================================================
CARVanta-Original: Patient stratification for CAR-T therapy targeting.

Identifies which patient subgroups would benefit most from a given
antigen target based on expression variance, cancer subtype analysis,
and co-expression biomarker patterns.

Usage:
    from features.patient_stratification import stratify_patients
    result = stratify_patients("CD19", "Leukemia")
"""

import math
import random
from features.tumor_features import antigen_df, generate_features
from scoring.cvs_engine import compute_cvs


# ─── Cancer subtype definitions ─────────────────────────────────────────────────
CANCER_SUBTYPES = {
    "Breast Cancer": [
        {"name": "Triple-Negative (TNBC)", "weight": 0.15, "aggression": "high"},
        {"name": "HER2-positive", "weight": 0.20, "aggression": "high"},
        {"name": "ER-positive/Luminal A", "weight": 0.40, "aggression": "low"},
        {"name": "ER-positive/Luminal B", "weight": 0.25, "aggression": "moderate"},
    ],
    "Lung Adenocarcinoma": [
        {"name": "EGFR-mutant", "weight": 0.25, "aggression": "moderate"},
        {"name": "ALK-rearranged", "weight": 0.05, "aggression": "moderate"},
        {"name": "KRAS-mutant", "weight": 0.30, "aggression": "high"},
        {"name": "Wild-type", "weight": 0.40, "aggression": "moderate"},
    ],
    "Leukemia": [
        {"name": "B-cell ALL", "weight": 0.35, "aggression": "high"},
        {"name": "T-cell ALL", "weight": 0.15, "aggression": "high"},
        {"name": "AML", "weight": 0.30, "aggression": "high"},
        {"name": "CLL", "weight": 0.20, "aggression": "low"},
    ],
    "Lymphoma": [
        {"name": "DLBCL", "weight": 0.40, "aggression": "high"},
        {"name": "Follicular", "weight": 0.25, "aggression": "low"},
        {"name": "Mantle Cell", "weight": 0.15, "aggression": "high"},
        {"name": "Marginal Zone", "weight": 0.10, "aggression": "low"},
        {"name": "Burkitt", "weight": 0.10, "aggression": "high"},
    ],
    "Myeloma": [
        {"name": "Standard Risk", "weight": 0.55, "aggression": "moderate"},
        {"name": "High Risk (del17p/t(4;14))", "weight": 0.25, "aggression": "high"},
        {"name": "Ultra-High Risk (double hit)", "weight": 0.10, "aggression": "high"},
        {"name": "Relapsed/Refractory", "weight": 0.10, "aggression": "high"},
    ],
    "Glioblastoma": [
        {"name": "IDH-wildtype", "weight": 0.70, "aggression": "high"},
        {"name": "IDH-mutant", "weight": 0.20, "aggression": "moderate"},
        {"name": "MGMT-methylated", "weight": 0.10, "aggression": "moderate"},
    ],
    "Melanoma": [
        {"name": "BRAF-mutant", "weight": 0.45, "aggression": "high"},
        {"name": "NRAS-mutant", "weight": 0.20, "aggression": "high"},
        {"name": "Wild-type", "weight": 0.25, "aggression": "moderate"},
        {"name": "Uveal", "weight": 0.10, "aggression": "moderate"},
    ],
    "Colorectal Cancer": [
        {"name": "MSI-High", "weight": 0.15, "aggression": "moderate"},
        {"name": "MSS/KRAS-mutant", "weight": 0.35, "aggression": "high"},
        {"name": "MSS/BRAF-mutant", "weight": 0.15, "aggression": "high"},
        {"name": "MSS/Wild-type", "weight": 0.35, "aggression": "moderate"},
    ],
}

# Default subtypes for cancer types not explicitly defined
DEFAULT_SUBTYPES = [
    {"name": "High Expression", "weight": 0.30, "aggression": "high"},
    {"name": "Moderate Expression", "weight": 0.45, "aggression": "moderate"},
    {"name": "Low Expression", "weight": 0.25, "aggression": "low"},
]

# ─── Co-expression biomarker families ────────────────────────────────────────────
CO_EXPRESSION_GROUPS = {
    "B-cell lineage": ["CD19", "CD20", "CD22", "CD37", "CD79A", "CD79B"],
    "Myeloid lineage": ["CD33", "CD123", "CLEC12A", "FLT3", "CD117"],
    "Plasma cell": ["BCMA", "CD38", "SLAMF7", "CD138"],
    "Adhesion molecules": ["EPCAM", "CEACAM5", "NECTIN4", "CD44V6"],
    "Growth factor receptors": ["HER2", "EGFR", "FGFR2", "PDGFRA", "MET"],
    "Immune checkpoints": ["PD1", "PDL1", "TIGIT", "LAG3", "CTLA4"],
}


def _compute_expression_variance_groups(antigen: str, cancer_type: str) -> dict:
    """
    CARVanta-Original: Analyze expression variance to identify patient subgroups.

    Uses the biomarker database to estimate expression variability across
    patients and identify high-responder vs low-responder subgroups.
    """
    features = generate_features(antigen)
    ts = features["tumor_specificity"]
    ner = features["normal_expression_risk"]
    stab = features["stability_score"]

    # Simulate patient expression distribution based on stability
    # High stability → narrow distribution → more patients respond
    # Low stability → wide distribution → variable response
    random.seed(hash(antigen + cancer_type) % (2**31))

    cv = 1 - stab  # Coefficient of variation (inverse of stability)
    mean_expr = features.get("raw_tumor_expression", 5.0)

    # Generate hypothetical patient groups
    n_patients = 100
    expressions = []
    for _ in range(n_patients):
        expr = random.gauss(mean_expr, mean_expr * cv)
        expressions.append(max(0.1, expr))

    expressions.sort(reverse=True)

    # Quartile analysis
    q1 = expressions[:25]
    q2 = expressions[25:50]
    q3 = expressions[50:75]
    q4 = expressions[75:]

    return {
        "high_expressors": {
            "percentage": 25,
            "mean_expression": round(sum(q1) / len(q1), 2),
            "predicted_response": "High" if ts > 0.7 else "Moderate",
            "estimated_response_rate": round(min(0.95, ts * 1.2), 2),
        },
        "moderate_high": {
            "percentage": 25,
            "mean_expression": round(sum(q2) / len(q2), 2),
            "predicted_response": "Moderate",
            "estimated_response_rate": round(min(0.80, ts * 0.9), 2),
        },
        "moderate_low": {
            "percentage": 25,
            "mean_expression": round(sum(q3) / len(q3), 2),
            "predicted_response": "Low-Moderate",
            "estimated_response_rate": round(min(0.55, ts * 0.6), 2),
        },
        "low_expressors": {
            "percentage": 25,
            "mean_expression": round(sum(q4) / len(q4), 2),
            "predicted_response": "Low",
            "estimated_response_rate": round(min(0.30, ts * 0.3), 2),
        },
        "expression_cv": round(cv, 3),
        "overall_mean": round(mean_expr, 2),
    }


def _find_co_expression_biomarkers(antigen: str) -> list:
    """
    CARVanta-Original: Identify co-expressed biomarkers that predict response.

    Finds genes in the same lineage/family that could serve as
    companion diagnostics for patient selection.
    """
    antigen = antigen.upper()
    co_markers = []

    for group_name, members in CO_EXPRESSION_GROUPS.items():
        if antigen in [m.upper() for m in members]:
            # Found the group — all other members are potential co-markers
            for member in members:
                if member.upper() != antigen:
                    # Check if this gene is in our database
                    match = antigen_df[
                        antigen_df["antigen_name"].str.upper() == member.upper()
                    ]
                    if not match.empty:
                        row = match.iloc[0]
                        co_markers.append({
                            "gene": member,
                            "group": group_name,
                            "correlation": "positive",
                            "tumor_expression": float(row["mean_tumor_expression"]),
                            "potential_use": "companion diagnostic",
                        })

    # If no co-expression group found, suggest based on cancer type
    if not co_markers:
        co_markers.append({
            "gene": "N/A",
            "group": "no co-expression group identified",
            "correlation": "unknown",
            "potential_use": "further research needed",
        })

    return co_markers


def stratify_patients(antigen_name: str, cancer_type: str = None) -> dict:
    """
    CARVanta-Original: Biomarker Stratification Engine.

    Identifies which patient subgroups would benefit most from
    CAR-T therapy targeting the specified antigen.

    Parameters
    ----------
    antigen_name : str
        Antigen target to evaluate.
    cancer_type : str, optional
        Specific cancer type. If None, uses the first cancer type in the database.

    Returns
    -------
    dict with subtype_analysis, expression_groups, co_expression_markers,
    eligibility_estimate, and recommendations
    """
    antigen = antigen_name.upper()

    # Determine cancer type
    if cancer_type is None:
        match = antigen_df[antigen_df["antigen_name"].str.upper() == antigen]
        if not match.empty:
            cancer_type = match.iloc[0]["cancer_type"]
        else:
            cancer_type = "General Cancer"

    # Get CVS for this antigen
    features = generate_features(antigen)
    cvs_result = compute_cvs(features)
    cvs = cvs_result["CVS"]

    # ── 1. Cancer subtype analysis ──────────────────────────────────────────
    subtypes = CANCER_SUBTYPES.get(cancer_type, DEFAULT_SUBTYPES)
    subtype_results = []

    for subtype in subtypes:
        # Estimate benefit based on antigen CVS + subtype aggression
        aggression_bonus = {
            "high": 0.15,
            "moderate": 0.05,
            "low": -0.05,
        }.get(subtype["aggression"], 0)

        subtype_benefit = round(min(cvs + aggression_bonus, 1.0), 3)

        if subtype_benefit >= 0.80:
            benefit_label = "High Benefit"
        elif subtype_benefit >= 0.65:
            benefit_label = "Moderate Benefit"
        elif subtype_benefit >= 0.50:
            benefit_label = "Low Benefit"
        else:
            benefit_label = "Minimal Benefit"

        subtype_results.append({
            "subtype": subtype["name"],
            "population_share": f"{subtype['weight']*100:.0f}%",
            "aggression": subtype["aggression"],
            "predicted_benefit": subtype_benefit,
            "benefit_label": benefit_label,
            "estimated_response_rate": round(subtype_benefit * 0.85, 2),
        })

    # Sort by predicted benefit
    subtype_results.sort(key=lambda x: x["predicted_benefit"], reverse=True)

    # ── 2. Expression variance groups ───────────────────────────────────────
    expr_groups = _compute_expression_variance_groups(antigen, cancer_type)

    # ── 3. Co-expression biomarkers ─────────────────────────────────────────
    co_markers = _find_co_expression_biomarkers(antigen)

    # ── 4. Overall eligibility estimate ─────────────────────────────────────
    # What percentage of patients with this cancer type would be eligible?
    high_responders = expr_groups["high_expressors"]["percentage"]
    moderate_responders = expr_groups["moderate_high"]["percentage"]

    if cvs >= 0.85:
        eligibility = round(high_responders + moderate_responders * 0.8, 1)
    elif cvs >= 0.70:
        eligibility = round(high_responders * 0.9 + moderate_responders * 0.5, 1)
    else:
        eligibility = round(high_responders * 0.6, 1)

    # ── 5. Recommendations ──────────────────────────────────────────────────
    recommendations = []

    if subtype_results[0]["predicted_benefit"] >= 0.80:
        recommendations.append(
            f"Prioritize {subtype_results[0]['subtype']} patients — "
            f"highest predicted benefit ({subtype_results[0]['predicted_benefit']})"
        )

    if expr_groups["expression_cv"] > 0.4:
        recommendations.append(
            "High expression variability — consider tumor biopsy "
            "expression screening for patient selection"
        )

    if co_markers and co_markers[0]["gene"] != "N/A":
        top_marker = co_markers[0]["gene"]
        recommendations.append(
            f"Consider {top_marker} as a companion diagnostic — "
            f"co-expressed in {co_markers[0]['group']}"
        )

    if eligibility < 30:
        recommendations.append(
            "Limited eligible population — consider combination therapy "
            "to expand coverage"
        )

    return {
        "antigen": antigen,
        "cancer_type": cancer_type,
        "cvs": cvs_result["CVS"],
        "tier": cvs_result["tier"],
        "subtype_analysis": subtype_results,
        "expression_groups": expr_groups,
        "co_expression_markers": co_markers,
        "estimated_eligibility_pct": eligibility,
        "recommendations": recommendations,
    }
