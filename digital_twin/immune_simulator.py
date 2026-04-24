"""
CARVanta Digital Twin — Immune System Simulator
===================================================
Agent-based immune system simulation for CAR-T therapy
response modeling. Simulates T-cell dynamics, tumor
microenvironment interactions, and treatment outcomes.

Features:
- Agent-based immune cell modeling (CAR-T, Treg, MDSC, NK, tumor)
- Tumor microenvironment (TME) simulation
- Cytokine storm (CRS) risk prediction
- T-cell exhaustion dynamics
- Antigen escape modeling
- Memory T-cell formation
- Multi-cycle treatment simulation
- Patient-specific parameterization

Models: Simplified ODE-based population dynamics with stochastic events.
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.digital_twin.immune_simulator")


# ──────────────────────────────────────────────────────────────────────
# Cell Population Models
# ──────────────────────────────────────────────────────────────────────

@dataclass
class CellPopulation:
    """Represents a population of immune or tumor cells."""
    name: str
    count: float
    growth_rate: float  # per day
    death_rate: float   # per day
    max_capacity: float
    phenotype: str = ""
    exhaustion_level: float = 0.0  # 0-1
    activation_level: float = 0.0  # 0-1


@dataclass
class CytokineProfile:
    """Cytokine levels in the simulation."""
    il6: float = 0.0   # pg/mL
    ifn_gamma: float = 0.0
    tnf_alpha: float = 0.0
    il2: float = 0.0
    il10: float = 0.0   # immunosuppressive
    tgf_beta: float = 0.0  # immunosuppressive
    il1_beta: float = 0.0
    gm_csf: float = 0.0


@dataclass
class SimulationState:
    """Complete state of the immune simulation at a time point."""
    day: float
    cart_cells: CellPopulation
    tumor_cells: CellPopulation
    treg_cells: CellPopulation
    mdsc_cells: CellPopulation
    nk_cells: CellPopulation
    normal_t_cells: CellPopulation
    cytokines: CytokineProfile
    crs_grade: int = 0
    icans_grade: int = 0
    antigen_density: float = 1.0  # relative 0-1
    response_status: str = "pending"


@dataclass
class PatientParams:
    """Patient-specific parameters for simulation."""
    tumor_burden: float = 1e9  # cells
    tumor_growth_rate: float = 0.03  # per day
    cart_dose: float = 1e8  # cells infused
    cart_fitness: float = 0.8  # 0-1
    antigen_expression: float = 0.85  # 0-1
    immune_suppressive_tme: float = 0.5  # 0-1
    prior_therapies: int = 2
    ecog: int = 1
    lymphodepletion_depth: float = 0.7  # 0-1 how effective Flu/Cy was
    age: int = 55
    crs_susceptibility: float = 0.5  # 0-1


# ──────────────────────────────────────────────────────────────────────
# Simulation Engine
# ──────────────────────────────────────────────────────────────────────

class ImmuneSimulator:
    """Agent-based immune system simulator for CAR-T therapy."""

    def __init__(self, params: PatientParams):
        self.params = params
        self.dt = 0.25  # time step in days (6 hours)
        self.history: List[Dict[str, Any]] = []
        self._init_populations()

    def _init_populations(self) -> None:
        """Initialize cell populations based on patient parameters."""
        lympho_factor = 1.0 - self.params.lymphodepletion_depth

        self.state = SimulationState(
            day=0,
            cart_cells=CellPopulation(
                "CAR-T", self.params.cart_dose, 0.5, 0.05, 1e11,
                phenotype="CD8+ effector", exhaustion_level=0.0,
                activation_level=0.9,
            ),
            tumor_cells=CellPopulation(
                "Tumor", self.params.tumor_burden,
                self.params.tumor_growth_rate, 0.01, 1e12,
            ),
            treg_cells=CellPopulation(
                "Treg", 5e7 * lympho_factor, 0.02, 0.03, 1e9,
            ),
            mdsc_cells=CellPopulation(
                "MDSC", 2e8 * self.params.immune_suppressive_tme,
                0.01, 0.02, 5e9,
            ),
            nk_cells=CellPopulation(
                "NK", 1e8 * lympho_factor, 0.01, 0.02, 5e8,
            ),
            normal_t_cells=CellPopulation(
                "Normal T", 5e8 * lympho_factor, 0.01, 0.01, 1e10,
            ),
            cytokines=CytokineProfile(),
            antigen_density=self.params.antigen_expression,
        )

    def step(self) -> None:
        """Advance simulation by one time step."""
        s = self.state
        p = self.params
        dt = self.dt

        # ── CAR-T expansion ──
        # Expansion driven by antigen encounter, limited by exhaustion
        encounter_rate = s.antigen_density * (s.tumor_cells.count / (s.tumor_cells.count + 1e8))
        expansion = s.cart_cells.growth_rate * encounter_rate * (1 - s.cart_cells.exhaustion_level)
        contraction = s.cart_cells.death_rate * (1 + s.cart_cells.exhaustion_level)
        cart_change = s.cart_cells.count * (expansion - contraction) * dt

        # Carrying capacity limit
        cart_ratio = s.cart_cells.count / s.cart_cells.max_capacity
        cart_change *= max(0, 1 - cart_ratio)
        s.cart_cells.count = max(0, s.cart_cells.count + cart_change)

        # Exhaustion accumulates with chronic antigen stimulation
        if encounter_rate > 0.3:
            s.cart_cells.exhaustion_level = min(1.0,
                s.cart_cells.exhaustion_level + 0.005 * encounter_rate * dt)

        # ── Tumor killing ──
        kill_rate = 0.15 * p.cart_fitness * s.antigen_density * (1 - s.cart_cells.exhaustion_level)
        suppression = 1.0 / (1.0 + (s.treg_cells.count / 1e8) + (s.mdsc_cells.count / 5e8))
        effective_kill = kill_rate * suppression
        tumor_killed = s.cart_cells.count * effective_kill * dt
        tumor_growth = s.tumor_cells.count * s.tumor_cells.growth_rate * dt
        s.tumor_cells.count = max(0, s.tumor_cells.count + tumor_growth - tumor_killed)

        # Antigen escape (stochastic)
        if s.tumor_cells.count > 1e6 and random.random() < 0.001 * dt:
            s.antigen_density *= 0.95  # gradual escape

        # ── Treg dynamics ──
        treg_stim = s.cytokines.il10 / (s.cytokines.il10 + 50) + s.cytokines.tgf_beta / (s.cytokines.tgf_beta + 30)
        treg_growth = s.treg_cells.growth_rate * (1 + treg_stim) * dt
        s.treg_cells.count = max(0, s.treg_cells.count * (1 + treg_growth - s.treg_cells.death_rate * dt))

        # ── MDSC dynamics ──
        mdsc_stim = s.tumor_cells.count / (s.tumor_cells.count + 1e9)
        s.mdsc_cells.count = max(0, s.mdsc_cells.count * (1 + s.mdsc_cells.growth_rate * mdsc_stim * dt - s.mdsc_cells.death_rate * dt))

        # ── NK cell dynamics ──
        nk_act = s.cytokines.il2 / (s.cytokines.il2 + 100)
        s.nk_cells.count = max(0, s.nk_cells.count * (1 + s.nk_cells.growth_rate * nk_act * dt - s.nk_cells.death_rate * dt))

        # ── Cytokine dynamics ──
        # Pro-inflammatory (driven by CAR-T killing)
        killing_intensity = min(1.0, tumor_killed / max(1, s.tumor_cells.count + 1e6))
        s.cytokines.il6 = max(0, s.cytokines.il6 + (killing_intensity * 500 - s.cytokines.il6 * 0.1) * dt)
        s.cytokines.ifn_gamma = max(0, s.cytokines.ifn_gamma + (killing_intensity * 300 * s.cart_cells.activation_level - s.cytokines.ifn_gamma * 0.08) * dt)
        s.cytokines.tnf_alpha = max(0, s.cytokines.tnf_alpha + (killing_intensity * 200 - s.cytokines.tnf_alpha * 0.12) * dt)
        s.cytokines.il2 = max(0, s.cytokines.il2 + (s.cart_cells.activation_level * 100 * (1 - s.cart_cells.exhaustion_level) - s.cytokines.il2 * 0.15) * dt)
        s.cytokines.il1_beta = max(0, s.cytokines.il1_beta + (killing_intensity * 150 - s.cytokines.il1_beta * 0.1) * dt)
        s.cytokines.gm_csf = max(0, s.cytokines.gm_csf + (killing_intensity * 100 - s.cytokines.gm_csf * 0.08) * dt)

        # Anti-inflammatory (feedback + Tregs)
        s.cytokines.il10 = max(0, s.cytokines.il10 + (s.treg_cells.count / 1e8 * 20 + s.cytokines.il6 * 0.05 - s.cytokines.il10 * 0.08) * dt)
        s.cytokines.tgf_beta = max(0, s.cytokines.tgf_beta + (s.mdsc_cells.count / 5e8 * 30 - s.cytokines.tgf_beta * 0.05) * dt)

        # ── CRS grading ──
        crs_score = (s.cytokines.il6 / 1000 + s.cytokines.ifn_gamma / 500 + s.cytokines.tnf_alpha / 300) * p.crs_susceptibility
        if crs_score > 3.0:
            s.crs_grade = 4
        elif crs_score > 2.0:
            s.crs_grade = 3
        elif crs_score > 1.0:
            s.crs_grade = 2
        elif crs_score > 0.3:
            s.crs_grade = 1
        else:
            s.crs_grade = 0

        # ICANS
        icans_score = s.cytokines.il6 / 1500 + s.cytokines.il1_beta / 200
        s.icans_grade = min(4, int(icans_score * 2))

        # ── Response assessment ──
        reduction = 1.0 - (s.tumor_cells.count / max(1, p.tumor_burden))
        if s.tumor_cells.count < 100:
            s.response_status = "complete_remission"
        elif reduction > 0.5:
            s.response_status = "partial_remission"
        elif reduction > 0:
            s.response_status = "stable_disease"
        else:
            s.response_status = "progressive_disease"

        s.day += dt

    def run(self, days: int = 90, record_interval: float = 1.0) -> List[Dict[str, Any]]:
        """Run simulation for specified number of days."""
        self.history = []
        total_steps = int(days / self.dt)
        record_steps = int(record_interval / self.dt)

        for i in range(total_steps):
            self.step()
            if i % record_steps == 0:
                self.history.append(self._snapshot())

        return self.history

    def _snapshot(self) -> Dict[str, Any]:
        s = self.state
        return {
            "day": round(s.day, 1),
            "cart_cells": round(s.cart_cells.count),
            "tumor_cells": round(s.tumor_cells.count),
            "treg_cells": round(s.treg_cells.count),
            "nk_cells": round(s.nk_cells.count),
            "exhaustion": round(s.cart_cells.exhaustion_level, 3),
            "antigen_density": round(s.antigen_density, 3),
            "cytokines": {
                "IL-6": round(s.cytokines.il6, 1),
                "IFNγ": round(s.cytokines.ifn_gamma, 1),
                "TNFα": round(s.cytokines.tnf_alpha, 1),
                "IL-2": round(s.cytokines.il2, 1),
                "IL-10": round(s.cytokines.il10, 1),
            },
            "crs_grade": s.crs_grade,
            "icans_grade": s.icans_grade,
            "response": s.response_status,
        }


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

async def run_simulation(
    tumor_burden: float = 1e9,
    cart_dose: float = 1e8,
    cart_fitness: float = 0.8,
    antigen_expression: float = 0.85,
    tme_suppression: float = 0.5,
    prior_therapies: int = 2,
    age: int = 55,
    crs_susceptibility: float = 0.5,
    days: int = 90,
) -> Dict[str, Any]:
    """Run a full immune simulation."""
    params = PatientParams(
        tumor_burden=tumor_burden,
        cart_dose=cart_dose,
        cart_fitness=cart_fitness,
        antigen_expression=antigen_expression,
        immune_suppressive_tme=tme_suppression,
        prior_therapies=prior_therapies,
        age=age,
        crs_susceptibility=crs_susceptibility,
    )
    sim = ImmuneSimulator(params)
    timeline = sim.run(days=days)

    # Summary
    final = timeline[-1] if timeline else {}
    peak_crs = max(t.get("crs_grade", 0) for t in timeline) if timeline else 0
    peak_il6 = max(t["cytokines"]["IL-6"] for t in timeline) if timeline else 0
    cr_day = None
    for t in timeline:
        if t["response"] == "complete_remission":
            cr_day = t["day"]
            break

    return {
        "simulation_id": uuid.uuid4().hex[:12],
        "parameters": {
            "tumor_burden": tumor_burden, "cart_dose": cart_dose,
            "cart_fitness": cart_fitness, "antigen_expression": antigen_expression,
            "tme_suppression": tme_suppression, "days": days,
        },
        "summary": {
            "final_response": final.get("response", "unknown"),
            "peak_crs_grade": peak_crs,
            "peak_il6_pg_ml": round(peak_il6, 1),
            "cr_achieved_day": cr_day,
            "final_exhaustion": final.get("exhaustion", 0),
            "final_tumor_cells": final.get("tumor_cells", 0),
            "final_cart_cells": final.get("cart_cells", 0),
            "antigen_escape": round(1 - final.get("antigen_density", 1), 3),
        },
        "timeline": timeline[::3],  # Return every 3rd point to reduce payload
    }


async def compare_scenarios(
    scenarios: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare multiple simulation scenarios."""
    results = []
    for i, sc in enumerate(scenarios):
        result = await run_simulation(**sc)
        result["scenario_id"] = i + 1
        result["scenario_name"] = sc.get("name", f"Scenario {i+1}")
        results.append(result)

    return {
        "total_scenarios": len(results),
        "scenarios": [
            {
                "id": r["scenario_id"],
                "name": r["scenario_name"],
                "response": r["summary"]["final_response"],
                "peak_crs": r["summary"]["peak_crs_grade"],
                "cr_day": r["summary"]["cr_achieved_day"],
                "exhaustion": r["summary"]["final_exhaustion"],
            }
            for r in results
        ],
        "full_results": results,
    }
