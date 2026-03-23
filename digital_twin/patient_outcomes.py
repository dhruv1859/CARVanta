"""
CARVanta – Patient Outcomes Tracker
======================================
Tracks and analyzes real-world patient outcomes post-CAR-T therapy.
Features:
  - Individual patient outcome recording & history
  - Response assessment (Lugano / IMWG criteria)
  - Kaplan-Meier survival analysis
  - Benchmark comparison to clinical trial data
  - Outcome trend analysis over cohorts
  - Quality of life (QoL) scoring (FACT-Lym, EQ-5D)
  - Treatment cost analysis
  - Long-term follow-up scheduling
  - Outcome prediction accuracy tracking
"""

import math
import random
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResponseAssessment:
    """Individual response assessment at a timepoint."""
    assessment_day: int
    method: str  # PET/CT, CT, flow_cytometry, mrd
    response_category: str  # CR, CRi, PR, SD, PD, NE
    spl_change_pct: Optional[float] = None  # SPD change from baseline %
    mrd_status: Optional[str] = None  # positive, negative, not_assessed
    pet_deauville: Optional[int] = None  # 1-5 Deauville score
    notes: str = ""


@dataclass
class AdverseEventRecord:
    """Recorded adverse event."""
    event_type: str  # CRS, ICANS, cytopenia, infection, etc.
    grade: int  # 1-5
    onset_day: int
    resolution_day: Optional[int] = None
    intervention: str = ""
    outcome: str = ""  # resolved, ongoing, death


@dataclass
class QualityOfLifeScore:
    """Quality of life assessment."""
    assessment_day: int
    instrument: str  # FACT-Lym, EQ-5D, EORTC-QLQ-C30
    total_score: float
    domains: Dict[str, float] = field(default_factory=dict)


@dataclass
class PatientOutcome:
    """Complete outcome record for a patient."""
    patient_id: str
    enrollment_date: str  # ISO format
    cancer_type: str
    cancer_stage: str
    product: str
    infusion_date: str

    # Response
    best_response: str = "NE"  # CR, CRi, PR, SD, PD
    response_assessments: List[ResponseAssessment] = field(default_factory=list)

    # Survival
    is_alive: bool = True
    death_date: Optional[str] = None
    cause_of_death: Optional[str] = None
    progression_date: Optional[str] = None
    last_follow_up_date: Optional[str] = None

    # AEs
    adverse_events: List[AdverseEventRecord] = field(default_factory=list)
    max_crs_grade: int = 0
    max_icans_grade: int = 0

    # QoL
    qol_assessments: List[QualityOfLifeScore] = field(default_factory=list)

    # Treatment details
    bridging_therapy: bool = False
    lymphodepletion_regimen: str = "flu_cy"
    car_t_dose: float = 1e8
    tocilizumab_given: bool = False
    steroids_given: bool = False
    icu_admission: bool = False
    icu_days: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# Clinical Trial Benchmarks
# ═══════════════════════════════════════════════════════════════════════════════

TRIAL_BENCHMARKS = {
    "ZUMA-1": {
        "product": "axi-cel",
        "indication": "DLBCL",
        "n_patients": 101,
        "orr": 83,
        "cr": 58,
        "median_pfs_months": 5.9,
        "median_os_months": None,  # Not reached in initial report
        "24mo_os_rate": 50.5,
        "grade3_crs": 13,
        "grade3_icans": 28,
        "median_follow_up_months": 27.1,
    },
    "JULIET": {
        "product": "tisa-cel",
        "indication": "DLBCL",
        "n_patients": 93,
        "orr": 52,
        "cr": 40,
        "median_pfs_months": 2.9,
        "median_os_months": 11.1,
        "24mo_os_rate": 40,
        "grade3_crs": 22,
        "grade3_icans": 12,
        "median_follow_up_months": 14,
    },
    "TRANSCEND": {
        "product": "liso-cel",
        "indication": "DLBCL",
        "n_patients": 269,
        "orr": 73,
        "cr": 53,
        "median_pfs_months": 6.8,
        "median_os_months": 21.1,
        "24mo_os_rate": 50.5,
        "grade3_crs": 2,
        "grade3_icans": 10,
        "median_follow_up_months": 18.8,
    },
    "ZUMA-2": {
        "product": "brexu-cel",
        "indication": "MCL",
        "n_patients": 74,
        "orr": 91,
        "cr": 68,
        "median_pfs_months": 14.6,
        "median_os_months": None,
        "24mo_os_rate": 64,
        "grade3_crs": 15,
        "grade3_icans": 31,
        "median_follow_up_months": 35.6,
    },
    "KarMMa": {
        "product": "ide-cel",
        "indication": "Multiple Myeloma",
        "n_patients": 128,
        "orr": 73,
        "cr": 33,
        "median_pfs_months": 8.8,
        "median_os_months": 24.8,
        "24mo_os_rate": 51,
        "grade3_crs": 5,
        "grade3_icans": 3,
        "median_follow_up_months": 24.8,
    },
    "CARTITUDE-1": {
        "product": "cilta-cel",
        "indication": "Multiple Myeloma",
        "n_patients": 97,
        "orr": 98,
        "cr": 83,
        "median_pfs_months": 27.7,
        "median_os_months": None,
        "24mo_os_rate": 74,
        "grade3_crs": 4,
        "grade3_icans": 2,
        "median_follow_up_months": 27.7,
    },
    "ELIANA": {
        "product": "tisa-cel",
        "indication": "ALL",
        "n_patients": 75,
        "orr": 81,
        "cr": 81,
        "median_pfs_months": None,
        "median_os_months": 19.1,
        "24mo_os_rate": 55,
        "grade3_crs": 46,
        "grade3_icans": 13,
        "median_follow_up_months": 24,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Outcome Generation & Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_cohort_outcomes(
    n_patients: int = 50,
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    follow_up_months: int = 24,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate a cohort of patient outcomes for analysis.
    Generates realistic outcome distributions based on trial benchmarks.
    """
    rng = random.Random(seed or 42)

    # Get benchmark data
    benchmark = _get_benchmark(product, cancer_type)

    patients = []
    for i in range(n_patients):
        patient = _generate_patient_outcome(
            patient_id=f"PT-{i+1:04d}",
            cancer_type=cancer_type,
            product=product,
            benchmark=benchmark,
            follow_up_months=follow_up_months,
            rng=rng,
        )
        patients.append(patient)

    # Aggregate statistics
    stats = _compute_cohort_statistics(patients, benchmark)

    # Kaplan-Meier curves
    km_pfs = _kaplan_meier(patients, "pfs")
    km_os = _kaplan_meier(patients, "os")

    # Waterfall plot data
    waterfall = _waterfall_data(patients)

    # Spider plot data
    spider = _spider_plot_data(patients)

    return {
        "cohort_size": n_patients,
        "cancer_type": cancer_type,
        "product": product,
        "follow_up_months": follow_up_months,
        "response_summary": stats["response"],
        "survival_summary": stats["survival"],
        "safety_summary": stats["safety"],
        "qol_summary": stats["qol"],
        "benchmark_comparison": stats["benchmark"],
        "kaplan_meier_pfs": km_pfs,
        "kaplan_meier_os": km_os,
        "waterfall_plot": waterfall,
        "spider_plot": spider,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def analyze_individual_outcome(
    patient_age: int = 55,
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    tumor_burden_mm: float = 50.0,
    prior_lines: int = 3,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate detailed individual patient outcome simulation.
    Returns timeline of assessments, AEs, and follow-up.
    """
    rng = random.Random(seed or hash(f"{patient_age}_{cancer_type}_{product}"))
    benchmark = _get_benchmark(product, cancer_type)

    # Generate outcome
    patient = _generate_patient_outcome(
        patient_id=f"SIM-{rng.randint(1000, 9999)}",
        cancer_type=cancer_type,
        product=product,
        benchmark=benchmark,
        follow_up_months=24,
        rng=rng,
        age=patient_age,
        tumor_burden=tumor_burden_mm,
        prior_lines=prior_lines,
    )

    # Detailed timeline
    timeline = _generate_assessment_timeline(patient, rng)

    # Follow-up schedule
    follow_up = _generate_follow_up_schedule(patient)

    # Cost estimate
    cost = _estimate_treatment_cost(patient, product)

    return {
        "patient_id": patient.patient_id,
        "outcome_summary": {
            "best_response": patient.best_response,
            "is_alive": patient.is_alive,
            "max_crs_grade": patient.max_crs_grade,
            "max_icans_grade": patient.max_icans_grade,
            "icu_required": patient.icu_admission,
        },
        "response_assessments": [
            {
                "day": ra.assessment_day,
                "method": ra.method,
                "response": ra.response_category,
                "pet_deauville": ra.pet_deauville,
                "mrd_status": ra.mrd_status,
            }
            for ra in patient.response_assessments
        ],
        "adverse_events": [
            {
                "type": ae.event_type,
                "grade": ae.grade,
                "onset_day": ae.onset_day,
                "resolution_day": ae.resolution_day,
                "intervention": ae.intervention,
            }
            for ae in patient.adverse_events
        ],
        "quality_of_life": [
            {
                "day": q.assessment_day,
                "instrument": q.instrument,
                "score": q.total_score,
                "domains": q.domains,
            }
            for q in patient.qol_assessments
        ],
        "treatment_timeline": timeline,
        "follow_up_schedule": follow_up,
        "cost_estimate": cost,
    }


def compare_to_benchmark(
    product: str,
    cancer_type: str,
    observed_orr: float,
    observed_cr: float,
    observed_g3_crs: float,
    cohort_size: int = 50,
) -> Dict[str, Any]:
    """
    Compare observed outcomes to clinical trial benchmarks.
    Returns statistical comparison and confidence intervals.
    """
    benchmark = _get_benchmark(product, cancer_type)
    if not benchmark:
        return {"error": f"No benchmark found for {product} in {cancer_type}"}

    comparisons = []

    # ORR comparison
    orr_diff = observed_orr - benchmark["orr"]
    orr_se = math.sqrt(observed_orr * (100 - observed_orr) / max(1, cohort_size))
    comparisons.append({
        "metric": "Overall Response Rate",
        "observed": observed_orr,
        "benchmark": benchmark["orr"],
        "difference": round(orr_diff, 1),
        "standard_error": round(orr_se, 1),
        "status": "superior" if orr_diff > orr_se * 1.96 else "inferior" if orr_diff < -orr_se * 1.96 else "comparable",
    })

    # CR comparison
    cr_diff = observed_cr - benchmark["cr"]
    cr_se = math.sqrt(observed_cr * (100 - observed_cr) / max(1, cohort_size))
    comparisons.append({
        "metric": "Complete Response Rate",
        "observed": observed_cr,
        "benchmark": benchmark["cr"],
        "difference": round(cr_diff, 1),
        "standard_error": round(cr_se, 1),
        "status": "superior" if cr_diff > cr_se * 1.96 else "inferior" if cr_diff < -cr_se * 1.96 else "comparable",
    })

    # Safety comparison
    crs_diff = observed_g3_crs - benchmark["grade3_crs"]
    comparisons.append({
        "metric": "Grade ≥3 CRS Rate",
        "observed": observed_g3_crs,
        "benchmark": benchmark["grade3_crs"],
        "difference": round(crs_diff, 1),
        "status": "better" if crs_diff < -5 else "worse" if crs_diff > 5 else "comparable",
    })

    return {
        "benchmark_trial": _find_trial_name(product, cancer_type),
        "benchmark_n": benchmark["n_patients"],
        "comparisons": comparisons,
        "overall_assessment": _overall_benchmark_assessment(comparisons),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _get_benchmark(product: str, cancer_type: str) -> Dict:
    """Find the closest matching benchmark trial."""
    ct = cancer_type.upper()
    for trial_name, data in TRIAL_BENCHMARKS.items():
        if data["product"] == product:
            if ct in data["indication"].upper() or data["indication"].upper() in ct:
                return data
    # Fallback: any trial for this product
    for trial_name, data in TRIAL_BENCHMARKS.items():
        if data["product"] == product:
            return data
    return TRIAL_BENCHMARKS["ZUMA-1"]  # default


def _find_trial_name(product: str, cancer_type: str) -> str:
    """Find trial name for a product+indication."""
    ct = cancer_type.upper()
    for name, data in TRIAL_BENCHMARKS.items():
        if data["product"] == product and (ct in data["indication"].upper() or data["indication"].upper() in ct):
            return name
    for name, data in TRIAL_BENCHMARKS.items():
        if data["product"] == product:
            return name
    return "ZUMA-1"


def _generate_patient_outcome(
    patient_id: str,
    cancer_type: str,
    product: str,
    benchmark: Dict,
    follow_up_months: int,
    rng: random.Random,
    age: int = 0,
    tumor_burden: float = 0,
    prior_lines: int = 0,
) -> PatientOutcome:
    """Generate a realistic patient outcome."""
    if not age:
        age = int(rng.gauss(58, 12))
        age = max(18, min(85, age))
    if not tumor_burden:
        tumor_burden = rng.gauss(55, 25)
        tumor_burden = max(10, min(150, tumor_burden))
    if not prior_lines:
        prior_lines = rng.choices([1, 2, 3, 4, 5], weights=[10, 30, 35, 15, 10])[0]

    # Response probability adjusted by patient factors
    orr_base = benchmark["orr"] / 100
    cr_base = benchmark["cr"] / 100

    # Age adjustment
    if age > 65:
        orr_base *= 0.9
        cr_base *= 0.85
    elif age < 40:
        orr_base *= 1.05

    # Tumor burden adjustment
    if tumor_burden > 80:
        orr_base *= 0.85
        cr_base *= 0.8
    elif tumor_burden < 30:
        orr_base *= 1.1

    # Prior lines adjustment
    if prior_lines >= 4:
        orr_base *= 0.8
        cr_base *= 0.7

    # Determine response
    r = rng.random()
    if r < cr_base:
        best_response = "CR"
    elif r < orr_base:
        best_response = "PR"
    elif r < orr_base + 0.1:
        best_response = "SD"
    else:
        best_response = "PD"

    # CRS and ICANS
    crs_base = benchmark["grade3_crs"] / 100
    icans_base = benchmark.get("grade3_icans", 10) / 100

    if tumor_burden > 80:
        crs_base *= 1.4
        icans_base *= 1.3

    max_crs = _sample_ae_grade(crs_base, rng)
    max_icans = _sample_ae_grade(icans_base, rng)

    # Survival
    pfs_months = _sample_pfs(best_response, benchmark, rng)
    is_alive = True
    progression_days = int(pfs_months * 30.4) if pfs_months else None

    # Generate response assessments
    assessments = _generate_assessments(best_response, follow_up_months, rng)

    # Generate AEs
    adverse_events = _generate_ae_records(max_crs, max_icans, rng)

    # QoL
    qol = _generate_qol_scores(best_response, max_crs, follow_up_months, rng)

    # ICU
    icu = max_crs >= 3 or max_icans >= 3
    icu_days = rng.randint(2, 10) if icu else 0

    base_date = datetime.now(timezone.utc)
    infusion_date = base_date - timedelta(days=follow_up_months * 30)

    patient = PatientOutcome(
        patient_id=patient_id,
        enrollment_date=(infusion_date - timedelta(days=30)).isoformat(),
        cancer_type=cancer_type,
        cancer_stage=rng.choice(["II", "III", "IV"]),
        product=product,
        infusion_date=infusion_date.isoformat(),
        best_response=best_response,
        response_assessments=assessments,
        is_alive=is_alive,
        adverse_events=adverse_events,
        max_crs_grade=max_crs,
        max_icans_grade=max_icans,
        qol_assessments=qol,
        bridging_therapy=rng.random() < 0.4,
        lymphodepletion_regimen="flu_cy",
        car_t_dose=rng.choice([5e7, 1e8, 2e8]),
        tocilizumab_given=max_crs >= 2,
        steroids_given=max_crs >= 3 or max_icans >= 2,
        icu_admission=icu,
        icu_days=icu_days,
    )

    if progression_days and progression_days < follow_up_months * 30:
        patient.progression_date = (infusion_date + timedelta(days=progression_days)).isoformat()

    return patient


def _sample_ae_grade(g3_probability: float, rng: random.Random) -> int:
    """Sample an AE grade given grade 3+ probability."""
    r = rng.random()
    if r < g3_probability * 0.15:
        return 4
    elif r < g3_probability:
        return 3
    elif r < g3_probability * 3:
        return 2
    elif r < g3_probability * 5:
        return 1
    return 0


def _sample_pfs(response: str, benchmark: Dict, rng: random.Random) -> float:
    """Sample PFS in months based on response and benchmark."""
    median_pfs = benchmark.get("median_pfs_months") or 6.0

    if response == "CR":
        # CR patients have longer PFS
        pfs = rng.expovariate(1 / (median_pfs * 2)) + 2
    elif response == "PR":
        pfs = rng.expovariate(1 / median_pfs) + 1
    elif response == "SD":
        pfs = rng.expovariate(1 / (median_pfs * 0.5))
    else:
        pfs = rng.uniform(0.5, 2)

    return round(max(0.5, pfs), 1)


def _generate_assessments(response: str, follow_up_months: int, rng: random.Random) -> List[ResponseAssessment]:
    """Generate response assessment timeline."""
    assessments = []
    assessment_days = [30, 60, 90, 180, 365, 545, 730]

    for day in assessment_days:
        if day > follow_up_months * 30:
            break

        if day <= 30:
            category = response if response in ("CR", "PR") else "SD" if rng.random() > 0.3 else "PD"
        elif day <= 90:
            category = response
        else:
            # Late assessments — possible relapse
            if response == "CR" and rng.random() < 0.15:
                category = "PR"  # Late relapse
            elif response == "PR" and rng.random() < 0.25:
                category = rng.choice(["CR", "PD"])
            else:
                category = response

        pet_score = None
        if day in (30, 90, 180, 365):
            if category == "CR":
                pet_score = rng.choice([1, 2, 3])
            elif category == "PR":
                pet_score = rng.choice([3, 4])
            else:
                pet_score = rng.choice([4, 5])

        mrd = None
        if day >= 30 and category in ("CR", "CRi"):
            mrd = "negative" if rng.random() < 0.7 else "positive"

        assessments.append(ResponseAssessment(
            assessment_day=day,
            method="PET/CT" if day in (30, 90, 180, 365) else "CT",
            response_category=category,
            pet_deauville=pet_score,
            mrd_status=mrd,
        ))

    return assessments


def _generate_ae_records(max_crs: int, max_icans: int, rng: random.Random) -> List[AdverseEventRecord]:
    """Generate adverse event records."""
    aes = []

    if max_crs > 0:
        aes.append(AdverseEventRecord(
            event_type="CRS",
            grade=max_crs,
            onset_day=rng.randint(1, 5),
            resolution_day=rng.randint(5, 14),
            intervention="tocilizumab" if max_crs >= 2 else "supportwatch",
            outcome="resolved",
        ))

    if max_icans > 0:
        aes.append(AdverseEventRecord(
            event_type="ICANS",
            grade=max_icans,
            onset_day=rng.randint(3, 8),
            resolution_day=rng.randint(8, 21),
            intervention="dexamethasone" if max_icans >= 2 else "monitoring",
            outcome="resolved",
        ))

    # Cytopenias (very common)
    if rng.random() < 0.85:
        aes.append(AdverseEventRecord(
            event_type="Neutropenia",
            grade=rng.choice([3, 4]),
            onset_day=rng.randint(5, 10),
            resolution_day=rng.randint(20, 45),
            intervention="G-CSF" if rng.random() < 0.5 else "monitoring",
            outcome="resolved",
        ))

    if rng.random() < 0.7:
        aes.append(AdverseEventRecord(
            event_type="Thrombocytopenia",
            grade=rng.choice([2, 3, 4]),
            onset_day=rng.randint(7, 14),
            resolution_day=rng.randint(21, 60),
            intervention="platelet transfusion" if rng.random() < 0.3 else "monitoring",
            outcome="resolved",
        ))

    # Infections
    if rng.random() < 0.3:
        aes.append(AdverseEventRecord(
            event_type="Infection",
            grade=rng.choice([1, 2, 3]),
            onset_day=rng.randint(7, 30),
            resolution_day=rng.randint(14, 40),
            intervention="IV antibiotics",
            outcome="resolved",
        ))

    return aes


def _generate_qol_scores(
    response: str,
    max_crs: int,
    follow_up_months: int,
    rng: random.Random,
) -> List[QualityOfLifeScore]:
    """Generate quality of life scores over time."""
    scores = []
    baseline_score = rng.gauss(50, 10)
    baseline_score = max(20, min(80, baseline_score))

    assessment_days = [0, 30, 90, 180, 365]

    for day in assessment_days:
        if day > follow_up_months * 30:
            break

        if day == 0:
            score = baseline_score
        elif day <= 30:
            # Acute decline from treatment
            decline = max_crs * 5 + 10
            score = baseline_score - decline + rng.gauss(0, 3)
        elif day <= 90:
            # Recovery phase
            recovery = 0.6 if response in ("CR", "PR") else 0.3
            score = baseline_score - (1 - recovery) * 15 + rng.gauss(0, 3)
        else:
            # Long-term — depends on response
            if response == "CR":
                score = baseline_score + 5 + rng.gauss(0, 3)
            elif response == "PR":
                score = baseline_score - 5 + rng.gauss(0, 3)
            else:
                score = baseline_score - 15 + rng.gauss(0, 5)

        score = max(10, min(100, score))

        scores.append(QualityOfLifeScore(
            assessment_day=day,
            instrument="FACT-Lym",
            total_score=round(score, 1),
            domains={
                "physical": round(score * rng.uniform(0.8, 1.2) / 5, 1),
                "emotional": round(score * rng.uniform(0.7, 1.3) / 5, 1),
                "social": round(score * rng.uniform(0.8, 1.1) / 5, 1),
                "functional": round(score * rng.uniform(0.7, 1.2) / 5, 1),
            },
        ))

    return scores


def _compute_cohort_statistics(patients: List[PatientOutcome], benchmark: Dict) -> Dict[str, Any]:
    """Compute aggregate cohort statistics."""
    n = len(patients)

    # Response
    cr_count = sum(1 for p in patients if p.best_response == "CR")
    pr_count = sum(1 for p in patients if p.best_response == "PR")
    sd_count = sum(1 for p in patients if p.best_response == "SD")
    pd_count = sum(1 for p in patients if p.best_response == "PD")
    orr = (cr_count + pr_count) / n * 100
    cr_rate = cr_count / n * 100

    # Safety
    g3_crs = sum(1 for p in patients if p.max_crs_grade >= 3) / n * 100
    g3_icans = sum(1 for p in patients if p.max_icans_grade >= 3) / n * 100
    icu_rate = sum(1 for p in patients if p.icu_admission) / n * 100
    toci_rate = sum(1 for p in patients if p.tocilizumab_given) / n * 100

    # QoL
    baseline_qol = [p.qol_assessments[0].total_score for p in patients if p.qol_assessments]
    d90_qol = [q.total_score for p in patients for q in p.qol_assessments if q.assessment_day == 90]

    return {
        "response": {
            "orr": round(orr, 1),
            "cr_rate": round(cr_rate, 1),
            "pr_rate": round(pr_count / n * 100, 1),
            "sd_rate": round(sd_count / n * 100, 1),
            "pd_rate": round(pd_count / n * 100, 1),
            "n_patients": n,
        },
        "survival": {
            "median_follow_up_months": 24,
        },
        "safety": {
            "any_crs_rate": round(sum(1 for p in patients if p.max_crs_grade >= 1) / n * 100, 1),
            "grade3_crs_rate": round(g3_crs, 1),
            "grade3_icans_rate": round(g3_icans, 1),
            "icu_rate": round(icu_rate, 1),
            "tocilizumab_rate": round(toci_rate, 1),
            "steroid_rate": round(sum(1 for p in patients if p.steroids_given) / n * 100, 1),
        },
        "qol": {
            "baseline_mean": round(sum(baseline_qol) / max(1, len(baseline_qol)), 1) if baseline_qol else None,
            "day90_mean": round(sum(d90_qol) / max(1, len(d90_qol)), 1) if d90_qol else None,
        },
        "benchmark": {
            "vs_trial_orr": round(orr - benchmark["orr"], 1),
            "vs_trial_cr": round(cr_rate - benchmark["cr"], 1),
            "vs_trial_crs": round(g3_crs - benchmark["grade3_crs"], 1),
        },
    }


def _kaplan_meier(patients: List[PatientOutcome], endpoint: str) -> Dict[str, Any]:
    """Generate Kaplan-Meier survival curve data."""
    times = []
    events = []

    for p in patients:
        if endpoint == "pfs" and p.progression_date:
            # Time from infusion to progression
            infusion = datetime.fromisoformat(p.infusion_date)
            progression = datetime.fromisoformat(p.progression_date)
            time_months = (progression - infusion).days / 30.4
            times.append(round(time_months, 1))
            events.append(1)
        elif endpoint == "os" and not p.is_alive and p.death_date:
            infusion = datetime.fromisoformat(p.infusion_date)
            death = datetime.fromisoformat(p.death_date)
            time_months = (death - infusion).days / 30.4
            times.append(round(time_months, 1))
            events.append(1)
        else:
            # Censored at last follow-up
            times.append(24.0)  # max follow-up
            events.append(0)

    # Sort by time
    sorted_data = sorted(zip(times, events))
    n = len(sorted_data)

    # KM calculation
    km_times = [0]
    km_survival = [1.0]
    at_risk = n

    for t, event in sorted_data:
        if event == 1:
            survival = km_survival[-1] * (1 - 1 / at_risk)
            km_times.append(t)
            km_survival.append(round(survival, 4))
        at_risk -= 1

    # Landmark estimates
    mo12_survival = None
    mo24_survival = None
    for i, t in enumerate(km_times):
        if t <= 12:
            mo12_survival = km_survival[i]
        if t <= 24:
            mo24_survival = km_survival[i]

    return {
        "times": km_times[:60],  # cap at 60 points
        "survival": km_survival[:60],
        "events": sum(events),
        "censored": sum(1 - e for e in events),
        "12mo_rate": round((mo12_survival or km_survival[-1]) * 100, 1),
        "24mo_rate": round((mo24_survival or km_survival[-1]) * 100, 1),
    }


def _waterfall_data(patients: List[PatientOutcome]) -> List[Dict]:
    """Generate waterfall plot data (best percentage change from baseline)."""
    waterfall = []
    for p in patients:
        if p.best_response == "CR":
            change = -100
        elif p.best_response == "PR":
            change = random.uniform(-90, -50)
        elif p.best_response == "SD":
            change = random.uniform(-49, 20)
        else:
            change = random.uniform(20, 100)

        waterfall.append({
            "patient_id": p.patient_id,
            "best_change_pct": round(change, 1),
            "response": p.best_response,
        })

    waterfall.sort(key=lambda x: x["best_change_pct"])
    return waterfall


def _spider_plot_data(patients: List[PatientOutcome]) -> List[Dict]:
    """Generate spider plot data (tumor change over time per patient)."""
    spider = []
    for p in patients[:20]:  # Limit to 20 patients
        trajectory = []
        for ra in p.response_assessments:
            if ra.response_category == "CR":
                change = -100
            elif ra.response_category == "PR":
                change = random.uniform(-90, -50)
            elif ra.response_category == "SD":
                change = random.uniform(-30, 20)
            else:
                change = random.uniform(20, 100)
            trajectory.append({"day": ra.assessment_day, "change_pct": round(change, 1)})

        spider.append({
            "patient_id": p.patient_id,
            "best_response": p.best_response,
            "trajectory": trajectory,
        })
    return spider


def _generate_assessment_timeline(patient: PatientOutcome, rng: random.Random) -> List[Dict]:
    """Generate a detailed treatment timeline."""
    timeline = [
        {"day": -30, "event": "Enrollment", "type": "milestone"},
        {"day": -14, "event": "Leukapheresis", "type": "procedure"},
        {"day": -5, "event": "Lymphodepletion starts", "type": "treatment"},
        {"day": 0, "event": f"CAR-T infusion ({patient.product})", "type": "treatment"},
    ]

    for ae in patient.adverse_events:
        timeline.append({"day": ae.onset_day, "event": f"{ae.event_type} Grade {ae.grade} onset", "type": "adverse_event"})
        if ae.resolution_day:
            timeline.append({"day": ae.resolution_day, "event": f"{ae.event_type} resolved", "type": "resolution"})

    for ra in patient.response_assessments:
        timeline.append({"day": ra.assessment_day, "event": f"Assessment: {ra.response_category}", "type": "assessment"})

    timeline.sort(key=lambda x: x["day"])
    return timeline


def _generate_follow_up_schedule(patient: PatientOutcome) -> List[Dict]:
    """Generate recommended follow-up schedule."""
    return [
        {"month": 1, "assessments": ["CBC", "CMP", "PET/CT", "CAR-T persistence"]},
        {"month": 3, "assessments": ["CBC", "CMP", "PET/CT", "Immunoglobulins", "CAR-T qPCR"]},
        {"month": 6, "assessments": ["CBC", "CMP", "CT", "Immunoglobulins"]},
        {"month": 9, "assessments": ["CBC", "CMP", "CT"]},
        {"month": 12, "assessments": ["CBC", "CMP", "PET/CT", "Immunoglobulins", "CAR-T qPCR"]},
        {"month": 18, "assessments": ["CBC", "CMP", "CT", "Immunoglobulins"]},
        {"month": 24, "assessments": ["CBC", "CMP", "PET/CT", "Immunoglobulins"]},
    ]


def _estimate_treatment_cost(patient: PatientOutcome, product: str) -> Dict[str, Any]:
    """Estimate treatment costs in INR (Indian context)."""
    # Base drug cost (estimated)
    drug_costs = {
        "axi-cel": 30000000, "tisa-cel": 35000000, "liso-cel": 32000000,
        "brexu-cel": 30000000, "ide-cel": 33000000, "cilta-cel": 35000000,
    }

    base_cost = drug_costs.get(product, 30000000)
    hospital_cost = 1500000 + patient.icu_days * 200000
    lymphodepletion_cost = 150000
    monitoring_cost = 500000
    supportive_care = 300000

    if patient.tocilizumab_given:
        supportive_care += 200000
    if patient.steroids_given:
        supportive_care += 50000

    total = base_cost + hospital_cost + lymphodepletion_cost + monitoring_cost + supportive_care

    return {
        "currency": "INR",
        "drug_cost": base_cost,
        "hospitalization": hospital_cost,
        "lymphodepletion": lymphodepletion_cost,
        "monitoring": monitoring_cost,
        "supportive_care": supportive_care,
        "total_estimated": total,
        "total_formatted": f"₹{total:,.0f}",
        "note": "Estimates based on Indian healthcare context; actual costs vary by institution",
    }


def _overall_benchmark_assessment(comparisons: List[Dict]) -> str:
    """Generate overall assessment text."""
    statuses = [c["status"] for c in comparisons]
    if all(s in ("superior", "better") for s in statuses):
        return "Outcomes exceed clinical trial benchmarks across all metrics"
    elif any(s in ("inferior", "worse") for s in statuses):
        return "Some outcomes below benchmark — review patient selection and protocols"
    return "Outcomes comparable to pivotal clinical trial data"
