"""
CARVanta Drug Discovery — Safety Switch Designer
====================================================
Design and evaluation of safety switches for CAR-T
constructs. Critical for managing severe adverse events
and enabling dose-titration of engineered T-cells.

Features:
- Inducible Caspase-9 (iCasp9) kill switch modeling
- CD20 rituximab-based depletion switch
- Truncated EGFR (EGFRt) cetuximab-based depletion
- SWIFF-CAR (proteolysis-based ON/OFF switch)
- Tetracycline-inducible expression system
- synNotch / logic-gated CAR design
- Dasatinib pause switch (reversible inhibition)
- Split CAR / heterodimer-dependent activation
"""

import logging
import random
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.drug_discovery.safety_switch")


@dataclass
class SafetySwitch:
    """Represents a safety switch mechanism for CAR-T cells."""
    name: str
    mechanism: str
    type: str  # suicide, depletion, reversible_pause, logic_gate
    trigger: str
    response_time_hours: float
    kill_efficiency_pct: float
    reversible: bool
    clinical_stage: str
    advantages: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


_SAFETY_SWITCHES: Dict[str, SafetySwitch] = {
    "iCasp9": SafetySwitch(
        "Inducible Caspase-9 (iCasp9)", "Dimerization of caspase-9 triggers apoptosis",
        "suicide", "AP1903 (rimiducid)", 0.5, 98.5, False, "Phase III (approved in allo-HSCT)",
        ["Rapid onset (<30 min)", "High efficiency (>95%)", "Clinical validation",
         "Does not require external antibody", "Selective for transduced cells"],
        ["Irreversible — kills all CAR-T permanently", "Requires CID drug availability",
         "Cost of AP1903/rimiducid", "No dose titration — all-or-nothing"],
    ),
    "RQR8": SafetySwitch(
        "RQR8 (CD34/CD20 epitope)", "Rituximab-mediated ADCC/CDC depletion",
        "depletion", "Rituximab", 4.0, 92.0, False, "Phase I/II",
        ["Uses FDA-approved drug (rituximab)", "Well-characterized mechanism",
         "Dual epitope (CD34 for selection, CD20 for depletion)"],
        ["Slower onset (hours vs minutes)", "Incomplete depletion in tissue-resident cells",
         "May deplete normal B-cells (if CD20+ compartment exists)",
         "Requires iv rituximab administration"],
    ),
    "EGFRt": SafetySwitch(
        "Truncated EGFR (EGFRt)", "Cetuximab-mediated ADCC depletion",
        "depletion", "Cetuximab", 6.0, 88.0, False, "Phase I/II",
        ["Uses FDA-approved drug (cetuximab)", "Also serves as tracking/selection marker",
         "No signaling (truncated — no intracellular domain)"],
        ["Slower onset", "Incomplete depletion in tissue-resident cells",
         "Cetuximab infusion reactions possible"],
    ),
    "HSV_TK": SafetySwitch(
        "HSV-TK (Herpes Simplex Virus Thymidine Kinase)", "Ganciclovir phosphorylation → DNA chain termination",
        "suicide", "Ganciclovir", 24.0, 95.0, False, "Phase II (historical)",
        ["Long clinical history", "Specific to transduced cells",
         "Ganciclovir is widely available"],
        ["Slow onset (requires cell division for effect)", "Immunogenic (viral protein)",
         "Can interfere with ganciclovir for CMV treatment",
         "Less suitable for modern CAR-T (replaced by iCasp9)"],
    ),
    "dasatinib": SafetySwitch(
        "Dasatinib Pause Switch", "Reversible Lck/Src kinase inhibition blocks TCR/CAR signaling",
        "reversible_pause", "Dasatinib (oral)", 1.0, 0.0, True, "Phase I (off-label concept)",
        ["Reversible — temporarily pauses CAR-T without killing",
         "Oral administration", "FDA-approved drug", "Dose-titratable",
         "Useful for managing CRS/ICANS without losing CAR-T cells"],
        ["Does not eliminate CAR-T cells (only pauses)", "Systemic immunosuppression",
         "Short half-life requires continuous dosing", "Not tested prospectively for this use"],
    ),
    "tet_ON": SafetySwitch(
        "Tet-ON Inducible CAR", "Doxycycline-dependent CAR expression via rtTA",
        "reversible_pause", "Doxycycline (oral)", 6.0, 0.0, True, "Preclinical",
        ["Reversible — CAR expression requires continuous doxycycline",
         "Dose-dependent titration of CAR expression", "Established platform",
         "Oral drug (convenient)"],
        ["Leaky expression in OFF state", "Immunogenic (bacterial components)",
         "Doxycycline interactions (photosensitivity, GI)", "Slow kinetics (gene expression)"],
    ),
    "synNotch": SafetySwitch(
        "synNotch Logic Gate", "AND-gate: synNotch receptor for priming + CAR for killing",
        "logic_gate", "Requires both antigens present", 12.0, 0.0, True, "Phase I",
        ["Incredible specificity — only kills cells expressing BOTH antigens",
         "Reduces on-target/off-tumor toxicity dramatically",
         "Programmable — can encode AND, OR, NOT logic"],
        ["Complex engineering (two receptors)", "Lower potency vs standard CAR",
         "Slow priming kinetics", "Limited clinical data"],
    ),
    "split_CAR": SafetySwitch(
        "Split CAR (Heterodimerizer-dependent)", "CAR signaling requires exogenous small molecule to dimerize split components",
        "reversible_pause", "Small molecule dimerizer (e.g., rapalog)", 2.0, 0.0, True, "Preclinical",
        ["Drug-dependent activation — CAR only functions when drug is present",
         "Reversible by drug withdrawal", "Dose-titratable",
         "Can be combined with other safety features"],
        ["Requires continuous drug supply", "Potential for incomplete signaling",
         "Engineering complexity", "Dimerizer drug not yet FDA-approved for this use"],
    ),
    "SWIFF_CAR": SafetySwitch(
        "SWIFF-CAR (degron-controlled)", "Proteasomal degradation of CAR unless stabilized by drug",
        "reversible_pause", "Shield-1 (stabilizer drug)", 4.0, 0.0, True, "Preclinical",
        ["Constitutive degradation when drug is absent — fail-safe design",
         "Drug-dependent stabilization for activation",
         "Fast OFF kinetics (protein degradation)"],
        ["Requires novel drug (not FDA-approved)", "Residual CAR expression in OFF state",
         "Complex protein engineering", "Early preclinical stage"],
    ),
}


async def design_safety_switch(
    car_construct: str = "anti-CD19 CAR",
    risk_profile: str = "moderate",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Design optimal safety switch strategy for a CAR construct."""
    if seed:
        random.seed(seed)

    # Score each switch based on risk profile
    scored_switches = []
    for code, switch in _SAFETY_SWITCHES.items():
        score = 0

        if risk_profile == "high":
            # High risk: prioritize fast-acting, high-kill switches
            if switch.type == "suicide":
                score += 0.4
            if switch.response_time_hours < 2:
                score += 0.3
            if switch.kill_efficiency_pct > 90:
                score += 0.2
            if switch.clinical_stage.startswith("Phase III") or "approved" in switch.clinical_stage.lower():
                score += 0.1
        elif risk_profile == "low":
            # Low risk: prefer reversible options for dose control
            if switch.reversible:
                score += 0.4
            if switch.type in ("reversible_pause", "logic_gate"):
                score += 0.3
            score += 0.2 * random.random()
        else:
            # Moderate: balanced approach
            score = 0.3 + 0.4 * random.random()
            if switch.clinical_stage.startswith("Phase"):
                score += 0.15

        scored_switches.append({
            "code": code,
            "name": switch.name,
            "type": switch.type,
            "mechanism": switch.mechanism,
            "trigger": switch.trigger,
            "response_time_hours": switch.response_time_hours,
            "kill_efficiency_pct": switch.kill_efficiency_pct,
            "reversible": switch.reversible,
            "clinical_stage": switch.clinical_stage,
            "score": round(score, 3),
            "advantages": switch.advantages,
            "limitations": switch.limitations,
        })

    scored_switches.sort(key=lambda x: x["score"], reverse=True)

    # Recommend combination strategy
    primary = scored_switches[0]
    backup = next((s for s in scored_switches[1:] if s["type"] != primary["type"]), scored_switches[1])

    combination_strategy = {
        "primary": primary["code"],
        "backup": backup["code"],
        "rationale": (
            f"Primary: {primary['name']} for {primary['type']} control. "
            f"Backup: {backup['name']} as {'reversible fallback' if backup['reversible'] else 'definitive elimination'}."
        ),
        "combined_safety_score": round((primary["score"] + backup["score"]) / 2 * 1.15, 3),
    }

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "car_construct": car_construct,
        "risk_profile": risk_profile,
        "total_switches_evaluated": len(scored_switches),
        "recommended_primary": primary,
        "recommended_backup": backup,
        "combination_strategy": combination_strategy,
        "all_switches_ranked": scored_switches,
    }


async def simulate_switch_activation(
    switch_type: str = "iCasp9",
    activation_time_hours: float = 0,
    simulation_hours: int = 72,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Simulate safety switch activation kinetics."""
    if seed:
        random.seed(seed)

    switch = _SAFETY_SWITCHES.get(switch_type)
    if not switch:
        return {"error": f"Unknown switch type: {switch_type}"}

    initial_car_t = 1_000_000  # 1M cells
    timepoints = []

    for t in range(simulation_hours + 1):
        if t < activation_time_hours:
            # Before switch activation: CAR-T expanding
            car_t_count = int(initial_car_t * (1 + 0.02 * t))
            car_t_active_pct = 95 + random.gauss(0, 2)
            cytokine_level = 50 + t * 5 + random.gauss(0, 10)
        else:
            # After activation
            hours_since_activation = t - activation_time_hours
            response_time = switch.response_time_hours

            if switch.type == "suicide":
                # Exponential decay
                decay_rate = -math.log(1 - switch.kill_efficiency_pct / 100) / max(response_time * 2, 0.1)
                surviving_fraction = math.exp(-decay_rate * hours_since_activation)
                car_t_count = int(initial_car_t * max(0.001, surviving_fraction))
                car_t_active_pct = max(0, surviving_fraction * 95)
                cytokine_level = max(0, (50 + activation_time_hours * 5) * surviving_fraction)

            elif switch.type == "depletion":
                # Slower elimination (antibody-mediated)
                if hours_since_activation < response_time:
                    surviving = 1 - (hours_since_activation / response_time) * 0.5
                else:
                    surviving = 0.5 * math.exp(-0.1 * (hours_since_activation - response_time))
                surviving = max(1 - switch.kill_efficiency_pct / 100, surviving)
                car_t_count = int(initial_car_t * surviving)
                car_t_active_pct = surviving * 90
                cytokine_level = max(0, (50 + activation_time_hours * 5) * surviving)

            elif switch.type == "reversible_pause":
                # CAR-T cells survive but become inactive
                car_t_count = int(initial_car_t * (1 + 0.02 * activation_time_hours))
                inhibition = min(0.95, hours_since_activation / max(response_time, 0.1) * 0.95)
                car_t_active_pct = max(5, 95 * (1 - inhibition))
                cytokine_level = max(5, (50 + activation_time_hours * 5) * (1 - inhibition * 0.8))

            else:
                car_t_count = int(initial_car_t)
                car_t_active_pct = 50
                cytokine_level = 30

        if t % max(1, simulation_hours // 50) == 0 or t == simulation_hours:
            timepoints.append({
                "hour": t,
                "car_t_count": max(0, car_t_count),
                "car_t_active_pct": round(max(0, min(100, car_t_active_pct)), 1),
                "cytokine_level_au": round(max(0, cytokine_level), 1),
                "switch_activated": t >= activation_time_hours,
            })

    return {
        "simulation_id": uuid.uuid4().hex[:12],
        "switch_type": switch_type,
        "switch_name": switch.name,
        "activation_time_hours": activation_time_hours,
        "simulation_hours": simulation_hours,
        "mechanism": switch.mechanism,
        "trigger": switch.trigger,
        "expected_response_time_hours": switch.response_time_hours,
        "expected_kill_efficiency_pct": switch.kill_efficiency_pct,
        "timepoints": timepoints,
        "summary": {
            "initial_car_t": initial_car_t,
            "final_car_t": timepoints[-1]["car_t_count"],
            "elimination_pct": round((1 - timepoints[-1]["car_t_count"] / initial_car_t) * 100, 1),
            "time_to_90pct_effect_hours": next(
                (tp["hour"] for tp in timepoints
                 if tp["switch_activated"] and tp["car_t_active_pct"] < 10),
                None,
            ),
        },
    }


async def get_all_switches() -> Dict[str, Any]:
    """Get all available safety switch mechanisms."""
    return {
        "total": len(_SAFETY_SWITCHES),
        "types": {
            "suicide": [k for k, v in _SAFETY_SWITCHES.items() if v.type == "suicide"],
            "depletion": [k for k, v in _SAFETY_SWITCHES.items() if v.type == "depletion"],
            "reversible_pause": [k for k, v in _SAFETY_SWITCHES.items() if v.type == "reversible_pause"],
            "logic_gate": [k for k, v in _SAFETY_SWITCHES.items() if v.type == "logic_gate"],
        },
        "switches": {
            code: {
                "name": s.name, "type": s.type, "mechanism": s.mechanism,
                "trigger": s.trigger, "response_time_hours": s.response_time_hours,
                "kill_efficiency_pct": s.kill_efficiency_pct, "reversible": s.reversible,
                "clinical_stage": s.clinical_stage,
            }
            for code, s in _SAFETY_SWITCHES.items()
        },
    }


# Need math import for simulate_switch_activation
import math
