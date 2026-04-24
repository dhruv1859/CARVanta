"""
CARVanta Drug Discovery — CAR-T Pharmacokinetics Engine
==========================================================
Model CAR-T cell pharmacokinetics (expansion, persistence, contraction)
and pharmacodynamic biomarker dynamics post-infusion.

Features:
- CAR-T expansion/contraction kinetics modeling
- Cytokine release syndrome (CRS) prediction
- ICANS neurotoxicity risk modeling
- Biomarker kinetics (CRP, ferritin, IL-6, IL-10, IFN-γ)
- B-cell aplasia duration prediction
- Response assessment (MRD, PET-CT correlation)
- Dose-response modeling
- Population PK variability simulation
"""

import logging
import math
import random
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("carvanta.drug_discovery.pk_engine")


# ──────────────────────────────────────────────────────────────────────
# PK Constants & Models
# ──────────────────────────────────────────────────────────────────────

_CRS_GRADING = {
    1: {"description": "Fever ≥38°C, no hypotension, no hypoxia", "management": "Supportive care, antipyretics", "tocilizumab": False},
    2: {"description": "Fever + hypotension (not requiring vasopressors) or hypoxia (low-flow O₂)", "management": "IV fluids, tocilizumab if not improving in 24h", "tocilizumab": True},
    3: {"description": "Fever + hypotension (requiring vasopressor ± vasopressin) or hypoxia (high-flow O₂/CPAP)", "management": "Tocilizumab + dexamethasone, ICU transfer", "tocilizumab": True},
    4: {"description": "Life-threatening: multiple vasopressors, mechanical ventilation, organ dysfunction", "management": "Tocilizumab + high-dose methylprednisolone, ICU, consider siltuximab if refractory", "tocilizumab": True},
}

_ICANS_GRADING = {
    1: {"ICE_score": "7-9", "description": "Mild confusion, dysgraphia", "management": "Monitoring Q4h, supportive care"},
    2: {"ICE_score": "3-6", "description": "Moderate confusion, dysphasia", "management": "Dexamethasone 10mg Q6h"},
    3: {"ICE_score": "0-2", "description": "Severe confusion, seizure (responds to benzodiazepines), focal edema on MRI", "management": "Dexamethasone 10mg Q6h + levetiracetam, consider ICU"},
    4: {"ICE_score": "0 (comatose)", "description": "Status epilepticus, cerebral edema, coma", "management": "High-dose methylprednisolone 1g/day, ICU, MRI stat"},
}


async def simulate_pk(
    dose_cells: float = 2e8,
    target: str = "CD19",
    costim: str = "4-1BB",
    tumor_burden: str = "high",
    n_days: int = 365,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Simulate CAR-T cell pharmacokinetics over time.
    Models expansion, peak, contraction, and long-term persistence phases.
    """
    if seed:
        random.seed(seed)

    # PK parameters based on costimulation
    pk_params = {
        "4-1BB": {"expansion_rate": 0.35, "peak_day": 12, "contraction_rate": 0.04, "persistence_baseline": 0.02},
        "CD28": {"expansion_rate": 0.45, "peak_day": 8, "contraction_rate": 0.08, "persistence_baseline": 0.005},
    }
    params = pk_params.get(costim, pk_params["4-1BB"])

    # Tumor burden affects expansion
    burden_multiplier = {"high": 1.5, "moderate": 1.0, "low": 0.6, "minimal": 0.3}.get(tumor_burden, 1.0)
    params["expansion_rate"] *= burden_multiplier

    timepoints = []
    peak_cells = 0
    peak_day = 0

    for day in range(n_days + 1):
        if day > 60 and day % 7 != 0 and day != n_days:
            continue

        # Three-phase PK model
        if day <= params["peak_day"]:
            # Expansion phase
            car_t_cells = dose_cells * math.exp(params["expansion_rate"] * day)
        elif day <= params["peak_day"] + 30:
            # Contraction phase
            peak_val = dose_cells * math.exp(params["expansion_rate"] * params["peak_day"])
            days_post_peak = day - params["peak_day"]
            car_t_cells = peak_val * math.exp(-params["contraction_rate"] * days_post_peak)
        else:
            # Persistence phase (slow decline or plateau)
            peak_val = dose_cells * math.exp(params["expansion_rate"] * params["peak_day"])
            contraction_val = peak_val * math.exp(-params["contraction_rate"] * 30)
            days_post_contraction = day - params["peak_day"] - 30
            car_t_cells = max(
                contraction_val * params["persistence_baseline"],
                contraction_val * math.exp(-0.005 * days_post_contraction),
            )

        # Add biological variability
        car_t_cells *= (1 + random.gauss(0, 0.05))
        car_t_cells = max(0, car_t_cells)

        if car_t_cells > peak_cells:
            peak_cells = car_t_cells
            peak_day = day

        # Cytokine levels (correlated with expansion)
        expansion_ratio = car_t_cells / max(dose_cells, 1)
        il6 = max(0, 5 + expansion_ratio * 200 + random.gauss(0, 10))
        il10 = max(0, 3 + expansion_ratio * 80 + random.gauss(0, 5))
        ifng = max(0, 10 + expansion_ratio * 500 + random.gauss(0, 20))
        crp = max(0, 5 + expansion_ratio * 150 + random.gauss(0, 8))
        ferritin = max(50, 300 + expansion_ratio * 5000 + random.gauss(0, 200))

        # B-cell aplasia (for CD19)
        b_cells = 0 if (target == "CD19" and car_t_cells > 1e4) else max(0, 50 + random.gauss(0, 20))

        timepoints.append({
            "day": day,
            "car_t_cells_per_uL": round(car_t_cells / 1e4, 2),
            "total_car_t": f"{car_t_cells:.2e}",
            "cytokines": {
                "IL-6_pg_mL": round(il6, 1),
                "IL-10_pg_mL": round(il10, 1),
                "IFN-γ_pg_mL": round(ifng, 1),
            },
            "inflammatory": {
                "CRP_mg_L": round(crp, 1),
                "Ferritin_ng_mL": round(ferritin, 0),
            },
            "b_cells_per_uL": round(b_cells, 0) if target == "CD19" else None,
        })

    # CRS prediction
    peak_expansion = peak_cells / dose_cells
    crs_grade = 1
    if peak_expansion > 500:
        crs_grade = 4
    elif peak_expansion > 100:
        crs_grade = 3
    elif peak_expansion > 20:
        crs_grade = 2

    crs_onset = max(1, params["peak_day"] - random.randint(2, 5))
    crs_duration = random.randint(3, 10)

    # ICANS prediction
    icans_grade = max(1, crs_grade - random.randint(0, 1))
    icans_onset = crs_onset + random.randint(1, 4)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "dose_cells": f"{dose_cells:.0e}",
        "target": target,
        "costimulation": costim,
        "tumor_burden": tumor_burden,
        "pk_summary": {
            "peak_day": peak_day,
            "peak_cells": f"{peak_cells:.2e}",
            "peak_expansion_fold": round(peak_cells / dose_cells, 1),
            "day_30_persistence": timepoints[min(30, len(timepoints) - 1)]["total_car_t"],
            "day_90_persistence": timepoints[min(len(timepoints) - 1, next((i for i, t in enumerate(timepoints) if t["day"] >= 90), len(timepoints) - 1))]["total_car_t"],
        },
        "crs_prediction": {
            "grade": crs_grade,
            "onset_day": crs_onset,
            "duration_days": crs_duration,
            "details": _CRS_GRADING[crs_grade],
        },
        "icans_prediction": {
            "grade": icans_grade,
            "onset_day": icans_onset,
            "details": _ICANS_GRADING[icans_grade],
        },
        "b_cell_aplasia": {
            "expected": target == "CD19",
            "duration_months": random.randint(3, 24) if target == "CD19" else 0,
            "management": "Monthly IVIG replacement therapy" if target == "CD19" else "N/A",
        },
        "timepoints": timepoints,
    }


async def dose_response_analysis(
    target: str = "CD19",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Model dose-response relationship for CAR-T therapy.
    Evaluates multiple dose levels and predicts efficacy vs toxicity trade-off.
    """
    if seed:
        random.seed(seed)

    dose_levels = [
        {"label": "Low", "cells": 5e7, "description": "5×10⁷ CAR+ cells"},
        {"label": "Medium-Low", "cells": 1e8, "description": "1×10⁸ CAR+ cells"},
        {"label": "Medium", "cells": 2e8, "description": "2×10⁸ CAR+ cells"},
        {"label": "Medium-High", "cells": 5e8, "description": "5×10⁸ CAR+ cells"},
        {"label": "High", "cells": 1e9, "description": "1×10⁹ CAR+ cells"},
    ]

    results = []
    for dl in dose_levels:
        dose = dl["cells"]
        # Efficacy follows Emax model
        ec50 = 2e8
        emax = 0.92
        efficacy = emax * dose / (ec50 + dose) + random.gauss(0, 0.03)
        cr_rate = efficacy * 0.7 + random.gauss(0, 0.05)
        orr = min(1, efficacy + 0.1 + random.gauss(0, 0.03))

        # Toxicity increases roughly linearly
        crs_3plus = min(0.6, 0.02 + (dose / 1e9) * 0.25 + random.gauss(0, 0.03))
        icans_3plus = min(0.4, 0.01 + (dose / 1e9) * 0.15 + random.gauss(0, 0.02))

        # Therapeutic index
        ti = efficacy / max(crs_3plus, 0.01)

        results.append({
            "dose_level": dl["label"],
            "dose_cells": dl["description"],
            "efficacy": {
                "ORR": round(min(1, max(0, orr)), 3),
                "CR_rate": round(min(1, max(0, cr_rate)), 3),
            },
            "toxicity": {
                "CRS_grade3plus_pct": round(max(0, crs_3plus), 3),
                "ICANS_grade3plus_pct": round(max(0, icans_3plus), 3),
            },
            "therapeutic_index": round(ti, 2),
        })

    # Find optimal dose
    optimal = max(results, key=lambda x: x["therapeutic_index"])

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "dose_levels": results,
        "optimal_dose": {
            "level": optimal["dose_level"],
            "dose": optimal["dose_cells"],
            "therapeutic_index": optimal["therapeutic_index"],
            "rationale": f"{optimal['dose_level']} dose provides best therapeutic index ({optimal['therapeutic_index']:.1f}x) balancing {optimal['efficacy']['ORR']*100:.0f}% ORR with {optimal['toxicity']['CRS_grade3plus_pct']*100:.0f}% CRS ≥3",
        },
        "ec50_estimate": "2×10⁸ CAR+ cells",
    }


async def population_pk(
    n_patients: int = 50,
    dose_cells: float = 2e8,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Simulate population PK variability across patients.
    Generates distribution of expansion, persistence, and toxicity outcomes.
    """
    if seed:
        random.seed(seed)

    patients = []
    for i in range(n_patients):
        # Patient-specific variability
        age = random.randint(18, 80)
        tumor_burden = random.choice(["low", "moderate", "high"])
        prior_therapies = random.randint(1, 6)
        lymphodepletion = random.choice(["flu_cy", "bendamustine", "none"])

        # PK variability based on patient factors
        expansion_modifier = 1.0
        if age > 65: expansion_modifier *= 0.7
        if prior_therapies > 4: expansion_modifier *= 0.6
        if lymphodepletion == "none": expansion_modifier *= 0.4
        elif lymphodepletion == "bendamustine": expansion_modifier *= 0.8
        if tumor_burden == "high": expansion_modifier *= 1.3
        elif tumor_burden == "low": expansion_modifier *= 0.7

        peak_expansion = dose_cells * random.lognormvariate(math.log(50 * expansion_modifier), 0.5)
        peak_day = max(5, int(random.gauss(10, 3)))
        persistence_day90 = peak_expansion * random.lognormvariate(math.log(0.01), 0.8)

        # Response
        response_prob = min(0.95, peak_expansion / (peak_expansion + 1e10))
        responded = random.random() < response_prob
        cr = responded and random.random() < 0.6

        # CRS grade
        crs = 1
        if peak_expansion > 5e11: crs = 4
        elif peak_expansion > 1e11: crs = 3
        elif peak_expansion > 5e10: crs = 2
        crs = min(4, max(1, crs + random.randint(-1, 1)))

        patients.append({
            "patient_id": i + 1,
            "age": age,
            "tumor_burden": tumor_burden,
            "prior_therapies": prior_therapies,
            "lymphodepletion": lymphodepletion,
            "peak_expansion_fold": round(peak_expansion / dose_cells, 1),
            "peak_day": peak_day,
            "day90_persistence": f"{persistence_day90:.1e}",
            "response": "CR" if cr else "PR" if responded else "NR",
            "crs_grade": crs,
        })

    # Summary statistics
    expansions = [p["peak_expansion_fold"] for p in patients]
    crs_grades = [p["crs_grade"] for p in patients]
    responses = [p["response"] for p in patients]

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "n_patients": n_patients,
        "dose": f"{dose_cells:.0e}",
        "summary": {
            "median_peak_expansion": round(sorted(expansions)[len(expansions) // 2], 1),
            "mean_peak_expansion": round(sum(expansions) / len(expansions), 1),
            "ORR_pct": round(sum(1 for r in responses if r != "NR") / len(responses) * 100, 1),
            "CR_pct": round(sum(1 for r in responses if r == "CR") / len(responses) * 100, 1),
            "CRS_3plus_pct": round(sum(1 for g in crs_grades if g >= 3) / len(crs_grades) * 100, 1),
            "median_peak_day": sorted([p["peak_day"] for p in patients])[len(patients) // 2],
        },
        "patients": patients[:20],  # Return first 20 for display
        "covariates_impact": {
            "age_over_65": "↓ 30% expansion",
            "prior_therapies_over_4": "↓ 40% expansion",
            "high_tumor_burden": "↑ 30% expansion, ↑ CRS risk",
            "no_lymphodepletion": "↓ 60% expansion",
        },
    }
