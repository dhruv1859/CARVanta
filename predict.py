"""
CARVanta – ML Prediction Module v4
=====================================
Loads the trained classifier AND regression ranker, provides
prediction + ranking score for individual antigen feature vectors.

v4: Adds predict_ranking_score() — continuous ML-driven ranking.
"""

import os
import joblib
import numpy as np

# ─── Load models ────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "car_t_model.pkl")
RANKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "car_t_ranker.pkl")

model = joblib.load(MODEL_PATH)

# Ranker is optional — may not be trained yet
ranker = None
if os.path.exists(RANKER_PATH):
    ranker = joblib.load(RANKER_PATH)

# ─── Feature order must match train_pipeline.py ────────────────────────────────
FEATURE_NAMES = [
    "tumor_specificity",
    "normal_expression_risk",
    "safety_margin",
    "stability_score",
    "literature_support",
    "immunogenicity_score",
    "surface_accessibility",
    "clinical_boost",
    "composite_score",
]


def _engineer(features: dict) -> dict:
    """Compute derived features from the raw feature dict (v2)."""
    ts = features["tumor_specificity"]
    ner = features["normal_expression_risk"]
    stab = features["stability_score"]
    lit = features["literature_support"]
    immuno = features.get("immunogenicity_score", 0.5)
    surface = features.get("surface_accessibility", 0.5)
    trials = features.get("clinical_trials_count", 0)

    safety_margin = max(1 - ner, 0)

    # Clinical boost: log-scaled, normalized to ~[0, 1]
    # Max observed is ~250 trials (CD19), log1p(250) ≈ 5.52
    clinical_boost = round(np.log1p(trials) / 5.52, 3)
    clinical_boost = min(clinical_boost, 1.0)

    composite = (
        0.25 * ts +
        0.20 * safety_margin +
        0.15 * stab +
        0.15 * lit +
        0.10 * immuno +
        0.10 * surface +
        0.05 * clinical_boost
    )

    return {
        "tumor_specificity": ts,
        "normal_expression_risk": ner,
        "safety_margin": round(safety_margin, 3),
        "stability_score": stab,
        "literature_support": lit,
        "immunogenicity_score": immuno,
        "surface_accessibility": surface,
        "clinical_boost": clinical_boost,
        "composite_score": round(composite, 3),
    }


def predict_viability(features: dict) -> dict:
    """
    Predict viability for a single antigen (v2).

    Parameters
    ----------
    features : dict with keys tumor_specificity, normal_expression_risk,
               stability_score, literature_support, and optionally
               immunogenicity_score, surface_accessibility, clinical_trials_count

    Returns
    -------
    dict with prediction, confidence, confidence_label, importance, contributions
    """

    eng = _engineer(features)

    input_data = np.array([[eng[f] for f in FEATURE_NAMES]])

    prediction = model.predict(input_data)[0]
    probability = float(model.predict_proba(input_data).max())

    # Feature importance
    importance_dict = {}
    try:
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "estimators_"):
            imp_list = [
                est.feature_importances_
                for _, est in model.estimators_
                if hasattr(est, "feature_importances_")
            ]
            importances = np.mean(imp_list, axis=0) if imp_list else None
        else:
            importances = None

        if importances is not None:
            importance_dict = {
                FEATURE_NAMES[i]: round(float(importances[i]), 4)
                for i in range(len(FEATURE_NAMES))
            }
    except Exception:
        pass

    # SHAP-like contribution (feature value × importance weight)
    contributions = {}
    for i, feat in enumerate(FEATURE_NAMES):
        value = input_data[0][i]
        weight = importance_dict.get(feat, 0)
        contributions[feat] = round(float(value * weight), 4)

    confidence_label = (
        "High" if probability > 0.9
        else "Medium" if probability > 0.75
        else "Low"
    )

    return {
        "prediction": int(prediction),
        "confidence": round(probability, 3),
        "confidence_label": confidence_label,
        "importance": importance_dict,
        "contributions": contributions,
    }


def predict_ranking_score(features: dict) -> float:
    """
    CARVanta v4: Predict a continuous Clinical Success Probability (0.0–1.0)
    using the trained XGBRegressor ranker.

    This score is meant to be BLENDED with the rule-based CVS to produce
    adaptive, ML-driven rankings that differ per antigen and context.

    Returns
    -------
    float in [0.0, 1.0] — higher = more likely clinical success
    Returns 0.5 (neutral) if ranker is not available.
    """
    if ranker is None:
        return 0.5  # Neutral fallback

    eng = _engineer(features)
    input_data = np.array([[eng[f] for f in FEATURE_NAMES]])
    score = float(ranker.predict(input_data)[0])
    return max(0.0, min(1.0, score))  # Clip to [0, 1]


def predict_ranking_scores_batch(features_list: list) -> np.ndarray:
    """
    CARVanta v4: Batch predict ranking scores for multiple antigens at once.
    Much faster than calling predict_ranking_score() in a loop.

    Parameters
    ----------
    features_list : list of dict
        Each dict contains tumor_specificity, normal_expression_risk, etc.

    Returns
    -------
    np.ndarray of shape (n,) with scores clipped to [0, 1].
    Returns array of 0.5 if ranker is not available.
    """
    n = len(features_list)
    if ranker is None or n == 0:
        return np.full(n, 0.5)

    # Engineer all features and build matrix at once
    rows = []
    for features in features_list:
        eng = _engineer(features)
        rows.append([eng[f] for f in FEATURE_NAMES])

    input_data = np.array(rows)
    scores = ranker.predict(input_data)
    return np.clip(scores, 0.0, 1.0)
