"""
CARVanta – ML Training Pipeline v4
=====================================
Trains Random Forest + XGBoost classifier AND XGBoost regression ranker.
v4: Adds regression ranker that predicts continuous Clinical Success
    Probability (0-1), enabling ML-driven adaptive rankings.

Usage:
    cd CARVanta
    python models/train_pipeline.py
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_validate
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score,
)

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# ─── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "biomarker_database.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "car_t_model.pkl")
RANKER_PATH = os.path.join(BASE_DIR, "models", "car_t_ranker.pkl")
REPORT_PATH = os.path.join(BASE_DIR, "data", "training_report.json")
CV_REPORT_PATH = os.path.join(BASE_DIR, "data", "cross_validation_report.json")

# ─── Feature engineering (v2) ──────────────────────────────────────────────────
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


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived features from raw expression values (v2)."""
    df = df.copy()

    t = df["mean_tumor_expression"]
    n = df["mean_normal_expression"]

    # Core features
    df["tumor_specificity"] = (t / (t + n)).round(3)
    df["normal_expression_risk"] = ((n / 10.0).clip(upper=1.0) ** 1.5).round(3)
    df["safety_margin"] = (1 - df["normal_expression_risk"]).clip(lower=0).round(3)

    # v2: Ensure columns exist
    if "immunogenicity_score" not in df.columns:
        df["immunogenicity_score"] = 0.5
    if "surface_accessibility" not in df.columns:
        df["surface_accessibility"] = 0.5
    if "clinical_trials_count" not in df.columns:
        df["clinical_trials_count"] = 0

    # Clinical boost: log-scaled trial count influence
    df["clinical_boost"] = np.log1p(df["clinical_trials_count"]).round(3)
    # Normalize to [0, 1]
    max_boost = df["clinical_boost"].max()
    if max_boost > 0:
        df["clinical_boost"] = (df["clinical_boost"] / max_boost).round(3)

    # Composite score (v2)
    df["composite_score"] = (
        0.25 * df["tumor_specificity"] +
        0.20 * df["safety_margin"] +
        0.15 * df["stability_score"] +
        0.15 * df["literature_support"] +
        0.10 * df["immunogenicity_score"] +
        0.10 * df["surface_accessibility"] +
        0.05 * df["clinical_boost"]
    ).round(3)

    return df


def train():
    """Main training pipeline (v4)."""

    print("=" * 60)
    print("  CARVanta ML Training Pipeline v4")
    print("=" * 60)

    # ── Load data ────────────────────────────────────────────────────────────
    print(f"\n  Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"  Rows: {len(df):,}  Columns: {list(df.columns)}")

    # ── Engineer features ────────────────────────────────────────────────────
    print("\n  Engineering features...")
    df = engineer_features(df)

    X = df[ENGINEERED_FEATURES].values
    y = df["viability_label"].values

    viable_count = int(y.sum())
    total = len(y)
    print(f"  Features: {ENGINEERED_FEATURES}")
    print(f"  Viable: {viable_count:,} ({viable_count/total:.1%})")
    print(f"  Non-viable: {total - viable_count:,} ({(total - viable_count)/total:.1%})")

    # ── Define models ────────────────────────────────────────────────────────
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    if HAS_XGB:
        xgb = XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=max((total - viable_count) / max(viable_count, 1), 1),
            random_state=42,
            eval_metric="logloss",
            use_label_encoder=False,
        )
        ensemble = VotingClassifier(
            estimators=[("rf", rf), ("xgb", xgb)],
            voting="soft",
        )
    else:
        print("  [WARN] XGBoost not available, using RandomForest only")
        ensemble = rf

    # ── Cross-validation with per-fold metrics ────────────────────────────────
    print("\n  Running 5-fold stratified cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Multi-metric CV
    scoring_metrics = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    cv_results = cross_validate(
        ensemble, X, y, cv=cv,
        scoring=scoring_metrics,
        return_train_score=False,
    )

    # Per-fold metrics log
    fold_results = []
    for i in range(5):
        fold_data = {
            "fold": i + 1,
            "accuracy": round(float(cv_results["test_accuracy"][i]), 4),
            "precision": round(float(cv_results["test_precision"][i]), 4),
            "recall": round(float(cv_results["test_recall"][i]), 4),
            "f1": round(float(cv_results["test_f1"][i]), 4),
            "roc_auc": round(float(cv_results["test_roc_auc"][i]), 4),
        }
        fold_results.append(fold_data)
        print(f"    Fold {i+1}: Acc={fold_data['accuracy']:.4f}  "
              f"F1={fold_data['f1']:.4f}  AUC={fold_data['roc_auc']:.4f}")

    # Aggregate CV metrics
    cv_aggregate = {}
    for metric in scoring_metrics:
        values = cv_results[f"test_{metric}"]
        cv_aggregate[metric] = {
            "mean": round(float(values.mean()), 4),
            "std": round(float(values.std()), 4),
        }
    print(f"\n  Aggregate CV Metrics:")
    for metric, vals in cv_aggregate.items():
        print(f"    {metric:<12} {vals['mean']:.4f} ± {vals['std']:.4f}")

    # ── Train final model on full data ───────────────────────────────────────
    print("\n  Training final model on full dataset...")
    ensemble.fit(X, y)

    preds = ensemble.predict(X)
    train_acc = accuracy_score(y, preds)
    train_prec = precision_score(y, preds, zero_division=0)
    train_rec = recall_score(y, preds, zero_division=0)
    train_f1 = f1_score(y, preds, zero_division=0)

    print(f"\n  Training Set Metrics:")
    print(f"    Accuracy:   {train_acc:.4f}")
    print(f"    Precision:  {train_prec:.4f}")
    print(f"    Recall:     {train_rec:.4f}")
    print(f"    F1-Score:   {train_f1:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y, preds, target_names=["Non-Viable", "Viable"]))

    cm = confusion_matrix(y, preds)
    print(f"  Confusion Matrix:")
    print(f"    TN={cm[0][0]:,}  FP={cm[0][1]:,}")
    print(f"    FN={cm[1][0]:,}  TP={cm[1][1]:,}")

    # ── Feature importance ───────────────────────────────────────────────────
    importance = {}
    try:
        if hasattr(ensemble, "feature_importances_"):
            imp = ensemble.feature_importances_
        elif hasattr(ensemble, "estimators_"):
            imp_list = [
                est.feature_importances_
                for _, est in ensemble.estimators_
                if hasattr(est, "feature_importances_")
            ]
            imp = np.mean(imp_list, axis=0) if imp_list else None
        else:
            imp = None

        if imp is not None:
            importance = {
                ENGINEERED_FEATURES[i]: round(float(imp[i]), 4)
                for i in range(len(ENGINEERED_FEATURES))
            }
            print("\n  Feature Importance:")
            for feat, val in sorted(importance.items(), key=lambda x: x[1], reverse=True):
                bar = "█" * int(val * 50)
                print(f"    {feat:<25s} {val:.4f}  {bar}")
    except Exception:
        pass

    # ── Save model ───────────────────────────────────────────────────────────
    joblib.dump(ensemble, MODEL_PATH)
    print(f"\n  Model saved: {MODEL_PATH}")

    # ── Save report ──────────────────────────────────────────────────────────
    report = {
        "version": "v3",
        "features": ENGINEERED_FEATURES,
        "dataset_rows": len(df),
        "viable_count": viable_count,
        "cv_metrics": cv_aggregate,
        "cv_fold_results": fold_results,
        "train_accuracy": round(train_acc, 4),
        "train_precision": round(train_prec, 4),
        "train_recall": round(train_rec, 4),
        "train_f1": round(train_f1, 4),
        "feature_importance": importance,
    }
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved: {REPORT_PATH}")

    # Save cross-validation report separately
    cv_report = {
        "k": 5,
        "scoring_metrics": scoring_metrics,
        "fold_results": fold_results,
        "aggregate": cv_aggregate,
    }
    with open(CV_REPORT_PATH, "w") as f:
        json.dump(cv_report, f, indent=2)
    print(f"  CV Report saved: {CV_REPORT_PATH}")
    print("\n" + "=" * 60)

    return report


def train_ranker():
    """
    CARVanta v4: Train a regression ranker that predicts continuous
    Clinical Success Probability (0.0 – 1.0).

    Ground truth is derived from:
    - clinical_trials_count (more trials → higher validation)
    - viability_label (binary expert annotation)
    - Feature quality signals (stability, specificity, etc.)

    The ranker output is blended with CVS for adaptive ranking.
    """
    print("\n" + "=" * 60)
    print("  CARVanta ML Ranker Training (v4)")
    print("=" * 60)

    if not HAS_XGB:
        print("  [WARN] XGBoost not available, skipping ranker training.")
        return None

    # Load and engineer features
    df = pd.read_csv(DATA_PATH)
    df = engineer_features(df)

    X = df[ENGINEERED_FEATURES].values

    # ── Compute continuous success target ──────────────────────────────────
    # This is the key innovation: instead of binary 0/1, we create a
    # continuous target (0.0 - 1.0) that represents clinical success
    # probability based on multiple evidence signals.
    trials = df["clinical_trials_count"].values.astype(float)
    label = df["viability_label"].values.astype(float)
    ts = df["tumor_specificity"].values
    sm = df["safety_margin"].values
    stab = df["stability_score"].values
    lit = df["literature_support"].values

    # Normalized trial score: log-scaled, capped at 1.0
    max_trials = max(trials.max(), 1)
    trial_score = np.log1p(trials) / np.log1p(max_trials)

    # Evidence-weighted success probability:
    #   40% clinical trial evidence (real-world validation)
    #   25% expert viability label
    #   15% tumor specificity (biological basis)
    #   10% safety margin (therapeutic window)
    #   10% literature + stability (data quality)
    y_continuous = (
        0.40 * trial_score +
        0.25 * label +
        0.15 * ts +
        0.10 * sm +
        0.10 * ((lit + stab) / 2)
    ).clip(0, 1)

    print(f"  Training data: {len(df):,} rows")
    print(f"  Target range: [{y_continuous.min():.3f}, {y_continuous.max():.3f}]")
    print(f"  Target mean:  {y_continuous.mean():.3f}")

    # ── Train XGBRegressor ─────────────────────────────────────────────────
    ranker = XGBRegressor(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
    )

    # 5-fold cross-validation for regression
    from sklearn.model_selection import KFold, cross_val_score
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_r2 = cross_val_score(ranker, X, y_continuous, cv=kf, scoring="r2")
    cv_mae = -cross_val_score(ranker, X, y_continuous, cv=kf, scoring="neg_mean_absolute_error")

    print(f"\n  Cross-Validation (5-fold):")
    print(f"    R²:  {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")
    print(f"    MAE: {cv_mae.mean():.4f} ± {cv_mae.std():.4f}")

    # Train on full data
    ranker.fit(X, y_continuous)

    # Training set predictions
    y_pred = ranker.predict(X)
    train_r2 = 1 - np.sum((y_continuous - y_pred) ** 2) / np.sum((y_continuous - y_continuous.mean()) ** 2)
    train_mae = np.mean(np.abs(y_continuous - y_pred))

    print(f"\n  Training Set Metrics:")
    print(f"    R²:  {train_r2:.4f}")
    print(f"    MAE: {train_mae:.4f}")

    # Feature importance for ranker
    importance = {}
    if hasattr(ranker, "feature_importances_"):
        imp = ranker.feature_importances_
        importance = {
            ENGINEERED_FEATURES[i]: round(float(imp[i]), 4)
            for i in range(len(ENGINEERED_FEATURES))
        }
        print("\n  Ranker Feature Importance:")
        for feat, val in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(val * 50)
            print(f"    {feat:<25s} {val:.4f}  {bar}")

    # Save ranker
    joblib.dump(ranker, RANKER_PATH)
    print(f"\n  Ranker saved: {RANKER_PATH}")

    # Verify: show top-5 predictions for known targets
    known = df[df["antigen_name"].isin(["CD19", "BCMA", "CD22", "HER2", "EGFR", "MESOTHELIN"])]
    if len(known) > 0:
        known_X = engineer_features(known)[ENGINEERED_FEATURES].values
        known_preds = ranker.predict(known_X)
        print("\n  Verification — Predicted Clinical Success Probability:")
        for i, (_, row) in enumerate(known.iterrows()):
            print(f"    {row['antigen_name']:>12s} ({row['cancer_type']:<20s}) → {known_preds[i]:.3f}")

    print("\n" + "=" * 60)
    return {"cv_r2_mean": round(cv_r2.mean(), 4), "cv_mae_mean": round(cv_mae.mean(), 4)}


if __name__ == "__main__":
    train()
    train_ranker()
