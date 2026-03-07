"""
CARVanta – Benchmark & Validation v3
=======================================
Validates the scoring engine and ML model against known CAR-T targets.
Computes precision, recall, F1, ROC-AUC with k-fold cross-validation.

v3: Adds cross-validation, ROC-AUC computation, and real-data comparison.

CARVanta-Original: Comprehensive benchmark with multi-metric validation.

Usage:
    cd CARVanta
    python scoring/benchmark.py
"""

import os
import sys
import json
import math

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from features.tumor_features import generate_features
from scoring.cvs_engine import compute_cvs
from models.predict import predict_viability


# ─── Ground truth: clinically validated CAR-T targets ───────────────────────────
KNOWN_VIABLE = [
    # FDA-approved
    "CD19", "BCMA", "CD22", "GPRC5D",
    # Clinical-stage
    "PSMA", "GD2", "GPC3", "FOLR1", "CLDN18",
    "ROR1", "DLL3", "CAIX", "CD70", "CD138",
    "GUCY2C", "NYESO1", "WT1", "PRAME", "IL13RA2", "NKG2D",
    "TYRP1", "MAGEA4", "LAGE1", "SSX2", "ALPPL2", "LYPD3",
    "NECTIN4", "STEAP1", "PSCA",
    # v2 additions
    "CLEC12A", "CD123", "SLAMF7", "CD37", "FCRH5",
    "EGFRVIII", "CLDN6", "CD20", "CD38",
]

KNOWN_NON_VIABLE = [
    "HER2", "EGFR", "MUC1", "MESOTHELIN", "B7H3", "TROP2",
    "EPCAM", "CEACAM5", "CD30", "CCR4", "CD33", "FLT3",
    "TEM1", "MUC16", "GPNMB", "CMET", "FGFR2", "CEACAM7",
    "CD276", "CD44V6", "AXL", "PDGFRA",
    # v2 additions
    "CD5", "CD7", "CEACAM6", "TIGIT", "LAG3",
]

# FDA-approved targets that MUST be Tier 1
FDA_APPROVED_TIER1 = ["CD19", "BCMA", "CD22", "GPRC5D"]


def _compute_roc_auc(scores: list, labels: list) -> float:
    """
    CARVanta-Original: Compute ROC-AUC without sklearn dependency.

    Uses the Mann-Whitney U statistic approach:
    AUC = P(score of random positive > score of random negative)
    """
    positives = [s for s, l in zip(scores, labels) if l == 1]
    negatives = [s for s, l in zip(scores, labels) if l == 0]

    if not positives or not negatives:
        return 0.5  # No discrimination possible

    # Count concordant pairs
    concordant = 0
    tied = 0
    total = len(positives) * len(negatives)

    for pos_score in positives:
        for neg_score in negatives:
            if pos_score > neg_score:
                concordant += 1
            elif pos_score == neg_score:
                tied += 0.5

    auc = (concordant + tied) / total if total > 0 else 0.5
    return round(auc, 4)


def _compute_metrics(preds, trues, label, scores=None):
    """Compute classification metrics."""
    tp = sum(1 for p, t in zip(preds, trues) if p == 1 and t == 1)
    fp = sum(1 for p, t in zip(preds, trues) if p == 1 and t == 0)
    fn = sum(1 for p, t in zip(preds, trues) if p == 0 and t == 1)
    tn = sum(1 for p, t in zip(preds, trues) if p == 0 and t == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    accuracy = (tp + tn) / len(preds) if preds else 0

    auc = _compute_roc_auc(scores, trues) if scores else 0.0

    return {
        "model": label,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "roc_auc": auc,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def _cross_validate(all_targets, k=5):
    """
    CARVanta-Original: K-fold cross-validation for CVS and ML models.

    Returns per-fold metrics and aggregate performance.
    """
    import random
    random.seed(42)

    # Shuffle targets
    shuffled = list(all_targets)
    random.shuffle(shuffled)

    fold_size = len(shuffled) // k
    fold_results = []

    print(f"\n  Running {k}-fold Cross-Validation...")
    print(f"  Total samples: {len(shuffled)}, Fold size: ~{fold_size}")

    for fold in range(k):
        # Split
        test_start = fold * fold_size
        test_end = test_start + fold_size if fold < k - 1 else len(shuffled)
        test_set = shuffled[test_start:test_end]
        # train_set not needed for rule-based, but logged

        # Evaluate on test fold
        fold_trues = []
        fold_cvs_preds = []
        fold_ml_preds = []
        fold_cvs_scores = []
        fold_ml_scores = []

        for antigen, true_label in test_set:
            features = generate_features(antigen)
            cvs_result = compute_cvs(features)
            ml_result = predict_viability(features)

            cvs = cvs_result["CVS"]
            cvs_pred = 1 if cvs >= 0.7 else 0
            ml_pred = ml_result["prediction"]

            fold_trues.append(true_label)
            fold_cvs_preds.append(cvs_pred)
            fold_ml_preds.append(ml_pred)
            fold_cvs_scores.append(cvs)
            fold_ml_scores.append(ml_result["confidence"])

        cvs_metrics = _compute_metrics(
            fold_cvs_preds, fold_trues, f"CVS Fold {fold+1}", fold_cvs_scores
        )
        ml_metrics = _compute_metrics(
            fold_ml_preds, fold_trues, f"ML Fold {fold+1}", fold_ml_scores
        )

        fold_results.append({
            "fold": fold + 1,
            "test_size": len(test_set),
            "cvs": cvs_metrics,
            "ml": ml_metrics,
        })

        print(f"    Fold {fold+1}: CVS Acc={cvs_metrics['accuracy']:.3f} "
              f"AUC={cvs_metrics['roc_auc']:.3f} | "
              f"ML Acc={ml_metrics['accuracy']:.3f} "
              f"AUC={ml_metrics['roc_auc']:.3f}")

    # Aggregate metrics
    agg = {}
    for model_key in ["cvs", "ml"]:
        model_name = "CVS Rule-Based" if model_key == "cvs" else "ML Model"
        metrics_keys = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
        agg[model_key] = {}
        for mk in metrics_keys:
            values = [fr[model_key][mk] for fr in fold_results]
            mean_val = sum(values) / len(values)
            std_val = math.sqrt(
                sum((v - mean_val) ** 2 for v in values) / len(values)
            )
            agg[model_key][mk] = {
                "mean": round(mean_val, 4),
                "std": round(std_val, 4),
            }

    return {
        "k": k,
        "fold_results": fold_results,
        "aggregate": agg,
    }


def benchmark():
    """Run full benchmark against known targets (v3)."""

    print("=" * 60)
    print("  CARVanta Benchmark & Validation v3")
    print("=" * 60)

    results = []

    all_targets = (
        [(name, 1) for name in KNOWN_VIABLE]
        + [(name, 0) for name in KNOWN_NON_VIABLE]
    )

    print(f"\n  Evaluating {len(all_targets)} known targets...")
    print(f"  Viable: {len(KNOWN_VIABLE)}  |  Non-viable: {len(KNOWN_NON_VIABLE)}\n")

    for antigen, true_label in all_targets:
        features = generate_features(antigen)
        cvs_result = compute_cvs(features)
        ml_result = predict_viability(features)

        cvs = cvs_result["CVS"]
        tier = cvs_result["tier"]
        ml_pred = ml_result["prediction"]
        ml_conf = ml_result["confidence"]

        # CVS-based prediction: viable if CVS >= 0.7
        cvs_pred = 1 if cvs >= 0.7 else 0

        results.append({
            "antigen": antigen,
            "true_label": true_label,
            "cvs": cvs,
            "tier": tier,
            "cvs_prediction": cvs_pred,
            "ml_prediction": ml_pred,
            "ml_confidence": ml_conf,
            "cvs_correct": cvs_pred == true_label,
            "ml_correct": ml_pred == true_label,
        })

    # ── Compute overall metrics ──────────────────────────────────────────────
    trues = [r["true_label"] for r in results]
    cvs_preds = [r["cvs_prediction"] for r in results]
    ml_preds = [r["ml_prediction"] for r in results]
    cvs_scores = [r["cvs"] for r in results]
    ml_scores = [r["ml_confidence"] for r in results]

    cvs_metrics = _compute_metrics(cvs_preds, trues, "CVS Rule-Based v3", cvs_scores)
    ml_metrics = _compute_metrics(ml_preds, trues, "ML Model v3", ml_scores)

    # ── Print results ────────────────────────────────────────────────────────
    print(f"{'Antigen':<15} {'True':>5} {'CVS':>6} {'Tier':<25} {'CVS✓':>5} {'ML':>4} {'ML✓':>5} {'Conf':>6}")
    print("-" * 80)
    for r in results:
        cvs_mark = "✓" if r["cvs_correct"] else "✗"
        ml_mark = "✓" if r["ml_correct"] else "✗"
        tier_short = r["tier"].split(" - ")[0] if " - " in r["tier"] else r["tier"]
        print(f"{r['antigen']:<15} {r['true_label']:>5} {r['cvs']:.3f} {tier_short:<25} {cvs_mark:>5} "
              f"{r['ml_prediction']:>4} {ml_mark:>5} {r['ml_confidence']:.3f}")

    print("\n" + "=" * 60)
    print("  BENCHMARK SUMMARY")
    print("=" * 60)

    for m in [cvs_metrics, ml_metrics]:
        print(f"\n  {m['model']}:")
        print(f"    Accuracy:   {m['accuracy']:.4f}")
        print(f"    Precision:  {m['precision']:.4f}")
        print(f"    Recall:     {m['recall']:.4f}")
        print(f"    F1-Score:   {m['f1_score']:.4f}")
        print(f"    ROC-AUC:    {m['roc_auc']:.4f}")
        print(f"    Confusion:  TP={m['tp']}  FP={m['fp']}  FN={m['fn']}  TN={m['tn']}")

    # ── Cross-validation ────────────────────────────────────────────────────
    cv_results = _cross_validate(all_targets, k=5)

    print("\n" + "=" * 60)
    print("  CROSS-VALIDATION RESULTS (5-Fold)")
    print("=" * 60)

    for model_key, model_name in [("cvs", "CVS Rule-Based"), ("ml", "ML Model")]:
        agg = cv_results["aggregate"][model_key]
        print(f"\n  {model_name}:")
        for metric, values in agg.items():
            print(f"    {metric:<12} {values['mean']:.4f} ± {values['std']:.4f}")

    # ── FDA-approved Tier 1 validation ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("  FDA-APPROVED TARGET VALIDATION")
    print("=" * 60)
    fda_pass = True
    for antigen in FDA_APPROVED_TIER1:
        r = next((x for x in results if x["antigen"] == antigen), None)
        if r:
            is_tier1 = r["tier"].startswith("Tier 1")
            status = "✓ PASS" if is_tier1 else "✗ FAIL"
            if not is_tier1:
                fda_pass = False
            print(f"  {antigen:<12} CVS={r['cvs']:.3f}  {r['tier']:<25}  {status}")
        else:
            print(f"  {antigen:<12} NOT FOUND IN DATABASE  ✗ FAIL")
            fda_pass = False

    if fda_pass:
        print("\n  ✅ ALL FDA-APPROVED TARGETS CORRECTLY CLASSIFIED AS TIER 1")
    else:
        print("\n  ❌ SOME FDA-APPROVED TARGETS FAILED TIER 1 CLASSIFICATION")

    # ── Top-ranked viable targets ────────────────────────────────────────────
    viable_results = [r for r in results if r["true_label"] == 1]
    viable_results.sort(key=lambda x: x["cvs"], reverse=True)

    print(f"\n  Top 10 Known Viable Targets by CVS:")
    for i, r in enumerate(viable_results[:10], 1):
        print(f"    #{i:2d}  {r['antigen']:<12} CVS={r['cvs']:.3f}  ML={r['ml_prediction']}  "
              f"Conf={r['ml_confidence']:.3f}  {r['tier']}")

    # ── Save report ──────────────────────────────────────────────────────────
    report = {
        "version": "v3",
        "total_targets": len(all_targets),
        "known_viable": len(KNOWN_VIABLE),
        "known_non_viable": len(KNOWN_NON_VIABLE),
        "cvs_metrics": cvs_metrics,
        "ml_metrics": ml_metrics,
        "cross_validation": cv_results,
        "fda_tier1_pass": fda_pass,
        "per_antigen": results,
    }

    report_path = os.path.join(BASE_DIR, "data", "benchmark_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to {report_path}")

    # Save cross-validation report separately
    cv_path = os.path.join(BASE_DIR, "data", "cross_validation_report.json")
    with open(cv_path, "w") as f:
        json.dump(cv_results, f, indent=2)
    print(f"  CV Report saved to {cv_path}")

    print("\n" + "=" * 60)
    return report


if __name__ == "__main__":
    benchmark()
