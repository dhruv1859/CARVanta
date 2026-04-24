"""
CARVanta Digital Twin — Manufacturing Process Simulator
=========================================================
End-to-end CAR-T manufacturing process simulation with
quality attribute tracking, deviation risk, and batch
optimization modeling.

Features:
- Leukapheresis to product release workflow
- In-process control monitoring
- Transduction efficiency modeling
- T-cell expansion kinetics
- Quality attribute tracking (viability, CAR+%, VCN, sterility)
- Process deviation simulation
- Batch success probability
- GMP time/cost estimation
- Scale-up/out modeling
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.digital_twin.manufacturing_sim")


@dataclass
class ProcessStep:
    name: str
    duration_hours: float
    success_rate: float
    critical_params: Dict[str, Any] = field(default_factory=dict)
    quality_impact: Dict[str, float] = field(default_factory=dict)  # attribute -> multiplier
    cost_usd: float = 0
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class BatchResult:
    step: str
    day: float
    cell_count: float
    viability: float
    car_positive_pct: float
    vcn: float  # vector copy number
    sterility_pass: bool
    mycoplasma_pass: bool
    endotoxin_eu_ml: float
    notes: List[str] = field(default_factory=list)


# Manufacturing process steps
_MFG_STEPS: List[ProcessStep] = [
    ProcessStep("Leukapheresis", 4, 0.98,
        {"target_volume_mL": 200, "target_cd3_pct": 50, "target_viability": 95},
        {"viability": 1.0, "cell_count": 1.0}, 5800,
        ["Poor venous access", "Low T-cell count", "DMSO toxicity"]),
    ProcessStep("T-cell Selection", 6, 0.95,
        {"selection_method": "CD4/CD8 positive", "purity_target": 90},
        {"viability": 0.95, "cell_count": 0.6}, 8000,
        ["Low CD3+ purity", "Excess monocytes"]),
    ProcessStep("Activation", 48, 0.97,
        {"method": "CD3/CD28 beads", "il2_IU_mL": 100, "il7_ng_mL": 5},
        {"viability": 0.98, "cell_count": 1.2}, 3500,
        ["Suboptimal activation", "Bead:cell ratio"]),
    ProcessStep("Viral Transduction", 24, 0.92,
        {"vector": "Lentivirus", "moi": 5, "transduction_enhancer": "RetroNectin"},
        {"viability": 0.90, "cell_count": 0.95, "car_positive": 0.45}, 45000,
        ["Low titer vector", "Transduction failure", "High VCN"]),
    ProcessStep("Expansion (Day 1-5)", 120, 0.96,
        {"culture_system": "G-Rex", "media": "X-VIVO 15", "feeding_schedule": "Day 3,5"},
        {"viability": 0.97, "cell_count": 4.0}, 15000,
        ["Slow expansion", "Contamination"]),
    ProcessStep("Expansion (Day 5-9)", 96, 0.95,
        {"il2_IU_mL": 300, "target_density": "1e6/mL", "split_ratio": "1:2"},
        {"viability": 0.96, "cell_count": 3.5}, 12000,
        ["Over-expansion", "Exhaustion markers"]),
    ProcessStep("Harvest & Wash", 4, 0.97,
        {"wash_buffer": "PlasmaLyte", "centrifuge_g": 300, "washes": 3},
        {"viability": 0.92, "cell_count": 0.85}, 4000,
        ["Cell loss during wash", "Residual beads"]),
    ProcessStep("Formulation", 2, 0.99,
        {"cryoprotectant": "CryoStor CS10", "concentration": "1-2e7/mL"},
        {"viability": 0.98, "cell_count": 0.98}, 6000,
        ["DMSO sensitivity"]),
    ProcessStep("Cryopreservation", 4, 0.96,
        {"method": "Controlled-rate freezer", "rate": "-1°C/min", "storage": "-150°C"},
        {"viability": 0.85, "cell_count": 0.95}, 8000,
        ["Freeze/thaw damage", "Storage breach"]),
    ProcessStep("QC Testing", 72, 0.90,
        {"tests": ["Sterility", "Mycoplasma", "Endotoxin", "CAR expression",
                    "VCN", "Cell count", "Viability", "Identity", "Potency"]},
        {"viability": 1.0, "cell_count": 1.0}, 25000,
        ["QC failure", "OOS results", "Sterility positive"]),
]


# ──────────────────────────────────────────────────────────────────────
# Simulation Functions
# ──────────────────────────────────────────────────────────────────────

async def simulate_manufacturing(
    starting_cells: float = 1e9,
    starting_viability: float = 0.95,
    product_target: str = "CD19",
    target_dose: float = 1e8,
    operator_skill: float = 0.85,  # 0-1
) -> Dict[str, Any]:
    """Simulate end-to-end CAR-T manufacturing."""
    sim_id = uuid.uuid4().hex[:12]
    cell_count = starting_cells
    viability = starting_viability
    car_pct = 0.0
    vcn = 0.0
    elapsed_hours = 0.0
    total_cost = 0.0
    steps_log: List[Dict[str, Any]] = []
    deviations: List[Dict[str, str]] = []
    batch_passed = True

    for step in _MFG_STEPS:
        # Determine if step succeeds
        adjusted_success = step.success_rate * (0.9 + 0.1 * operator_skill)
        success = random.random() < adjusted_success

        if not success:
            # Minor deviation
            dev_risk = random.choice(step.risk_factors) if step.risk_factors else "Process deviation"
            deviations.append({"step": step.name, "issue": dev_risk, "severity": "minor"})

        # Apply quality impact
        viability *= step.quality_impact.get("viability", 1.0)
        cell_count *= step.quality_impact.get("cell_count", 1.0)

        # Add some noise
        viability *= random.gauss(1.0, 0.02)
        cell_count *= random.gauss(1.0, 0.05)
        viability = min(1.0, max(0.3, viability))
        cell_count = max(0, cell_count)

        # Transduction
        if "car_positive" in step.quality_impact:
            car_pct = step.quality_impact["car_positive"] * random.gauss(1.0, 0.1)
            car_pct = min(0.95, max(0.1, car_pct))
            vcn = random.gauss(2.5, 0.8)
            vcn = min(5.0, max(0.5, vcn))

        elapsed_hours += step.duration_hours
        total_cost += step.cost_usd

        steps_log.append({
            "step": step.name,
            "day": round(elapsed_hours / 24, 1),
            "duration_hours": step.duration_hours,
            "cell_count": round(cell_count),
            "viability_pct": round(viability * 100, 1),
            "car_positive_pct": round(car_pct * 100, 1) if car_pct > 0 else None,
            "vcn": round(vcn, 2) if vcn > 0 else None,
            "success": success,
            "cost": step.cost_usd,
        })

    # Final QC
    sterility = random.random() > 0.02
    mycoplasma = random.random() > 0.01
    endotoxin = random.gauss(0.5, 0.3)
    endotoxin = max(0, min(5.0, endotoxin))

    meets_release = (
        viability > 0.70 and
        car_pct > 0.20 and
        cell_count >= target_dose and
        vcn < 5.0 and
        sterility and mycoplasma and
        endotoxin < 3.5
    )

    return {
        "simulation_id": sim_id,
        "product_target": product_target,
        "parameters": {
            "starting_cells": starting_cells,
            "target_dose": target_dose,
            "operator_skill": operator_skill,
        },
        "result": {
            "batch_released": meets_release,
            "total_days": round(elapsed_hours / 24, 1),
            "total_cost_usd": round(total_cost, 2),
            "final_cell_count": round(cell_count),
            "final_viability_pct": round(viability * 100, 1),
            "car_positive_pct": round(car_pct * 100, 1),
            "vcn": round(vcn, 2),
            "sterility": "Pass" if sterility else "Fail",
            "mycoplasma": "Pass" if mycoplasma else "Fail",
            "endotoxin_eu_ml": round(endotoxin, 2),
            "meets_target_dose": cell_count >= target_dose,
        },
        "deviations": deviations,
        "process_log": steps_log,
        "release_criteria": {
            "viability_min": 70, "car_positive_min": 20,
            "vcn_max": 5.0, "endotoxin_max": 3.5,
            "dose_target": target_dose,
        },
    }


async def batch_statistics(n_batches: int = 100) -> Dict[str, Any]:
    """Simulate multiple batches and calculate statistics."""
    results = []
    for _ in range(n_batches):
        r = await simulate_manufacturing()
        results.append(r)

    released = sum(1 for r in results if r["result"]["batch_released"])
    costs = [r["result"]["total_cost_usd"] for r in results]
    viabilities = [r["result"]["final_viability_pct"] for r in results]
    car_pcts = [r["result"]["car_positive_pct"] for r in results]

    return {
        "batches_simulated": n_batches,
        "batches_released": released,
        "success_rate_pct": round(released / n_batches * 100, 1),
        "cost_statistics": {
            "mean": round(sum(costs) / len(costs), 2),
            "min": round(min(costs), 2),
            "max": round(max(costs), 2),
        },
        "viability_statistics": {
            "mean": round(sum(viabilities) / len(viabilities), 1),
            "min": round(min(viabilities), 1),
            "max": round(max(viabilities), 1),
        },
        "car_positive_statistics": {
            "mean": round(sum(car_pcts) / len(car_pcts), 1),
            "min": round(min(car_pcts), 1),
            "max": round(max(car_pcts), 1),
        },
        "common_deviations": _count_deviations(results),
    }


def _count_deviations(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Dict[str, int] = {}
    for r in results:
        for d in r["deviations"]:
            key = d["issue"]
            counts[key] = counts.get(key, 0) + 1
    sorted_devs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"issue": k, "occurrences": v} for k, v in sorted_devs[:10]]
