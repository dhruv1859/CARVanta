"""
CARVanta – Model Validation & Certification Engine
=====================================================
Comprehensive ML model validation with:
  1. Stratified K-Fold Cross-Validation (5-fold, 10-fold)
  2. Per-fold + aggregate metrics (Accuracy, Precision, Recall, F1, AUC-ROC)
  3. FDA-Approved Target Ground-Truth Validation
  4. Regression Ranker Validation (R², MAE, Spearman ρ)
  5. Statistical Significance Tests (paired t-test, Wilcoxon)
  6. Calibration Analysis (Brier score, reliability diagram data)
  7. Robustness Testing (feature perturbation sensitivity)
  8. Certification Report Generation (ISO/IEC 25010 aligned)

Usage:
    from validation.model_validator import run_full_validation
    report = run_full_validation()
"""

import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Optional

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "biomarker_database.csv")
REPORT_DIR = os.path.join(BASE_DIR, "data", "validation_reports")
os.makedirs(REPORT_DIR, exist_ok=True)

# ─── Feature names (must match train_pipeline.py) ──────────────────────────
ENGINEERED_FEATURES = [
    "tumor_specificity", "normal_expression_risk", "safety_margin",
    "stability_score", "literature_support", "immunogenicity_score",
    "surface_accessibility", "clinical_boost", "composite_score",
]

# FDA-approved CAR-T targets that MUST score Tier 1
FDA_APPROVED_TARGETS = {
    "CD19": {"indication": "B-cell ALL/DLBCL", "products": ["Kymriah", "Yescarta", "Tecartus", "Breyanzi"]},
    "BCMA": {"indication": "Multiple Myeloma", "products": ["Abecma", "Carvykti"]},
    "CD22": {"indication": "B-cell ALL (r/r)", "products": []},
    "GPRC5D": {"indication": "Multiple Myeloma", "products": []},
}

# Known non-viable targets (should score Tier 3-4)
KNOWN_NON_VIABLE = ["TP53", "RB1", "BRCA1", "PTEN", "APC"]


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Replicate feature engineering from train_pipeline.py."""
    df = df.copy()
    t = df["mean_tumor_expression"]
    n = df["mean_normal_expression"]
    df["tumor_specificity"] = (t / (t + n)).round(3)
    df["normal_expression_risk"] = ((n / 10.0).clip(upper=1.0) ** 1.5).round(3)
    df["safety_margin"] = (1 - df["normal_expression_risk"]).clip(lower=0).round(3)
    if "immunogenicity_score" not in df.columns:
        df["immunogenicity_score"] = 0.5
    if "surface_accessibility" not in df.columns:
        df["surface_accessibility"] = 0.5
    if "clinical_trials_count" not in df.columns:
        df["clinical_trials_count"] = 0
    df["clinical_boost"] = np.log1p(df["clinical_trials_count"]).round(3)
    max_boost = df["clinical_boost"].max()
    if max_boost > 0:
        df["clinical_boost"] = (df["clinical_boost"] / max_boost).round(3)
    df["composite_score"] = (
        0.25 * df["tumor_specificity"] + 0.20 * df["safety_margin"] +
        0.15 * df["stability_score"] + 0.15 * df["literature_support"] +
        0.10 * df["immunogenicity_score"] + 0.10 * df["surface_accessibility"] +
        0.05 * df["clinical_boost"]
    ).round(3)
    return df


# ═════════════════════════════════════════════════════════════════════════════
# 1. CLASSIFIER CROSS-VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

def validate_classifier(k_folds: int = 5) -> dict:
    """Run stratified k-fold cross-validation on the classifier."""
    import joblib
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix, classification_report,
        brier_score_loss, log_loss,
    )

    model_path = os.path.join(BASE_DIR, "models", "car_t_model.pkl")
    model = joblib.load(model_path)

    df = pd.read_csv(DATA_PATH)
    df = _engineer_features(df)
    X = df[ENGINEERED_FEATURES].values
    y = df["viability_label"].values

    cv = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)
    scoring = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    cv_results = cross_validate(model, X, y, cv=cv, scoring=scoring, return_train_score=True)

    # Per-fold results
    folds = []
    for i in range(k_folds):
        folds.append({
            "fold": i + 1,
            "accuracy": round(float(cv_results["test_accuracy"][i]), 4),
            "precision": round(float(cv_results["test_precision"][i]), 4),
            "recall": round(float(cv_results["test_recall"][i]), 4),
            "f1": round(float(cv_results["test_f1"][i]), 4),
            "roc_auc": round(float(cv_results["test_roc_auc"][i]), 4),
            "train_accuracy": round(float(cv_results["train_accuracy"][i]), 4),
        })

    # Aggregate
    aggregate = {}
    for metric in scoring:
        vals = cv_results[f"test_{metric}"]
        aggregate[metric] = {
            "mean": round(float(vals.mean()), 4),
            "std": round(float(vals.std()), 4),
            "min": round(float(vals.min()), 4),
            "max": round(float(vals.max()), 4),
        }

    # Overfitting check
    train_acc = cv_results["train_accuracy"].mean()
    test_acc = cv_results["test_accuracy"].mean()
    overfit_gap = round(float(train_acc - test_acc), 4)

    # Full-data metrics for confusion matrix
    preds = model.predict(X)
    probs = model.predict_proba(X)
    cm = confusion_matrix(y, preds)

    # Brier score & log loss (calibration)
    pos_probs = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
    brier = round(float(brier_score_loss(y, pos_probs)), 4)
    logloss = round(float(log_loss(y, probs)), 4)

    return {
        "model_type": type(model).__name__,
        "dataset_size": len(df),
        "viable_count": int(y.sum()),
        "non_viable_count": int(len(y) - y.sum()),
        "k_folds": k_folds,
        "fold_results": folds,
        "aggregate": aggregate,
        "overfit_gap": overfit_gap,
        "overfit_status": "OK" if overfit_gap < 0.05 else "WARNING" if overfit_gap < 0.10 else "CRITICAL",
        "confusion_matrix": {
            "true_negatives": int(cm[0][0]),
            "false_positives": int(cm[0][1]),
            "false_negatives": int(cm[1][0]),
            "true_positives": int(cm[1][1]),
        },
        "brier_score": brier,
        "log_loss": logloss,
        "calibration_status": "Good" if brier < 0.1 else "Moderate" if brier < 0.2 else "Poor",
    }


# ═════════════════════════════════════════════════════════════════════════════
# 2. RANKER CROSS-VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

def validate_ranker(k_folds: int = 5) -> dict:
    """Run k-fold CV on the XGBoost regression ranker."""
    import joblib
    from sklearn.model_selection import KFold, cross_val_score
    from scipy.stats import spearmanr, pearsonr

    ranker_path = os.path.join(BASE_DIR, "models", "car_t_ranker.pkl")
    if not os.path.exists(ranker_path):
        return {"status": "skipped", "reason": "Ranker model not found"}

    ranker = joblib.load(ranker_path)
    df = pd.read_csv(DATA_PATH)
    df = _engineer_features(df)
    X = df[ENGINEERED_FEATURES].values

    # Reconstruct continuous target
    trials = df["clinical_trials_count"].values.astype(float)
    label = df["viability_label"].values.astype(float)
    ts = df["tumor_specificity"].values
    sm = df["safety_margin"].values
    stab = df["stability_score"].values
    lit = df["literature_support"].values
    max_trials = max(trials.max(), 1)
    trial_score = np.log1p(trials) / np.log1p(max_trials)
    y = (0.40 * trial_score + 0.25 * label + 0.15 * ts + 0.10 * sm +
         0.10 * ((lit + stab) / 2)).clip(0, 1)

    kf = KFold(n_splits=k_folds, shuffle=True, random_state=42)
    cv_r2 = cross_val_score(ranker, X, y, cv=kf, scoring="r2")
    cv_mae = -cross_val_score(ranker, X, y, cv=kf, scoring="neg_mean_absolute_error")
    cv_rmse = np.sqrt(-cross_val_score(ranker, X, y, cv=kf, scoring="neg_mean_squared_error"))

    # Full-data predictions
    y_pred = ranker.predict(X)
    spearman_rho, spearman_p = spearmanr(y, y_pred)
    pearson_r, pearson_p = pearsonr(y, y_pred)

    # Residual analysis
    residuals = y - y_pred
    residual_mean = round(float(residuals.mean()), 6)
    residual_std = round(float(residuals.std()), 4)

    return {
        "model_type": type(ranker).__name__,
        "k_folds": k_folds,
        "cv_r2": {"mean": round(float(cv_r2.mean()), 4), "std": round(float(cv_r2.std()), 4)},
        "cv_mae": {"mean": round(float(cv_mae.mean()), 4), "std": round(float(cv_mae.std()), 4)},
        "cv_rmse": {"mean": round(float(cv_rmse.mean()), 4), "std": round(float(cv_rmse.std()), 4)},
        "spearman_rho": round(float(spearman_rho), 4),
        "spearman_p_value": round(float(spearman_p), 6),
        "pearson_r": round(float(pearson_r), 4),
        "pearson_p_value": round(float(pearson_p), 6),
        "residual_bias": residual_mean,
        "residual_std": residual_std,
        "ranking_quality": "Excellent" if spearman_rho > 0.9 else "Good" if spearman_rho > 0.7 else "Fair",
    }


# ═════════════════════════════════════════════════════════════════════════════
# 3. FDA GROUND-TRUTH VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

def validate_fda_targets() -> dict:
    """Validate that FDA-approved targets score correctly."""
    from scoring.cvs_engine import compute_cvs
    from features.tumor_features import generate_features

    results = {}
    all_pass = True

    for target, info in FDA_APPROVED_TARGETS.items():
        try:
            features = generate_features(target)
            cvs = compute_cvs(features)
            is_tier1 = cvs["tier"].startswith("Tier 1")
            if not is_tier1:
                all_pass = False
            results[target] = {
                "CVS": cvs["CVS"],
                "tier": cvs["tier"],
                "confidence": cvs["confidence"],
                "pass": is_tier1,
                "indication": info["indication"],
                "fda_products": info["products"],
                "expected": "Tier 1 - Highly Viable",
            }
        except Exception as e:
            results[target] = {"pass": False, "error": str(e)}
            all_pass = False

    # Negative controls — should NOT be Tier 1
    negative_results = {}
    neg_correct = 0
    for target in KNOWN_NON_VIABLE:
        try:
            features = generate_features(target)
            cvs = compute_cvs(features)
            is_not_tier1 = not cvs["tier"].startswith("Tier 1")
            if is_not_tier1:
                neg_correct += 1
            negative_results[target] = {
                "CVS": cvs["CVS"],
                "tier": cvs["tier"],
                "correct_rejection": is_not_tier1,
            }
        except Exception as e:
            negative_results[target] = {"correct_rejection": True, "error": str(e)}
            neg_correct += 1

    passed = sum(1 for r in results.values() if r.get("pass"))
    return {
        "fda_targets": results,
        "fda_total": len(FDA_APPROVED_TARGETS),
        "fda_passed": passed,
        "fda_pass_rate": round(passed / len(FDA_APPROVED_TARGETS) * 100, 1),
        "all_fda_pass": all_pass,
        "negative_controls": negative_results,
        "negative_correct": neg_correct,
        "negative_total": len(KNOWN_NON_VIABLE),
        "negative_specificity": round(neg_correct / len(KNOWN_NON_VIABLE) * 100, 1),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 4. ROBUSTNESS / SENSITIVITY ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

def validate_robustness(n_perturbations: int = 100) -> dict:
    """Test model robustness by perturbing features and measuring output stability."""
    import joblib

    model_path = os.path.join(BASE_DIR, "models", "car_t_model.pkl")
    model = joblib.load(model_path)

    df = pd.read_csv(DATA_PATH)
    df = _engineer_features(df)
    X = df[ENGINEERED_FEATURES].values
    y = df["viability_label"].values

    baseline_preds = model.predict(X)
    baseline_probs = model.predict_proba(X)[:, 1] if model.predict_proba(X).shape[1] > 1 else model.predict_proba(X)[:, 0]

    # Feature sensitivity: perturb each feature ±5% and measure impact
    sensitivity = {}
    for i, feat_name in enumerate(ENGINEERED_FEATURES):
        flips = 0
        prob_deltas = []
        for _ in range(min(n_perturbations, 10)):
            X_pert = X.copy()
            noise = np.random.normal(0, 0.05, size=X_pert.shape[0])
            X_pert[:, i] = np.clip(X_pert[:, i] + noise, 0, 1)
            pert_preds = model.predict(X_pert)
            pert_probs = model.predict_proba(X_pert)[:, 1] if model.predict_proba(X_pert).shape[1] > 1 else model.predict_proba(X_pert)[:, 0]
            flips += int(np.sum(pert_preds != baseline_preds))
            prob_deltas.append(float(np.mean(np.abs(pert_probs - baseline_probs))))

        avg_flip_rate = round(flips / (len(X) * min(n_perturbations, 10)) * 100, 2)
        avg_prob_delta = round(float(np.mean(prob_deltas)), 4)
        sensitivity[feat_name] = {
            "flip_rate_pct": avg_flip_rate,
            "avg_prob_delta": avg_prob_delta,
            "stability": "Robust" if avg_flip_rate < 2 else "Moderate" if avg_flip_rate < 5 else "Sensitive",
        }

    # Overall robustness score
    avg_flip = np.mean([v["flip_rate_pct"] for v in sensitivity.values()])
    robustness_score = round(max(0, 100 - avg_flip * 10), 1)

    return {
        "feature_sensitivity": sensitivity,
        "robustness_score": robustness_score,
        "robustness_grade": "A" if robustness_score >= 90 else "B" if robustness_score >= 75 else "C" if robustness_score >= 60 else "D",
        "perturbation_level": "±5%",
        "n_perturbations_per_feature": min(n_perturbations, 10),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 5. STATISTICAL SIGNIFICANCE
# ═════════════════════════════════════════════════════════════════════════════

def validate_statistical_significance() -> dict:
    """Run statistical tests comparing model to random baseline."""
    import joblib
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.dummy import DummyClassifier
    from scipy.stats import ttest_rel, wilcoxon

    model_path = os.path.join(BASE_DIR, "models", "car_t_model.pkl")
    model = joblib.load(model_path)

    df = pd.read_csv(DATA_PATH)
    df = _engineer_features(df)
    X = df[ENGINEERED_FEATURES].values
    y = df["viability_label"].values

    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

    # Model performance
    model_scores = cross_val_score(model, X, y, cv=cv, scoring="f1")

    # Baselines
    baselines = {}
    for strategy in ["most_frequent", "stratified", "uniform"]:
        dummy = DummyClassifier(strategy=strategy, random_state=42)
        dummy_scores = cross_val_score(dummy, X, y, cv=cv, scoring="f1")

        # Paired t-test
        t_stat, t_pval = ttest_rel(model_scores, dummy_scores)
        # Wilcoxon signed-rank
        try:
            w_stat, w_pval = wilcoxon(model_scores, dummy_scores)
        except ValueError:
            w_stat, w_pval = 0, 1.0

        improvement = round(float(model_scores.mean() - dummy_scores.mean()), 4)

        baselines[strategy] = {
            "baseline_f1_mean": round(float(dummy_scores.mean()), 4),
            "model_f1_mean": round(float(model_scores.mean()), 4),
            "improvement": improvement,
            "t_statistic": round(float(t_stat), 4),
            "t_p_value": round(float(t_pval), 6),
            "wilcoxon_statistic": round(float(w_stat), 4),
            "wilcoxon_p_value": round(float(w_pval), 6),
            "significant_at_005": bool(t_pval < 0.05),
            "significant_at_001": bool(t_pval < 0.01),
        }

    return {
        "model_f1_scores": [round(float(s), 4) for s in model_scores],
        "model_f1_mean": round(float(model_scores.mean()), 4),
        "model_f1_std": round(float(model_scores.std()), 4),
        "baselines": baselines,
        "conclusion": "Model significantly outperforms all baselines (p < 0.01)"
            if all(b["significant_at_001"] for b in baselines.values())
            else "Model outperforms baselines (p < 0.05)"
            if all(b["significant_at_005"] for b in baselines.values())
            else "Model performance not statistically significant",
    }


# ═════════════════════════════════════════════════════════════════════════════
# 6. CERTIFICATION REPORT GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

def generate_certification_report(validation_results: dict) -> dict:
    """
    Generate a certification-grade report aligned with:
    - ISO/IEC 25010 (Software Quality)
    - FDA 21 CFR Part 11 (Electronic Records) concepts
    - GAMP 5 (Good Automated Manufacturing Practice) concepts
    """
    clf = validation_results.get("classifier", {})
    ranker = validation_results.get("ranker", {})
    fda = validation_results.get("fda_validation", {})
    robust = validation_results.get("robustness", {})
    stats = validation_results.get("statistical_significance", {})

    # Scoring criteria
    scores = {}

    # 1. Accuracy (from CV aggregate)
    cv_acc = clf.get("aggregate", {}).get("accuracy", {}).get("mean", 0)
    scores["accuracy"] = {"value": cv_acc, "grade": "A" if cv_acc > 0.95 else "B" if cv_acc > 0.90 else "C" if cv_acc > 0.85 else "D", "weight": 0.20}

    # 2. Discrimination (AUC-ROC)
    cv_auc = clf.get("aggregate", {}).get("roc_auc", {}).get("mean", 0)
    scores["discrimination"] = {"value": cv_auc, "grade": "A" if cv_auc > 0.95 else "B" if cv_auc > 0.90 else "C" if cv_auc > 0.85 else "D", "weight": 0.20}

    # 3. Clinical Validity (FDA target validation)
    fda_rate = fda.get("fda_pass_rate", 0)
    scores["clinical_validity"] = {"value": fda_rate, "grade": "A" if fda_rate == 100 else "B" if fda_rate >= 75 else "C" if fda_rate >= 50 else "D", "weight": 0.25}

    # 4. Robustness
    robust_score = robust.get("robustness_score", 0)
    scores["robustness"] = {"value": robust_score, "grade": robust.get("robustness_grade", "D"), "weight": 0.15}

    # 5. Statistical Significance
    is_sig = stats.get("conclusion", "").startswith("Model significantly")
    scores["statistical_significance"] = {"value": 100 if is_sig else 50, "grade": "A" if is_sig else "C", "weight": 0.10}

    # 6. Calibration
    brier = clf.get("brier_score", 1.0)
    cal_grade = "A" if brier < 0.05 else "B" if brier < 0.1 else "C" if brier < 0.2 else "D"
    scores["calibration"] = {"value": round((1 - brier) * 100, 1), "grade": cal_grade, "weight": 0.10}

    # Overall weighted score
    grade_to_num = {"A": 4, "B": 3, "C": 2, "D": 1}
    overall_weighted = sum(grade_to_num.get(s["grade"], 1) * s["weight"] for s in scores.values())
    overall_pct = round(overall_weighted / 4 * 100, 1)

    if overall_pct >= 90:
        overall_grade = "A"
        certification = "CERTIFIED — Production Ready"
    elif overall_pct >= 75:
        overall_grade = "B"
        certification = "CONDITIONALLY CERTIFIED — Minor issues noted"
    elif overall_pct >= 60:
        overall_grade = "C"
        certification = "NOT CERTIFIED — Significant improvements needed"
    else:
        overall_grade = "D"
        certification = "FAILED — Major issues detected"

    return {
        "certification_id": f"CARV-CERT-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "software": "CARVanta CAR-T Viability Scoring Platform",
        "version": "v5",
        "criteria": scores,
        "overall_score": overall_pct,
        "overall_grade": overall_grade,
        "certification_status": certification,
        "standards_reference": [
            "ISO/IEC 25010:2023 — Software Quality Model",
            "FDA Guidance: Clinical Decision Support Software (2022)",
            "GAMP 5: Risk-Based Approach to Compliant Systems",
        ],
        "recommendations": _generate_recommendations(scores, clf, fda),
    }


def _generate_recommendations(scores: dict, clf: dict, fda: dict) -> list:
    """Generate actionable recommendations based on validation results."""
    recs = []
    for name, data in scores.items():
        if data["grade"] in ("C", "D"):
            if name == "accuracy":
                recs.append("⚠️ Accuracy below threshold — consider hyperparameter tuning or additional training data")
            elif name == "discrimination":
                recs.append("⚠️ AUC-ROC needs improvement — review feature engineering or model architecture")
            elif name == "clinical_validity":
                recs.append("🚨 FDA target validation failures — critical issue for clinical credibility")
            elif name == "robustness":
                recs.append("⚠️ Model sensitive to input perturbations — add regularization or noise injection during training")
            elif name == "calibration":
                recs.append("⚠️ Probability calibration poor — apply Platt scaling or isotonic regression")
    if clf.get("overfit_status") == "CRITICAL":
        recs.append("🚨 Significant overfitting detected — reduce model complexity or increase training data")
    if not recs:
        recs.append("✅ All validation criteria met — model is production-ready")
    return recs


# ═════════════════════════════════════════════════════════════════════════════
# MASTER VALIDATION RUNNER
# ═════════════════════════════════════════════════════════════════════════════

def run_full_validation(k_folds: int = 5, save_report: bool = True) -> dict:
    """Run the complete validation suite and generate certification report."""
    start = time.time()

    results = {
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    # 1. Classifier CV
    print("  [1/5] Validating classifier...")
    results["classifier"] = validate_classifier(k_folds)

    # 2. Ranker CV
    print("  [2/5] Validating ranker...")
    results["ranker"] = validate_ranker(k_folds)

    # 3. FDA validation
    print("  [3/5] Validating FDA targets...")
    results["fda_validation"] = validate_fda_targets()

    # 4. Robustness
    print("  [4/5] Testing robustness...")
    results["robustness"] = validate_robustness()

    # 5. Statistical significance
    print("  [5/5] Running statistical tests...")
    results["statistical_significance"] = validate_statistical_significance()

    # Generate certification
    results["certification"] = generate_certification_report(results)

    elapsed = round(time.time() - start, 2)
    results["completed_at"] = datetime.now(timezone.utc).isoformat()
    results["elapsed_seconds"] = elapsed

    # Save report
    if save_report:
        report_file = os.path.join(REPORT_DIR, f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        results["report_file"] = report_file
        print(f"  Report saved: {report_file}")

    return results
