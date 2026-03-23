"""
CARVanta – Immune Dynamics Simulator
======================================
Models CAR-T cell expansion, exhaustion, and tumor cell killing
using systems of ordinary differential equations (ODEs).

Based on published pharmacokinetic/pharmacodynamic models:
- Sahoo et al., 2020 (CAR-T cell dynamics)
- Stein et al., 2019 (tumor-immune interactions)
- Singh et al., 2020 (cytokine release kinetics)
"""

import math
import random
from typing import Optional


# ─── Constants (biologically calibrated) ────────────────────────────────────────

class BiologicalParams:
    """Default biological parameters for CAR-T simulation."""

    # T-cell dynamics
    T_CELL_INFUSION_DOSE = 1e8          # Initial CAR-T cells infused
    T_CELL_DOUBLING_TIME = 1.5          # Days for T-cell doubling in vivo
    T_CELL_MAX_EXPANSION = 1e11         # Max T-cell count (carrying capacity)
    T_CELL_EXHAUSTION_RATE = 0.03       # Daily exhaustion rate
    T_CELL_HALF_LIFE = 14.0             # Days before persistence decline
    T_CELL_MEMORY_FRACTION = 0.1        # Fraction becoming memory T-cells

    # Tumor dynamics
    TUMOR_DOUBLING_TIME = 30.0          # Days for tumor doubling (untreated)
    TUMOR_KILLING_RATE = 0.15           # Kill rate per T-cell interaction
    TUMOR_RESISTANCE_RATE = 0.005       # Daily rate of antigen loss/escape

    # CRS (Cytokine Release Syndrome)
    CRS_ONSET_DAY = 2                   # Typical onset day
    CRS_PEAK_DAY = 5                    # Peak cytokine day
    CRS_RESOLUTION_DAY = 14             # Typical resolution
    IL6_BASELINE = 5.0                  # pg/mL
    IL6_CRS_MULTIPLIER = 200            # Max fold increase
    CRP_BASELINE = 3.0                  # mg/L
    FERRITIN_BASELINE = 100.0           # ng/mL


def simulate_immune_dynamics(
    days: int = 365,
    tumor_burden: float = 50.0,          # mm, initial tumor size
    t_cell_dose: float = 1e8,
    cancer_stage: str = "III",
    prior_car_t: bool = False,
    lymphodepletion: bool = True,
    antigen_expression: float = 0.7,     # 0-1, target expression level
    patient_age: int = 55,
    patient_weight: float = 70.0,
    alc: Optional[float] = None,         # Absolute lymphocyte count
    ldh: Optional[float] = None,         # LDH level
    noise_seed: Optional[int] = None,
) -> dict:
    """
    Simulate complete CAR-T treatment dynamics over N days.

    Returns a dict with daily values for:
    - t_cells: CAR-T cell count
    - tumor_mm: Tumor size in mm
    - tumor_cells: Estimated tumor cell count
    - il6: IL-6 cytokine level (pg/mL)
    - crp: CRP level (mg/L)
    - ferritin: Ferritin level (ng/mL)
    - crs_grade: CRS severity (0-4) per day
    - response: Clinical response category per day
    """

    if noise_seed is not None:
        random.seed(noise_seed)

    params = BiologicalParams()

    # ── Adjust parameters based on patient ──────────────────────────

    # Stage affects initial tumor cell count
    stage_multiplier = {"I": 0.2, "II": 0.5, "III": 1.0, "IV": 2.5}.get(cancer_stage, 1.0)
    initial_tumor_cells = (tumor_burden ** 3) * 1e6 * stage_multiplier  # rough volume-to-cells

    # Prior CAR-T reduces efficacy (exhausted microenvironment)
    efficacy_modifier = 0.6 if prior_car_t else 1.0

    # Age affects T-cell fitness
    age_modifier = max(0.5, 1.0 - (patient_age - 40) * 0.008)

    # Antigen expression affects killing efficiency
    killing_eff = params.TUMOR_KILLING_RATE * antigen_expression * efficacy_modifier * age_modifier

    # Lymphodepletion boost
    expansion_boost = 2.0 if lymphodepletion else 1.0

    # ALC affects expansion capacity
    if alc is not None:
        if alc < 0.5:
            expansion_boost *= 0.7  # Very low ALC = poor expansion
        elif alc > 1.5:
            expansion_boost *= 1.2

    # LDH indicates tumor burden/aggressiveness
    tumor_growth_modifier = 1.0
    if ldh is not None:
        if ldh > 500:
            tumor_growth_modifier = 1.5
        elif ldh > 250:
            tumor_growth_modifier = 1.2

    # ── Initialize state ────────────────────────────────────────────

    t_cells = t_cell_dose
    tumor_cells = initial_tumor_cells
    tumor_mm = tumor_burden

    # Track daily values
    timeline = {
        "days": [],
        "t_cells": [],
        "tumor_mm": [],
        "tumor_cells": [],
        "il6": [],
        "crp": [],
        "ferritin": [],
        "crs_grade": [],
        "response": [],
        "t_cell_phase": [],
    }

    # ── Run simulation ──────────────────────────────────────────────

    for day in range(days):

        # Daily noise factor (biological variability)
        noise = 1.0 + random.gauss(0, 0.02)

        # ── T-cell dynamics ─────────────────────────────────────────

        # Phase 1: Expansion (days 0-14)
        if day < 14:
            growth_rate = (math.log(2) / params.T_CELL_DOUBLING_TIME) * expansion_boost * noise
            t_cells *= math.exp(growth_rate)
            phase = "expansion"

        # Phase 2: Peak & contraction (days 14-28)
        elif day < 28:
            contraction_rate = 0.08 * noise
            t_cells *= (1 - contraction_rate)
            phase = "contraction"

        # Phase 3: Persistence (days 28+)
        else:
            # Slow decline with memory fraction persisting
            memory_cells = t_cell_dose * params.T_CELL_MEMORY_FRACTION * age_modifier
            decline_rate = params.T_CELL_EXHAUSTION_RATE * noise
            t_cells = max(memory_cells, t_cells * (1 - decline_rate))
            phase = "persistence"

        # Cap at carrying capacity
        t_cells = min(t_cells, params.T_CELL_MAX_EXPANSION)
        t_cells = max(t_cells, 1e4)  # Never go to zero

        # ── Tumor dynamics ──────────────────────────────────────────

        # Tumor growth (logistic)
        tumor_growth_rate = (math.log(2) / params.TUMOR_DOUBLING_TIME) * tumor_growth_modifier * noise
        tumor_growth = tumor_cells * tumor_growth_rate * (1 - tumor_cells / 1e13)

        # CAR-T killing (mass action)
        killing = killing_eff * t_cells * tumor_cells / (tumor_cells + 1e9) * noise

        # Antigen escape (resistance)
        escape = tumor_cells * params.TUMOR_RESISTANCE_RATE * (day / 365)

        # Net tumor change
        tumor_cells = max(0, tumor_cells + tumor_growth - killing + escape)

        # Convert tumor cells back to mm (rough approximation)
        if tumor_cells > 0:
            tumor_mm = max(0, (tumor_cells / (1e6 * stage_multiplier)) ** (1/3))
        else:
            tumor_mm = 0

        # ── Cytokine dynamics (CRS) ─────────────────────────────────

        # IL-6 peaks around day 3-7, proportional to tumor lysis
        crs_activity = 0
        if day < 21:
            # Bell curve of cytokine release
            crs_center = params.CRS_PEAK_DAY
            crs_width = 3.0
            crs_activity = math.exp(-0.5 * ((day - crs_center) / crs_width) ** 2)
            # Scale by tumor burden (more tumor = more CRS)
            crs_activity *= min(1.0, initial_tumor_cells / 1e10) * noise

        il6 = params.IL6_BASELINE + params.IL6_BASELINE * params.IL6_CRS_MULTIPLIER * crs_activity
        crp = params.CRP_BASELINE * (1 + 50 * crs_activity)
        ferritin = params.FERRITIN_BASELINE * (1 + 30 * crs_activity)

        # CRS Grade (ASTCT grading)
        if il6 > 5000:
            crs_grade = 4  # Life-threatening
        elif il6 > 1000:
            crs_grade = 3  # Severe
        elif il6 > 200:
            crs_grade = 2  # Moderate
        elif il6 > 50:
            crs_grade = 1  # Mild
        else:
            crs_grade = 0  # None

        # ── Clinical response assessment ────────────────────────────

        tumor_reduction = 1 - (tumor_mm / max(tumor_burden, 0.1))
        if tumor_cells <= 0 or tumor_mm < 0.1:
            response = "CR"   # Complete Response
        elif tumor_reduction >= 0.5:
            response = "PR"   # Partial Response
        elif tumor_reduction >= 0.0:
            response = "SD"   # Stable Disease
        else:
            response = "PD"   # Progressive Disease

        # ── Record ──────────────────────────────────────────────────

        timeline["days"].append(day)
        timeline["t_cells"].append(round(t_cells))
        timeline["tumor_mm"].append(round(tumor_mm, 2))
        timeline["tumor_cells"].append(round(tumor_cells))
        timeline["il6"].append(round(il6, 1))
        timeline["crp"].append(round(crp, 1))
        timeline["ferritin"].append(round(ferritin, 1))
        timeline["crs_grade"].append(crs_grade)
        timeline["response"].append(response)
        timeline["t_cell_phase"].append(phase)

    # ── Summary statistics ──────────────────────────────────────────

    peak_t_cells = max(timeline["t_cells"])
    peak_t_cell_day = timeline["t_cells"].index(peak_t_cells)
    nadir_tumor = min(timeline["tumor_mm"])
    nadir_tumor_day = timeline["tumor_mm"].index(nadir_tumor)
    max_crs = max(timeline["crs_grade"])
    max_il6 = max(timeline["il6"])

    # Final status
    final_tumor = timeline["tumor_mm"][-1]
    final_response = timeline["response"][-1]

    # Best response achieved
    response_order = {"CR": 4, "PR": 3, "SD": 2, "PD": 1}
    best_response = max(timeline["response"], key=lambda r: response_order.get(r, 0))

    # Duration of response (days in CR or PR)
    dor = sum(1 for r in timeline["response"] if r in ("CR", "PR"))

    # Progression-free survival estimate
    pfs_days = days
    for i, r in enumerate(timeline["response"]):
        if i > 30 and r == "PD":
            pfs_days = i
            break

    summary = {
        "peak_t_cells": peak_t_cells,
        "peak_t_cell_day": peak_t_cell_day,
        "nadir_tumor_mm": round(nadir_tumor, 2),
        "nadir_tumor_day": nadir_tumor_day,
        "final_tumor_mm": round(final_tumor, 2),
        "final_response": final_response,
        "best_response": best_response,
        "max_crs_grade": max_crs,
        "max_il6": round(max_il6, 1),
        "duration_of_response_days": dor,
        "progression_free_survival_days": pfs_days,
        "tumor_reduction_pct": round((1 - final_tumor / max(tumor_burden, 0.1)) * 100, 1),
        "simulation_days": days,
    }

    return {
        "timeline": timeline,
        "summary": summary,
        "parameters": {
            "tumor_burden_mm": tumor_burden,
            "t_cell_dose": t_cell_dose,
            "cancer_stage": cancer_stage,
            "prior_car_t": prior_car_t,
            "lymphodepletion": lymphodepletion,
            "antigen_expression": antigen_expression,
            "patient_age": patient_age,
        },
    }


def compare_targets(
    targets: list,
    patient_params: dict,
    days: int = 365,
) -> dict:
    """
    Simulate treatment with multiple antigen targets and compare outcomes.

    Args:
        targets: List of dicts with 'name' and 'expression' keys
        patient_params: Patient parameters passed to simulate_immune_dynamics
        days: Simulation duration

    Returns comparison dict with per-target results and ranking.
    """

    results = []
    for i, target in enumerate(targets):
        sim = simulate_immune_dynamics(
            days=days,
            antigen_expression=target.get("expression", 0.7),
            noise_seed=42 + i,  # Deterministic for comparison
            **patient_params,
        )
        results.append({
            "target": target["name"],
            "expression": target.get("expression", 0.7),
            "summary": sim["summary"],
            "timeline_snapshot": {
                "day_30": {
                    "tumor_mm": sim["timeline"]["tumor_mm"][min(30, days-1)],
                    "t_cells": sim["timeline"]["t_cells"][min(30, days-1)],
                    "response": sim["timeline"]["response"][min(30, days-1)],
                },
                "day_90": {
                    "tumor_mm": sim["timeline"]["tumor_mm"][min(90, days-1)],
                    "t_cells": sim["timeline"]["t_cells"][min(90, days-1)],
                    "response": sim["timeline"]["response"][min(90, days-1)],
                },
                "day_180": {
                    "tumor_mm": sim["timeline"]["tumor_mm"][min(180, days-1)],
                    "t_cells": sim["timeline"]["t_cells"][min(180, days-1)],
                    "response": sim["timeline"]["response"][min(180, days-1)],
                },
                "day_365": {
                    "tumor_mm": sim["timeline"]["tumor_mm"][-1],
                    "t_cells": sim["timeline"]["t_cells"][-1],
                    "response": sim["timeline"]["response"][-1],
                },
            },
        })

    # Rank by best outcome (tumor reduction %, then PFS)
    results.sort(key=lambda r: (
        -r["summary"]["tumor_reduction_pct"],
        -r["summary"]["progression_free_survival_days"],
        r["summary"]["max_crs_grade"],
    ))

    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {
        "comparisons": results,
        "recommended_target": results[0]["target"] if results else None,
        "recommendation_reason": _get_recommendation_reason(results[0]) if results else None,
    }


def predict_crs_risk(
    tumor_burden: float,
    cancer_stage: str,
    ldh: Optional[float] = None,
    il6_baseline: Optional[float] = None,
    crp_baseline: Optional[float] = None,
    ferritin_baseline: Optional[float] = None,
    prior_car_t: bool = False,
    patient_age: int = 55,
) -> dict:
    """
    Predict CRS risk without running full simulation.
    Uses a risk scoring model based on clinical factors.
    """

    risk_score = 0.0
    risk_factors = []

    # Tumor burden is the #1 predictor
    if tumor_burden > 100:
        risk_score += 35
        risk_factors.append({"factor": "High tumor burden (>100mm)", "impact": "high", "points": 35})
    elif tumor_burden > 50:
        risk_score += 20
        risk_factors.append({"factor": "Moderate tumor burden (50-100mm)", "impact": "moderate", "points": 20})
    else:
        risk_score += 5
        risk_factors.append({"factor": "Low tumor burden (<50mm)", "impact": "low", "points": 5})

    # Cancer stage
    stage_risk = {"I": 5, "II": 10, "III": 20, "IV": 30}.get(cancer_stage, 15)
    risk_score += stage_risk
    risk_factors.append({"factor": f"Cancer stage {cancer_stage}", "impact": "moderate" if stage_risk > 15 else "low", "points": stage_risk})

    # LDH (tumor lysis marker)
    if ldh is not None:
        if ldh > 500:
            risk_score += 20
            risk_factors.append({"factor": "Elevated LDH (>500 U/L)", "impact": "high", "points": 20})
        elif ldh > 250:
            risk_score += 10
            risk_factors.append({"factor": "Moderately elevated LDH", "impact": "moderate", "points": 10})

    # Baseline IL-6
    if il6_baseline is not None and il6_baseline > 10:
        risk_score += 15
        risk_factors.append({"factor": "Elevated baseline IL-6", "impact": "high", "points": 15})

    # CRP
    if crp_baseline is not None and crp_baseline > 10:
        risk_score += 10
        risk_factors.append({"factor": "Elevated baseline CRP", "impact": "moderate", "points": 10})

    # Ferritin
    if ferritin_baseline is not None and ferritin_baseline > 500:
        risk_score += 10
        risk_factors.append({"factor": "Elevated ferritin (>500 ng/mL)", "impact": "moderate", "points": 10})

    # Prior CAR-T (may reduce CRS but also reduce efficacy)
    if prior_car_t:
        risk_score -= 5
        risk_factors.append({"factor": "Prior CAR-T therapy (reduced reactivity)", "impact": "protective", "points": -5})

    # Age
    if patient_age > 65:
        risk_score += 10
        risk_factors.append({"factor": "Age >65 (reduced tolerance)", "impact": "moderate", "points": 10})

    # Clamp
    risk_score = max(0, min(100, risk_score))

    # Grade prediction
    if risk_score >= 70:
        predicted_grade = 4
        severity = "Life-threatening"
        management = "ICU admission likely. Prepare tocilizumab + corticosteroids. Consider reduced CAR-T dose."
    elif risk_score >= 50:
        predicted_grade = 3
        severity = "Severe"
        management = "Close monitoring in hospital. Tocilizumab on standby. Monitor vitals q2h."
    elif risk_score >= 30:
        predicted_grade = 2
        severity = "Moderate"
        management = "Hospital observation. Supportive care. Monitor IL-6 and CRP daily."
    elif risk_score >= 15:
        predicted_grade = 1
        severity = "Mild"
        management = "Outpatient monitoring possible. Antipyretics as needed."
    else:
        predicted_grade = 0
        severity = "Minimal"
        management = "Low risk. Standard post-infusion monitoring."

    return {
        "risk_score": round(risk_score, 1),
        "predicted_max_crs_grade": predicted_grade,
        "severity": severity,
        "management_recommendation": management,
        "risk_factors": risk_factors,
        "risk_level": "high" if risk_score >= 50 else "moderate" if risk_score >= 30 else "low",
    }


def _get_recommendation_reason(result: dict) -> str:
    """Generate a human-readable recommendation explanation."""
    s = result["summary"]
    reasons = []

    if s["best_response"] == "CR":
        reasons.append("achieves complete response")
    elif s["best_response"] == "PR":
        reasons.append("achieves partial response")

    reasons.append(f"{s['tumor_reduction_pct']}% tumor reduction")

    if s["max_crs_grade"] <= 2:
        reasons.append("manageable CRS risk")
    elif s["max_crs_grade"] >= 3:
        reasons.append(f"⚠️ CRS grade {s['max_crs_grade']} risk")

    reasons.append(f"{s['progression_free_survival_days']}-day PFS")

    return f"{result['target']} is recommended because it {', '.join(reasons)}."
