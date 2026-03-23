"""
CARVanta – Adverse Event Prediction Model
============================================
Predictive model for CAR-T therapy adverse events.
Covers:
  - Cytokine Release Syndrome (CRS) grading & kinetics
  - Immune Effector Cell-Associated Neurotoxicity (ICANS)
  - Hematologic toxicity (cytopenias)
  - Infection risk modeling
  - Organ-specific toxicity (cardiac, hepatic, renal, pulmonary)
  - Long-term complications (B-cell aplasia, hypogammaglobulinemia)
  - Macrophage Activation Syndrome / HLH
  - Tumor Lysis Syndrome (TLS)
  - Coagulopathy / DIC

Uses evidence-based scoring with patient-specific risk adjustments.
"""

import math
import random
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# CRS Grading System (ASTCT 2019 Consensus)
# ═══════════════════════════════════════════════════════════════════════════════

CRS_GRADING = {
    1: {
        "description": "Fever ≥38°C",
        "management": "Supportive care, antipyretics",
        "tocilizumab": False,
        "vasopressors": False,
        "oxygen": False,
        "icu_required": False,
    },
    2: {
        "description": "Fever with hypotension (not requiring vasopressors) and/or hypoxia (low-flow O2)",
        "management": "Tocilizumab ± corticosteroids",
        "tocilizumab": True,
        "vasopressors": False,
        "oxygen": True,
        "icu_required": False,
    },
    3: {
        "description": "Fever with hypotension (requiring vasopressor ± vasopressin) and/or hypoxia (high-flow/CPAP/BiPAP)",
        "management": "Tocilizumab + corticosteroids, ICU transfer",
        "tocilizumab": True,
        "vasopressors": True,
        "oxygen": True,
        "icu_required": True,
    },
    4: {
        "description": "Life-threatening: ventilator required and/or multiple vasopressors",
        "management": "Aggressive ICU management, tocilizumab + high-dose steroids, consider siltuximab or ruxolitinib",
        "tocilizumab": True,
        "vasopressors": True,
        "oxygen": True,
        "icu_required": True,
    },
}

ICANS_GRADING = {
    1: {"ice_score": "7-9", "description": "Mild encephalopathy", "management": "Monitor q4h, supportive"},
    2: {"ice_score": "3-6", "description": "Moderate encephalopathy", "management": "Dexamethasone 10mg q6h"},
    3: {"ice_score": "0-2", "description": "Severe: seizures, cerebral edema risk",
        "management": "High-dose methylprednisolone, consider anti-epileptics"},
    4: {"ice_score": "0", "description": "Life-threatening: cerebral edema, coma",
        "management": "ICU, high-dose steroids, mannitol/hypertonic saline, consider anakinra"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# Adverse Event Risk Factors
# ═══════════════════════════════════════════════════════════════════════════════

CRS_RISK_FACTORS = {
    "high_tumor_burden": {
        "threshold": {"tumor_burden_mm": 80},
        "risk_increase": 1.8,
        "description": "Tumor burden >80mm increases CRS severity",
    },
    "elevated_ldh": {
        "threshold": {"ldh": 400},
        "risk_increase": 1.5,
        "description": "LDH >400 U/L correlates with higher CRS grade",
    },
    "elevated_ferritin": {
        "threshold": {"ferritin": 1000},
        "risk_increase": 1.6,
        "description": "Elevated ferritin suggests pre-existing inflammation",
    },
    "elevated_crp": {
        "threshold": {"crp": 50},
        "risk_increase": 1.4,
        "description": "CRP >50 indicates systemic inflammation",
    },
    "high_il6_baseline": {
        "threshold": {"il6": 20},
        "risk_increase": 1.7,
        "description": "Elevated baseline IL-6 predicts severe CRS",
    },
    "cd28_costimulation": {
        "threshold": {"costimulatory": "CD28"},
        "risk_increase": 1.3,
        "description": "CD28 costimulatory domain associated with faster, more intense CRS",
    },
    "high_dose": {
        "threshold": {"dose_cells": 2e8},
        "risk_increase": 1.4,
        "description": "Higher CAR-T dose correlates with increased CRS",
    },
    "prior_car_t": {
        "threshold": {"prior_car_t": True},
        "risk_increase": 0.7,
        "description": "Prior CAR-T may reduce CRS on retreatment (lower T-cell fitness)",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Comprehensive AE Prediction
# ═══════════════════════════════════════════════════════════════════════════════

def predict_adverse_events(
    patient_age: int = 55,
    cancer_type: str = "DLBCL",
    tumor_burden_mm: float = 50.0,
    car_t_product: str = "axi-cel",
    dose_cells: float = 1e8,
    prior_car_t: bool = False,
    ecog: int = 1,
    ldh: Optional[float] = None,
    crp: Optional[float] = None,
    ferritin: Optional[float] = None,
    il6: Optional[float] = None,
    alc: Optional[float] = None,
    platelets: Optional[float] = None,
    comorbidities: Optional[List[str]] = None,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Predict comprehensive adverse event profile for a CAR-T treatment.
    Returns risk scores and management recommendations for each AE category.
    """
    rng = random.Random(seed or 42)
    comorbidities = comorbidities or []

    # Build patient risk context
    ctx = {
        "age": patient_age, "cancer_type": cancer_type,
        "tumor_burden_mm": tumor_burden_mm, "product": car_t_product,
        "dose_cells": dose_cells, "prior_car_t": prior_car_t,
        "ecog": ecog, "ldh": ldh, "crp": crp, "ferritin": ferritin,
        "il6": il6, "alc": alc, "platelets": platelets,
        "comorbidities": comorbidities,
    }

    # Product-specific baseline risks
    product_risks = _get_product_baselines(car_t_product)

    # Calculate each AE category
    crs = _predict_crs(ctx, product_risks, rng)
    icans = _predict_icans(ctx, product_risks, rng)
    cytopenias = _predict_cytopenias(ctx, product_risks, rng)
    infections = _predict_infections(ctx, cytopenias, rng)
    organ_tox = _predict_organ_toxicity(ctx, rng)
    mas_hlh = _predict_mas_hlh(ctx, crs, rng)
    tls = _predict_tls(ctx, rng)
    coagulopathy = _predict_coagulopathy(ctx, crs, rng)
    long_term = _predict_long_term(ctx, rng)

    # Aggregate risk score
    all_risks = [crs["risk_score"], icans["risk_score"], cytopenias["risk_score"],
                 infections["risk_score"], organ_tox["overall_risk"], mas_hlh["risk_score"],
                 tls["risk_score"], coagulopathy["risk_score"]]
    overall_risk = 1 - math.prod(1 - r for r in all_risks)

    return {
        "patient_context": {
            "age": patient_age, "cancer_type": cancer_type,
            "tumor_burden_mm": tumor_burden_mm, "product": car_t_product,
        },
        "cytokine_release_syndrome": crs,
        "neurotoxicity_icans": icans,
        "cytopenias": cytopenias,
        "infections": infections,
        "organ_toxicity": organ_tox,
        "macrophage_activation_syndrome": mas_hlh,
        "tumor_lysis_syndrome": tls,
        "coagulopathy": coagulopathy,
        "long_term_complications": long_term,
        "overall_toxicity_risk": round(overall_risk, 3),
        "overall_risk_level": _risk_cat(overall_risk),
        "icu_probability": round(crs["icu_probability"] + mas_hlh["risk_score"] * 0.3, 3),
        "monitoring_protocol": _generate_monitoring_protocol(crs, icans, cytopenias),
        "premedication_recommendations": _premedication_recs(ctx, crs),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def simulate_crs_kinetics(
    patient_age: int = 55,
    tumor_burden_mm: float = 50.0,
    costimulatory: str = "CD28",
    days: int = 30,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate CRS cytokine kinetics over time.
    Models IL-6, IFN-γ, TNF-α, and temperature kinetics.
    """
    rng = random.Random(seed or 42)

    # Peak timing depends on costimulatory domain
    if costimulatory == "CD28":
        peak_day = 2 + rng.gauss(0, 0.5)  # CD28: earlier, more intense
        intensity = 1.3
    else:
        peak_day = 5 + rng.gauss(0, 1)  # 4-1BB: later, more gradual
        intensity = 0.9

    # Tumor burden affects intensity
    burden_factor = 0.5 + (tumor_burden_mm / 100)
    intensity *= burden_factor

    # Age affects recovery speed
    recovery_rate = 0.15 if patient_age < 50 else 0.10 if patient_age < 65 else 0.07

    timeline = {
        "days": [],
        "il6_pg_ml": [],
        "ifn_gamma_pg_ml": [],
        "tnf_alpha_pg_ml": [],
        "temperature_c": [],
        "crs_grade": [],
        "ferritin_ng_ml": [],
    }

    for day in range(days):
        t = day
        # IL-6 kinetics (primary CRS driver)
        if t < peak_day:
            il6 = 10 * math.exp(1.5 * t / peak_day) * intensity
        else:
            il6 = 10 * math.exp(1.5) * intensity * math.exp(-recovery_rate * (t - peak_day))
        il6 += rng.gauss(0, il6 * 0.08)
        il6 = max(5, il6)

        # IFN-γ (peaks slightly before IL-6)
        ifn = il6 * 0.6 * math.exp(-0.3 * max(0, t - peak_day + 1))
        ifn += rng.gauss(0, ifn * 0.1)
        ifn = max(2, ifn)

        # TNF-α (early peak, fast decay)
        tnf = il6 * 0.3 * math.exp(-0.5 * max(0, t - peak_day))
        tnf += rng.gauss(0, tnf * 0.1)
        tnf = max(1, tnf)

        # Temperature
        temp_base = 36.8
        temp_crs = min(3.5, il6 / 100) if il6 > 30 else 0
        temp = temp_base + temp_crs + rng.gauss(0, 0.2)
        temp = max(36.2, min(41.5, temp))

        # CRS grade based on IL-6 and clinical features
        if il6 > 1000:
            grade = 4
        elif il6 > 300:
            grade = 3
        elif il6 > 80:
            grade = 2
        elif temp > 38.0:
            grade = 1
        else:
            grade = 0

        # Ferritin (rises with CRS, peaks 1-2 days after IL-6 peak)
        ferritin_base = 200
        ferritin_crs = il6 * 2.5 * math.exp(-0.05 * max(0, t - peak_day - 1))
        ferritin = ferritin_base + ferritin_crs + rng.gauss(0, 50)
        ferritin = max(100, ferritin)

        timeline["days"].append(day)
        timeline["il6_pg_ml"].append(round(il6, 1))
        timeline["ifn_gamma_pg_ml"].append(round(ifn, 1))
        timeline["tnf_alpha_pg_ml"].append(round(tnf, 1))
        timeline["temperature_c"].append(round(temp, 1))
        timeline["crs_grade"].append(grade)
        timeline["ferritin_ng_ml"].append(round(ferritin, 0))

    # Summary
    peak_il6 = max(timeline["il6_pg_ml"])
    max_grade = max(timeline["crs_grade"])
    peak_temp = max(timeline["temperature_c"])
    crs_duration = sum(1 for g in timeline["crs_grade"] if g >= 1)

    return {
        "timeline": timeline,
        "summary": {
            "peak_il6": peak_il6,
            "peak_il6_day": timeline["il6_pg_ml"].index(peak_il6),
            "max_crs_grade": max_grade,
            "max_crs_grade_day": timeline["crs_grade"].index(max_grade),
            "peak_temperature": peak_temp,
            "crs_duration_days": crs_duration,
            "peak_ferritin": max(timeline["ferritin_ng_ml"]),
            "management": CRS_GRADING.get(max_grade, CRS_GRADING[1]),
        },
        "costimulatory": costimulatory,
        "tumor_burden_mm": tumor_burden_mm,
    }


def predict_cytopenia_recovery(
    patient_age: int = 55,
    baseline_anc: float = 4.0,
    baseline_platelets: float = 200.0,
    baseline_hgb: float = 12.0,
    lymphodepletion: str = "flu_cy",
    crs_severity: float = 0.5,
    days: int = 120,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Model hematologic recovery trajectory post-CAR-T.
    Tracks ANC, platelets, hemoglobin, and lymphocyte recovery.
    """
    rng = random.Random(seed or 42)

    # Lymphodepletion nadir timing
    if "flu_cy" in lymphodepletion:
        nadir_day = 7
        depth_factor = 0.9  # 90% reduction
    elif "benda" in lymphodepletion:
        nadir_day = 10
        depth_factor = 0.85
    else:
        nadir_day = 5
        depth_factor = 0.75

    # CRS prolongs cytopenias
    recovery_delay = int(crs_severity * 20)

    timeline = {
        "days": [], "anc": [], "platelets": [],
        "hemoglobin": [], "lymphocytes": [],
    }

    for day in range(days):
        # ANC kinetics
        if day < nadir_day:
            anc = baseline_anc * (1 - depth_factor * (day / nadir_day))
        else:
            recovery_start = nadir_day + recovery_delay
            if day < recovery_start:
                anc = baseline_anc * (1 - depth_factor)
            else:
                recovery_phase = (day - recovery_start)
                anc = baseline_anc * (1 - depth_factor) + baseline_anc * depth_factor * (1 - math.exp(-0.05 * recovery_phase))
        anc += rng.gauss(0, 0.2)
        anc = max(0, anc)

        # Platelets (slower recovery)
        if day < nadir_day + 3:
            plt = baseline_platelets * (1 - depth_factor * 0.8 * min(1, day / (nadir_day + 3)))
        else:
            recovery_phase = max(0, day - nadir_day - 3 - recovery_delay)
            plt = baseline_platelets * 0.2 + baseline_platelets * 0.8 * (1 - math.exp(-0.03 * recovery_phase))
        plt += rng.gauss(0, 10)
        plt = max(0, plt)

        # Hemoglobin (gradual decline and slow recovery)
        if day < 14:
            hgb = baseline_hgb - (baseline_hgb * 0.25 * min(1, day / 14))
        else:
            recovery_phase = day - 14
            hgb = baseline_hgb * 0.75 + baseline_hgb * 0.25 * (1 - math.exp(-0.02 * recovery_phase))
        hgb += rng.gauss(0, 0.3)
        hgb = max(4, hgb)

        # Lymphocytes (very slow recovery — B-cell aplasia)
        if day < nadir_day:
            lymph = 1.5 * (1 - 0.95 * min(1, day / nadir_day))
        else:
            recovery_phase = max(0, day - nadir_day - recovery_delay * 2)
            lymph = 0.05 + 1.45 * (1 - math.exp(-0.008 * recovery_phase))
        lymph += rng.gauss(0, 0.05)
        lymph = max(0, lymph)

        timeline["days"].append(day)
        timeline["anc"].append(round(anc, 2))
        timeline["platelets"].append(round(plt, 1))
        timeline["hemoglobin"].append(round(hgb, 1))
        timeline["lymphocytes"].append(round(lymph, 2))

    # Key timepoints
    anc_nadir = min(timeline["anc"])
    plt_nadir = min(timeline["platelets"])
    anc_recovery_day = None
    plt_recovery_day = None

    for i, val in enumerate(timeline["anc"]):
        if val >= 1.0 and i > nadir_day and anc_recovery_day is None:
            anc_recovery_day = i
    for i, val in enumerate(timeline["platelets"]):
        if val >= 75 and i > nadir_day + 3 and plt_recovery_day is None:
            plt_recovery_day = i

    return {
        "timeline": {
            k: v[::max(1, days // 120)] for k, v in timeline.items()
        },
        "summary": {
            "anc_nadir": round(anc_nadir, 2),
            "anc_nadir_day": timeline["anc"].index(anc_nadir),
            "anc_recovery_day": anc_recovery_day,
            "febrile_neutropenia_risk": "high" if anc_nadir < 0.5 else "moderate" if anc_nadir < 1.0 else "low",
            "platelet_nadir": round(plt_nadir, 1),
            "platelet_nadir_day": timeline["platelets"].index(plt_nadir),
            "platelet_recovery_day": plt_recovery_day,
            "transfusion_likely": plt_nadir < 20 or min(timeline["hemoglobin"]) < 7,
            "prolonged_cytopenia": (anc_recovery_day or days) > 28,
            "gcsf_recommended": anc_nadir < 0.5,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Prediction Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _get_product_baselines(product: str) -> Dict[str, float]:
    """Get baseline AE rates for a specific CAR-T product."""
    baselines = {
        "axi-cel": {"crs": 0.93, "g3_crs": 0.13, "icans": 0.64, "g3_icans": 0.28, "cytopenia_d30": 0.30},
        "tisa-cel": {"crs": 0.58, "g3_crs": 0.22, "icans": 0.21, "g3_icans": 0.12, "cytopenia_d30": 0.32},
        "liso-cel": {"crs": 0.42, "g3_crs": 0.02, "icans": 0.30, "g3_icans": 0.10, "cytopenia_d30": 0.35},
        "brexu-cel": {"crs": 0.91, "g3_crs": 0.15, "icans": 0.63, "g3_icans": 0.31, "cytopenia_d30": 0.28},
        "ide-cel": {"crs": 0.84, "g3_crs": 0.05, "icans": 0.18, "g3_icans": 0.03, "cytopenia_d30": 0.40},
        "cilta-cel": {"crs": 0.95, "g3_crs": 0.04, "icans": 0.17, "g3_icans": 0.02, "cytopenia_d30": 0.45},
    }
    return baselines.get(product, baselines["axi-cel"])


def _predict_crs(ctx: Dict, baselines: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict CRS risk and severity."""
    base_risk = baselines["crs"]
    g3_risk = baselines["g3_crs"]

    # Apply risk modifiers
    modifier = 1.0
    risk_factors = []

    if ctx["tumor_burden_mm"] > 80:
        modifier *= 1.4
        risk_factors.append({"factor": "High tumor burden", "impact": "high", "modifier": 1.4})
    elif ctx["tumor_burden_mm"] > 50:
        modifier *= 1.15
        risk_factors.append({"factor": "Moderate tumor burden", "impact": "moderate", "modifier": 1.15})

    if ctx.get("ldh") and ctx["ldh"] > 400:
        modifier *= 1.3
        risk_factors.append({"factor": "Elevated LDH", "impact": "moderate", "modifier": 1.3})

    if ctx.get("ferritin") and ctx["ferritin"] > 1000:
        modifier *= 1.4
        risk_factors.append({"factor": "Elevated ferritin", "impact": "high", "modifier": 1.4})

    if ctx["prior_car_t"]:
        modifier *= 0.7
        risk_factors.append({"factor": "Prior CAR-T", "impact": "protective", "modifier": 0.7})

    if ctx["age"] > 65:
        modifier *= 1.15
        risk_factors.append({"factor": "Age >65", "impact": "moderate", "modifier": 1.15})

    adjusted_g3_risk = min(0.8, g3_risk * modifier)
    overall_risk = min(1.0, base_risk * min(modifier, 1.5))

    # Predicted max grade
    r = rng.random()
    if r < adjusted_g3_risk * 0.3:
        predicted_grade = 4
    elif r < adjusted_g3_risk:
        predicted_grade = 3
    elif r < overall_risk * 0.6:
        predicted_grade = 2
    elif r < overall_risk:
        predicted_grade = 1
    else:
        predicted_grade = 0

    return {
        "risk_score": round(overall_risk, 3),
        "risk_level": _risk_cat(adjusted_g3_risk),
        "predicted_max_grade": predicted_grade,
        "grade3_plus_probability": round(adjusted_g3_risk, 3),
        "expected_onset_day": 2 if ctx["product"] in ("axi-cel", "brexu-cel") else 5,
        "expected_duration_days": 7 + int(adjusted_g3_risk * 10),
        "icu_probability": round(adjusted_g3_risk * 0.85, 3),
        "tocilizumab_needed": predicted_grade >= 2,
        "steroids_needed": predicted_grade >= 3,
        "risk_factors": risk_factors,
        "management": CRS_GRADING.get(max(1, predicted_grade), CRS_GRADING[1]),
    }


def _predict_icans(ctx: Dict, baselines: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict neurotoxicity risk."""
    base_risk = baselines["icans"]
    g3_risk = baselines["g3_icans"]

    modifier = 1.0
    risk_factors = []

    if ctx["age"] > 60:
        modifier *= 1.4
        risk_factors.append({"factor": "Age >60", "impact": "high"})

    if ctx["tumor_burden_mm"] > 80:
        modifier *= 1.3
        risk_factors.append({"factor": "High tumor burden", "impact": "moderate"})

    if "neurologic" in (ctx.get("comorbidities") or []):
        modifier *= 1.5
        risk_factors.append({"factor": "Pre-existing neurologic condition", "impact": "high"})

    adjusted_risk = min(0.7, g3_risk * modifier)

    r = rng.random()
    if r < adjusted_risk * 0.2:
        grade = 4
    elif r < adjusted_risk:
        grade = 3
    elif r < base_risk * modifier * 0.5:
        grade = 2
    elif r < base_risk * modifier:
        grade = 1
    else:
        grade = 0

    return {
        "risk_score": round(min(1.0, base_risk * modifier), 3),
        "risk_level": _risk_cat(adjusted_risk),
        "predicted_max_grade": grade,
        "grade3_plus_probability": round(adjusted_risk, 3),
        "expected_onset_day": 5,
        "expected_duration_days": 5 + int(adjusted_risk * 8),
        "risk_factors": risk_factors,
        "management": ICANS_GRADING.get(max(1, grade), ICANS_GRADING[1]),
        "seizure_prophylaxis_recommended": adjusted_risk > 0.2,
    }


def _predict_cytopenias(ctx: Dict, baselines: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict hematologic toxicity."""
    base_cytopenia = baselines["cytopenia_d30"]

    modifier = 1.0
    if ctx["age"] > 65:
        modifier *= 1.3
    if ctx.get("platelets") and ctx["platelets"] < 100:
        modifier *= 1.5
    if ctx.get("alc") and ctx["alc"] < 0.5:
        modifier *= 1.3

    prolonged_risk = min(0.8, base_cytopenia * modifier)

    return {
        "risk_score": round(prolonged_risk, 3),
        "risk_level": _risk_cat(prolonged_risk),
        "prolonged_cytopenia_d30_risk": round(prolonged_risk, 3),
        "neutropenia_expected_days": int(14 + prolonged_risk * 30),
        "thrombocytopenia_expected_days": int(21 + prolonged_risk * 40),
        "transfusion_probability": round(prolonged_risk * 0.8, 3),
        "gcsf_recommended": prolonged_risk > 0.3,
        "infection_prophylaxis_recommended": True,
    }


def _predict_infections(ctx: Dict, cytopenias: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict infection risk based on cytopenia severity."""
    base_risk = 0.3 + cytopenias["risk_score"] * 0.4

    if ctx["age"] > 65:
        base_risk += 0.1
    if ctx["ecog"] >= 2:
        base_risk += 0.1

    risk = min(0.9, base_risk)

    return {
        "risk_score": round(risk, 3),
        "risk_level": _risk_cat(risk),
        "bacterial_infection_risk": round(risk * 0.6, 3),
        "viral_reactivation_risk": round(risk * 0.3, 3),
        "fungal_infection_risk": round(risk * 0.15, 3),
        "prophylaxis": [
            "Acyclovir/valacyclovir for HSV/VZV prophylaxis",
            "Fluconazole for fungal prophylaxis if prolonged neutropenia",
            "TMP-SMX for PCP prophylaxis",
            "IVIG if IgG <400 mg/dL",
        ],
        "monitoring": "Blood cultures, CMV monitoring weekly, chest imaging PRN",
    }


def _predict_organ_toxicity(ctx: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict organ-specific toxicity risks."""
    age_factor = 1.0 + max(0, (ctx["age"] - 55)) * 0.02

    cardiac = 0.05 * age_factor
    if "cardiac" in (ctx.get("comorbidities") or []):
        cardiac *= 2.0

    hepatic = 0.08 * age_factor
    if ctx.get("ferritin") and ctx["ferritin"] > 2000:
        hepatic *= 1.5

    renal = 0.06 * age_factor
    if "renal" in (ctx.get("comorbidities") or []):
        renal *= 2.0

    pulmonary = 0.04 * age_factor
    if "pulmonary" in (ctx.get("comorbidities") or []):
        pulmonary *= 2.0

    overall = 1 - (1 - cardiac) * (1 - hepatic) * (1 - renal) * (1 - pulmonary)

    return {
        "overall_risk": round(overall, 3),
        "cardiac": {"risk": round(cardiac, 3), "monitoring": "Troponin, BNP, ECG daily during CRS"},
        "hepatic": {"risk": round(hepatic, 3), "monitoring": "LFTs daily during CRS, then twice weekly"},
        "renal": {"risk": round(renal, 3), "monitoring": "Creatinine, electrolytes daily"},
        "pulmonary": {"risk": round(pulmonary, 3), "monitoring": "SpO2 continuous, chest X-ray PRN"},
    }


def _predict_mas_hlh(ctx: Dict, crs: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict MAS/HLH (macrophage activation syndrome)."""
    risk = crs["grade3_plus_probability"] * 0.15
    if ctx.get("ferritin") and ctx["ferritin"] > 2000:
        risk += 0.1
    risk = min(0.4, risk)

    return {
        "risk_score": round(risk, 3),
        "risk_level": _risk_cat(risk),
        "diagnostic_criteria": [
            "Ferritin >10,000 ng/mL",
            "Rising AST/ALT",
            "Hypofibrinogenemia (<150 mg/dL)",
            "Refractory CRS despite tocilizumab",
        ],
        "management": "Anakinra (IL-1 receptor antagonist), high-dose steroids, ruxolitinib",
    }


def _predict_tls(ctx: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict tumor lysis syndrome risk."""
    risk = 0.05
    if ctx["tumor_burden_mm"] > 100:
        risk += 0.15
    if ctx.get("ldh") and ctx["ldh"] > 500:
        risk += 0.1
    risk = min(0.5, risk)

    return {
        "risk_score": round(risk, 3),
        "risk_level": _risk_cat(risk),
        "prophylaxis": [
            "IV hydration",
            "Allopurinol prophylaxis",
            "Monitor electrolytes, uric acid, LDH, creatinine q6h for 72h",
        ] if risk > 0.1 else ["Standard monitoring"],
    }


def _predict_coagulopathy(ctx: Dict, crs: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict coagulopathy/DIC risk."""
    risk = crs["grade3_plus_probability"] * 0.2
    if ctx.get("platelets") and ctx["platelets"] < 50:
        risk += 0.1
    risk = min(0.4, risk)

    return {
        "risk_score": round(risk, 3),
        "risk_level": _risk_cat(risk),
        "monitoring": "PT/INR, aPTT, fibrinogen, D-dimer daily during CRS",
        "management": "Cryoprecipitate for fibrinogen <100, FFP for coagulopathy",
    }


def _predict_long_term(ctx: Dict, rng: random.Random) -> Dict[str, Any]:
    """Predict long-term complications."""
    return {
        "b_cell_aplasia": {
            "risk": round(0.85, 3),
            "duration": "Months to years (if CAR-T persists)",
            "management": "IVIG replacement if IgG <400, monitor immunoglobulin levels monthly",
        },
        "hypogammaglobulinemia": {
            "risk": round(0.80, 3),
            "management": "IVIG 400-600 mg/kg every 3-4 weeks",
        },
        "secondary_malignancy": {
            "risk": round(0.02, 3),
            "note": "T-cell lymphoma reported in rare cases — long-term monitoring",
        },
        "growth_factor_delays": {
            "risk": round(0.15 if ctx["age"] > 60 else 0.05, 3),
            "note": "Delayed hematopoietic recovery may require extended growth factor support",
        },
    }


def _risk_cat(score: float) -> str:
    """Convert numeric risk to category."""
    if score > 0.6: return "high"
    if score > 0.3: return "moderate"
    if score > 0.1: return "low"
    return "very_low"


def _generate_monitoring_protocol(crs: Dict, icans: Dict, cytopenias: Dict) -> Dict[str, Any]:
    """Generate a risk-stratified monitoring protocol."""
    intensity = "standard"
    if crs["grade3_plus_probability"] > 0.2 or icans["grade3_plus_probability"] > 0.2:
        intensity = "intensive"
    elif crs["grade3_plus_probability"] > 0.1:
        intensity = "enhanced"

    return {
        "intensity": intensity,
        "protocol": {
            "day_minus_5_to_minus_1": ["Lymphodepletion chemotherapy", "Daily CBC, CMP"],
            "day_0": ["CAR-T infusion", "Vitals q15min × 2h, then q1h × 4h, then q4h"],
            "day_1_to_7": [
                "Vitals q4h" if intensity == "standard" else "Vitals q2h",
                "CBC daily", "CMP daily", "CRP daily",
                "Ferritin daily" if intensity != "standard" else "Ferritin q2d",
                "ICE assessment q12h" if icans["grade3_plus_probability"] > 0.1 else "ICE assessment daily",
            ],
            "day_8_to_14": [
                "Vitals q6h", "CBC q2d", "CRP q2d",
                "ICE assessment daily",
            ],
            "day_15_to_28": [
                "CBC twice weekly", "CMP weekly",
                "Immunoglobulin levels weekly",
            ],
            "month_2_to_3": [
                "CBC weekly → biweekly", "CMP biweekly",
                "CAR-T persistence by qPCR monthly",
                "Response assessment (PET/CT) at Day 30 and Day 90",
            ],
        },
    }


def _premedication_recs(ctx: Dict, crs: Dict) -> List[str]:
    """Generate pre-medication recommendations."""
    recs = [
        "Acetaminophen 650mg PO 30-60 min before infusion",
        "Diphenhydramine 25-50mg PO/IV 30-60 min before infusion",
    ]
    if crs["grade3_plus_probability"] > 0.3:
        recs.append("Consider prophylactic tocilizumab (8mg/kg IV) — discuss with team")
    if crs["grade3_plus_probability"] > 0.2:
        recs.append("Ensure tocilizumab available at bedside")
    recs.append("Avoid corticosteroids pre-infusion (may impair CAR-T expansion)")
    recs.append("Levetiracetam 750mg PO BID for seizure prophylaxis (if ICANS risk elevated)")
    return recs
