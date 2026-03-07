"""
CARVanta – Safety & Toxicity Analysis v3
==========================================
CARVanta-Original: Tissue Risk Heatmap & Off-Tumor Toxicity Prediction.

Evaluates off-target toxicity risk using GTEx-style normal tissue panels.
Builds an organ-level risk heatmap covering 15+ organ systems.
Flags critical organ expression (brain, heart, lung, liver, kidney).

v3: Adds Tissue Risk Heatmap, organ-level toxicity scoring, and
    real GTEx data integration via real_data_fetcher.
"""

from features.tumor_features import generate_features


# ─── Constants ──────────────────────────────────────────────────────────────────
MAX_NORMAL_EXPRESSION = 10.0
SAFETY_RISK_EXPONENT = 1.5

# Risk level thresholds
_HIGH_RISK_THRESHOLD = 0.50
_MODERATE_RISK_THRESHOLD = 0.25

# Critical organ threshold (TPM) — expression above this is a red flag
_CRITICAL_ORGAN_TPM_THRESHOLD = 5.0

# ─── Organ systems for Tissue Risk Heatmap ──────────────────────────────────────
ORGAN_SYSTEMS = [
    "Brain", "Heart", "Lung", "Liver", "Kidney",
    "GI Tract", "Blood", "Skin", "Muscle", "Nerve",
    "Adipose", "Breast", "Reproductive", "Endocrine",
    "Immune", "Vascular", "Bladder",
]

# Critical organs — expression here is an immediate safety concern
CRITICAL_ORGANS = {"Brain", "Heart", "Lung", "Liver", "Kidney"}

# ─── GTEx-modeled normal tissue expression baselines (TPM) ──────────────────────
# Used when real GTEx data is unavailable
# These are approximate median TPM values for a "typical" antigen
_DEFAULT_TISSUE_BASELINES = {
    "Brain": 0.8,
    "Heart": 1.2,
    "Lung": 2.5,
    "Liver": 1.5,
    "Kidney": 2.0,
    "GI Tract": 3.0,
    "Blood": 4.0,
    "Skin": 1.8,
    "Muscle": 0.5,
    "Nerve": 0.6,
    "Adipose": 1.0,
    "Breast": 1.5,
    "Reproductive": 2.0,
    "Endocrine": 2.5,
    "Immune": 3.5,
    "Vascular": 1.2,
    "Bladder": 1.5,
}


def compute_safety_profile(features: dict) -> dict:
    """
    Compute a safety profile from a feature dictionary (v3).

    Parameters
    ----------
    features : dict
        Must contain keys: tumor_specificity, normal_expression_risk,
        stability_score, literature_support.
        Optional: surface_accessibility, immunogenicity_score

    Returns
    -------
    dict with safety_margin, risk_level, toxicity_flags, and overall_safe
    """
    ner = features["normal_expression_risk"]
    ts = features["tumor_specificity"]
    stability = features["stability_score"]
    surface_access = features.get("surface_accessibility", 0.5)
    immunogenicity = features.get("immunogenicity_score", 0.5)

    safety_margin = round(max(1 - ner, 0), 3)

    # Risk level classification
    if ner >= _HIGH_RISK_THRESHOLD:
        risk_level = "High"
    elif ner >= _MODERATE_RISK_THRESHOLD:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Toxicity flags
    toxicity_flags = []
    if ner >= _HIGH_RISK_THRESHOLD:
        toxicity_flags.append("High normal-tissue expression — significant off-target risk")
    if ts < 0.60:
        toxicity_flags.append("Low tumor specificity — poor selective targeting")
    if stability < 0.70:
        toxicity_flags.append("Unstable antigen expression — inconsistent targeting")
    if safety_margin < 0.30:
        toxicity_flags.append("Narrow safety margin — limited therapeutic window")

    # Surface accessibility flags
    if surface_access < 0.30:
        toxicity_flags.append("Primarily intracellular — not accessible to CAR-T cells")
    elif surface_access < 0.50:
        toxicity_flags.append("Limited surface expression — may reduce CAR-T efficacy")

    # Immunogenicity flags
    if immunogenicity < 0.30:
        toxicity_flags.append("Low immunogenicity — antigen may evade immune detection")

    overall_safe = risk_level == "Low" and len(toxicity_flags) == 0

    return {
        "safety_margin": safety_margin,
        "risk_level": risk_level,
        "toxicity_flags": toxicity_flags,
        "overall_safe": overall_safe,
        "surface_accessible": surface_access > 0.50,
        "immunogenic": immunogenicity > 0.60,
    }


def compute_therapeutic_index(tumor_expr: float, normal_expr: float) -> dict:
    """
    Compute the therapeutic index (ratio of tumor to normal expression).

    A higher TI indicates a wider therapeutic window and better
    candidate for targeted therapy.
    """
    if normal_expr <= 0:
        normal_expr = 0.01

    ti = round(tumor_expr / normal_expr, 2)

    if ti >= 5.0:
        window = "Wide — excellent therapeutic window"
    elif ti >= 3.0:
        window = "Moderate — acceptable therapeutic window"
    elif ti >= 1.5:
        window = "Narrow — limited therapeutic window"
    else:
        window = "Poor — tumor and normal expression nearly equal"

    return {
        "therapeutic_index": ti,
        "window_label": window,
    }


def predict_off_tumor_toxicity(antigen_name: str) -> dict:
    """
    CARVanta-Original: Tissue Risk Heatmap — organ-level toxicity prediction.

    Predicts off-tumor/on-target toxicity by mapping antigen expression
    across 15+ organ systems using a GTEx-modeled normal tissue panel.
    Flags any critical organ (brain, heart, etc.) with significant expression.

    Parameters
    ----------
    antigen_name : str
        Antigen to evaluate.

    Returns
    -------
    dict with tissue_risk_map, critical_organ_alerts, aggregate_toxicity_index,
    tissue_risk_score (0-1), and safety_recommendation
    """
    antigen = antigen_name.upper()
    features = generate_features(antigen)

    # Get base normal expression level for this antigen
    raw_normal = features.get("raw_normal_expression", 3.0)
    ner = features["normal_expression_risk"]

    # Try to fetch real GTEx data
    tissue_data = {}
    real_data_available = False

    try:
        from data.real_data_fetcher import get_fetcher
        fetcher = get_fetcher()
        gtex_data = fetcher.fetch_gtex_expression(antigen)
        if gtex_data.get("status") == "fetched" and gtex_data.get("organ_summary"):
            tissue_data = gtex_data["organ_summary"]
            real_data_available = True
    except (ImportError, Exception):
        pass

    # If no real data, generate tissue-level estimates from base expression
    if not real_data_available:
        import random
        random.seed(hash(antigen) % (2**31))
        for organ in ORGAN_SYSTEMS:
            # Scale baseline by the antigen's overall normal expression
            baseline = _DEFAULT_TISSUE_BASELINES.get(organ, 1.5)
            scale_factor = raw_normal / 3.0  # Normalize to average
            tissue_tpm = round(baseline * scale_factor * random.uniform(0.5, 1.5), 2)
            tissue_data[organ] = tissue_tpm

    # ── Build Tissue Risk Heatmap ───────────────────────────────────────────
    tissue_risk_map = {}
    critical_organ_alerts = []
    risk_scores = []

    for organ in ORGAN_SYSTEMS:
        tpm = tissue_data.get(organ, 0.0)

        # Compute organ-level risk score (0-1)
        # Higher TPM in normal tissue → higher risk
        organ_risk = round(min((tpm / MAX_NORMAL_EXPRESSION) ** SAFETY_RISK_EXPONENT, 1.0), 3)

        # Risk classification
        if organ_risk >= 0.50:
            risk_class = "HIGH"
        elif organ_risk >= 0.20:
            risk_class = "MODERATE"
        elif organ_risk >= 0.05:
            risk_class = "LOW"
        else:
            risk_class = "NEGLIGIBLE"

        tissue_risk_map[organ] = {
            "estimated_tpm": round(tpm, 2),
            "risk_score": organ_risk,
            "risk_class": risk_class,
            "is_critical": organ in CRITICAL_ORGANS,
            "data_source": "GTEx" if real_data_available else "estimated",
        }

        risk_scores.append(organ_risk)

        # Flag critical organs
        if organ in CRITICAL_ORGANS and tpm > _CRITICAL_ORGAN_TPM_THRESHOLD:
            critical_organ_alerts.append({
                "organ": organ,
                "estimated_tpm": round(tpm, 2),
                "risk_score": organ_risk,
                "severity": "CRITICAL" if tpm > 10 else "WARNING",
                "message": (
                    f"{organ}: TPM={tpm:.1f} — "
                    f"{'CRITICAL: high expression in vital organ' if tpm > 10 else 'Warning: moderate expression in vital organ'}"
                ),
            })

    # ── Aggregate Toxicity Index ────────────────────────────────────────────
    # CARVanta-Original: weighted average giving 2x importance to critical organs
    weighted_risks = []
    for organ in ORGAN_SYSTEMS:
        entry = tissue_risk_map[organ]
        weight = 2.0 if organ in CRITICAL_ORGANS else 1.0
        weighted_risks.append(entry["risk_score"] * weight)

    total_weight = len(ORGAN_SYSTEMS) + len(CRITICAL_ORGANS)  # Extra weight for critical
    aggregate_toxicity = round(sum(weighted_risks) / total_weight, 3) if total_weight > 0 else 0.0

    # Tissue risk score (0-1, inverted: 1 = safe, 0 = dangerous)
    tissue_risk_score = round(1 - aggregate_toxicity, 3)

    # ── Safety Recommendation ───────────────────────────────────────────────
    if len(critical_organ_alerts) == 0 and aggregate_toxicity < 0.15:
        recommendation = (
            f"FAVORABLE — {antigen} shows low normal tissue expression across all organ systems. "
            f"Minimal predicted off-tumor toxicity."
        )
    elif len(critical_organ_alerts) == 0 and aggregate_toxicity < 0.30:
        recommendation = (
            f"ACCEPTABLE — {antigen} has moderate normal tissue expression in some organs. "
            f"Standard CAR-T safety monitoring recommended."
        )
    elif any(a["severity"] == "CRITICAL" for a in critical_organ_alerts):
        critical_organs_str = ", ".join(
            a["organ"] for a in critical_organ_alerts if a["severity"] == "CRITICAL"
        )
        recommendation = (
            f"DANGEROUS — {antigen} has high expression in critical organs ({critical_organs_str}). "
            f"Severe off-tumor toxicity risk. Consider safety switches (e.g., suicide genes) "
            f"or alternative targets."
        )
    else:
        warned_organs_str = ", ".join(a["organ"] for a in critical_organ_alerts)
        recommendation = (
            f"CAUTION — {antigen} has notable expression in {warned_organs_str}. "
            f"Dose optimization and safety monitoring essential."
        )

    return {
        "antigen": antigen,
        "tissue_risk_map": tissue_risk_map,
        "critical_organ_alerts": critical_organ_alerts,
        "aggregate_toxicity_index": aggregate_toxicity,
        "tissue_risk_score": tissue_risk_score,
        "data_source": "GTEx (real)" if real_data_available else "estimated (GTEx-modeled)",
        "safety_recommendation": recommendation,
        "organs_analyzed": len(tissue_risk_map),
    }


def generate_safety_report(antigen_name: str) -> dict:
    """
    Generate a comprehensive safety report for a given antigen (v3).

    Combines feature extraction, safety profile analysis, therapeutic
    index, Tissue Risk Heatmap, and surface/immunogenicity analysis.
    """
    features = generate_features(antigen_name)
    profile = compute_safety_profile(features)

    # Use raw expression values if available, otherwise estimate
    tumor_expr = features.get("raw_tumor_expression", None)
    normal_expr = features.get("raw_normal_expression", None)

    if tumor_expr is None or normal_expr is None:
        ts = features["tumor_specificity"]
        ner = features["normal_expression_risk"]
        approx_normal = (ner ** (1 / SAFETY_RISK_EXPONENT)) * MAX_NORMAL_EXPRESSION
        if ts < 1.0:
            approx_tumor = ts * approx_normal / (1 - ts)
        else:
            approx_tumor = approx_normal * 10
        tumor_expr = approx_tumor
        normal_expr = approx_normal

    ti_result = compute_therapeutic_index(tumor_expr, normal_expr)

    # v3: Tissue Risk Heatmap
    toxicity_map = predict_off_tumor_toxicity(antigen_name)

    # Build summary
    flags = profile["toxicity_flags"]
    surface_note = "surface-accessible" if profile["surface_accessible"] else "intracellular"
    immuno_note = "immunogenic" if profile["immunogenic"] else "low immunogenicity"
    critical_count = len(toxicity_map["critical_organ_alerts"])

    if profile["overall_safe"] and critical_count == 0:
        summary = (
            f"{antigen_name.upper()} demonstrates a favorable safety profile "
            f"with a {profile['risk_level'].lower()} off-target risk, "
            f"therapeutic index of {ti_result['therapeutic_index']}, "
            f"{surface_note}, {immuno_note}, and no critical organ alerts."
        )
    elif profile["risk_level"] == "High" or critical_count > 0:
        alert_organs = ", ".join(
            a["organ"] for a in toxicity_map["critical_organ_alerts"]
        )
        summary = (
            f"{antigen_name.upper()} poses significant safety concerns: "
            f"{'; '.join(flags)}. Therapeutic index: {ti_result['therapeutic_index']}. "
            f"Critical organ alerts: {alert_organs if alert_organs else 'none'}."
        )
    else:
        summary = (
            f"{antigen_name.upper()} has a {profile['risk_level'].lower()} risk profile. "
            f"Flagged issues: {'; '.join(flags) if flags else 'none'}. "
            f"Therapeutic index: {ti_result['therapeutic_index']}. "
            f"Surface: {surface_note}. Immunogenicity: {immuno_note}."
        )

    return {
        "antigen": antigen_name.upper(),
        "features": features,
        "safety_profile": profile,
        "therapeutic_index": ti_result,
        "tissue_risk_heatmap": toxicity_map,
        "clinical_trials": features.get("clinical_trials_count", 0),
        "summary": summary,
    }
