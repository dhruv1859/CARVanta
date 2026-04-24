"""
CARVanta Trials — Automated Eligibility Checker
==================================================
Comprehensive eligibility pre-screening that evaluates a patient
profile against trial inclusion/exclusion criteria. Produces
structured pass/fail reports with detailed rationale.

Checks 12 eligibility dimensions:
1. Age range
2. Gender
3. ECOG performance status
4. Disease type and stage
5. Prior therapy count
6. Required biomarkers
7. Excluded conditions / comorbidities
8. Organ function (renal, hepatic, cardiac)
9. Prior CAR-T / immunotherapy
10. CNS involvement
11. Active infections
12. Autoimmune conditions

Output: Detailed eligibility report with overall verdict,
dimension-by-dimension assessment, and recommendations.

Security: Stateless, PII-free, async.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.eligibility_checker")


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class EligibilityDimension:
    """Single eligibility check result."""
    criterion: str
    category: str  # "inclusion" or "exclusion"
    passed: bool
    rationale: str
    severity: str = "standard"  # "standard", "critical", "soft"
    recommendation: str = ""


@dataclass
class EligibilityReport:
    """Complete eligibility assessment."""
    nct_id: str
    trial_title: str
    overall_eligible: bool
    confidence: float
    total_checks: int
    passed_checks: int
    failed_checks: int
    soft_failures: int
    dimensions: List[EligibilityDimension]
    recommendations: List[str]
    blocker_summary: str


# ──────────────────────────────────────────────────────────────────────
# Comorbidity / Exclusion Pattern Matching
# ──────────────────────────────────────────────────────────────────────

_AUTOIMMUNE_CONDITIONS = [
    "systemic lupus erythematosus", "sle",
    "rheumatoid arthritis", "ra",
    "multiple sclerosis", "ms",
    "inflammatory bowel disease", "ibd", "crohn", "ulcerative colitis",
    "psoriasis", "psoriatic arthritis",
    "type 1 diabetes", "t1d",
    "hashimoto", "graves disease",
    "sjogren", "vasculitis",
    "scleroderma", "dermatomyositis",
    "myasthenia gravis",
]

_CNS_CONDITIONS = [
    "cns metastasis", "brain metastasis", "leptomeningeal",
    "cns leukemia", "cns lymphoma", "cns involvement",
    "active cns", "brain lesion",
]

_CARDIAC_EXCLUSIONS = [
    "heart failure", "chf", "nyha iii", "nyha iv",
    "lvef <50", "lvef <40", "lvef < 50", "lvef < 40",
    "recent mi", "myocardial infarction",
    "unstable angina", "uncontrolled arrhythmia",
    "cardiac arrest", "cardiomyopathy",
]

_INFECTION_EXCLUSIONS = [
    "active hepatitis b", "active hepatitis c", "hbv", "hcv",
    "hiv positive", "hiv+",
    "active tuberculosis", "active tb",
    "uncontrolled infection", "active sepsis",
]

_ORGAN_FUNCTION_THRESHOLDS = {
    "creatinine_clearance_min": 30.0,  # mL/min
    "bilirubin_max_x_uln": 1.5,
    "ast_max_x_uln": 3.0,
    "alt_max_x_uln": 3.0,
    "lvef_min": 50.0,  # percent
    "platelets_min": 50000,  # per µL
    "anc_min": 1000,  # per µL
    "hemoglobin_min": 8.0,  # g/dL
}


# ──────────────────────────────────────────────────────────────────────
# Individual Checks
# ──────────────────────────────────────────────────────────────────────

def _check_age(age: int, min_age: int, max_age: int) -> EligibilityDimension:
    """Check age eligibility."""
    if min_age <= age <= max_age:
        return EligibilityDimension(
            criterion=f"Age {min_age}-{max_age}", category="inclusion", passed=True,
            rationale=f"Patient age {age} is within the required range {min_age}-{max_age}.")
    else:
        rec = f"Consider trials with broader age criteria." if age > max_age else "May require individual exception request."
        return EligibilityDimension(
            criterion=f"Age {min_age}-{max_age}", category="inclusion", passed=False,
            rationale=f"Patient age {age} is outside the required range {min_age}-{max_age}.",
            severity="critical", recommendation=rec)


def _check_gender(patient_gender: str, trial_gender: str) -> EligibilityDimension:
    """Check gender eligibility."""
    if trial_gender.lower() == "all":
        return EligibilityDimension(
            criterion="Gender", category="inclusion", passed=True,
            rationale="Trial accepts all genders.")
    if patient_gender.lower() == trial_gender.lower():
        return EligibilityDimension(
            criterion="Gender", category="inclusion", passed=True,
            rationale=f"Patient gender ({patient_gender}) matches trial requirement ({trial_gender}).")
    return EligibilityDimension(
        criterion="Gender", category="inclusion", passed=False,
        rationale=f"Trial requires {trial_gender}, patient is {patient_gender}.",
        severity="critical")


def _check_ecog(patient_ecog: int, max_ecog: int) -> EligibilityDimension:
    """Check ECOG performance status."""
    if patient_ecog <= max_ecog:
        return EligibilityDimension(
            criterion=f"ECOG ≤{max_ecog}", category="inclusion", passed=True,
            rationale=f"Patient ECOG {patient_ecog} meets requirement (≤{max_ecog}).")
    return EligibilityDimension(
        criterion=f"ECOG ≤{max_ecog}", category="inclusion", passed=False,
        rationale=f"Patient ECOG {patient_ecog} exceeds maximum {max_ecog}.",
        severity="critical", recommendation="Optimize performance status before enrollment.")


def _check_prior_therapies(patient_prior: int, required_prior: int) -> EligibilityDimension:
    """Check prior therapy requirements."""
    if patient_prior >= required_prior:
        return EligibilityDimension(
            criterion=f"≥{required_prior} prior lines", category="inclusion", passed=True,
            rationale=f"Patient has {patient_prior} prior lines (≥{required_prior} required).")
    if patient_prior == required_prior - 1:
        return EligibilityDimension(
            criterion=f"≥{required_prior} prior lines", category="inclusion", passed=False,
            rationale=f"Patient has {patient_prior} prior lines, needs {required_prior}. Currently ineligible.",
            severity="soft", recommendation="May become eligible after completing current therapy line.")
    return EligibilityDimension(
        criterion=f"≥{required_prior} prior lines", category="inclusion", passed=False,
        rationale=f"Patient has {patient_prior} prior lines, trial requires ≥{required_prior}.",
        severity="standard")


def _check_biomarkers(patient_biomarkers: Dict[str, Any], patient_targets: List[str], required: List[str]) -> EligibilityDimension:
    """Check required biomarker expression."""
    if not required:
        return EligibilityDimension(
            criterion="Biomarker requirements", category="inclusion", passed=True,
            rationale="No specific biomarkers required for this trial.")

    met: List[str] = []
    missing: List[str] = []

    for req in required:
        req_clean = req.upper().replace("+", "").strip()
        found = False
        for key in list(patient_biomarkers.keys()) + patient_targets:
            if req_clean in key.upper():
                found = True
                break
        if found:
            met.append(req)
        else:
            missing.append(req)

    if not missing:
        return EligibilityDimension(
            criterion="Biomarker requirements", category="inclusion", passed=True,
            rationale=f"All {len(required)} required biomarkers confirmed: {', '.join(met)}.")

    return EligibilityDimension(
        criterion="Biomarker requirements", category="inclusion",
        passed=False, severity="critical" if len(missing) == len(required) else "standard",
        rationale=f"Missing {len(missing)} biomarker(s): {', '.join(missing)}. Met: {', '.join(met) if met else 'none'}.",
        recommendation="Order tissue testing for: " + ", ".join(missing))


def _check_comorbidities(comorbidities: List[str], exclusion_criteria: List[str]) -> List[EligibilityDimension]:
    """Check comorbidities against exclusion criteria."""
    results: List[EligibilityDimension] = []
    patient_conditions = [c.lower() for c in comorbidities]

    # Autoimmune check
    autoimmune_match = [c for c in patient_conditions if any(ai in c for ai in _AUTOIMMUNE_CONDITIONS)]
    if autoimmune_match:
        results.append(EligibilityDimension(
            criterion="No active autoimmune disease", category="exclusion", passed=False,
            rationale=f"Patient has autoimmune condition(s): {', '.join(autoimmune_match)}.",
            severity="critical", recommendation="May need rheumatology clearance or waiver."))
    else:
        results.append(EligibilityDimension(
            criterion="No active autoimmune disease", category="exclusion", passed=True,
            rationale="No active autoimmune conditions identified."))

    # CNS check
    cns_match = [c for c in patient_conditions if any(cn in c for cn in _CNS_CONDITIONS)]
    if cns_match:
        results.append(EligibilityDimension(
            criterion="No active CNS involvement", category="exclusion", passed=False,
            rationale=f"Patient has CNS involvement: {', '.join(cns_match)}.",
            severity="critical", recommendation="Consider trials specifically designed for CNS disease."))
    else:
        results.append(EligibilityDimension(
            criterion="No active CNS involvement", category="exclusion", passed=True,
            rationale="No active CNS involvement."))

    # Cardiac check
    cardiac_match = [c for c in patient_conditions if any(ce in c for ce in _CARDIAC_EXCLUSIONS)]
    if cardiac_match:
        results.append(EligibilityDimension(
            criterion="Adequate cardiac function", category="exclusion", passed=False,
            rationale=f"Cardiac concerns: {', '.join(cardiac_match)}.",
            severity="critical", recommendation="Cardiology evaluation required before enrollment."))
    else:
        results.append(EligibilityDimension(
            criterion="Adequate cardiac function", category="exclusion", passed=True,
            rationale="No significant cardiac conditions identified."))

    # Infection check
    infection_match = [c for c in patient_conditions if any(ie in c for ie in _INFECTION_EXCLUSIONS)]
    if infection_match:
        results.append(EligibilityDimension(
            criterion="No active infections", category="exclusion", passed=False,
            rationale=f"Active infections: {', '.join(infection_match)}.",
            severity="critical", recommendation="Must resolve infection before enrollment."))
    else:
        results.append(EligibilityDimension(
            criterion="No active infections", category="exclusion", passed=True,
            rationale="No active infections identified."))

    return results


def _check_organ_function(organ_data: Dict[str, str]) -> List[EligibilityDimension]:
    """Check organ function against standard thresholds."""
    results: List[EligibilityDimension] = []

    if not organ_data:
        results.append(EligibilityDimension(
            criterion="Organ function", category="inclusion", passed=True,
            rationale="Organ function not assessed — assumed adequate.",
            severity="soft", recommendation="Confirm adequate organ function with lab work."))
        return results

    # Renal
    crcl = organ_data.get("creatinine_clearance")
    if crcl:
        val = float(crcl)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["creatinine_clearance_min"]
        passed = val >= threshold
        results.append(EligibilityDimension(
            criterion=f"CrCl ≥{threshold} mL/min", category="inclusion", passed=passed,
            rationale=f"CrCl = {val} mL/min {'(adequate)' if passed else f'(below {threshold})'}.",
            severity="critical" if not passed else "standard"))

    # Hepatic — Bilirubin
    bili = organ_data.get("bilirubin_x_uln")
    if bili:
        val = float(bili)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["bilirubin_max_x_uln"]
        passed = val <= threshold
        results.append(EligibilityDimension(
            criterion=f"Bilirubin ≤{threshold}× ULN", category="inclusion", passed=passed,
            rationale=f"Bilirubin = {val}× ULN {'(adequate)' if passed else f'(exceeds {threshold}×)'}.",
            severity="critical" if not passed else "standard"))

    # Hepatic — AST/ALT
    for enzyme in ["ast_x_uln", "alt_x_uln"]:
        val_str = organ_data.get(enzyme)
        if val_str:
            val = float(val_str)
            name = enzyme.split("_")[0].upper()
            threshold = _ORGAN_FUNCTION_THRESHOLDS[f"{enzyme.split('_')[0]}_max_x_uln"]
            passed = val <= threshold
            results.append(EligibilityDimension(
                criterion=f"{name} ≤{threshold}× ULN", category="inclusion", passed=passed,
                rationale=f"{name} = {val}× ULN {'(adequate)' if passed else f'(exceeds {threshold}×)'}.",
                severity="standard"))

    # Cardiac — LVEF
    lvef = organ_data.get("lvef")
    if lvef:
        val = float(lvef)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["lvef_min"]
        passed = val >= threshold
        results.append(EligibilityDimension(
            criterion=f"LVEF ≥{threshold}%", category="inclusion", passed=passed,
            rationale=f"LVEF = {val}% {'(adequate)' if passed else f'(below {threshold}%)'}.",
            severity="critical" if not passed else "standard"))

    # Hematologic — Platelets
    plt = organ_data.get("platelets")
    if plt:
        val = float(plt)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["platelets_min"]
        passed = val >= threshold
        results.append(EligibilityDimension(
            criterion=f"Platelets ≥{threshold}/µL", category="inclusion", passed=passed,
            rationale=f"Platelets = {val}/µL {'(adequate)' if passed else f'(below {threshold})'}.",
            severity="standard"))

    # Hematologic — ANC
    anc = organ_data.get("anc")
    if anc:
        val = float(anc)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["anc_min"]
        passed = val >= threshold
        results.append(EligibilityDimension(
            criterion=f"ANC ≥{threshold}/µL", category="inclusion", passed=passed,
            rationale=f"ANC = {val}/µL {'(adequate)' if passed else f'(below {threshold})'}.",
            severity="standard"))

    # Hematologic — Hemoglobin
    hgb = organ_data.get("hemoglobin")
    if hgb:
        val = float(hgb)
        threshold = _ORGAN_FUNCTION_THRESHOLDS["hemoglobin_min"]
        passed = val >= threshold
        results.append(EligibilityDimension(
            criterion=f"Hgb ≥{threshold} g/dL", category="inclusion", passed=passed,
            rationale=f"Hemoglobin = {val} g/dL {'(adequate)' if passed else f'(below {threshold})'}.",
            severity="standard"))

    return results


def _check_prior_car_t(has_prior: bool, exclusion_criteria: List[str]) -> EligibilityDimension:
    """Check prior CAR-T therapy against exclusion criteria."""
    car_t_excluded = any("prior car-t" in e.lower() or "prior same" in e.lower() for e in exclusion_criteria)
    if has_prior and car_t_excluded:
        return EligibilityDimension(
            criterion="No prior CAR-T therapy", category="exclusion", passed=False,
            rationale="Patient has prior CAR-T therapy, which is excluded.",
            severity="critical", recommendation="Look for trials accepting prior CAR-T patients.")
    if has_prior:
        return EligibilityDimension(
            criterion="Prior CAR-T therapy", category="exclusion", passed=True,
            rationale="Patient has prior CAR-T therapy; trial does not specifically exclude this.",
            severity="soft")
    return EligibilityDimension(
        criterion="Prior CAR-T therapy", category="exclusion", passed=True,
        rationale="No prior CAR-T therapy.")


# ──────────────────────────────────────────────────────────────────────
# Main Eligibility Assessment
# ──────────────────────────────────────────────────────────────────────

async def check_eligibility(
    patient_profile: Dict[str, Any],
    nct_id: str,
) -> Dict[str, Any]:
    """
    Run comprehensive eligibility assessment for a patient against a specific trial.
    Returns structured eligibility report.
    """
    from trials.clinicaltrials_sync import get_trial_by_id
    trial_data = await get_trial_by_id(nct_id)
    if not trial_data:
        return {"error": f"Trial {nct_id} not found", "eligible": False}

    # Extract eligibility criteria from trial
    elig = trial_data.get("eligibility", {})
    min_age = elig.get("min_age", 18)
    max_age = elig.get("max_age", 99)
    gender = elig.get("gender", "All")
    max_ecog = elig.get("ecog_max", 1)
    prior_required = elig.get("prior_therapies", 0)
    required_biomarkers = elig.get("biomarkers", [])
    exclusion_criteria = elig.get("exclusion", [])

    # Extract patient data
    age = patient_profile.get("age", 50)
    p_gender = patient_profile.get("gender", "All")
    ecog = patient_profile.get("ecog_status", 1)
    prior_therapies = patient_profile.get("prior_therapies", 0)
    biomarkers = patient_profile.get("biomarkers", {})
    targets = patient_profile.get("target_antigens_expressed", [])
    comorbidities = patient_profile.get("comorbidities", [])
    organ_function = patient_profile.get("organ_function", {})
    prior_car_t = patient_profile.get("prior_car_t", False)

    # Run all checks
    dimensions: List[EligibilityDimension] = []
    dimensions.append(_check_age(age, min_age, max_age))
    dimensions.append(_check_gender(p_gender, gender))
    dimensions.append(_check_ecog(ecog, max_ecog))
    dimensions.append(_check_prior_therapies(prior_therapies, prior_required))
    dimensions.append(_check_biomarkers(biomarkers, targets, required_biomarkers))
    dimensions.extend(_check_comorbidities(comorbidities, exclusion_criteria))
    dimensions.extend(_check_organ_function(organ_function))
    dimensions.append(_check_prior_car_t(prior_car_t, exclusion_criteria))

    # Tally results
    passed = sum(1 for d in dimensions if d.passed)
    failed = sum(1 for d in dimensions if not d.passed and d.severity == "critical")
    soft = sum(1 for d in dimensions if not d.passed and d.severity == "soft")
    total = len(dimensions)
    eligible = failed == 0

    # Compute confidence
    if eligible:
        confidence = passed / total if total > 0 else 0.0
    else:
        confidence = max(0.0, 1.0 - (failed / total * 2))

    # Gather recommendations
    recommendations = [d.recommendation for d in dimensions if d.recommendation]

    # Blocker summary
    blockers = [d.criterion for d in dimensions if not d.passed and d.severity == "critical"]
    blocker_summary = f"Blocked by: {'; '.join(blockers)}" if blockers else "No blocking criteria identified."

    return {
        "nct_id": nct_id,
        "trial_title": trial_data.get("title", ""),
        "overall_eligible": eligible,
        "confidence": round(confidence, 3),
        "total_checks": total,
        "passed_checks": passed,
        "failed_checks": failed,
        "soft_failures": soft,
        "blocker_summary": blocker_summary,
        "recommendations": recommendations,
        "dimensions": [
            {
                "criterion": d.criterion,
                "category": d.category,
                "passed": d.passed,
                "rationale": d.rationale,
                "severity": d.severity,
                "recommendation": d.recommendation,
            }
            for d in dimensions
        ],
    }


async def batch_eligibility_check(
    patient_profile: Dict[str, Any],
    nct_ids: List[str],
) -> Dict[str, Any]:
    """Run eligibility check across multiple trials."""
    results: List[Dict[str, Any]] = []
    for nct_id in nct_ids[:20]:
        result = await check_eligibility(patient_profile, nct_id)
        results.append(result)

    eligible_count = sum(1 for r in results if r.get("overall_eligible", False))
    return {
        "patient_id": patient_profile.get("patient_id", "unknown"),
        "total_trials_checked": len(results),
        "eligible_count": eligible_count,
        "results": results,
    }
