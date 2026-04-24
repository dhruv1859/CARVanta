"""
CARVanta Health Economics — QALY & Outcomes Modeling
======================================================
Quality-Adjusted Life Year modeling for CAR-T therapies.
Markov state-transition model for long-term health outcomes.

Features:
- Markov model with 6 health states
- Cycle-by-cycle QALY accrual with state-specific utilities
- Survival extrapolation (exponential, Weibull)
- Cost accrual per health state
- Scenario comparison (CAR-T vs SOC)
- Utility decrement for adverse events
"""

import logging
import math
import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.health_econ.qaly_model")


@dataclass
class HealthState:
    name: str
    utility: float  # 0-1 quality weight
    monthly_cost: float  # maintenance cost per month
    description: str = ""


# Health states for CAR-T Markov model
_STATES: Dict[str, HealthState] = {
    "complete_remission": HealthState("Complete Remission", 0.85, 800, "CR with ongoing monitoring"),
    "partial_remission":  HealthState("Partial Remission",  0.72, 2500, "PR with active monitoring"),
    "stable_disease":     HealthState("Stable Disease",     0.60, 3500, "SD with supportive care"),
    "progressive":        HealthState("Progressive Disease", 0.45, 8000, "PD, subsequent therapy"),
    "treatment_toxicity": HealthState("AE Management",       0.35, 15000, "Active CRS/ICANS management"),
    "death":              HealthState("Death",               0.0,  0, "Absorbing state"),
}

# Transition matrices per cycle (monthly) - CAR-T
_CART_TRANSITIONS: Dict[str, Dict[str, float]] = {
    "complete_remission": {"complete_remission": 0.92, "partial_remission": 0.03, "progressive": 0.02, "death": 0.01, "stable_disease": 0.02},
    "partial_remission":  {"partial_remission": 0.80, "complete_remission": 0.05, "progressive": 0.08, "stable_disease": 0.05, "death": 0.02},
    "stable_disease":     {"stable_disease": 0.75, "progressive": 0.12, "partial_remission": 0.03, "death": 0.05, "complete_remission": 0.05},
    "progressive":        {"progressive": 0.60, "death": 0.15, "stable_disease": 0.10, "partial_remission": 0.10, "complete_remission": 0.05},
    "treatment_toxicity": {"complete_remission": 0.50, "partial_remission": 0.20, "treatment_toxicity": 0.15, "progressive": 0.10, "death": 0.05},
}

# SOC transitions (more pessimistic)
_SOC_TRANSITIONS: Dict[str, Dict[str, float]] = {
    "complete_remission": {"complete_remission": 0.82, "partial_remission": 0.05, "progressive": 0.06, "death": 0.03, "stable_disease": 0.04},
    "partial_remission":  {"partial_remission": 0.70, "progressive": 0.12, "stable_disease": 0.08, "death": 0.05, "complete_remission": 0.05},
    "stable_disease":     {"stable_disease": 0.65, "progressive": 0.18, "death": 0.08, "partial_remission": 0.05, "complete_remission": 0.04},
    "progressive":        {"progressive": 0.50, "death": 0.25, "stable_disease": 0.15, "partial_remission": 0.05, "complete_remission": 0.05},
    "treatment_toxicity": {"complete_remission": 0.30, "partial_remission": 0.15, "treatment_toxicity": 0.20, "progressive": 0.20, "death": 0.15},
}


async def run_markov_model(
    treatment: str = "cart",  # "cart" or "soc"
    initial_state: str = "treatment_toxicity",  # post-infusion
    time_horizon_months: int = 60,
    discount_rate_annual: float = 0.03,
    orr: float = 0.82,
) -> Dict[str, Any]:
    """Run Markov state-transition model."""
    transitions = _CART_TRANSITIONS if treatment == "cart" else _SOC_TRANSITIONS
    monthly_discount = (1 + discount_rate_annual) ** (1/12) - 1

    # State distribution starts based on initial response
    if initial_state == "treatment_toxicity":
        distribution = {
            "complete_remission": orr * 0.6,
            "partial_remission": orr * 0.4,
            "stable_disease": (1 - orr) * 0.5,
            "progressive": (1 - orr) * 0.3,
            "treatment_toxicity": 0.0,
            "death": (1 - orr) * 0.2,
        }
    else:
        distribution = {s: (1.0 if s == initial_state else 0.0) for s in _STATES}

    cycles = []
    total_qalys = 0.0
    total_cost = 0.0
    total_lys = 0.0

    for month in range(time_horizon_months):
        discount = 1 / ((1 + monthly_discount) ** month)

        cycle_qaly = 0.0
        cycle_cost = 0.0
        cycle_alive = 0.0

        for state_name, prob in distribution.items():
            state = _STATES[state_name]
            cycle_qaly += prob * state.utility / 12  # monthly → annual QALY
            cycle_cost += prob * state.monthly_cost
            if state_name != "death":
                cycle_alive += prob

        total_qalys += cycle_qaly * discount
        total_cost += cycle_cost * discount
        total_lys += cycle_alive / 12 * discount

        cycles.append({
            "month": month + 1,
            "qaly_accrued": round(cycle_qaly * discount, 4),
            "cost_accrued": round(cycle_cost * discount, 2),
            "alive_pct": round(cycle_alive * 100, 1),
            "cr_pct": round(distribution.get("complete_remission", 0) * 100, 1),
            "death_pct": round(distribution.get("death", 0) * 100, 1),
        })

        # Transition
        new_dist: Dict[str, float] = {s: 0.0 for s in _STATES}
        for from_state, from_prob in distribution.items():
            if from_state == "death":
                new_dist["death"] += from_prob
                continue
            trans = transitions.get(from_state, {})
            for to_state, t_prob in trans.items():
                new_dist[to_state] = new_dist.get(to_state, 0.0) + from_prob * t_prob
        distribution = new_dist

    return {
        "treatment": treatment,
        "time_horizon_months": time_horizon_months,
        "total_qalys": round(total_qalys, 3),
        "total_cost": round(total_cost, 2),
        "total_life_years": round(total_lys, 3),
        "final_alive_pct": round((1 - distribution.get("death", 0)) * 100, 1),
        "final_cr_pct": round(distribution.get("complete_remission", 0) * 100, 1),
        "cost_per_qaly": round(total_cost / max(total_qalys, 0.01), 2),
        "cycles_summary": cycles[::6],  # Every 6 months
        "discount_rate": discount_rate_annual,
    }


async def compare_treatments(
    time_horizon_months: int = 60,
    cart_orr: float = 0.82,
    soc_orr: float = 0.28,
    cart_upfront_cost: float = 550000,
    soc_upfront_cost: float = 65000,
) -> Dict[str, Any]:
    """Compare CAR-T vs. SOC Markov model outcomes."""
    cart = await run_markov_model("cart", time_horizon_months=time_horizon_months, orr=cart_orr)
    soc = await run_markov_model("soc", time_horizon_months=time_horizon_months, orr=soc_orr)

    cart_total_cost = cart_upfront_cost + cart["total_cost"]
    soc_total_cost = soc_upfront_cost + soc["total_cost"]

    inc_cost = cart_total_cost - soc_total_cost
    inc_qaly = cart["total_qalys"] - soc["total_qalys"]
    icer = inc_cost / inc_qaly if inc_qaly > 0 else float("inf")

    return {
        "cart": {**cart, "upfront_cost": cart_upfront_cost, "total_cost_with_upfront": round(cart_total_cost, 2)},
        "soc": {**soc, "upfront_cost": soc_upfront_cost, "total_cost_with_upfront": round(soc_total_cost, 2)},
        "incremental_cost": round(inc_cost, 2),
        "incremental_qalys": round(inc_qaly, 3),
        "icer": round(icer, 2),
        "icer_formatted": f"${icer:,.0f}/QALY",
        "net_monetary_benefit_100k": round(inc_qaly * 100000 - inc_cost, 2),
        "net_monetary_benefit_150k": round(inc_qaly * 150000 - inc_cost, 2),
    }


async def utility_analysis() -> Dict[str, Any]:
    """Return health state utility values and sources."""
    return {
        "health_states": [
            {"state": s.name, "utility": s.utility, "monthly_cost": s.monthly_cost, "description": s.description}
            for s in _STATES.values()
        ],
        "utility_decrements": {
            "crs_grade_1_2": -0.15, "crs_grade_3_4": -0.35,
            "icans_any": -0.20, "cytopenia_prolonged": -0.10,
            "infection_requiring_iv": -0.25,
        },
        "source": "Derived from published utilities in Zhang et al. 2021, Lin et al. 2019",
    }
