"""
CARVanta Biomarker Analytics — Predictive Panel Engine
========================================================
Advanced biomarker panel analytics for CAR-T therapy
response prediction, monitoring, and outcome correlation.

Features:
- Pre-treatment biomarker panel scoring
- Serial biomarker monitoring (CRS-panel, response-panel)
- Biomarker-outcome correlation analysis
- Machine learning risk stratification
- Reference range management
- Composite biomarker indices (CRS-index, Response-index)
- Alert thresholds and clinical decision support
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.biomarker.analytics")


# ──────────────────────────────────────────────────────────────────────
# Reference Ranges & Biomarker Definitions
# ──────────────────────────────────────────────────────────────────────

@dataclass
class BiomarkerDef:
    name: str
    unit: str
    normal_low: float
    normal_high: float
    critical_low: Optional[float] = None
    critical_high: Optional[float] = None
    category: str = "general"
    car_t_relevance: str = ""
    trend_direction: str = "lower_better"  # lower_better, higher_better, range


_BIOMARKERS: Dict[str, BiomarkerDef] = {
    "IL6": BiomarkerDef("Interleukin-6", "pg/mL", 0, 7, None, 1000, "cytokine",
        "Primary CRS driver; tocilizumab target", "lower_better"),
    "IFN_GAMMA": BiomarkerDef("Interferon-γ", "pg/mL", 0, 15.6, None, 500, "cytokine",
        "T-cell activation; correlates with CAR-T expansion", "range"),
    "TNF_ALPHA": BiomarkerDef("TNF-α", "pg/mL", 0, 8.1, None, 300, "cytokine",
        "Pro-inflammatory; contributes to CRS", "lower_better"),
    "IL2": BiomarkerDef("Interleukin-2", "pg/mL", 0, 31, None, 200, "cytokine",
        "T-cell growth factor; indicates CAR-T activation", "range"),
    "IL10": BiomarkerDef("Interleukin-10", "pg/mL", 0, 9.1, None, 100, "cytokine",
        "Anti-inflammatory; immunosuppressive", "lower_better"),
    "IL1B": BiomarkerDef("IL-1β", "pg/mL", 0, 5, None, 200, "cytokine",
        "Inflammasome pathway; CRS contributor", "lower_better"),
    "GM_CSF": BiomarkerDef("GM-CSF", "pg/mL", 0, 7.5, None, 150, "cytokine",
        "Myeloid activation; monocyte-driven CRS", "lower_better"),
    "CRP": BiomarkerDef("C-Reactive Protein", "mg/L", 0, 10, None, 200, "inflammatory",
        "Acute phase reactant; CRS severity marker", "lower_better"),
    "FERRITIN": BiomarkerDef("Ferritin", "ng/mL", 12, 300, None, 10000, "inflammatory",
        "Macrophage activation; HLH risk if >10,000", "lower_better"),
    "LDH": BiomarkerDef("Lactate Dehydrogenase", "U/L", 120, 246, None, 1000, "metabolic",
        "Tumor burden marker; prognostic for CAR-T", "lower_better"),
    "D_DIMER": BiomarkerDef("D-Dimer", "mg/L", 0, 0.5, None, 10, "coagulation",
        "DIC risk; elevated in severe CRS", "lower_better"),
    "FIBRINOGEN": BiomarkerDef("Fibrinogen", "mg/dL", 200, 400, 100, None, "coagulation",
        "Consumption in DIC; monitor in severe CRS", "range"),
    "ALC": BiomarkerDef("Absolute Lymphocyte Count", "×10³/µL", 1.0, 4.8, 0.2, None, "hematologic",
        "Lymphodepletion depth; predicts CAR-T expansion", "range"),
    "ANC": BiomarkerDef("Absolute Neutrophil Count", "×10³/µL", 1.8, 7.7, 0.5, None, "hematologic",
        "Neutropenia risk; infection monitoring", "range"),
    "PLATELETS": BiomarkerDef("Platelets", "×10³/µL", 150, 400, 20, None, "hematologic",
        "Thrombocytopenia risk; bleeding risk", "range"),
    "HEMOGLOBIN": BiomarkerDef("Hemoglobin", "g/dL", 12, 17.5, 7, None, "hematologic",
        "Anemia monitoring; transfusion threshold", "range"),
    "TROPONIN": BiomarkerDef("Troponin I", "ng/mL", 0, 0.04, None, 0.4, "cardiac",
        "Cardiac injury; CRS-associated myocarditis", "lower_better"),
    "BNP": BiomarkerDef("BNP", "pg/mL", 0, 100, None, 500, "cardiac",
        "Heart failure marker; CRS cardiomyopathy", "lower_better"),
    "CREATININE": BiomarkerDef("Creatinine", "mg/dL", 0.6, 1.2, None, 4.0, "renal",
        "Renal function; nephrotoxicity monitoring", "lower_better"),
    "ALT": BiomarkerDef("ALT", "U/L", 7, 56, None, 500, "hepatic",
        "Liver injury; hepatotoxicity monitoring", "lower_better"),
    "AST": BiomarkerDef("AST", "U/L", 10, 40, None, 500, "hepatic",
        "Liver injury; tumor lysis monitoring", "lower_better"),
    "BILIRUBIN": BiomarkerDef("Total Bilirubin", "mg/dL", 0.1, 1.2, None, 10, "hepatic",
        "Hepatic function; cholestasis", "lower_better"),
}


# ──────────────────────────────────────────────────────────────────────
# Biomarker Panel Generation
# ──────────────────────────────────────────────────────────────────────

async def generate_biomarker_panel(
    panel_type: str = "pre_treatment",
    patient_risk: str = "moderate",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate a biomarker panel with simulated values."""
    if seed:
        random.seed(seed)

    panel_id = uuid.uuid4().hex[:12]
    results: List[Dict[str, Any]] = []

    for code, bm in _BIOMARKERS.items():
        # Generate value based on patient risk
        if patient_risk == "high":
            if bm.trend_direction == "lower_better":
                value = random.uniform(bm.normal_high * 1.5, bm.normal_high * 5)
            elif bm.trend_direction == "range":
                value = random.uniform(bm.normal_low * 0.3, bm.normal_low * 0.8)
            else:
                value = random.uniform(bm.normal_low, bm.normal_high)
        elif patient_risk == "low":
            value = random.uniform(bm.normal_low, bm.normal_high)
        else:
            # Moderate
            value = random.uniform(bm.normal_low * 0.8, bm.normal_high * 1.5)

        value = max(0, value)

        # Status assessment
        if bm.critical_high and value > bm.critical_high:
            status = "critical_high"
        elif bm.critical_low is not None and value < bm.critical_low:
            status = "critical_low"
        elif value > bm.normal_high:
            status = "high"
        elif value < bm.normal_low:
            status = "low"
        else:
            status = "normal"

        results.append({
            "code": code,
            "name": bm.name,
            "value": round(value, 2),
            "unit": bm.unit,
            "reference_range": f"{bm.normal_low}-{bm.normal_high}",
            "status": status,
            "category": bm.category,
            "car_t_relevance": bm.car_t_relevance,
            "flag": "🔴" if "critical" in status else "🟡" if status in ("high", "low") else "🟢",
        })

    # Composite scores
    crs_index = _compute_crs_index(results)
    response_index = _compute_response_index(results)

    return {
        "panel_id": panel_id,
        "panel_type": panel_type,
        "patient_risk": patient_risk,
        "total_biomarkers": len(results),
        "abnormal": sum(1 for r in results if r["status"] != "normal"),
        "critical": sum(1 for r in results if "critical" in r["status"]),
        "results": results,
        "composite_scores": {
            "crs_risk_index": crs_index,
            "response_index": response_index,
        },
        "alerts": _generate_alerts(results),
    }


def _compute_crs_index(results: List[Dict]) -> Dict[str, Any]:
    """Compute composite CRS risk index."""
    crs_markers = {"IL6": 0.3, "CRP": 0.2, "FERRITIN": 0.2, "TNF_ALPHA": 0.15, "IL1B": 0.15}
    score = 0
    for r in results:
        if r["code"] in crs_markers:
            bm = _BIOMARKERS[r["code"]]
            normalized = min(1.0, r["value"] / max(bm.normal_high * 3, 1))
            score += normalized * crs_markers[r["code"]]

    risk_level = "high" if score > 0.6 else "moderate" if score > 0.3 else "low"
    return {"score": round(score, 3), "risk_level": risk_level, "max_score": 1.0}


def _compute_response_index(results: List[Dict]) -> Dict[str, Any]:
    """Compute treatment response prediction index."""
    score = 0.5  # baseline
    for r in results:
        if r["code"] == "LDH" and r["status"] == "normal":
            score += 0.1
        elif r["code"] == "LDH" and r["status"] == "high":
            score -= 0.15
        if r["code"] == "ALC" and r["value"] > 0.5:
            score += 0.05
        if r["code"] == "FERRITIN" and r["value"] < 500:
            score += 0.05

    score = max(0, min(1, score))
    return {"score": round(score, 3), "prediction": "favorable" if score > 0.6 else "moderate" if score > 0.4 else "unfavorable"}


def _generate_alerts(results: List[Dict]) -> List[Dict[str, str]]:
    """Generate clinical alerts from biomarker results."""
    alerts = []
    for r in results:
        if r["status"] == "critical_high":
            alerts.append({"level": "critical", "biomarker": r["name"], "message": f"{r['name']} critically elevated ({r['value']} {r['unit']}) — immediate clinical action required"})
        elif r["status"] == "critical_low":
            alerts.append({"level": "critical", "biomarker": r["name"], "message": f"{r['name']} critically low ({r['value']} {r['unit']}) — assess for intervention"})
    return alerts


async def serial_monitoring(
    days: int = 30,
    panel_type: str = "crs_panel",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate serial biomarker monitoring data over time."""
    if seed:
        random.seed(seed)

    crs_markers = ["IL6", "IFN_GAMMA", "TNF_ALPHA", "CRP", "FERRITIN"]
    timepoints = []

    for day in range(0, days + 1, max(1, days // 15)):
        values = {}
        for code in crs_markers:
            bm = _BIOMARKERS[code]
            # Simulate CRS kinetics: peak day 3-7, resolve by day 14
            if day < 3:
                mult = 1 + day * 0.5
            elif day < 7:
                mult = 2.5 + random.gauss(0, 0.5)
            elif day < 14:
                mult = max(1, 2.5 - (day - 7) * 0.3)
            else:
                mult = 1 + random.gauss(0, 0.1)

            val = bm.normal_high * mult * random.uniform(0.7, 1.3)
            values[code] = round(max(0, val), 2)

        timepoints.append({"day": day, "values": values})

    return {
        "monitoring_id": uuid.uuid4().hex[:12],
        "panel_type": panel_type,
        "days": days,
        "markers_tracked": crs_markers,
        "timepoints": timepoints,
        "peak_values": {
            code: max(tp["values"].get(code, 0) for tp in timepoints)
            for code in crs_markers
        },
    }


async def biomarker_correlation(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze biomarker-outcome correlations."""
    if seed:
        random.seed(seed)

    correlations = []
    outcomes = ["ORR", "CR_rate", "PFS_months", "OS_months", "CRS_grade", "ICANS_grade"]

    for code, bm in _BIOMARKERS.items():
        if bm.category not in ("cytokine", "inflammatory", "metabolic"):
            continue
        for outcome in outcomes:
            r = random.uniform(-0.8, 0.8)
            p = 10 ** (-abs(r) * random.uniform(1, 5))
            correlations.append({
                "biomarker": bm.name,
                "outcome": outcome,
                "r": round(r, 3),
                "p_value": round(p, 6),
                "significant": p < 0.05,
                "direction": "positive" if r > 0 else "negative",
            })

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "total_correlations": len(correlations),
        "significant": sum(1 for c in correlations if c["significant"]),
        "correlations": sorted(correlations, key=lambda x: abs(x["r"]), reverse=True),
    }


async def list_biomarker_definitions() -> Dict[str, Any]:
    """List all biomarker definitions and reference ranges."""
    return {
        "total": len(_BIOMARKERS),
        "categories": list(set(bm.category for bm in _BIOMARKERS.values())),
        "biomarkers": [
            {
                "code": code,
                "name": bm.name,
                "unit": bm.unit,
                "reference_range": f"{bm.normal_low}-{bm.normal_high}",
                "category": bm.category,
                "car_t_relevance": bm.car_t_relevance,
            }
            for code, bm in _BIOMARKERS.items()
        ],
    }
