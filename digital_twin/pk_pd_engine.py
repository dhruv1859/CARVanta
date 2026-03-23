"""
CARVanta – Pharmacokinetics / Pharmacodynamics Engine
=======================================================
Models the pharmacokinetic behavior of CAR-T cells and 
pharmacodynamic effects on tumor and immune system.

Implements:
- CAR-T cell biodistribution (blood, tumor, spleen, bone marrow, lymph nodes)
- Cytokine pharmacokinetics (IL-6, IFN-γ, TNF-α, IL-2, IL-10, IL-15)
- Drug interaction modeling for combination therapies
- Lymphodepletion chemotherapy modeling (Flu/Cy, Bendamustine)
- Tocilizumab PK for CRS management
- Corticosteroid PK for CRS/ICANS management
- Population PK variability modeling

References:
    - Mueller et al., Blood (2017) — CAR-T PK in ALL
    - Turtle et al., JCI (2016) — CAR-T biodistribution
    - Nishimoto & Kishimoto, Nature Reviews (2006) — Tocilizumab PK
    - Hay et al., Blood (2017) — CRS management protocols
"""

import math
import random
from typing import Optional, Dict, List
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# Compartmental PK Model for CAR-T Cells
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CompartmentState:
    """PK compartment: tracks cell counts in each body location."""
    blood: float = 0.0           # Peripheral blood
    tumor: float = 0.0           # Tumor infiltrating
    spleen: float = 0.0          # Splenic pool
    bone_marrow: float = 0.0     # Bone marrow reservoir
    lymph_nodes: float = 0.0     # Lymph node expansion
    csf: float = 0.0             # Cerebrospinal fluid (ICANS relevant)


@dataclass
class CytokineProfile:
    """Serum cytokine levels in pg/mL."""
    il6: float = 5.0              # Interleukin-6 (CRS marker)
    ifn_gamma: float = 10.0       # IFN-γ (effector cytokine)
    tnf_alpha: float = 8.0        # TNF-α (inflammation)
    il2: float = 15.0             # IL-2 (T-cell growth factor)
    il10: float = 3.0             # IL-10 (immunosuppressive)
    il15: float = 5.0             # IL-15 (T-cell homeostasis)
    il1_beta: float = 4.0         # IL-1β (inflammasome)
    gm_csf: float = 2.0           # GM-CSF (myeloid activation)
    
    # Derived markers
    crp: float = 3.0              # C-reactive protein (mg/L)
    ferritin: float = 100.0       # Ferritin (ng/mL)
    d_dimer: float = 0.5          # D-dimer (μg/mL) — coagulopathy
    fibrinogen: float = 300.0     # Fibrinogen (mg/dL)
    
    def get_crs_score(self) -> float:
        """Composite CRS biomarker score."""
        score = 0.0
        score += min(1.0, self.il6 / 1000) * 30
        score += min(1.0, self.ifn_gamma / 500) * 15
        score += min(1.0, self.tnf_alpha / 200) * 10
        score += min(1.0, self.crp / 200) * 15
        score += min(1.0, self.ferritin / 5000) * 15
        score += min(1.0, self.il1_beta / 100) * 10
        score += min(1.0, self.d_dimer / 5) * 5
        return round(min(100, score), 1)
    
    def get_crs_grade(self) -> int:
        """ASTCT CRS grading from biomarkers."""
        score = self.get_crs_score()
        if score >= 70: return 4
        if score >= 50: return 3
        if score >= 30: return 2
        if score >= 15: return 1
        return 0

    def to_dict(self) -> dict:
        return {
            "il6": round(self.il6, 1),
            "ifn_gamma": round(self.ifn_gamma, 1),
            "tnf_alpha": round(self.tnf_alpha, 1),
            "il2": round(self.il2, 1),
            "il10": round(self.il10, 1),
            "il15": round(self.il15, 1),
            "il1_beta": round(self.il1_beta, 1),
            "gm_csf": round(self.gm_csf, 1),
            "crp": round(self.crp, 1),
            "ferritin": round(self.ferritin, 1),
            "d_dimer": round(self.d_dimer, 2),
            "fibrinogen": round(self.fibrinogen, 1),
            "crs_score": self.get_crs_score(),
            "crs_grade": self.get_crs_grade(),
        }


# ─── Transfer Rate Constants ───────────────────────────────────────────────────

class TransferRates:
    """Inter-compartmental transfer rate constants (per day)."""
    
    # Blood ↔ Tumor
    BLOOD_TO_TUMOR = 0.15        # Extravasation + chemotaxis
    TUMOR_TO_BLOOD = 0.02        # Efflux from tumor
    
    # Blood ↔ Spleen
    BLOOD_TO_SPLEEN = 0.08
    SPLEEN_TO_BLOOD = 0.12
    
    # Blood ↔ Bone Marrow
    BLOOD_TO_BM = 0.05
    BM_TO_BLOOD = 0.10
    
    # Blood ↔ Lymph Nodes
    BLOOD_TO_LN = 0.10
    LN_TO_BLOOD = 0.15
    
    # Blood → CSF (rare, but matters for ICANS)
    BLOOD_TO_CSF = 0.001
    CSF_TO_BLOOD = 0.005


def simulate_car_t_pk(
    days: int = 60,
    infusion_dose: float = 1e8,
    patient_weight: float = 70.0,
    tumor_burden_ml: float = 50.0,
    cancer_category: str = "hematologic",
    lymphodepletion: bool = True,
    seed: int = 42,
) -> Dict:
    """
    Simulate CAR-T cell pharmacokinetics across body compartments.
    
    Returns daily compartment concentrations and AUC (area under curve).
    """
    random.seed(seed)
    
    # Blood volume estimation (Nadler's formula, simplified)
    blood_vol_ml = patient_weight * 70  # ~70 mL/kg
    
    # Initialize: all cells start in blood after infusion
    state = CompartmentState(blood=infusion_dose)
    
    # Lymphodepletion enhances expansion
    expansion_boost = 2.5 if lymphodepletion else 1.0
    
    # Solid tumors have lower infiltration
    infiltration_mult = 0.4 if cancer_category == "solid" else 1.0
    
    timeline = {
        "days": [], "blood": [], "tumor": [], "spleen": [],
        "bone_marrow": [], "lymph_nodes": [], "csf": [],
        "blood_concentration": [],  # cells/μL (clinical unit)
    }
    
    auc_blood = 0.0  # Area under curve
    peak_blood = 0.0
    peak_day = 0
    
    rates = TransferRates()
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.03)
        
        # ── Expansion ────────────────────────────────────────
        if day < 14:
            growth = math.log(2) / 1.5 * expansion_boost * noise
            state.blood *= math.exp(growth * 0.6)
            state.tumor *= math.exp(growth * 0.8)
            state.lymph_nodes *= math.exp(growth * 1.2)  # LN is prime expansion site
            state.spleen *= math.exp(growth * 0.5)
        elif day < 28:
            contraction = 0.06 * noise
            state.blood *= (1 - contraction)
            state.tumor *= (1 - contraction * 0.5)  # Tumor-resident persist longer
            state.lymph_nodes *= (1 - contraction * 0.8)
            state.spleen *= (1 - contraction * 0.7)
        else:
            decline = 0.02 * noise
            memory_floor = infusion_dose * 0.05
            state.blood = max(memory_floor, state.blood * (1 - decline))
            state.tumor = max(memory_floor * 0.1, state.tumor * (1 - decline * 0.5))
            state.lymph_nodes = max(memory_floor * 0.2, state.lymph_nodes * (1 - decline * 0.7))
            state.spleen = max(memory_floor * 0.1, state.spleen * (1 - decline * 0.6))
        
        # ── Inter-compartmental transfer ─────────────────────
        # Blood → Tumor
        transfer = state.blood * rates.BLOOD_TO_TUMOR * infiltration_mult * noise
        state.blood -= transfer
        state.tumor += transfer
        
        # Tumor → Blood
        transfer = state.tumor * rates.TUMOR_TO_BLOOD * noise
        state.tumor -= transfer
        state.blood += transfer
        
        # Blood → Spleen
        transfer = state.blood * rates.BLOOD_TO_SPLEEN * noise
        state.blood -= transfer
        state.spleen += transfer
        
        # Spleen → Blood
        transfer = state.spleen * rates.SPLEEN_TO_BLOOD * noise
        state.spleen -= transfer
        state.blood += transfer
        
        # Blood → Bone Marrow
        transfer = state.blood * rates.BLOOD_TO_BM * noise
        state.blood -= transfer
        state.bone_marrow += transfer
        
        # BM → Blood
        transfer = state.bone_marrow * rates.BM_TO_BLOOD * noise
        state.bone_marrow -= transfer
        state.blood += transfer
        
        # Blood → LN
        transfer = state.blood * rates.BLOOD_TO_LN * noise
        state.blood -= transfer
        state.lymph_nodes += transfer
        
        # LN → Blood
        transfer = state.lymph_nodes * rates.LN_TO_BLOOD * noise
        state.lymph_nodes -= transfer
        state.blood += transfer
        
        # Blood → CSF (small but relevant for ICANS)
        transfer = state.blood * rates.BLOOD_TO_CSF * noise
        state.blood -= transfer
        state.csf += transfer
        # CSF → Blood
        transfer = state.csf * rates.CSF_TO_BLOOD * noise
        state.csf -= transfer
        state.blood += transfer
        
        # Ensure non-negative
        state.blood = max(0, state.blood)
        state.tumor = max(0, state.tumor)
        state.spleen = max(0, state.spleen)
        state.bone_marrow = max(0, state.bone_marrow)
        state.lymph_nodes = max(0, state.lymph_nodes)
        state.csf = max(0, state.csf)
        
        # Blood concentration (cells/μL — clinical unit)
        concentration = state.blood / blood_vol_ml  # cells/mL → cells/μL * 1000
        
        auc_blood += state.blood
        if state.blood > peak_blood:
            peak_blood = state.blood
            peak_day = day
        
        timeline["days"].append(day)
        timeline["blood"].append(round(state.blood))
        timeline["tumor"].append(round(state.tumor))
        timeline["spleen"].append(round(state.spleen))
        timeline["bone_marrow"].append(round(state.bone_marrow))
        timeline["lymph_nodes"].append(round(state.lymph_nodes))
        timeline["csf"].append(round(state.csf))
        timeline["blood_concentration"].append(round(concentration, 2))
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_blood_cells": round(peak_blood),
            "peak_day": peak_day,
            "auc_blood": round(auc_blood),
            "final_distribution": {
                "blood": round(state.blood),
                "tumor": round(state.tumor),
                "spleen": round(state.spleen),
                "bone_marrow": round(state.bone_marrow),
                "lymph_nodes": round(state.lymph_nodes),
                "csf": round(state.csf),
            },
            "persistence_day60": round(state.blood + state.tumor + state.lymph_nodes),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Cytokine PK Simulation
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_cytokine_pk(
    days: int = 30,
    tumor_burden_cells: float = 1e10,
    t_cell_count: float = 1e8,
    cancer_crs_risk: float = 1.0,
    patient_age: int = 55,
    seed: int = 42,
) -> Dict:
    """
    Detailed cytokine kinetics during CAR-T therapy.
    Models each cytokine individually with production/clearance rates.
    """
    random.seed(seed)
    
    cytokines = CytokineProfile()
    
    # Baseline adjustments for age
    age_factor = 1.0 + max(0, patient_age - 50) * 0.01
    
    timeline = {"days": []}
    for field_name in ["il6", "ifn_gamma", "tnf_alpha", "il2", "il10", "il15",
                        "crp", "ferritin", "d_dimer", "crs_score", "crs_grade"]:
        timeline[field_name] = []
    
    # Half-lives (hours) for each cytokine
    half_lives = {
        "il6": 4, "ifn_gamma": 5, "tnf_alpha": 1.5, "il2": 2,
        "il10": 3, "il15": 8, "il1_beta": 2, "gm_csf": 1.5,
    }
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.05)
        
        # Tumor killing activity (peaks early, declines)
        kill_activity = 0
        if day < 21:
            kill_peak = 5.0
            kill_width = 3.5
            kill_activity = math.exp(-0.5 * ((day - kill_peak) / kill_width) ** 2)
            kill_activity *= min(1.0, tumor_burden_cells / 1e10)
            kill_activity *= cancer_crs_risk * noise
        
        # T-cell activation intensity
        t_activation = min(1.0, t_cell_count / 1e10) * (1 + kill_activity)
        
        # ── IL-6 (from monocytes/macrophages activated by CAR-T) ──
        il6_prod = 5.0 * kill_activity * age_factor * 200
        il6_clear = cytokines.il6 * (1 - math.exp(-math.log(2) / (half_lives["il6"] / 24)))
        cytokines.il6 = max(5.0, cytokines.il6 + il6_prod - il6_clear)
        
        # ── IFN-γ (from activated T-cells) ────────────────────────
        ifng_prod = 10.0 * t_activation * kill_activity * 50
        ifng_clear = cytokines.ifn_gamma * (1 - math.exp(-math.log(2) / (half_lives["ifn_gamma"] / 24)))
        cytokines.ifn_gamma = max(10.0, cytokines.ifn_gamma + ifng_prod - ifng_clear)
        
        # ── TNF-α (from macrophages) ──────────────────────────────
        tnfa_prod = 8.0 * kill_activity * 25
        tnfa_clear = cytokines.tnf_alpha * (1 - math.exp(-math.log(2) / (half_lives["tnf_alpha"] / 24)))
        cytokines.tnf_alpha = max(8.0, cytokines.tnf_alpha + tnfa_prod - tnfa_clear)
        
        # ── IL-2 (T-cell autocrine growth factor) ─────────────────
        il2_prod = 15.0 * t_activation * 10
        il2_clear = cytokines.il2 * (1 - math.exp(-math.log(2) / (half_lives["il2"] / 24)))
        cytokines.il2 = max(15.0, cytokines.il2 + il2_prod - il2_clear)
        
        # ── IL-10 (regulatory, counter-acts inflammation) ─────────
        il10_prod = 3.0 * kill_activity * 8 * (day / 10)  # Delayed response
        il10_clear = cytokines.il10 * (1 - math.exp(-math.log(2) / (half_lives["il10"] / 24)))
        cytokines.il10 = max(3.0, cytokines.il10 + il10_prod - il10_clear)
        
        # ── IL-15 (homeostatic, supports T-cell persistence) ─────
        il15_prod = 5.0 * (1 + 0.5 * t_activation)
        il15_clear = cytokines.il15 * (1 - math.exp(-math.log(2) / (half_lives["il15"] / 24)))
        cytokines.il15 = max(5.0, cytokines.il15 + il15_prod - il15_clear)
        
        # ── Acute phase reactants (downstream of IL-6) ────────────
        cytokines.crp = 3.0 + (cytokines.il6 / 10) * 2 * noise  # CRP follows IL-6
        cytokines.ferritin = 100 + (cytokines.il6 / 5) * 1.5 * noise  # Ferritin is delayed
        cytokines.d_dimer = 0.5 + kill_activity * 3 * noise  # Coagulopathy from CRS
        cytokines.fibrinogen = max(50, 300 - kill_activity * 150 * noise)  # Consumption
        
        timeline["days"].append(day)
        timeline["il6"].append(round(cytokines.il6, 1))
        timeline["ifn_gamma"].append(round(cytokines.ifn_gamma, 1))
        timeline["tnf_alpha"].append(round(cytokines.tnf_alpha, 1))
        timeline["il2"].append(round(cytokines.il2, 1))
        timeline["il10"].append(round(cytokines.il10, 1))
        timeline["il15"].append(round(cytokines.il15, 1))
        timeline["crp"].append(round(cytokines.crp, 1))
        timeline["ferritin"].append(round(cytokines.ferritin, 1))
        timeline["d_dimer"].append(round(cytokines.d_dimer, 2))
        timeline["crs_score"].append(cytokines.get_crs_score())
        timeline["crs_grade"].append(cytokines.get_crs_grade())
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_il6": round(max(timeline["il6"]), 1),
            "peak_il6_day": timeline["il6"].index(max(timeline["il6"])),
            "peak_ifn_gamma": round(max(timeline["ifn_gamma"]), 1),
            "peak_crp": round(max(timeline["crp"]), 1),
            "peak_ferritin": round(max(timeline["ferritin"]), 1),
            "max_crs_grade": max(timeline["crs_grade"]),
            "max_crs_score": max(timeline["crs_score"]),
            "crs_duration_days": sum(1 for g in timeline["crs_grade"] if g >= 1),
            "severe_crs_days": sum(1 for g in timeline["crs_grade"] if g >= 3),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Lymphodepletion Chemotherapy PK
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LymphodepletiionRegimen:
    """Lymphodepletion chemotherapy regimen."""
    name: str
    drugs: List[str]
    days_before_infusion: int
    duration_days: int
    alc_nadir_day: int            # Day of lowest ALC (relative to chemo start)
    alc_nadir_value: float        # Expected ALC nadir (×10⁹/L)
    lymphocyte_kill_pct: float    # % of lymphocytes killed
    neutrophil_kill_pct: float    # % of neutrophils killed
    recovery_start_day: int       # Day lymphocytes start recovering
    infection_risk: str           # "low", "moderate", "high"
    nausea_risk: float
    cytopenias_risk: float


LYMPHODEPLETION_REGIMENS = {
    "flu_cy": LymphodepletiionRegimen(
        name="Fludarabine + Cyclophosphamide (Flu/Cy)",
        drugs=["Fludarabine 30mg/m² × 3d", "Cyclophosphamide 500mg/m² × 3d"],
        days_before_infusion=5,
        duration_days=3,
        alc_nadir_day=7,
        alc_nadir_value=0.05,
        lymphocyte_kill_pct=95,
        neutrophil_kill_pct=60,
        recovery_start_day=14,
        infection_risk="moderate",
        nausea_risk=0.4,
        cytopenias_risk=0.8,
    ),
    "flu_cy_high": LymphodepletiionRegimen(
        name="High-Dose Flu/Cy",
        drugs=["Fludarabine 30mg/m² × 4d", "Cyclophosphamide 750mg/m² × 3d"],
        days_before_infusion=6,
        duration_days=4,
        alc_nadir_day=8,
        alc_nadir_value=0.02,
        lymphocyte_kill_pct=99,
        neutrophil_kill_pct=75,
        recovery_start_day=21,
        infection_risk="high",
        nausea_risk=0.6,
        cytopenias_risk=0.9,
    ),
    "bendamustine": LymphodepletiionRegimen(
        name="Bendamustine",
        drugs=["Bendamustine 90mg/m² × 2d"],
        days_before_infusion=5,
        duration_days=2,
        alc_nadir_day=7,
        alc_nadir_value=0.10,
        lymphocyte_kill_pct=85,
        neutrophil_kill_pct=40,
        recovery_start_day=10,
        infection_risk="moderate",
        nausea_risk=0.3,
        cytopenias_risk=0.6,
    ),
    "flu_only": LymphodepletiionRegimen(
        name="Fludarabine Only",
        drugs=["Fludarabine 25mg/m² × 3d"],
        days_before_infusion=4,
        duration_days=3,
        alc_nadir_day=6,
        alc_nadir_value=0.15,
        lymphocyte_kill_pct=75,
        neutrophil_kill_pct=25,
        recovery_start_day=10,
        infection_risk="low",
        nausea_risk=0.2,
        cytopenias_risk=0.4,
    ),
    "none": LymphodepletiionRegimen(
        name="No Lymphodepletion",
        drugs=[],
        days_before_infusion=0,
        duration_days=0,
        alc_nadir_day=0,
        alc_nadir_value=1.0,
        lymphocyte_kill_pct=0,
        neutrophil_kill_pct=0,
        recovery_start_day=0,
        infection_risk="low",
        nausea_risk=0,
        cytopenias_risk=0,
    ),
}


def simulate_lymphodepletion(
    regimen_key: str = "flu_cy",
    baseline_alc: float = 1.5,
    baseline_anc: float = 4.0,
    days: int = 30,
    seed: int = 42,
) -> Dict:
    """
    Simulate lymphodepletion chemotherapy effects on blood counts.
    Models ALC (absolute lymphocyte count), ANC (absolute neutrophil count),
    and platelet trajectory.
    """
    random.seed(seed)
    regimen = LYMPHODEPLETION_REGIMENS.get(regimen_key, LYMPHODEPLETION_REGIMENS["flu_cy"])
    
    timeline = {"days": [], "alc": [], "anc": [], "platelets": [], "infection_risk_score": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.05)
        
        # ALC trajectory
        if day < regimen.alc_nadir_day:
            # Decline phase
            decline_rate = regimen.lymphocyte_kill_pct / 100 / regimen.alc_nadir_day
            alc = max(regimen.alc_nadir_value, baseline_alc * (1 - decline_rate * day) * noise)
        elif day < regimen.recovery_start_day:
            # Nadir plateau
            alc = regimen.alc_nadir_value * noise
        else:
            # Recovery phase (slow)
            days_recovering = day - regimen.recovery_start_day
            recovery_rate = 0.05
            alc = min(baseline_alc, regimen.alc_nadir_value + days_recovering * recovery_rate * noise)
        
        # ANC trajectory (similar pattern, different kinetics)
        if day < regimen.alc_nadir_day + 1:
            anc_decline = regimen.neutrophil_kill_pct / 100 / (regimen.alc_nadir_day + 1)
            anc = max(0.5, baseline_anc * (1 - anc_decline * day) * noise)
        elif day < regimen.recovery_start_day - 2:
            anc = max(0.5, baseline_anc * (1 - regimen.neutrophil_kill_pct / 100)) * noise
        else:
            days_rec = day - (regimen.recovery_start_day - 2)
            anc = min(baseline_anc, 0.5 + days_rec * 0.3 * noise)
        
        # Platelet trajectory
        plt = max(20, 250 * (1 - regimen.cytopenias_risk * 0.7 *
                math.exp(-0.5 * ((day - regimen.alc_nadir_day) / 5) ** 2))) * noise
        
        # Infection risk score
        infection_score = 0
        if alc < 0.5: infection_score += 40
        elif alc < 1.0: infection_score += 20
        if anc < 1.0: infection_score += 30
        elif anc < 1.5: infection_score += 15
        if plt < 50: infection_score += 15
        elif plt < 100: infection_score += 5
        
        timeline["days"].append(day)
        timeline["alc"].append(round(alc, 3))
        timeline["anc"].append(round(anc, 2))
        timeline["platelets"].append(round(plt))
        timeline["infection_risk_score"].append(round(infection_score))
    
    return {
        "regimen": {
            "name": regimen.name,
            "drugs": regimen.drugs,
            "infection_risk": regimen.infection_risk,
        },
        "timeline": timeline,
        "summary": {
            "alc_nadir": round(min(timeline["alc"]), 3),
            "anc_nadir": round(min(timeline["anc"]), 2),
            "platelet_nadir": round(min(timeline["platelets"])),
            "peak_infection_risk": max(timeline["infection_risk_score"]),
            "days_febrile_neutropenia_risk": sum(1 for a in timeline["anc"] if a < 0.5),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CRS Management: Tocilizumab + Corticosteroid PK
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_crs_intervention(
    crs_grade: int,
    il6_level: float,
    crp_level: float,
    patient_weight: float = 70.0,
    use_tocilizumab: bool = True,
    use_steroids: bool = False,
    days: int = 14,
    seed: int = 42,
) -> Dict:
    """
    Simulate CRS intervention with tocilizumab ± corticosteroids.
    
    Tocilizumab: IL-6R antagonist (blocks IL-6 signaling)
    Dexamethasone: Broad immunosuppression
    """
    random.seed(seed)
    
    toci_dose = patient_weight * 8  # 8 mg/kg
    toci_half_life = 13 * 24  # 13 days in hours
    toci_trough = 0.0
    
    dexa_dose = 10  # mg
    dexa_half_life = 36  # hours
    dexa_level = 0.0
    
    il6 = il6_level
    crp_ = crp_level
    current_grade = crs_grade
    
    timeline = {
        "days": [], "il6": [], "crp": [], "crs_grade": [],
        "tocilizumab_level": [], "dexamethasone_level": [],
        "fever": [], "hypotension_risk": [],
    }
    
    toci_doses_given = 0
    steroid_days = 0
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.03)
        
        # ── Tocilizumab administration ───────────────────────
        if use_tocilizumab:
            if day == 0:
                toci_trough = toci_dose
                toci_doses_given = 1
            elif day == 1 and current_grade >= 3 and toci_doses_given < 4:
                toci_trough += toci_dose * 0.8  # Repeat dose
                toci_doses_given += 1
            
            # PK decay
            toci_trough *= math.exp(-math.log(2) / (toci_half_life / 24))
            
            # Efficacy: blocks IL-6 signaling (paradoxically raises serum IL-6)
            il6_suppression = min(0.8, toci_trough / (toci_dose * 0.5))
            actual_il6_signal = il6 * (1 - il6_suppression)  # Effective IL-6
        else:
            il6_suppression = 0
            actual_il6_signal = il6
        
        # ── Corticosteroid administration ────────────────────
        if use_steroids:
            if current_grade >= 2:
                dexa_level += dexa_dose
                steroid_days += 1
            
            dexa_level *= math.exp(-math.log(2) / (dexa_half_life / 24))
            
            # Steroids suppress T-cell function → reduce all cytokines
            steroid_suppression = min(0.6, dexa_level / 20)
        else:
            steroid_suppression = 0
        
        # ── CRS resolution dynamics ──────────────────────────
        total_suppression = min(0.9, il6_suppression + steroid_suppression * 0.5)
        
        # IL-6 natural decline + drug effects
        il6_natural_decline = 0.15  # 15% daily clearance
        il6 = max(5, il6 * (1 - il6_natural_decline * (1 + total_suppression)) * noise)
        
        # CRP follows IL-6 with 24h delay
        crp_ = max(3, crp_ * 0.7 + (il6 / 100) * noise)
        
        # CRS grade assessment
        if actual_il6_signal > 5000:
            current_grade = 4
        elif actual_il6_signal > 1000:
            current_grade = 3
        elif actual_il6_signal > 200:
            current_grade = 2
        elif actual_il6_signal > 50:
            current_grade = 1
        else:
            current_grade = 0
        
        # Clinical features
        fever = actual_il6_signal > 100
        hypotension_risk = min(100, actual_il6_signal / 50)
        
        timeline["days"].append(day)
        timeline["il6"].append(round(il6, 1))
        timeline["crp"].append(round(crp_, 1))
        timeline["crs_grade"].append(current_grade)
        timeline["tocilizumab_level"].append(round(toci_trough, 1))
        timeline["dexamethasone_level"].append(round(dexa_level, 2))
        timeline["fever"].append(fever)
        timeline["hypotension_risk"].append(round(hypotension_risk, 1))
    
    return {
        "timeline": timeline,
        "summary": {
            "initial_grade": crs_grade,
            "final_grade": current_grade,
            "grade_resolved_day": next((i for i, g in enumerate(timeline["crs_grade"]) if g == 0), None),
            "tocilizumab_doses": toci_doses_given,
            "steroid_days": steroid_days,
            "il6_reduction_pct": round((1 - il6 / max(il6_level, 1)) * 100, 1),
            "intervention_successful": current_grade < crs_grade,
        },
        "recommendations": _crs_management_plan(crs_grade, il6_level),
    }


def _crs_management_plan(grade: int, il6: float) -> Dict:
    """Generate evidence-based CRS management plan."""
    plans = {
        0: {
            "grade": 0,
            "management": "No intervention needed",
            "monitoring": "Vital signs q8h, daily labs",
            "medications": [],
        },
        1: {
            "grade": 1,
            "management": "Supportive care",
            "monitoring": "Vital signs q4h, labs q12h",
            "medications": ["Acetaminophen PRN for fever"],
        },
        2: {
            "grade": 2,
            "management": "Tocilizumab ± fluids",
            "monitoring": "Continuous telemetry, labs q8h, ICU evaluation",
            "medications": [
                "Tocilizumab 8mg/kg IV (max 800mg)",
                "IV fluids for hypotension",
                "Supplemental O2 if needed",
            ],
        },
        3: {
            "grade": 3,
            "management": "Tocilizumab + consider steroids + ICU",
            "monitoring": "ICU (continuous vitals, q4h labs, echocardiogram)",
            "medications": [
                "Tocilizumab 8mg/kg IV (max 800mg), may repeat ×1",
                "Dexamethasone 10mg IV q6h if no improvement in 24h",
                "Vasopressors if refractory hypotension",
                "High-flow O2 or mechanical ventilation if needed",
            ],
        },
        4: {
            "grade": 4,
            "management": "Tocilizumab + steroids + ICU + organ support",
            "monitoring": "ICU (continuous, q2h labs, multi-organ assessment)",
            "medications": [
                "Tocilizumab 8mg/kg IV (may repeat q8h × 3 max)",
                "Methylprednisolone 2mg/kg/day IV",
                "Vasopressors + inotropes",
                "Mechanical ventilation",
                "Consider siltuximab if tocilizumab-refractory",
                "Consider anakinra for macrophage activation syndrome",
            ],
        },
    }
    return plans.get(min(grade, 4), plans[0])


def get_lymphodepletion_options() -> List[Dict]:
    """Return all available lymphodepletion regimens for frontend."""
    return [
        {
            "key": key,
            "name": reg.name,
            "drugs": reg.drugs,
            "duration_days": reg.duration_days,
            "infection_risk": reg.infection_risk,
            "lymphocyte_kill_pct": reg.lymphocyte_kill_pct,
        }
        for key, reg in LYMPHODEPLETION_REGIMENS.items()
    ]
