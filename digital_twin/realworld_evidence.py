"""
CARVanta – Real-World Evidence Engine
=========================================
Generates and analyzes real-world evidence (RWE) for CAR-T therapies.
Features:
  - Registry simulation with multi-site data
  - Real-world vs clinical trial outcome comparison
  - Insurance and access analytics
  - Manufacturing failure simulation
  - Time-to-treatment analysis
  - Geographic disparity modeling
  - Socioeconomic impact assessment
  - Post-market safety surveillance
  - Comparative effectiveness research
  - Health technology assessment (HTA) support
"""

import math
import random
import statistics
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta


# ═══════════════════════════════════════════════════════════════════════════════
# Registry Data Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RegistryPatient:
    """Simulated registry patient."""
    patient_id: str
    site_id: str
    country: str
    state: str
    age: int
    sex: str
    cancer_type: str
    product: str
    insurance_type: str
    socioeconomic_tier: str  # high, middle, low
    referral_date: str
    apheresis_date: Optional[str] = None
    infusion_date: Optional[str] = None
    manufacturing_success: bool = True
    manufacturing_days: int = 21
    time_to_infusion_days: int = 0
    response: str = "NE"
    pfs_months: float = 0
    os_months: float = 0
    grade3_crs: bool = False
    grade3_icans: bool = False
    icu_admission: bool = False
    death_within_30d: bool = False
    total_cost_inr: float = 0
    lost_to_followup: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# Site/Center Database
# ═══════════════════════════════════════════════════════════════════════════════

TREATMENT_CENTERS = {
    "AIIMS-Delhi": {
        "city": "New Delhi", "state": "Delhi", "tier": "Tier-1",
        "beds": 12, "annual_capacity": 50, "experience_level": "high",
        "avg_turnaround_days": 28, "manufacturing_partner": "in-house",
    },
    "TMH-Mumbai": {
        "city": "Mumbai", "state": "Maharashtra", "tier": "Tier-1",
        "beds": 10, "annual_capacity": 40, "experience_level": "high",
        "avg_turnaround_days": 30, "manufacturing_partner": "Novartis",
    },
    "CMC-Vellore": {
        "city": "Vellore", "state": "Tamil Nadu", "tier": "Tier-2",
        "beds": 8, "annual_capacity": 30, "experience_level": "moderate",
        "avg_turnaround_days": 35, "manufacturing_partner": "in-house",
    },
    "KGMU-Lucknow": {
        "city": "Lucknow", "state": "Uttar Pradesh", "tier": "Tier-2",
        "beds": 6, "annual_capacity": 25, "experience_level": "moderate",
        "avg_turnaround_days": 38, "manufacturing_partner": "contracted",
    },
    "PGIMER-Chandigarh": {
        "city": "Chandigarh", "state": "Chandigarh", "tier": "Tier-1",
        "beds": 8, "annual_capacity": 30, "experience_level": "moderate",
        "avg_turnaround_days": 32, "manufacturing_partner": "in-house",
    },
    "Kidwai-Bangalore": {
        "city": "Bangalore", "state": "Karnataka", "tier": "Tier-1",
        "beds": 6, "annual_capacity": 20, "experience_level": "developing",
        "avg_turnaround_days": 40, "manufacturing_partner": "contracted",
    },
    "RGCIRC-Delhi": {
        "city": "New Delhi", "state": "Delhi", "tier": "Tier-1",
        "beds": 10, "annual_capacity": 35, "experience_level": "high",
        "avg_turnaround_days": 30, "manufacturing_partner": "Kite/Gilead",
    },
    "Apollo-Chennai": {
        "city": "Chennai", "state": "Tamil Nadu", "tier": "Tier-1",
        "beds": 8, "annual_capacity": 25, "experience_level": "developing",
        "avg_turnaround_days": 42, "manufacturing_partner": "contracted",
    },
}

# Insurance profiles
INSURANCE_PROFILES = {
    "government": {"coverage_pct": 30, "approval_days": 60, "denial_rate": 0.35, "population_pct": 40},
    "private": {"coverage_pct": 50, "approval_days": 21, "denial_rate": 0.15, "population_pct": 25},
    "employer": {"coverage_pct": 60, "approval_days": 14, "denial_rate": 0.10, "population_pct": 15},
    "self_pay": {"coverage_pct": 0, "approval_days": 0, "denial_rate": 0.0, "population_pct": 15},
    "clinical_trial": {"coverage_pct": 100, "approval_days": 0, "denial_rate": 0.0, "population_pct": 5},
}


# ═══════════════════════════════════════════════════════════════════════════════
# Registry Analysis Functions
# ═══════════════════════════════════════════════════════════════════════════════

def generate_registry_data(
    n_patients: int = 200,
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    time_period_months: int = 24,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate simulated registry data for real-world evidence analysis."""
    rng = random.Random(seed or 42)

    patients = []
    sites = list(TREATMENT_CENTERS.keys())

    for i in range(n_patients):
        site = rng.choice(sites)
        center = TREATMENT_CENTERS[site]

        age = int(rng.gauss(58, 13))
        age = max(2, min(88, age))
        sex = "M" if rng.random() < 0.58 else "F"

        # Insurance
        ins_types = list(INSURANCE_PROFILES.keys())
        ins_weights = [INSURANCE_PROFILES[t]["population_pct"] for t in ins_types]
        insurance = rng.choices(ins_types, weights=ins_weights)[0]
        ins_profile = INSURANCE_PROFILES[insurance]

        # Socioeconomic tier
        ses = rng.choices(["high", "middle", "low"], weights=[15, 45, 40])[0]

        # Time to treatment
        referral_delay = max(1, int(rng.gauss(14, 7)))
        insurance_delay = ins_profile["approval_days"]
        manufacturing_days = max(14, int(rng.gauss(center["avg_turnaround_days"], 5)))
        total_delay = referral_delay + insurance_delay + manufacturing_days

        # Manufacturing failure
        mfg_fail_rate = 0.05 if center["experience_level"] == "high" else 0.10 if center["experience_level"] == "moderate" else 0.15
        mfg_success = rng.random() > mfg_fail_rate

        # Insurance denial
        denied = rng.random() < ins_profile["denial_rate"]
        if denied:
            mfg_success = False

        # Response (RWE typically lower than trial)
        orr_rwe = 0.75 if product == "axi-cel" else 0.45 if product == "tisa-cel" else 0.65
        if age > 70:
            orr_rwe *= 0.85
        if ses == "low":
            orr_rwe *= 0.90
        if center["experience_level"] == "developing":
            orr_rwe *= 0.92

        r = rng.random()
        if r < orr_rwe * 0.55:
            response = "CR"
        elif r < orr_rwe:
            response = "PR"
        elif r < orr_rwe + 0.08:
            response = "SD"
        else:
            response = "PD"

        # PFS
        if response == "CR":
            pfs = rng.expovariate(1 / 14) + 2
        elif response == "PR":
            pfs = rng.expovariate(1 / 6) + 1
        elif response == "SD":
            pfs = rng.expovariate(1 / 3)
        else:
            pfs = rng.uniform(0.3, 1.5)

        # OS
        os_months = pfs + rng.expovariate(1 / 8)

        # Safety (RWE grade 3+ rates)
        g3_crs = rng.random() < 0.10 if product == "liso-cel" else rng.random() < 0.18
        g3_icans = rng.random() < 0.15 if product == "axi-cel" else rng.random() < 0.08
        icu = g3_crs or g3_icans
        death_30d = rng.random() < 0.03

        # Cost (variable by insurance and center)
        base_cost = 30000000
        hospital_cost = manufacturing_days * 50000 + 1500000
        if icu:
            hospital_cost += rng.randint(500000, 2000000)
        coverage = ins_profile["coverage_pct"] / 100
        out_of_pocket = (base_cost + hospital_cost) * (1 - coverage)
        total_cost = base_cost + hospital_cost

        # Lost to follow-up
        ltfu = rng.random() < 0.08 if ses == "low" else rng.random() < 0.03

        base_date = datetime.now(timezone.utc) - timedelta(days=time_period_months * 30)
        ref_date = base_date + timedelta(days=rng.randint(0, time_period_months * 30))

        patient = RegistryPatient(
            patient_id=f"RWE-{i+1:05d}",
            site_id=site,
            country="India",
            state=center["state"],
            age=age,
            sex=sex,
            cancer_type=cancer_type,
            product=product if mfg_success else "none",
            insurance_type=insurance,
            socioeconomic_tier=ses,
            referral_date=ref_date.isoformat(),
            manufacturing_success=mfg_success,
            manufacturing_days=manufacturing_days if mfg_success else 0,
            time_to_infusion_days=total_delay if mfg_success else 0,
            response=response if mfg_success else "NE",
            pfs_months=round(pfs, 1) if mfg_success else 0,
            os_months=round(os_months, 1),
            grade3_crs=g3_crs if mfg_success else False,
            grade3_icans=g3_icans if mfg_success else False,
            icu_admission=icu if mfg_success else False,
            death_within_30d=death_30d,
            total_cost_inr=total_cost if mfg_success else 500000,
            lost_to_followup=ltfu,
        )
        patients.append(patient)

    # Analyze
    treated = [p for p in patients if p.manufacturing_success]
    n_treated = len(treated)

    # Response rates
    cr_n = sum(1 for p in treated if p.response == "CR")
    pr_n = sum(1 for p in treated if p.response == "PR")
    orr_rwe_actual = (cr_n + pr_n) / max(1, n_treated) * 100

    # Safety
    g3_crs_rate = sum(1 for p in treated if p.grade3_crs) / max(1, n_treated) * 100
    g3_icans_rate = sum(1 for p in treated if p.grade3_icans) / max(1, n_treated) * 100

    # Time metrics
    infusion_times = [p.time_to_infusion_days for p in treated if p.time_to_infusion_days > 0]
    median_time = sorted(infusion_times)[len(infusion_times) // 2] if infusion_times else 0

    # Cost
    costs = [p.total_cost_inr for p in treated]
    median_cost = sorted(costs)[len(costs) // 2] if costs else 0

    # Manufacturing
    mfg_success_rate = n_treated / n_patients * 100

    # By site
    site_analysis = {}
    for site in sites:
        site_pts = [p for p in patients if p.site_id == site]
        site_treated = [p for p in site_pts if p.manufacturing_success]
        if site_treated:
            site_cr = sum(1 for p in site_treated if p.response == "CR")
            site_pr = sum(1 for p in site_treated if p.response == "PR")
            site_analysis[site] = {
                "n_referred": len(site_pts),
                "n_treated": len(site_treated),
                "orr": round((site_cr + site_pr) / len(site_treated) * 100, 1),
                "mfg_success_rate": round(len(site_treated) / max(1, len(site_pts)) * 100, 1),
                "city": TREATMENT_CENTERS[site]["city"],
            }

    # By insurance
    insurance_analysis = {}
    for ins in INSURANCE_PROFILES:
        ins_pts = [p for p in patients if p.insurance_type == ins]
        ins_treated = [p for p in ins_pts if p.manufacturing_success]
        if ins_pts:
            insurance_analysis[ins] = {
                "n": len(ins_pts),
                "treated_rate": round(len(ins_treated) / len(ins_pts) * 100, 1),
                "orr": round(sum(1 for p in ins_treated if p.response in ("CR", "PR")) / max(1, len(ins_treated)) * 100, 1),
                "median_delay_days": sorted([p.time_to_infusion_days for p in ins_treated])[len(ins_treated) // 2] if ins_treated else 0,
            }

    # By SES
    ses_analysis = {}
    for tier in ["high", "middle", "low"]:
        ses_pts = [p for p in patients if p.socioeconomic_tier == tier]
        ses_treated = [p for p in ses_pts if p.manufacturing_success]
        if ses_pts:
            ses_analysis[tier] = {
                "n": len(ses_pts),
                "treated_rate": round(len(ses_treated) / len(ses_pts) * 100, 1),
                "orr": round(sum(1 for p in ses_treated if p.response in ("CR", "PR")) / max(1, len(ses_treated)) * 100, 1),
                "ltfu_rate": round(sum(1 for p in ses_pts if p.lost_to_followup) / len(ses_pts) * 100, 1),
            }

    return {
        "registry_id": f"RWE-REG-{rng.randint(1000, 9999)}",
        "n_referred": n_patients,
        "n_treated": n_treated,
        "manufacturing_success_rate": round(mfg_success_rate, 1),
        "efficacy": {
            "orr": round(orr_rwe_actual, 1),
            "cr_rate": round(cr_n / max(1, n_treated) * 100, 1),
            "pr_rate": round(pr_n / max(1, n_treated) * 100, 1),
            "median_pfs_months": round(sorted([p.pfs_months for p in treated])[n_treated // 2], 1) if treated else 0,
        },
        "safety": {
            "grade3_crs_rate": round(g3_crs_rate, 1),
            "grade3_icans_rate": round(g3_icans_rate, 1),
            "icu_rate": round(sum(1 for p in treated if p.icu_admission) / max(1, n_treated) * 100, 1),
            "30d_mortality": round(sum(1 for p in treated if p.death_within_30d) / max(1, n_treated) * 100, 1),
        },
        "access": {
            "median_time_to_infusion_days": median_time,
            "median_cost_inr": median_cost,
            "median_cost_formatted": f"₹{median_cost:,.0f}",
            "ltfu_rate": round(sum(1 for p in patients if p.lost_to_followup) / n_patients * 100, 1),
        },
        "site_analysis": site_analysis,
        "insurance_analysis": insurance_analysis,
        "socioeconomic_analysis": ses_analysis,
        "disparities": _compute_disparities(site_analysis, insurance_analysis, ses_analysis),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def compare_rwe_vs_trial(
    product: str = "axi-cel",
    cancer_type: str = "DLBCL",
    rwe_n: int = 200,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Compare real-world evidence to clinical trial results."""
    rwe = generate_registry_data(rwe_n, cancer_type, product, seed=seed)

    trial_data = {
        "axi-cel": {"trial": "ZUMA-1", "orr": 83, "cr": 58, "g3_crs": 13, "g3_icans": 28, "n": 101},
        "tisa-cel": {"trial": "JULIET", "orr": 52, "cr": 40, "g3_crs": 22, "g3_icans": 12, "n": 93},
        "liso-cel": {"trial": "TRANSCEND", "orr": 73, "cr": 53, "g3_crs": 2, "g3_icans": 10, "n": 269},
    }

    trial = trial_data.get(product, trial_data["axi-cel"])

    comparisons = [
        {
            "metric": "Overall Response Rate",
            "trial_value": trial["orr"],
            "rwe_value": rwe["efficacy"]["orr"],
            "difference": round(rwe["efficacy"]["orr"] - trial["orr"], 1),
            "interpretation": "RWE typically shows lower response rates due to broader patient selection",
        },
        {
            "metric": "Complete Response Rate",
            "trial_value": trial["cr"],
            "rwe_value": rwe["efficacy"]["cr_rate"],
            "difference": round(rwe["efficacy"]["cr_rate"] - trial["cr"], 1),
            "interpretation": "Consistent with real-world performance expectations",
        },
        {
            "metric": "Grade ≥3 CRS",
            "trial_value": trial["g3_crs"],
            "rwe_value": rwe["safety"]["grade3_crs_rate"],
            "difference": round(rwe["safety"]["grade3_crs_rate"] - trial["g3_crs"], 1),
            "interpretation": "Safety profiles may vary with institutional experience",
        },
        {
            "metric": "Grade ≥3 ICANS",
            "trial_value": trial["g3_icans"],
            "rwe_value": rwe["safety"]["grade3_icans_rate"],
            "difference": round(rwe["safety"]["grade3_icans_rate"] - trial["g3_icans"], 1),
            "interpretation": "ICANS management varies across centers",
        },
    ]

    effectiveness_gap = trial["orr"] - rwe["efficacy"]["orr"]

    return {
        "product": product,
        "trial_name": trial["trial"],
        "trial_n": trial["n"],
        "rwe_n": rwe["n_treated"],
        "comparisons": comparisons,
        "effectiveness_gap": round(effectiveness_gap, 1),
        "gap_interpretation": (
            "Minimal effectiveness-efficacy gap — strong real-world performance"
            if effectiveness_gap < 5
            else "Moderate gap — expected for RWE due to broader population"
            if effectiveness_gap < 15
            else "Significant gap — investigate patient selection and center experience"
        ),
        "rwe_summary": rwe,
    }


def post_market_surveillance(
    product: str = "axi-cel",
    n_patients: int = 500,
    monitoring_months: int = 36,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Simulate post-market safety surveillance data."""
    rng = random.Random(seed or 42)

    safety_signals = []
    monthly_data = []

    cumulative_cases = 0
    for month in range(1, monitoring_months + 1):
        new_cases = max(0, int(rng.gauss(n_patients / monitoring_months, 3)))
        cumulative_cases += new_cases

        # AE rates this month (may trend down as experience grows)
        experience_factor = max(0.6, 1 - month * 0.01)
        crs_rate = 0.15 * experience_factor
        icans_rate = 0.12 * experience_factor
        infection_rate = 0.08
        cytopenia_rate = 0.30

        # Rare events (signal detection)
        delayed_neuro = rng.random() < 0.005  # Delayed neurotoxicity
        secondary_malignancy = rng.random() < 0.002
        cardiac_event = rng.random() < 0.01

        monthly_data.append({
            "month": month,
            "new_cases": new_cases,
            "cumulative": cumulative_cases,
            "crs_events": int(new_cases * crs_rate),
            "icans_events": int(new_cases * icans_rate),
            "infection_events": int(new_cases * infection_rate),
        })

        if delayed_neuro:
            safety_signals.append({
                "month": month,
                "signal": "Delayed Neurotoxicity",
                "severity": "serious",
                "action": "Investigate — potential new safety signal",
            })
        if secondary_malignancy:
            safety_signals.append({
                "month": month,
                "signal": "Secondary Malignancy (T-cell lymphoma)",
                "severity": "critical",
                "action": "Mandatory reporting to regulatory authority (CDSCO/FDA)",
            })
        if cardiac_event:
            safety_signals.append({
                "month": month,
                "signal": "Cardiac Adverse Event",
                "severity": "serious",
                "action": "Evaluate for cardiomyopathy, update REMS monitoring",
            })

    return {
        "product": product,
        "monitoring_months": monitoring_months,
        "total_patients": cumulative_cases,
        "monthly_summary": monthly_data,
        "safety_signals": safety_signals,
        "signal_count": len(safety_signals),
        "risk_benefit_assessment": (
            "Favorable" if len(safety_signals) < 3
            else "Under review" if len(safety_signals) < 8
            else "Requires regulatory discussion"
        ),
    }


def health_technology_assessment(
    product: str = "axi-cel",
    cancer_type: str = "DLBCL",
    comparator: str = "salvage_chemotherapy",
    time_horizon_years: int = 5,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Health technology assessment for CAR-T vs. comparator."""
    rng = random.Random(seed or 42)

    # CAR-T arm
    cart_cost = 30000000 + 3000000  # drug + hospital
    cart_orr = 0.75
    cart_pfs_years = 1.5
    cart_utility = 0.72
    cart_ae_cost = 2000000

    # Comparator
    comp_costs = {
        "salvage_chemotherapy": {"cost": 5000000, "orr": 0.30, "pfs_years": 0.5, "utility": 0.55},
        "best_supportive_care": {"cost": 2000000, "orr": 0.05, "pfs_years": 0.25, "utility": 0.40},
        "auto_sct": {"cost": 15000000, "orr": 0.45, "pfs_years": 1.0, "utility": 0.60},
    }

    comp = comp_costs.get(comparator, comp_costs["salvage_chemotherapy"])

    # QALYs
    cart_qaly = cart_utility * min(cart_pfs_years, time_horizon_years) * cart_orr
    cart_qaly += 0.40 * max(0, time_horizon_years - cart_pfs_years) * (1 - cart_orr)
    comp_qaly = comp["utility"] * min(comp["pfs_years"], time_horizon_years) * comp["orr"]
    comp_qaly += 0.30 * max(0, time_horizon_years - comp["pfs_years"]) * (1 - comp["orr"])

    incremental_qaly = cart_qaly - comp_qaly
    incremental_cost = (cart_cost + cart_ae_cost) - comp["cost"]
    icer = incremental_cost / max(0.01, incremental_qaly)

    # Willingness-to-pay thresholds (India-specific)
    wtp_1x_gdp = 170000  # ~1x GDP per capita
    wtp_3x_gdp = 510000
    wtp_india = 1500000  # practical threshold

    return {
        "product": product,
        "comparator": comparator,
        "time_horizon_years": time_horizon_years,
        "car_t_arm": {
            "total_cost_inr": cart_cost + cart_ae_cost,
            "orr": f"{cart_orr * 100:.0f}%",
            "median_pfs_years": cart_pfs_years,
            "qaly_gained": round(cart_qaly, 2),
        },
        "comparator_arm": {
            "total_cost_inr": comp["cost"],
            "orr": f"{comp['orr'] * 100:.0f}%",
            "median_pfs_years": comp["pfs_years"],
            "qaly_gained": round(comp_qaly, 2),
        },
        "incremental_analysis": {
            "incremental_cost": incremental_cost,
            "incremental_qaly": round(incremental_qaly, 2),
            "icer": round(icer),
            "icer_formatted": f"₹{icer:,.0f}/QALY",
        },
        "cost_effectiveness_conclusion": (
            "Cost-effective at India WTP threshold" if icer < wtp_india
            else "Not cost-effective at current pricing — consider outcomes-based agreements"
        ),
        "budget_impact": {
            "eligible_patients_annual": 3750,
            "total_budget_if_all_treated": f"₹{3750 * (cart_cost + cart_ae_cost):,.0f}",
            "budget_impact_vs_comparator": f"₹{3750 * incremental_cost:,.0f}",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_disparities(sites: Dict, insurance: Dict, ses: Dict) -> Dict[str, Any]:
    """Compute access and outcome disparities."""
    disparities = []

    # Insurance disparity
    if insurance:
        orr_values = {k: v.get("orr", 0) for k, v in insurance.items() if v.get("orr")}
        if orr_values:
            max_orr_ins = max(orr_values, key=orr_values.get)
            min_orr_ins = min(orr_values, key=orr_values.get)
            if orr_values[max_orr_ins] - orr_values[min_orr_ins] > 10:
                disparities.append({
                    "type": "Insurance",
                    "finding": f"ORR gap of {orr_values[max_orr_ins] - orr_values[min_orr_ins]:.1f}% between {max_orr_ins} ({orr_values[max_orr_ins]:.1f}%) and {min_orr_ins} ({orr_values[min_orr_ins]:.1f}%)",
                    "severity": "significant",
                })

    # SES disparity
    if ses:
        high_orr = ses.get("high", {}).get("orr", 0)
        low_orr = ses.get("low", {}).get("orr", 0)
        if high_orr - low_orr > 8:
            disparities.append({
                "type": "Socioeconomic",
                "finding": f"ORR gap of {high_orr - low_orr:.1f}% between high-SES ({high_orr:.1f}%) and low-SES ({low_orr:.1f}%)",
                "severity": "significant",
            })

        high_ltfu = ses.get("low", {}).get("ltfu_rate", 0)
        if high_ltfu > 5:
            disparities.append({
                "type": "Follow-up",
                "finding": f"Low-SES patients have {high_ltfu:.1f}% lost-to-follow-up rate",
                "severity": "moderate",
            })

    return {
        "disparities_found": len(disparities),
        "findings": disparities,
        "recommendation": (
            "Significant disparities detected — implement equity-focused interventions"
            if len(disparities) >= 2
            else "Minor disparities — continue monitoring"
            if disparities
            else "No significant disparities detected"
        ),
    }
