"""
CARVanta – Model Validation API Router
========================================
REST endpoints for model validation, benchmarking & certification.
Uses run_in_executor for CPU-bound ML validation to avoid blocking the event loop.
"""

import asyncio
from functools import partial
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v5/validation", tags=["Model Validation"])


def _run_sync(func, *args, **kwargs):
    """Helper to run sync functions — called inside run_in_executor."""
    return func(*args, **kwargs)


@router.get("/run")
async def run_validation(k_folds: int = 5):
    """Run the full validation suite — classifier + ranker + FDA + robustness + stats."""
    from validation.model_validator import run_full_validation
    from features.llm_insight import is_llm_available, call_llm

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None, partial(run_full_validation, k_folds=k_folds, save_report=True)
    )

    # Add LLM interpretation
    if is_llm_available():
        cert = results.get("certification", {})
        clf = results.get("classifier", {})
        agg = clf.get("aggregate", {})
        prompt = (
            f"You are a biomedical AI validation expert. Interpret this model validation report for CARVanta, "
            f"a CAR-T cell therapy antigen scoring platform.\n\n"
            f"Overall Grade: {cert.get('overall_grade', '?')} ({cert.get('overall_score', 0)}%)\n"
            f"Certification: {cert.get('certification_status', '?')}\n"
            f"CV Accuracy: {agg.get('accuracy', {}).get('mean', 0)} ± {agg.get('accuracy', {}).get('std', 0)}\n"
            f"CV AUC-ROC: {agg.get('roc_auc', {}).get('mean', 0)} ± {agg.get('roc_auc', {}).get('std', 0)}\n"
            f"CV F1: {agg.get('f1', {}).get('mean', 0)} ± {agg.get('f1', {}).get('std', 0)}\n"
            f"FDA Target Pass Rate: {results.get('fda_validation', {}).get('fda_pass_rate', 0)}%\n"
            f"Robustness Grade: {results.get('robustness', {}).get('robustness_grade', '?')}\n"
            f"Brier Score: {clf.get('brier_score', '?')}\n"
            f"Overfit Gap: {clf.get('overfit_gap', '?')}\n\n"
            f"Provide: 1) A 2-sentence executive summary, 2) The 3 strongest validation points, "
            f"3) Any concerns or risks, 4) Whether this model is ready for clinical decision support. "
            f"Be specific with numbers. Keep response under 200 words."
        )
        llm_interpretation = await loop.run_in_executor(None, call_llm, prompt)
        if llm_interpretation:
            results["ai_insight"] = llm_interpretation
            results["ai_insight_source"] = "llm"

    return results


@router.get("/classifier")
async def validate_classifier_only(k_folds: int = 5):
    """Run classifier cross-validation only."""
    from validation.model_validator import validate_classifier
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(validate_classifier, k_folds))


@router.get("/ranker")
async def validate_ranker_only(k_folds: int = 5):
    """Run ranker regression validation only."""
    from validation.model_validator import validate_ranker
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(validate_ranker, k_folds))


@router.get("/fda-targets")
async def validate_fda_only():
    """Validate against FDA-approved ground-truth targets."""
    from validation.model_validator import validate_fda_targets
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, validate_fda_targets)


@router.get("/robustness")
async def validate_robustness_only():
    """Test model robustness via feature perturbation."""
    from validation.model_validator import validate_robustness
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, validate_robustness)


@router.get("/statistical-significance")
async def validate_stats_only():
    """Run statistical significance tests vs baselines."""
    from validation.model_validator import validate_statistical_significance
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, validate_statistical_significance)


@router.get("/certification")
async def get_certification():
    """Generate the full certification report."""
    from validation.model_validator import run_full_validation
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None, partial(run_full_validation, k_folds=5, save_report=True)
    )
    return results.get("certification", {})


@router.get("/quick")
async def quick_validation():
    """Quick validation — classifier CV + FDA targets only (faster)."""
    from validation.model_validator import validate_classifier, validate_fda_targets
    loop = asyncio.get_event_loop()
    clf = await loop.run_in_executor(None, partial(validate_classifier, k_folds=5))
    fda = await loop.run_in_executor(None, validate_fda_targets)
    return {
        "classifier": {
            "accuracy": clf["aggregate"]["accuracy"],
            "f1": clf["aggregate"]["f1"],
            "roc_auc": clf["aggregate"]["roc_auc"],
            "overfit_status": clf["overfit_status"],
            "calibration_status": clf["calibration_status"],
        },
        "fda": {
            "pass_rate": fda["fda_pass_rate"],
            "all_pass": fda["all_fda_pass"],
            "targets": {k: {"CVS": v.get("CVS"), "tier": v.get("tier"), "pass": v.get("pass")}
                        for k, v in fda["fda_targets"].items()},
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
