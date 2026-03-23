"""
CARVanta – Population-Level CAR-T Simulator
=============================================
Monte Carlo simulation engine for population-level CAR-T outcomes.
Enables:
  - Large-scale cohort simulations (100-10,000 patients)
  - Sensitivity analysis across input parameters
  - Subgroup analysis by demographics and genomics
  - Cost-effectiveness modeling (ICER calculations)
  - Number needed to treat (NNT) calculations
  - Real-world evidence generation
  - Geographic access modeling
  - Capacity planning for treatment centers
"""

import math
import random
import statistics
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# Population Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PopulationConfig:
    """Configuration for population simulation."""
    n_patients: int = 500
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    follow_up_months: int = 24
    # Demographics
    age_mean: float = 58.0
    age_sd: float = 12.0
    male_fraction: float = 0.58
    # Disease characteristics
    stage_distribution: Dict[str, float] = field(default_factory=lambda: {
        "I": 0.05, "II": 0.15, "III": 0.35, "IV": 0.45
    })
    median_prior_lines: int = 3
    prior_car_t_rate: float = 0.05
    double_hit_rate: float = 0.10
    tp53_mutation_rate: float = 0.20
    # Treatment parameters
    bridging_rate: float = 0.40
    median_tumor_burden: float = 55.0
    # Geographic / access
    country: str = "India"
    urban_fraction: float = 0.65


@dataclass
class SimulationResult:
    """Aggregated result from a population simulation."""
    config: PopulationConfig
    outcomes: List[Dict]  # per-patient outcomes
    summary: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# Core Simulation Engine
# ═══════════════════════════════════════════════════════════════════════════════

def run_population_simulation(
    n_patients: int = 500,
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    follow_up_months: int = 24,
    seed: Optional[int] = None,
    config: Optional[PopulationConfig] = None,
) -> Dict[str, Any]:
    """
    Run a Monte Carlo population simulation.
    Generates a synthetic cohort with realistic outcome distributions.
    """
    rng = random.Random(seed or 42)

    if config is None:
        config = PopulationConfig(
            n_patients=n_patients,
            cancer_type=cancer_type,
            product=product,
            follow_up_months=follow_up_months,
        )

    # Generate patient population
    patients = _generate_population(config, rng)

    # Simulate outcomes for each patient
    outcomes = []
    for pt in patients:
        outcome = _simulate_patient_outcome(pt, config, rng)
        outcomes.append(outcome)

    # Compute statistics
    summary = _compute_population_stats(outcomes, config)

    # Subgroup analyses
    subgroups = _subgroup_analysis(outcomes)

    # Sensitivity analysis
    sensitivity = _sensitivity_analysis(config, rng)

    # Cost-effectiveness
    cost_eff = _cost_effectiveness_analysis(outcomes, config)

    # Capacity planning
    capacity = _capacity_planning(config)

    return {
        "simulation_id": f"SIM-{rng.randint(10000, 99999)}",
        "config": {
            "n_patients": config.n_patients,
            "cancer_type": config.cancer_type,
            "product": config.product,
            "follow_up_months": config.follow_up_months,
            "country": config.country,
        },
        "summary": summary,
        "subgroup_analysis": subgroups,
        "sensitivity_analysis": sensitivity,
        "cost_effectiveness": cost_eff,
        "capacity_planning": capacity,
        "distribution_data": _distribution_data(outcomes),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_sensitivity_analysis(
    parameter: str = "tumor_burden",
    values: Optional[List[float]] = None,
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    n_simulations: int = 200,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying a single parameter across a range.
    Returns outcome metrics at each parameter value.
    """
    rng = random.Random(seed or 42)

    if values is None:
        if parameter == "tumor_burden":
            values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150]
        elif parameter == "age":
            values = [20, 30, 40, 50, 55, 60, 65, 70, 75, 80]
        elif parameter == "prior_lines":
            values = [1, 2, 3, 4, 5]
        elif parameter == "dose":
            values = [5e7, 1e8, 1.5e8, 2e8, 3e8, 5e8]
        else:
            values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    results = []

    for val in values:
        # Create config with varied parameter
        cfg = PopulationConfig(
            n_patients=n_simulations,
            cancer_type=cancer_type,
            product=product,
        )

        if parameter == "tumor_burden":
            cfg.median_tumor_burden = val
        elif parameter == "age":
            cfg.age_mean = val
            cfg.age_sd = 5
        elif parameter == "prior_lines":
            cfg.median_prior_lines = int(val)
        elif parameter == "double_hit_rate":
            cfg.double_hit_rate = val
        elif parameter == "tp53_rate":
            cfg.tp53_mutation_rate = val

        patients = _generate_population(cfg, rng)
        outcomes = [_simulate_patient_outcome(pt, cfg, rng) for pt in patients]
        stats = _compute_population_stats(outcomes, cfg)

        results.append({
            "parameter_value": val,
            "orr": stats["response"]["orr"],
            "cr_rate": stats["response"]["cr_rate"],
            "median_pfs_months": stats["survival"]["median_pfs_months"],
            "grade3_crs_rate": stats["safety"]["grade3_crs_rate"],
            "overall_toxicity": stats["safety"]["overall_toxicity_rate"],
        })

    return {
        "parameter": parameter,
        "values": values,
        "results": results,
        "interpretation": _interpret_sensitivity(parameter, results),
    }


def compare_products(
    cancer_type: str = "DLBCL",
    products: Optional[List[str]] = None,
    n_simulations: int = 300,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Head-to-head population-level comparison of CAR-T products.
    """
    rng = random.Random(seed or 42)

    if products is None:
        products = ["axi-cel", "tisa-cel", "liso-cel"]

    comparisons = []

    for product in products:
        cfg = PopulationConfig(
            n_patients=n_simulations,
            cancer_type=cancer_type,
            product=product,
        )
        patients = _generate_population(cfg, rng)
        outcomes = [_simulate_patient_outcome(pt, cfg, rng) for pt in patients]
        stats = _compute_population_stats(outcomes, cfg)

        comparisons.append({
            "product": product,
            "orr": stats["response"]["orr"],
            "cr_rate": stats["response"]["cr_rate"],
            "median_pfs": stats["survival"]["median_pfs_months"],
            "grade3_crs": stats["safety"]["grade3_crs_rate"],
            "grade3_icans": stats["safety"]["grade3_icans_rate"],
            "icu_rate": stats["safety"]["icu_rate"],
            "cost_total": stats.get("cost", {}).get("total_per_patient", 0),
        })

    # Rank by ORR
    comparisons.sort(key=lambda c: c["orr"], reverse=True)

    return {
        "cancer_type": cancer_type,
        "n_per_product": n_simulations,
        "comparisons": comparisons,
        "winner_efficacy": comparisons[0]["product"],
        "winner_safety": min(comparisons, key=lambda c: c["grade3_crs"])["product"],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Population Generation
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_population(cfg: PopulationConfig, rng: random.Random) -> List[Dict]:
    """Generate a synthetic patient population."""
    patients = []

    for i in range(cfg.n_patients):
        age = int(rng.gauss(cfg.age_mean, cfg.age_sd))
        age = max(2, min(90, age))

        # Stage distribution
        stages = list(cfg.stage_distribution.keys())
        weights = list(cfg.stage_distribution.values())
        stage = rng.choices(stages, weights=weights)[0]

        # Tumor burden (log-normal distribution)
        tb = rng.lognormvariate(math.log(cfg.median_tumor_burden), 0.5)
        tb = max(5, min(200, tb))

        # Prior lines (Poisson-like)
        prior = max(1, min(8, int(rng.gauss(cfg.median_prior_lines, 1.2))))

        # Risk factors
        tp53 = rng.random() < cfg.tp53_mutation_rate
        double_hit = rng.random() < cfg.double_hit_rate
        prior_cart = rng.random() < cfg.prior_car_t_rate
        ecog = rng.choices([0, 1, 2, 3], weights=[20, 50, 25, 5])[0]

        # Labs
        ldh = rng.gauss(250, 120)
        ldh = max(100, ldh)
        if stage == "IV":
            ldh += rng.gauss(100, 50)

        patients.append({
            "id": f"POP-{i+1:05d}",
            "age": age,
            "sex": "M" if rng.random() < cfg.male_fraction else "F",
            "stage": stage,
            "tumor_burden_mm": round(tb, 1),
            "prior_lines": prior,
            "prior_car_t": prior_cart,
            "tp53_mutated": tp53,
            "double_hit": double_hit,
            "ecog": ecog,
            "ldh": round(ldh, 0),
            "bridging": rng.random() < cfg.bridging_rate,
        })

    return patients


def _simulate_patient_outcome(
    patient: Dict,
    cfg: PopulationConfig,
    rng: random.Random,
) -> Dict:
    """Simulate outcome for a single patient."""
    # Base response rates by product
    product_baselines = {
        "axi-cel": {"orr": 83, "cr": 58, "pfs": 5.9, "g3_crs": 13, "g3_icans": 28},
        "tisa-cel": {"orr": 52, "cr": 40, "pfs": 2.9, "g3_crs": 22, "g3_icans": 12},
        "liso-cel": {"orr": 73, "cr": 53, "pfs": 6.8, "g3_crs": 2, "g3_icans": 10},
        "brexu-cel": {"orr": 91, "cr": 68, "pfs": 14.6, "g3_crs": 15, "g3_icans": 31},
        "ide-cel": {"orr": 73, "cr": 33, "pfs": 8.8, "g3_crs": 5, "g3_icans": 3},
        "cilta-cel": {"orr": 98, "cr": 83, "pfs": 27.7, "g3_crs": 4, "g3_icans": 2},
    }

    base = product_baselines.get(cfg.product, product_baselines["axi-cel"])

    # Adjust response probability
    orr_prob = base["orr"] / 100
    cr_prob = base["cr"] / 100

    # Age factor
    if patient["age"] > 70:
        orr_prob *= 0.85
        cr_prob *= 0.8
    elif patient["age"] > 60:
        orr_prob *= 0.95
    elif patient["age"] < 30:
        orr_prob *= 1.08

    # Tumor burden factor
    if patient["tumor_burden_mm"] > 100:
        orr_prob *= 0.8
        cr_prob *= 0.7
    elif patient["tumor_burden_mm"] > 70:
        orr_prob *= 0.9
    elif patient["tumor_burden_mm"] < 25:
        orr_prob *= 1.1
        cr_prob *= 1.1

    # Genomic factors
    if patient.get("double_hit"):
        orr_prob *= 0.7
        cr_prob *= 0.55
    if patient.get("tp53_mutated"):
        orr_prob *= 0.85
        cr_prob *= 0.75

    # Prior lines
    if patient["prior_lines"] >= 5:
        orr_prob *= 0.7
    elif patient["prior_lines"] >= 4:
        orr_prob *= 0.8

    # ECOG
    if patient["ecog"] >= 2:
        orr_prob *= 0.8

    # Clamp
    orr_prob = max(0.1, min(0.99, orr_prob))
    cr_prob = max(0.05, min(orr_prob, cr_prob))

    # Sample response
    r = rng.random()
    if r < cr_prob:
        response = "CR"
    elif r < orr_prob:
        response = "PR"
    elif r < orr_prob + 0.08:
        response = "SD"
    else:
        response = "PD"

    # PFS
    base_pfs = base["pfs"]
    pfs_modifier = 1.0
    if response == "CR":
        pfs_modifier = 2.0
    elif response == "PR":
        pfs_modifier = 1.0
    elif response == "SD":
        pfs_modifier = 0.4
    else:
        pfs_modifier = 0.15

    if patient.get("double_hit"):
        pfs_modifier *= 0.5
    if patient.get("tp53_mutated"):
        pfs_modifier *= 0.7

    pfs_months = rng.expovariate(1 / max(0.5, base_pfs * pfs_modifier))
    pfs_months = max(0.5, min(cfg.follow_up_months, pfs_months))

    # CRS
    crs_base = base["g3_crs"] / 100
    if patient["tumor_burden_mm"] > 80:
        crs_base *= 1.5
    if patient["ldh"] > 400:
        crs_base *= 1.3

    crs_grade = 0
    r = rng.random()
    if r < crs_base * 0.2:
        crs_grade = 4
    elif r < crs_base:
        crs_grade = 3
    elif r < crs_base * 4:
        crs_grade = 2
    elif r < crs_base * 7:
        crs_grade = 1

    # ICANS
    icans_base = base["g3_icans"] / 100
    if patient["age"] > 65:
        icans_base *= 1.4

    icans_grade = 0
    r = rng.random()
    if r < icans_base:
        icans_grade = rng.choice([3, 4])
    elif r < icans_base * 3:
        icans_grade = 2
    elif r < icans_base * 5:
        icans_grade = 1

    # ICU
    icu = crs_grade >= 3 or icans_grade >= 3

    # Cost (INR)
    drug_cost = 30000000
    hospital_days = 14 + (7 if icu else 0) + crs_grade * 3
    total_cost = drug_cost + hospital_days * 100000 + 1000000  # support

    return {
        "id": patient["id"],
        "age": patient["age"],
        "sex": patient["sex"],
        "stage": patient["stage"],
        "tumor_burden_mm": patient["tumor_burden_mm"],
        "prior_lines": patient["prior_lines"],
        "double_hit": patient.get("double_hit", False),
        "tp53": patient.get("tp53_mutated", False),
        "ecog": patient["ecog"],
        "response": response,
        "pfs_months": round(pfs_months, 1),
        "crs_grade": crs_grade,
        "icans_grade": icans_grade,
        "icu": icu,
        "cost_inr": total_cost,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Statistical Analysis
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_population_stats(outcomes: List[Dict], cfg: PopulationConfig) -> Dict[str, Any]:
    """Compute population-level statistics."""
    n = len(outcomes)

    # Response
    cr_n = sum(1 for o in outcomes if o["response"] == "CR")
    pr_n = sum(1 for o in outcomes if o["response"] == "PR")
    sd_n = sum(1 for o in outcomes if o["response"] == "SD")
    pd_n = sum(1 for o in outcomes if o["response"] == "PD")
    orr = (cr_n + pr_n) / n * 100

    # PFS
    pfs_values = [o["pfs_months"] for o in outcomes]
    pfs_values.sort()
    median_pfs = pfs_values[n // 2] if n else 0

    # Safety
    g3_crs_n = sum(1 for o in outcomes if o["crs_grade"] >= 3)
    g3_icans_n = sum(1 for o in outcomes if o["icans_grade"] >= 3)
    icu_n = sum(1 for o in outcomes if o["icu"])
    any_tox = sum(1 for o in outcomes if o["crs_grade"] >= 1 or o["icans_grade"] >= 1)

    # Cost
    costs = [o["cost_inr"] for o in outcomes]
    mean_cost = statistics.mean(costs) if costs else 0

    return {
        "response": {
            "orr": round(orr, 1),
            "cr_rate": round(cr_n / n * 100, 1),
            "pr_rate": round(pr_n / n * 100, 1),
            "sd_rate": round(sd_n / n * 100, 1),
            "pd_rate": round(pd_n / n * 100, 1),
            "n": n,
        },
        "survival": {
            "median_pfs_months": round(median_pfs, 1),
            "6mo_pfs_rate": round(sum(1 for p in pfs_values if p >= 6) / n * 100, 1),
            "12mo_pfs_rate": round(sum(1 for p in pfs_values if p >= 12) / n * 100, 1),
        },
        "safety": {
            "any_crs_rate": round(sum(1 for o in outcomes if o["crs_grade"] >= 1) / n * 100, 1),
            "grade3_crs_rate": round(g3_crs_n / n * 100, 1),
            "grade3_icans_rate": round(g3_icans_n / n * 100, 1),
            "icu_rate": round(icu_n / n * 100, 1),
            "overall_toxicity_rate": round(any_tox / n * 100, 1),
        },
        "cost": {
            "total_per_patient": round(mean_cost),
            "total_per_patient_formatted": f"₹{mean_cost:,.0f}",
            "cost_per_response": round(mean_cost / max(1, (cr_n + pr_n) / n)),
        },
    }


def _subgroup_analysis(outcomes: List[Dict]) -> Dict[str, Any]:
    """Run subgroup analyses by key demographics."""
    subgroups = {}

    # By age
    young = [o for o in outcomes if o["age"] < 50]
    middle = [o for o in outcomes if 50 <= o["age"] < 65]
    elderly = [o for o in outcomes if o["age"] >= 65]

    subgroups["age"] = {
        "<50": _subgroup_stats(young),
        "50-64": _subgroup_stats(middle),
        "≥65": _subgroup_stats(elderly),
    }

    # By tumor burden
    low_tb = [o for o in outcomes if o["tumor_burden_mm"] < 40]
    high_tb = [o for o in outcomes if o["tumor_burden_mm"] >= 80]
    subgroups["tumor_burden"] = {
        "low (<40mm)": _subgroup_stats(low_tb),
        "high (≥80mm)": _subgroup_stats(high_tb),
    }

    # By genomics
    dh = [o for o in outcomes if o.get("double_hit")]
    non_dh = [o for o in outcomes if not o.get("double_hit")]
    subgroups["double_hit"] = {
        "double_hit": _subgroup_stats(dh),
        "non_double_hit": _subgroup_stats(non_dh),
    }

    tp53 = [o for o in outcomes if o.get("tp53")]
    wt = [o for o in outcomes if not o.get("tp53")]
    subgroups["tp53"] = {
        "mutated": _subgroup_stats(tp53),
        "wild_type": _subgroup_stats(wt),
    }

    # By stage
    early = [o for o in outcomes if o["stage"] in ("I", "II")]
    late = [o for o in outcomes if o["stage"] in ("III", "IV")]
    subgroups["stage"] = {
        "early (I-II)": _subgroup_stats(early),
        "advanced (III-IV)": _subgroup_stats(late),
    }

    return subgroups


def _subgroup_stats(outcomes: List[Dict]) -> Dict[str, Any]:
    """Compute stats for a subgroup."""
    n = len(outcomes)
    if n == 0:
        return {"n": 0, "orr": 0, "cr_rate": 0, "grade3_crs": 0}

    cr = sum(1 for o in outcomes if o["response"] == "CR")
    pr = sum(1 for o in outcomes if o["response"] == "PR")
    g3_crs = sum(1 for o in outcomes if o["crs_grade"] >= 3)

    pfs = sorted([o["pfs_months"] for o in outcomes])

    return {
        "n": n,
        "orr": round((cr + pr) / n * 100, 1),
        "cr_rate": round(cr / n * 100, 1),
        "median_pfs": round(pfs[n // 2], 1),
        "grade3_crs": round(g3_crs / n * 100, 1),
    }


def _sensitivity_analysis(cfg: PopulationConfig, rng: random.Random) -> Dict[str, Any]:
    """Run quick sensitivity analysis on key parameters."""
    params = {
        "tumor_burden": [20, 50, 100],
        "age_mean": [40, 58, 72],
        "tp53_rate": [0.0, 0.20, 0.40],
    }

    results = {}

    for param, values in params.items():
        param_results = []
        for val in values:
            test_cfg = PopulationConfig(
                n_patients=100,
                cancer_type=cfg.cancer_type,
                product=cfg.product,
            )

            if param == "tumor_burden":
                test_cfg.median_tumor_burden = val
            elif param == "age_mean":
                test_cfg.age_mean = val
            elif param == "tp53_rate":
                test_cfg.tp53_mutation_rate = val

            pts = _generate_population(test_cfg, rng)
            outs = [_simulate_patient_outcome(p, test_cfg, rng) for p in pts]
            stats = _compute_population_stats(outs, test_cfg)

            param_results.append({
                "value": val,
                "orr": stats["response"]["orr"],
                "cr_rate": stats["response"]["cr_rate"],
            })

        results[param] = param_results

    return results


def _cost_effectiveness_analysis(outcomes: List[Dict], cfg: PopulationConfig) -> Dict[str, Any]:
    """Cost-effectiveness analysis."""
    n = len(outcomes)
    responders = sum(1 for o in outcomes if o["response"] in ("CR", "PR"))
    cr_patients = sum(1 for o in outcomes if o["response"] == "CR")

    costs = [o["cost_inr"] for o in outcomes]
    total_cost = sum(costs)
    mean_cost = total_cost / n
    pfs_months = sorted([o["pfs_months"] for o in outcomes])
    mean_pfs = statistics.mean(pfs_months)

    # NNT
    nnt_response = max(1, round(n / max(1, responders)))
    nnt_cr = max(1, round(n / max(1, cr_patients)))

    # ICER (vs best supportive care)
    bsc_cost = 2000000  # estimated BSC cost
    bsc_pfs = 2.0  # BSC median PFS months
    icer = (mean_cost - bsc_cost) / max(0.1, mean_pfs - bsc_pfs)

    # QALYs
    mean_pfs_years = mean_pfs / 12
    utility_response = 0.75
    utility_no_response = 0.45
    qaly = (responders / n * utility_response + (n - responders) / n * utility_no_response) * mean_pfs_years

    cost_per_qaly = mean_cost / max(0.01, qaly)

    return {
        "mean_cost_per_patient": round(mean_cost),
        "mean_cost_formatted": f"₹{mean_cost:,.0f}",
        "cost_per_response": round(total_cost / max(1, responders)),
        "cost_per_cr": round(total_cost / max(1, cr_patients)),
        "nnt_response": nnt_response,
        "nnt_cr": nnt_cr,
        "icer_vs_bsc": round(icer),
        "icer_formatted": f"₹{icer:,.0f}/PFS-month gained",
        "qaly_gained": round(qaly, 2),
        "cost_per_qaly": round(cost_per_qaly),
        "cost_per_qaly_formatted": f"₹{cost_per_qaly:,.0f}/QALY",
        "cost_effective": cost_per_qaly < 15000000,  # threshold
    }


def _capacity_planning(cfg: PopulationConfig) -> Dict[str, Any]:
    """Treatment center capacity planning."""
    # India-specific estimates
    annual_cases = {
        "DLBCL": 25000, "ALL": 15000, "MCL": 3000,
        "Multiple Myeloma": 20000, "FL": 8000,
    }

    ct = cfg.cancer_type
    incident = annual_cases.get(ct, 10000)
    eligible_fraction = 0.15  # fraction eligible for CAR-T
    eligible = int(incident * eligible_fraction)

    # Treatment capacity
    manufacturing_days = 21
    bed_days = 21  # average stay
    annual_capacity_per_center = 365 // manufacturing_days

    centers_needed = math.ceil(eligible / annual_capacity_per_center)

    return {
        "annual_incident_cases": incident,
        "car_t_eligible": eligible,
        "eligible_fraction": f"{eligible_fraction*100:.0f}%",
        "manufacturing_cycle_days": manufacturing_days,
        "bed_days_per_patient": bed_days,
        "capacity_per_center": annual_capacity_per_center,
        "centers_needed": centers_needed,
        "current_centers_india": 5,
        "capacity_gap": max(0, centers_needed - 5),
        "geographical_model": {
            "tier1_cities": int(eligible * 0.45),
            "tier2_cities": int(eligible * 0.30),
            "rural": int(eligible * 0.25),
        },
    }


def _distribution_data(outcomes: List[Dict]) -> Dict[str, Any]:
    """Generate distribution data for histograms."""
    ages = [o["age"] for o in outcomes]
    tumor_burdens = [o["tumor_burden_mm"] for o in outcomes]
    pfs_values = [o["pfs_months"] for o in outcomes]
    costs = [o["cost_inr"] / 1e6 for o in outcomes]  # in millions

    return {
        "age_distribution": _histogram(ages, 10),
        "tumor_burden_distribution": _histogram(tumor_burdens, 10),
        "pfs_distribution": _histogram(pfs_values, 8),
        "cost_distribution_millions": _histogram(costs, 8),
    }


def _histogram(values: List[float], n_bins: int) -> Dict[str, Any]:
    """Create histogram bins."""
    if not values:
        return {"bins": [], "counts": []}

    min_val = min(values)
    max_val = max(values)
    bin_width = (max_val - min_val) / n_bins

    bins = []
    counts = []

    for i in range(n_bins):
        low = min_val + i * bin_width
        high = low + bin_width
        count = sum(1 for v in values if low <= v < high)
        bins.append(round(low, 1))
        counts.append(count)

    return {"bins": bins, "counts": counts, "bin_width": round(bin_width, 1)}


def _interpret_sensitivity(parameter: str, results: List[Dict]) -> str:
    """Interpret sensitivity analysis results."""
    orr_range = max(r["orr"] for r in results) - min(r["orr"] for r in results)

    if orr_range > 20:
        sensitivity = "highly sensitive"
    elif orr_range > 10:
        sensitivity = "moderately sensitive"
    else:
        sensitivity = "minimally sensitive"

    return f"ORR is {sensitivity} to {parameter} (range: {min(r['orr'] for r in results):.1f}–{max(r['orr'] for r in results):.1f}%)"
