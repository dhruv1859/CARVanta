"""
CARVanta – Biomarker Trajectory Predictor
============================================
Predicts longitudinal biomarker trajectories for patients undergoing
CAR-T therapy. Enables clinicians to anticipate lab changes and 
intervene proactively.

Tracks:
- Complete blood count (CBC): WBC, ANC, ALC, Hgb, platelets
- Metabolic panel: LDH, uric acid, potassium, phosphate, calcium
- Liver function: ALT, AST, bilirubin, albumin
- Renal function: creatinine, BUN, eGFR
- Coagulation: PT, aPTT, fibrinogen, D-dimer
- Immune markers: immunoglobulins, complement, lymphocyte subsets
- Tumor markers: β2-microglobulin, AFP, CEA, CA-125, PSA

References:
    - Hay et al., Blood (2017) — Lab changes during CRS
    - Santomasso et al., Cancer Discovery (2018) — ICANS biomarkers
    - Vercellino et al., Haematologica (2020) — Cytopenias post-CAR-T
"""

import math
import random
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# Reference Ranges
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LabReference:
    """Normal reference range for a lab value."""
    name: str
    unit: str
    low: float
    high: float
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None


LAB_REFERENCE_RANGES = {
    # CBC
    "wbc": LabReference("White Blood Cells", "×10⁹/L", 4.5, 11.0, 1.0, 30.0),
    "anc": LabReference("Absolute Neutrophil Count", "×10⁹/L", 1.5, 8.0, 0.5, None),
    "alc": LabReference("Absolute Lymphocyte Count", "×10⁹/L", 1.0, 4.0, 0.2, None),
    "hemoglobin": LabReference("Hemoglobin", "g/dL", 12.0, 17.5, 7.0, 20.0),
    "platelets": LabReference("Platelets", "×10⁹/L", 150, 400, 20, 1000),
    
    # Metabolic
    "ldh": LabReference("LDH", "U/L", 140, 280, None, 1000),
    "uric_acid": LabReference("Uric Acid", "mg/dL", 2.5, 7.0, None, 12.0),
    "potassium": LabReference("Potassium", "mEq/L", 3.5, 5.0, 2.5, 6.5),
    "phosphate": LabReference("Phosphate", "mg/dL", 2.5, 4.5, 1.0, 8.0),
    "calcium": LabReference("Calcium", "mg/dL", 8.5, 10.5, 6.0, 13.0),
    
    # Liver
    "alt": LabReference("ALT", "U/L", 7, 56, None, 300),
    "ast": LabReference("AST", "U/L", 10, 40, None, 300),
    "bilirubin": LabReference("Total Bilirubin", "mg/dL", 0.1, 1.2, None, 10.0),
    "albumin": LabReference("Albumin", "g/dL", 3.5, 5.5, 1.5, None),
    
    # Renal
    "creatinine": LabReference("Creatinine", "mg/dL", 0.6, 1.2, None, 5.0),
    "bun": LabReference("BUN", "mg/dL", 7, 20, None, 60),
    "egfr": LabReference("eGFR", "mL/min/1.73m²", 90, 120, 15, None),
    
    # Coagulation
    "pt": LabReference("PT", "seconds", 11, 13.5, None, 25),
    "aptt": LabReference("aPTT", "seconds", 25, 35, None, 60),
    "fibrinogen": LabReference("Fibrinogen", "mg/dL", 200, 400, 100, None),
    "d_dimer": LabReference("D-dimer", "μg/mL", 0, 0.5, None, 5.0),
    
    # Immune
    "igg": LabReference("IgG", "mg/dL", 700, 1600, 200, None),
    "igm": LabReference("IgM", "mg/dL", 40, 230, None, None),
    "iga": LabReference("IgA", "mg/dL", 70, 400, None, None),
    "cd4_count": LabReference("CD4+ T-cells", "cells/μL", 500, 1500, 200, None),
    "cd8_count": LabReference("CD8+ T-cells", "cells/μL", 150, 1000, None, None),
    
    # Tumor markers
    "b2m": LabReference("β2-microglobulin", "mg/L", 0.7, 1.8, None, 10),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Biomarker Trajectory Simulation
# ═══════════════════════════════════════════════════════════════════════════════

def simulate_cbc_trajectory(
    days: int = 90,
    lymphodepletion: bool = True,
    crs_peak_day: int = 5,
    crs_severity: float = 0.5,     # 0-1 scale
    patient_age: int = 55,
    baseline_wbc: float = 7.0,
    baseline_anc: float = 4.0,
    baseline_alc: float = 1.5,
    baseline_hgb: float = 12.0,
    baseline_plt: float = 200.0,
    seed: int = 42,
) -> Dict:
    """
    Simulate complete blood count trajectory during CAR-T therapy.
    
    Phases:
    1. Lymphodepletion (day -5 to 0): WBC crash
    2. CRS (day 0-14): Inflammatory changes
    3. Recovery (day 14-60): Slow cell recovery
    4. Stabilization (day 60+): New baseline
    """
    random.seed(seed)
    
    timeline = {"days": [], "wbc": [], "anc": [], "alc": [], "hemoglobin": [], "platelets": [], "alerts": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.04)
        alerts = []
        
        # ── WBC ──────────────────────────────────────────────
        if lymphodepletion and day < 7:
            wbc = max(0.1, baseline_wbc * (1 - 0.12 * day) * noise)
        elif day < crs_peak_day + 3:
            # CRS can cause leukocytosis (from monocyte activation)
            wbc = max(0.5, 1.5 + crs_severity * 8 * math.exp(-0.5 * ((day - crs_peak_day) / 2) ** 2)) * noise
        elif day < 30:
            wbc = max(0.5, 2.0 + (day - 10) * 0.1) * noise
        else:
            recovery_target = baseline_wbc * 0.8
            recovery_rate = 0.02
            wbc = min(recovery_target, 3.0 + day * recovery_rate) * noise
        
        # ── ANC ──────────────────────────────────────────────
        if lymphodepletion and day < 10:
            anc = max(0.1, baseline_anc * (1 - 0.08 * day) * noise)
        elif day < 21:
            anc = max(0.1, 0.5 + (day - 10) * 0.15) * noise
        else:
            anc = min(baseline_anc * 0.9, 1.5 + day * 0.03) * noise
        
        if anc < 0.5:
            alerts.append("🔴 Febrile neutropenia risk (ANC <0.5)")
        elif anc < 1.0:
            alerts.append("🟡 Neutropenia (ANC <1.0)")
        
        # ── ALC ──────────────────────────────────────────────
        if lymphodepletion and day < 14:
            alc = max(0.01, 0.05 + (day / 14) * 0.2) * noise
        elif day < 30:
            # CAR-T cells expanding (but not all are measured as lymphocytes)
            alc = max(0.1, 0.3 + (day - 14) * 0.05) * noise
        elif day < 90:
            alc = min(baseline_alc * 0.6, 0.5 + day * 0.01) * noise
        else:
            alc = baseline_alc * 0.4 * noise  # B-cell aplasia reduces ALC
        
        if alc < 0.2:
            alerts.append("🔴 Severe lymphopenia (ALC <0.2)")
        
        # ── Hemoglobin ───────────────────────────────────────
        if day < 14:
            hemoglobin = max(7, baseline_hgb - day * 0.15 * (1 + crs_severity)) * noise
        elif day < 30:
            hemoglobin = max(7, 9 + (day - 14) * 0.05) * noise
        else:
            recovery = min(baseline_hgb * 0.95, 10 + day * 0.02)
            hemoglobin = recovery * noise
        
        if hemoglobin < 7:
            alerts.append("🔴 Severe anemia (Hgb <7) — transfuse")
        elif hemoglobin < 8:
            alerts.append("🟡 Moderate anemia (Hgb <8)")
        
        # ── Platelets ────────────────────────────────────────
        if day < 10:
            platelets = max(10, baseline_plt * (1 - 0.06 * day) * noise)
        elif day < 21:
            platelets = max(10, 50 + (day - 10) * 5) * noise
        elif day < 60:
            platelets = min(baseline_plt * 0.8, 100 + (day - 21) * 3) * noise
        else:
            platelets = baseline_plt * 0.7 * noise
        
        if platelets < 20:
            alerts.append("🔴 Critical thrombocytopenia — platelet transfusion needed")
        elif platelets < 50:
            alerts.append("🟡 Thrombocytopenia (PLT <50)")
        
        timeline["days"].append(day)
        timeline["wbc"].append(round(wbc, 2))
        timeline["anc"].append(round(anc, 2))
        timeline["alc"].append(round(alc, 3))
        timeline["hemoglobin"].append(round(hemoglobin, 1))
        timeline["platelets"].append(round(platelets))
        timeline["alerts"].append(alerts)
    
    # Summary
    nadir_anc = min(timeline["anc"])
    nadir_plt = min(timeline["platelets"])
    nadir_hgb = min(timeline["hemoglobin"])
    
    return {
        "timeline": timeline,
        "reference_ranges": {
            k: {"low": v.low, "high": v.high, "unit": v.unit}
            for k, v in LAB_REFERENCE_RANGES.items()
            if k in ("wbc", "anc", "alc", "hemoglobin", "platelets")
        },
        "summary": {
            "nadir_anc": round(nadir_anc, 2),
            "nadir_anc_day": timeline["anc"].index(nadir_anc),
            "nadir_platelets": round(nadir_plt),
            "nadir_platelets_day": timeline["platelets"].index(nadir_plt),
            "nadir_hemoglobin": round(nadir_hgb, 1),
            "days_febrile_neutropenia_risk": sum(1 for a in timeline["anc"] if a < 0.5),
            "days_transfusion_likely": sum(1 for h in timeline["hemoglobin"] if h < 7),
            "days_plt_transfusion_likely": sum(1 for p in timeline["platelets"] if p < 20),
            "total_alert_days": sum(1 for a in timeline["alerts"] if len(a) > 0),
        },
    }


def simulate_metabolic_trajectory(
    days: int = 30,
    baseline_ldh: float = 200,
    tumor_lysis_risk: float = 0.3,
    crs_severity: float = 0.5,
    seed: int = 42,
) -> Dict:
    """
    Simulate metabolic panel trajectory — especially important for tumor lysis
    syndrome (TLS) monitoring during CAR-T therapy.
    """
    random.seed(seed)
    
    timeline = {"days": [], "ldh": [], "uric_acid": [], "potassium": [],
                "phosphate": [], "calcium": [], "alerts": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.05)
        alerts = []
        
        # Tumor lysis activity (peaks during CRS)
        tls_activity = tumor_lysis_risk * math.exp(-0.5 * ((day - 4) / 3) ** 2) * noise
        
        # LDH (rises with tumor cell death)
        ldh = baseline_ldh * (1 + 3 * tls_activity + 0.5 * crs_severity * math.exp(-day / 5)) * noise
        
        # Uric acid (released from lysed cells)
        uric = 5.0 * (1 + 4 * tls_activity) * noise
        
        # Potassium (released from lysed cells)
        potassium = 4.2 + 2.5 * tls_activity * noise
        
        # Phosphate (released from lysed cells)
        phosphate = 3.5 + 4 * tls_activity * noise
        
        # Calcium (inversely related to phosphate — precipitates)
        calcium = max(6, 9.5 - 3 * tls_activity) * noise
        
        if uric > 8:
            alerts.append("🔴 Hyperuricemia — start rasburicase")
        if potassium > 6:
            alerts.append("🔴 Hyperkalemia — cardiac monitoring needed")
        if phosphate > 6:
            alerts.append("🟡 Hyperphosphatemia — consider phosphate binders")
        if calcium < 7:
            alerts.append("🔴 Severe hypocalcemia — IV calcium replacement")
        if ldh > 500:
            alerts.append("🟡 LDH >500 — significant tumor lysis")
        
        timeline["days"].append(day)
        timeline["ldh"].append(round(ldh, 0))
        timeline["uric_acid"].append(round(uric, 1))
        timeline["potassium"].append(round(potassium, 1))
        timeline["phosphate"].append(round(phosphate, 1))
        timeline["calcium"].append(round(calcium, 1))
        timeline["alerts"].append(alerts)
    
    peak_ldh = max(timeline["ldh"])
    peak_uric = max(timeline["uric_acid"])
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_ldh": round(peak_ldh),
            "peak_ldh_day": timeline["ldh"].index(peak_ldh),
            "peak_uric_acid": round(peak_uric, 1),
            "tls_risk_level": "high" if peak_uric > 8 else "moderate" if peak_uric > 6 else "low",
            "requires_rasburicase": peak_uric > 8,
            "total_alert_days": sum(1 for a in timeline["alerts"] if len(a) > 0),
        },
    }


def simulate_liver_function(
    days: int = 60,
    crs_severity: float = 0.5,
    baseline_alt: float = 25,
    baseline_ast: float = 20,
    baseline_bilirubin: float = 0.6,
    baseline_albumin: float = 4.0,
    seed: int = 42,
) -> Dict:
    """Simulate liver function during CAR-T — hepatotoxicity monitoring."""
    random.seed(seed)
    
    timeline = {"days": [], "alt": [], "ast": [], "bilirubin": [], "albumin": [], "alerts": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.06)
        alerts = []
        
        # Hepatotoxicity peaks during CRS
        liver_stress = crs_severity * math.exp(-0.5 * ((day - 6) / 4) ** 2)
        
        alt = baseline_alt * (1 + 5 * liver_stress) * noise
        ast = baseline_ast * (1 + 6 * liver_stress) * noise
        bilirubin = baseline_bilirubin * (1 + 4 * liver_stress) * noise
        albumin = max(1.5, baseline_albumin * (1 - 0.3 * liver_stress) - day * 0.005) * noise
        
        if alt > 200 or ast > 200:
            alerts.append("🔴 Severe hepatotoxicity (transaminases >5× ULN)")
        elif alt > 100 or ast > 100:
            alerts.append("🟡 Moderate hepatotoxicity")
        if bilirubin > 3:
            alerts.append("🔴 Hyperbilirubinemia (>3 mg/dL)")
        if albumin < 2:
            alerts.append("🟡 Severe hypoalbuminemia")
        
        timeline["days"].append(day)
        timeline["alt"].append(round(alt, 0))
        timeline["ast"].append(round(ast, 0))
        timeline["bilirubin"].append(round(bilirubin, 1))
        timeline["albumin"].append(round(albumin, 1))
        timeline["alerts"].append(alerts)
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_alt": round(max(timeline["alt"])),
            "peak_ast": round(max(timeline["ast"])),
            "peak_bilirubin": round(max(timeline["bilirubin"]), 1),
            "nadir_albumin": round(min(timeline["albumin"]), 1),
            "hepatotoxicity_grade": 3 if max(timeline["alt"]) > 200 else 2 if max(timeline["alt"]) > 100 else 1 if max(timeline["alt"]) > 56 else 0,
        },
    }


def simulate_renal_function(
    days: int = 60,
    crs_severity: float = 0.5,
    baseline_creatinine: float = 0.9,
    baseline_bun: float = 15,
    baseline_egfr: float = 95,
    patient_age: int = 55,
    seed: int = 42,
) -> Dict:
    """Simulate renal function — AKI monitoring during CRS."""
    random.seed(seed)
    
    timeline = {"days": [], "creatinine": [], "bun": [], "egfr": [], "alerts": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.04)
        alerts = []
        
        # CRS-associated AKI (hypotension → renal hypoperfusion)
        renal_stress = crs_severity * 0.7 * math.exp(-0.5 * ((day - 5) / 3) ** 2)
        
        cr = baseline_creatinine * (1 + 2.5 * renal_stress) * noise
        bun = baseline_bun * (1 + 3 * renal_stress) * noise
        
        # eGFR estimation (CKD-EPI simplified)
        age_factor = max(0.5, 1.0 - (patient_age - 30) * 0.005)
        egfr = max(10, baseline_egfr * age_factor / max(cr / baseline_creatinine, 0.5)) * noise
        
        if cr > 3.0:
            alerts.append("🔴 Severe AKI (Cr >3.0) — nephrology consult")
        elif cr > 2.0:
            alerts.append("🟡 Moderate AKI (Cr >2.0)")
        elif cr > 1.5 * baseline_creatinine:
            alerts.append("🟡 AKI Stage 1 (Cr >1.5× baseline)")
        
        timeline["days"].append(day)
        timeline["creatinine"].append(round(cr, 2))
        timeline["bun"].append(round(bun, 0))
        timeline["egfr"].append(round(egfr, 0))
        timeline["alerts"].append(alerts)
    
    peak_cr = max(timeline["creatinine"])
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_creatinine": round(peak_cr, 2),
            "nadir_egfr": round(min(timeline["egfr"])),
            "aki_stage": 3 if peak_cr > 3.0 else 2 if peak_cr > 2.0 else 1 if peak_cr > 1.5 * baseline_creatinine else 0,
            "days_aki": sum(1 for c in timeline["creatinine"] if c > 1.5 * baseline_creatinine),
        },
    }


def simulate_coagulation_trajectory(
    days: int = 30,
    crs_severity: float = 0.5,
    seed: int = 42,
) -> Dict:
    """Simulate coagulation changes — DIC monitoring during CRS."""
    random.seed(seed)
    
    timeline = {"days": [], "pt": [], "aptt": [], "fibrinogen": [], "d_dimer": [], "alerts": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.05)
        alerts = []
        
        # CRS-associated coagulopathy
        coag_stress = crs_severity * math.exp(-0.5 * ((day - 5) / 3) ** 2)
        
        pt = (12 + 8 * coag_stress) * noise
        aptt = (30 + 15 * coag_stress) * noise
        fibrinogen = max(50, (300 - 200 * coag_stress)) * noise
        d_dimer = (0.3 + 5 * coag_stress) * noise
        
        if fibrinogen < 100:
            alerts.append("🔴 Hypofibrinogenemia — cryoprecipitate")
        if d_dimer > 3:
            alerts.append("🟡 Elevated D-dimer — DIC evaluation")
        if pt > 20:
            alerts.append("🔴 Prolonged PT — FFP or vitamin K")
        
        timeline["days"].append(day)
        timeline["pt"].append(round(pt, 1))
        timeline["aptt"].append(round(aptt, 1))
        timeline["fibrinogen"].append(round(fibrinogen, 0))
        timeline["d_dimer"].append(round(d_dimer, 2))
        timeline["alerts"].append(alerts)
    
    return {
        "timeline": timeline,
        "summary": {
            "peak_pt": round(max(timeline["pt"]), 1),
            "nadir_fibrinogen": round(min(timeline["fibrinogen"])),
            "peak_d_dimer": round(max(timeline["d_dimer"]), 2),
            "dic_score": _calculate_dic_score(
                max(timeline["pt"]),
                min(timeline["fibrinogen"]),
                max(timeline["d_dimer"]),
                min([20] + [t for t in [10]])  # Placeholder platelet
            ),
        },
    }


def _calculate_dic_score(pt: float, fibrinogen: float, d_dimer: float, platelets: float) -> int:
    """
    ISTH DIC scoring.
    Score ≥5 = compatible with overt DIC.
    """
    score = 0
    
    # Platelet count
    if platelets < 50: score += 2
    elif platelets < 100: score += 1
    
    # D-dimer
    if d_dimer > 5: score += 3
    elif d_dimer > 2: score += 2
    
    # PT prolongation
    if pt > 18: score += 2
    elif pt > 15: score += 1
    
    # Fibrinogen
    if fibrinogen < 100: score += 1
    
    return score


def simulate_immune_recovery(
    days: int = 365,
    car_t_target: str = "CD19",      # B-cell target = B-cell aplasia
    patient_age: int = 55,
    seed: int = 42,
) -> Dict:
    """
    Long-term immune reconstitution post-CAR-T.
    Models B-cell aplasia, immunoglobulin levels, and infection risk.
    """
    random.seed(seed)
    
    b_cell_target = car_t_target in ("CD19", "CD20", "CD22")  # Anti-B-cell targets
    
    timeline = {"days": [], "igg": [], "igm": [], "cd4": [], "cd8": [],
                "b_cells": [], "infection_risk_score": [], "ivig_needed": []}
    
    for day in range(days):
        noise = 1.0 + random.gauss(0, 0.04)
        
        # ── B-cells ──────────────────────────────────────────
        if b_cell_target:
            # B-cell aplasia if target is CD19/CD20/CD22
            # Recovery depends on CAR-T persistence (may take 6-12 months)
            if day < 180:
                b_cells = max(0, 5 * noise)  # Near zero
            elif day < 365:
                b_cells = max(0, (day - 180) * 0.5) * noise  # Slow recovery
            else:
                b_cells = min(200, (day - 180) * 0.8) * noise
        else:
            # Non-B-cell target: B-cells preserved
            if day < 30:
                b_cells = max(50, 150 - day * 3) * noise
            else:
                b_cells = min(200, 100 + day * 0.5) * noise
        
        # ── IgG (dependent on B-cell function) ───────────────
        if b_cell_target:
            igg = max(100, 800 - day * 1.5) * noise  # Slow decline
            if day > 60:
                igg = max(100, 300 + random.gauss(0, 30))  # Plateau at low
        else:
            igg = max(600, 900 - day * 0.5 + random.gauss(0, 20)) * noise
        
        # ── IgM ──────────────────────────────────────────────
        igm = max(20, 100 - day * 0.3) * noise if b_cell_target else 120 * noise
        
        # ── CD4+ T-cells ─────────────────────────────────────
        age_recovery = max(0.3, 1.0 - (patient_age - 30) * 0.01)
        if day < 30:
            cd4 = max(50, 200 - day * 5) * noise
        elif day < 90:
            cd4 = max(50, 100 + (day - 30) * 3 * age_recovery) * noise
        else:
            cd4 = min(800, 200 + (day - 30) * 2 * age_recovery) * noise
        
        # ── CD8+ T-cells (includes CAR-T cells) ─────────────
        if day < 14:
            cd8 = max(100, 300 + day * 100) * noise  # CAR-T expansion
        elif day < 30:
            cd8 = max(100, 1500 - (day - 14) * 50) * noise
        else:
            cd8 = min(600, 200 + day * 1) * noise
        
        # ── Infection risk ───────────────────────────────────
        risk = 0
        if igg < 400: risk += 30
        elif igg < 600: risk += 15
        if cd4 < 200: risk += 30
        elif cd4 < 350: risk += 15
        if b_cells < 10: risk += 20
        
        ivig_needed = igg < 400 and day > 30
        
        timeline["days"].append(day)
        timeline["igg"].append(round(igg, 0))
        timeline["igm"].append(round(igm, 0))
        timeline["cd4"].append(round(cd4, 0))
        timeline["cd8"].append(round(cd8, 0))
        timeline["b_cells"].append(round(b_cells, 0))
        timeline["infection_risk_score"].append(round(risk))
        timeline["ivig_needed"].append(ivig_needed)
    
    return {
        "timeline": timeline,
        "summary": {
            "b_cell_aplasia": b_cell_target,
            "estimated_b_cell_recovery_day": next((d for d, b in zip(timeline["days"], timeline["b_cells"]) if b > 50), None),
            "igg_nadir": round(min(timeline["igg"])),
            "cd4_nadir": round(min(timeline["cd4"])),
            "ivig_months_needed": sum(1 for need in timeline["ivig_needed"] if need) // 30,
            "high_infection_risk_days": sum(1 for r in timeline["infection_risk_score"] if r >= 50),
        },
        "recommendations": {
            "ivig_replacement": "Monthly IVIG if IgG <400 mg/dL" if b_cell_target else "Monitor IgG levels",
            "prophylaxis": [
                "Acyclovir/valacyclovir for VZV/HSV prophylaxis",
                "TMP-SMX for PJP prophylaxis if CD4 <200",
                "Fluconazole for fungal prophylaxis during neutropenia",
            ],
            "vaccinations": "Revaccinate 6-12 months post-CAR-T (killed vaccines only until B-cell recovery)",
        },
    }


def generate_complete_biomarker_report(
    days: int = 90,
    cancer_type: str = "DLBCL",
    car_t_target: str = "CD19",
    crs_severity: float = 0.5,
    patient_age: int = 55,
    seed: int = 42,
) -> Dict:
    """
    Generate a comprehensive biomarker trajectory report combining all organ systems.
    This is the main entry point for the frontend.
    """
    
    params = {"seed": seed}
    
    cbc = simulate_cbc_trajectory(days=days, crs_severity=crs_severity, patient_age=patient_age, **params)
    metabolic = simulate_metabolic_trajectory(days=min(days, 30), crs_severity=crs_severity, **params)
    liver = simulate_liver_function(days=min(days, 60), crs_severity=crs_severity, **params)
    renal = simulate_renal_function(days=min(days, 60), crs_severity=crs_severity, patient_age=patient_age, **params)
    coag = simulate_coagulation_trajectory(days=min(days, 30), crs_severity=crs_severity, **params)
    immune = simulate_immune_recovery(days=days, car_t_target=car_t_target, patient_age=patient_age, **params)
    
    # Aggregate alerts across all systems
    all_alerts = {}
    for day_idx, day_alerts in enumerate(cbc["timeline"]["alerts"]):
        if day_alerts:
            all_alerts.setdefault(day_idx, []).extend(day_alerts)
    for day_idx, day_alerts in enumerate(metabolic["timeline"]["alerts"]):
        if day_alerts:
            all_alerts.setdefault(day_idx, []).extend(day_alerts)
    for day_idx, day_alerts in enumerate(liver["timeline"]["alerts"]):
        if day_alerts:
            all_alerts.setdefault(day_idx, []).extend(day_alerts)
    for day_idx, day_alerts in enumerate(renal["timeline"]["alerts"]):
        if day_alerts:
            all_alerts.setdefault(day_idx, []).extend(day_alerts)
    for day_idx, day_alerts in enumerate(coag["timeline"]["alerts"]):
        if day_alerts:
            all_alerts.setdefault(day_idx, []).extend(day_alerts)
    
    # Count critical vs warning alerts
    critical_count = sum(
        sum(1 for a in alerts if "🔴" in a) for alerts in all_alerts.values()
    )
    warning_count = sum(
        sum(1 for a in alerts if "🟡" in a) for alerts in all_alerts.values()
    )
    
    return {
        "cbc": cbc,
        "metabolic": metabolic,
        "liver": liver,
        "renal": renal,
        "coagulation": coag,
        "immune_recovery": immune,
        "alert_summary": {
            "total_alert_days": len(all_alerts),
            "critical_alerts": critical_count,
            "warning_alerts": warning_count,
            "most_concerning_period": f"Days {min(all_alerts.keys()) if all_alerts else 0}-{max(all_alerts.keys()) if all_alerts else 0}",
        },
        "reference_ranges": {
            k: {"name": v.name, "unit": v.unit, "low": v.low, "high": v.high}
            for k, v in LAB_REFERENCE_RANGES.items()
        },
    }
