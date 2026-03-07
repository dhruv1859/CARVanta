"""
CARVanta – CVS (CAR-T Viability Score) Engine v3
====================================================
CARVanta-Original: Adaptive Weighted Scoring Algorithm

8-feature weighted scoring formula with confidence-adjusted weights.
Multi-source consensus scoring combining TCGA, GTEx, HPA, UniProt data.

Features:
    1. Tumor Specificity        (0.25) – TCGA differential expression
    2. Safety Score             (0.20) – GTEx normal tissue risk (inverted)
    3. Stability Score          (0.12) – Expression consistency across samples
    4. Literature/Evidence      (0.10) – Published clinical support + trial data
    5. Immunogenicity Score     (0.10) – Immune recognition potential
    6. Surface Accessibility    (0.08) – Membrane localization (UniProt/HPA)
    7. Tissue Risk Score        (0.08) – GTEx organ-level risk heatmap
    8. Protein Validation       (0.07) – HPA protein-level confirmation

Adaptive Weight Adjustment:
    When real data is available, weights shift to give more credence to
    features backed by real data vs estimated values.
"""


# ─── Default v3 weights ────────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "tumor_specificity":    0.25,
    "safety":               0.20,
    "stability":            0.12,
    "evidence":             0.10,
    "immunogenicity":       0.10,
    "surface_accessibility": 0.08,
    "tissue_risk":          0.08,
    "protein_validation":   0.07,
}


def _adaptive_weights(features: dict, base_weights: dict = None) -> dict:
    """
    CARVanta-Original: Adaptive Weight Adjustment.

    Shifts weights based on data confidence — features backed by real data
    receive higher weights, while estimated features receive lower weights.

    Parameters
    ----------
    features : dict
        Feature dictionary with optional `_data_confidence` dict indicating
        which features have real data backing (0.0 = synthetic, 1.0 = real).
    base_weights : dict
        Base weight configuration. Defaults to DEFAULT_WEIGHTS.

    Returns
    -------
    dict of adjusted weights (still sums to 1.0)
    """
    weights = dict(base_weights or DEFAULT_WEIGHTS)

    confidence = features.get("_data_confidence", {})
    if not confidence:
        return weights

    # Adjust: boost weights for high-confidence features, reduce for low
    adjustment_factor = 0.15  # max ±15% shift

    for key in weights:
        conf = confidence.get(key, 0.5)  # default moderate confidence
        # Scale: conf=1.0 → +15%, conf=0.0 → -15%, conf=0.5 → no change
        shift = adjustment_factor * (conf - 0.5) * 2
        weights[key] = weights[key] * (1 + shift)

    # Renormalize to sum to 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 4) for k, v in weights.items()}

    return weights


def compute_cvs(features: dict, weights: dict = None) -> dict:
    """
    Compute the CAR-T Viability Score (CVS v3) from a feature dictionary.

    CARVanta-Original: 8-feature Adaptive Weighted Scoring.

    Parameters
    ----------
    features : dict
        Must contain: tumor_specificity, normal_expression_risk,
        stability_score, literature_support.
        Optional (v2+): immunogenicity_score, surface_accessibility
        Optional (v3): tissue_risk_score, protein_validation_score,
                       _data_confidence

    weights : dict, optional
        Custom weight configuration. If None, uses adaptive weights.

    Returns
    -------
    dict with CVS, confidence, tier, breakdown, version, weights_used
    """

    # ─── Extract features ───────────────────────────────────────────────────
    tumor_score = features["tumor_specificity"]
    safety_score = 1 - features["normal_expression_risk"]
    stability_score = features["stability_score"]
    evidence_score = features["literature_support"]

    # v2 features (backward compat)
    immunogenicity = features.get("immunogenicity_score", 0.5)
    surface_access = features.get("surface_accessibility", 0.5)

    # v3 features (new)
    tissue_risk_raw = features.get("tissue_risk_score", None)
    protein_validation = features.get("protein_validation_score", None)

    # If v3 features unavailable, estimate from existing data
    if tissue_risk_raw is None:
        # Estimate from normal expression risk (lower normal expr → lower tissue risk)
        tissue_risk_score = 1 - features["normal_expression_risk"]
    else:
        tissue_risk_score = 1 - tissue_risk_raw  # Invert: lower risk = better

    if protein_validation is None:
        # Estimate from surface accessibility + stability as proxy
        protein_validation = round(
            0.6 * surface_access + 0.4 * stability_score, 3
        )

    # ─── Compute adaptive weights ───────────────────────────────────────────
    if weights is None:
        w = _adaptive_weights(features)
    else:
        w = weights

    # ─── CVS v3: 8-feature Adaptive Weighted Scoring ───────────────────────
    cvs = (
        w.get("tumor_specificity", 0.25) * tumor_score +
        w.get("safety", 0.20) * safety_score +
        w.get("stability", 0.12) * stability_score +
        w.get("evidence", 0.10) * evidence_score +
        w.get("immunogenicity", 0.10) * immunogenicity +
        w.get("surface_accessibility", 0.08) * surface_access +
        w.get("tissue_risk", 0.08) * tissue_risk_score +
        w.get("protein_validation", 0.07) * protein_validation
    )

    # ─── Feature breakdown ──────────────────────────────────────────────────
    breakdown = {
        "tumor_specificity": round(tumor_score, 3),
        "safety_component": round(safety_score, 3),
        "stability": round(stability_score, 3),
        "evidence": round(evidence_score, 3),
        "immunogenicity": round(immunogenicity, 3),
        "surface_accessibility": round(surface_access, 3),
        "tissue_risk": round(tissue_risk_score, 3),
        "protein_validation": round(protein_validation, 3),
    }

    # ─── Multi-source Consensus Confidence ──────────────────────────────────
    # CARVanta-Original: confidence is based on how many data sources agree
    data_conf = features.get("_data_confidence", {})
    if data_conf:
        # More real data sources → higher confidence
        real_count = sum(1 for v in data_conf.values() if v >= 0.7)
        total_features = len(data_conf)
        source_confidence = real_count / max(total_features, 1)
    else:
        source_confidence = 0.5  # Unknown data provenance

    # Combine feature-based and source-based confidence
    feature_confidence = round(
        (stability_score + evidence_score + immunogenicity + protein_validation) / 4,
        3
    )
    confidence_score = round(
        0.6 * feature_confidence + 0.4 * source_confidence, 3
    )

    # ─── Tier classification ────────────────────────────────────────────────
    cvs_rounded = round(cvs, 3)
    if cvs_rounded >= 0.85:
        tier = "Tier 1 - Highly Viable"
    elif cvs_rounded >= 0.70:
        tier = "Tier 2 - Promising"
    elif cvs_rounded >= 0.55:
        tier = "Tier 3 - Experimental"
    else:
        tier = "Tier 4 - High Risk"

    return {
        "CVS": cvs_rounded,
        "confidence": confidence_score,
        "tier": tier,
        "breakdown": breakdown,
        "version": "v3",
        "weights_used": w,
    }


def validate_fda_targets(features_func) -> dict:
    """
    Validate that FDA-approved CAR-T targets score in Tier 1.

    Parameters
    ----------
    features_func : callable
        A function that takes an antigen name and returns a feature dict.
        Typically `generate_features` from tumor_features.py.

    Returns
    -------
    dict with per-target results and overall pass/fail
    """
    FDA_TARGETS = ["CD19", "BCMA", "CD22", "GPRC5D"]

    results = {}
    all_pass = True

    for target in FDA_TARGETS:
        features = features_func(target)
        cvs_result = compute_cvs(features)

        is_tier1 = cvs_result["tier"].startswith("Tier 1")
        if not is_tier1:
            all_pass = False

        results[target] = {
            "CVS": cvs_result["CVS"],
            "tier": cvs_result["tier"],
            "pass": is_tier1,
        }

    return {
        "targets": results,
        "all_pass": all_pass,
        "total": len(FDA_TARGETS),
        "passed": sum(1 for r in results.values() if r["pass"]),
    }


def compute_adaptive_score(features: dict, weights: dict = None) -> dict:
    """
    CARVanta v4: Adaptive Score = CVS + ML Ranker Blend.

    Computes the CVS rule-based score AND the ML regression ranker score,
    then blends them:
        adaptive_score = (1 - ml_weight) * CVS + ml_weight * ML_score

    The ML weight is dynamic:
    - Base: 0.40 (40% ML, 60% CVS)
    - If ML ranker is unavailable: falls back to 100% CVS
    - ML weight scales with data quality

    Returns
    -------
    dict with adaptive_score, cvs, ml_score, ml_weight, tier, breakdown
    """
    # Get CVS
    cvs_result = compute_cvs(features, weights)
    cvs_score = cvs_result["CVS"]

    # Get ML ranking score
    try:
        from models.predict import predict_ranking_score
        ml_score = predict_ranking_score(features)
        has_ml = True
    except Exception:
        ml_score = 0.5
        has_ml = False

    # Dynamic ML weight
    if has_ml:
        base_ml_weight = 0.40
        # Scale ML weight by confidence — higher confidence features → trust ML more
        confidence = cvs_result.get("confidence", 0.5)
        ml_weight = base_ml_weight * (0.5 + 0.5 * confidence)  # Range: 0.20 — 0.40
    else:
        ml_weight = 0.0

    # Blend
    adaptive = (1 - ml_weight) * cvs_score + ml_weight * ml_score
    adaptive_rounded = round(adaptive, 3)

    # Tier (on adaptive score)
    if adaptive_rounded >= 0.85:
        tier = "Tier 1 - Highly Viable"
    elif adaptive_rounded >= 0.70:
        tier = "Tier 2 - Promising"
    elif adaptive_rounded >= 0.55:
        tier = "Tier 3 - Experimental"
    else:
        tier = "Tier 4 - High Risk"

    return {
        "adaptive_score": adaptive_rounded,
        "cvs_score": cvs_score,
        "ml_score": round(ml_score, 3),
        "ml_weight": round(ml_weight, 3),
        "confidence": cvs_result.get("confidence", 0.5),
        "tier": tier,
        "breakdown": cvs_result["breakdown"],
        "version": "v4-adaptive",
    }