"""
CARVanta – Explainable AI Module v1
======================================
SHAP-based feature importance explanations for individual predictions.
Shows *why* each antigen scored the way it did, not just the score.

CARVanta-Original: Explainable AI for regulatory transparency.

Usage:
    from features.explainability import explain_prediction
    result = explain_prediction(features_dict)
"""

import os
import numpy as np
import joblib

# ─── Paths ──────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(_BASE_DIR, "models", "car_t_model.pkl")

# ─── Feature names matching train_pipeline.py ───────────────────────────────────
ENGINEERED_FEATURES = [
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

# Human-readable labels
FEATURE_LABELS = {
    "tumor_specificity": "Tumor Specificity",
    "normal_expression_risk": "Normal Tissue Risk",
    "safety_margin": "Safety Margin",
    "stability_score": "Expression Stability",
    "literature_support": "Literature Evidence",
    "immunogenicity_score": "Immunogenicity",
    "surface_accessibility": "Surface Accessibility",
    "clinical_boost": "Clinical Trial Evidence",
    "composite_score": "Composite Score",
}

# ─── Cached explainer ──────────────────────────────────────────────────────────
_explainer = None
_model = None


def _load_model():
    """Load the trained model."""
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            _model = None
    return _model


def _get_explainer():
    """Get or create the SHAP TreeExplainer (cached)."""
    global _explainer
    if _explainer is not None:
        return _explainer

    model = _load_model()
    if model is None:
        return None

    try:
        import shap

        # For VotingClassifier, use the first tree-based estimator
        if hasattr(model, "estimators_"):
            # VotingClassifier — get the RandomForest or XGBoost
            for name, est in model.estimators_:
                if hasattr(est, "feature_importances_"):
                    _explainer = shap.TreeExplainer(est)
                    return _explainer

        # Direct tree model
        if hasattr(model, "feature_importances_"):
            _explainer = shap.TreeExplainer(model)
            return _explainer

    except ImportError:
        # SHAP not installed — use fallback
        pass
    except Exception:
        pass

    return None


def _engineer_features_dict(features: dict) -> np.ndarray:
    """Convert a feature dict into the model's expected numpy array."""
    t = features.get("tumor_specificity", 0.5)
    n = features.get("normal_expression_risk", 0.5)
    safety_margin = max(1 - n, 0)
    stability = features.get("stability_score", 0.5)
    literature = features.get("literature_support", 0.3)
    immunogenicity = features.get("immunogenicity_score", 0.5)
    surface_access = features.get("surface_accessibility", 0.5)

    clinical_trials = features.get("clinical_trials_count", 0)
    clinical_boost = np.log1p(clinical_trials) / max(np.log1p(250), 1)  # Normalize

    composite = (
        0.25 * t + 0.20 * safety_margin + 0.15 * stability +
        0.15 * literature + 0.10 * immunogenicity +
        0.10 * surface_access + 0.05 * clinical_boost
    )

    return np.array([[t, n, safety_margin, stability, literature,
                      immunogenicity, surface_access, clinical_boost,
                      round(composite, 3)]])


def explain_prediction(features: dict) -> dict:
    """
    Generate SHAP-based explanation for a prediction.

    Parameters
    ----------
    features : dict
        Feature dictionary from generate_features().

    Returns
    -------
    dict with shap_values, top_drivers, direction indicators, and narrative
    """
    X = _engineer_features_dict(features)

    explainer = _get_explainer()

    if explainer is not None:
        # SHAP TreeExplainer
        try:
            shap_values = explainer.shap_values(X)

            # For binary classification, use class 1 (viable) SHAP values
            if isinstance(shap_values, list):
                sv = shap_values[1][0]  # Class 1
            else:
                sv = shap_values[0]

            method = "shap_tree"

        except Exception:
            # Fallback to feature-importance-based explanation
            sv = _fallback_importance(features)
            method = "feature_importance"
    else:
        sv = _fallback_importance(features)
        method = "feature_importance"

    # Build explanation
    shap_dict = {}
    top_drivers = []

    for i, feat_name in enumerate(ENGINEERED_FEATURES):
        val = float(sv[i]) if i < len(sv) else 0.0
        label = FEATURE_LABELS.get(feat_name, feat_name)
        direction = "positive" if val > 0 else "negative" if val < 0 else "neutral"

        shap_dict[feat_name] = {
            "value": round(val, 4),
            "label": label,
            "direction": direction,
            "feature_value": round(float(X[0][i]), 3),
        }

        top_drivers.append({
            "feature": feat_name,
            "label": label,
            "shap_value": round(val, 4),
            "direction": direction,
            "feature_value": round(float(X[0][i]), 3),
        })

    # Sort by absolute SHAP value
    top_drivers.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    # Generate narrative
    narrative = _generate_narrative(top_drivers[:5])

    return {
        "method": method,
        "shap_values": shap_dict,
        "top_drivers": top_drivers[:5],
        "narrative": narrative,
        "feature_count": len(ENGINEERED_FEATURES),
    }


def _fallback_importance(features: dict) -> list:
    """
    When SHAP is not available, use model feature importances
    weighted by the actual feature values to approximate explanation.
    """
    model = _load_model()
    X = _engineer_features_dict(features)

    if model is not None:
        try:
            if hasattr(model, "feature_importances_"):
                imp = model.feature_importances_
            elif hasattr(model, "estimators_"):
                imps = [
                    est.feature_importances_
                    for _, est in model.estimators_
                    if hasattr(est, "feature_importances_")
                ]
                imp = np.mean(imps, axis=0) if imps else np.ones(len(ENGINEERED_FEATURES)) / len(ENGINEERED_FEATURES)
            else:
                imp = np.ones(len(ENGINEERED_FEATURES)) / len(ENGINEERED_FEATURES)
        except Exception:
            imp = np.ones(len(ENGINEERED_FEATURES)) / len(ENGINEERED_FEATURES)
    else:
        imp = np.ones(len(ENGINEERED_FEATURES)) / len(ENGINEERED_FEATURES)

    # Approximate SHAP: importance × (feature_value - 0.5) to get direction
    approx_shap = []
    for i in range(len(ENGINEERED_FEATURES)):
        feat_val = float(X[0][i]) if i < X.shape[1] else 0.5
        direction_sign = feat_val - 0.5
        approx = imp[i] * direction_sign
        approx_shap.append(round(float(approx), 4))

    return approx_shap


def _generate_narrative(top_drivers: list) -> str:
    """Generate a human-readable narrative from top SHAP drivers."""
    if not top_drivers:
        return "Insufficient data for explanation."

    parts = []
    for driver in top_drivers[:3]:
        label = driver["label"]
        direction = driver["direction"]
        feat_val = driver["feature_value"]

        if direction == "positive":
            if feat_val > 0.8:
                parts.append(f"Strong {label.lower()} ({feat_val:.2f}) significantly boosts viability")
            else:
                parts.append(f"{label} ({feat_val:.2f}) contributes positively")
        elif direction == "negative":
            if feat_val < 0.3:
                parts.append(f"Low {label.lower()} ({feat_val:.2f}) reduces viability prediction")
            else:
                parts.append(f"{label} ({feat_val:.2f}) has a dampening effect")

    if parts:
        narrative = ". ".join(parts) + "."
    else:
        narrative = "The prediction is based on a balanced combination of features."

    return narrative
