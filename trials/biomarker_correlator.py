"""
CARVanta Trials — Biomarker Correlation & Companion Diagnostics
=================================================================
Correlate biomarker profiles with clinical trial outcomes
to identify predictive/prognostic markers for CAR-T therapy.

Features:
- Predictive biomarker panel (pre-infusion)
- Pharmacodynamic biomarker tracking (post-infusion)
- Cytokine kinetics modeling (IL-6, IFN-γ, ferritin, CRP)
- CAR-T expansion correlation with response
- Biomarker-response association analysis
- Companion diagnostic test panel design
- Liquid biopsy integration (ctDNA, MRD)
- Immune reconstitution monitoring
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.biomarker_correlator")


# ──────────────────────────────────────────────────────────────────────
# Pre-Infusion Biomarker Panel
# ──────────────────────────────────────────────────────────────────────

_PRE_INFUSION_PANEL = {
    "LDH": {
        "name": "Lactate Dehydrogenase",
        "unit": "U/L",
        "normal_range": [120, 246],
        "prognostic": True,
        "association": "Elevated LDH associated with lower CR rate (OR 0.45) and shorter PFS",
        "threshold": {"favorable": "<ULN", "unfavorable": ">2× ULN"},
    },
    "CRP": {
        "name": "C-Reactive Protein",
        "unit": "mg/L",
        "normal_range": [0, 10],
        "prognostic": True,
        "association": "Baseline CRP >50 mg/L associated with higher CRS severity",
        "threshold": {"low_risk": "<10", "moderate_risk": "10-50", "high_risk": ">50"},
    },
    "ferritin": {
        "name": "Serum Ferritin",
        "unit": "ng/mL",
        "normal_range": [12, 300],
        "prognostic": True,
        "association": "Ferritin >1000 ng/mL pre-infusion associated with Grade ≥3 CRS (OR 2.8)",
        "threshold": {"low_risk": "<500", "high_risk": ">1000"},
    },
    "IL6": {
        "name": "Interleukin-6",
        "unit": "pg/mL",
        "normal_range": [0, 7],
        "prognostic": True,
        "association": "Pre-infusion IL-6 >10 pg/mL predicts early CRS onset",
        "threshold": {"normal": "<7", "elevated": ">10"},
    },
    "tumor_burden": {
        "name": "Tumor Burden (SPD)",
        "unit": "cm²",
        "normal_range": [0, 0],
        "prognostic": True,
        "association": "High tumor burden (SPD >50 cm²) associated with CRS severity but also higher CR rates with CD19 CAR-T",
        "threshold": {"low": "<20", "moderate": "20-50", "high": ">50"},
    },
    "ALC": {
        "name": "Absolute Lymphocyte Count",
        "unit": "cells/μL",
        "normal_range": [1000, 4800],
        "prognostic": True,
        "association": "Pre-LD ALC predicts CAR-T expansion; higher ALC → better product quality",
        "threshold": {"low": "<500", "adequate": "≥500"},
    },
    "CD4_CD8_ratio": {
        "name": "CD4:CD8 T-cell Ratio",
        "unit": "ratio",
        "normal_range": [1.0, 2.5],
        "prognostic": True,
        "association": "CD4:CD8 ratio >1 in apheresis product associated with better CAR-T expansion",
        "threshold": {"favorable": ">1", "unfavorable": "<0.5"},
    },
    "b2_microglobulin": {
        "name": "β2-Microglobulin",
        "unit": "mg/L",
        "normal_range": [0.7, 1.8],
        "prognostic": True,
        "association": "Elevated β2M reflects tumor burden and immune activation",
        "threshold": {"normal": "<3.5", "elevated": ">5.5"},
    },
}


# ──────────────────────────────────────────────────────────────────────
# Post-Infusion Pharmacodynamic Biomarkers
# ──────────────────────────────────────────────────────────────────────

_PD_BIOMARKERS = {
    "CAR_T_expansion": {
        "name": "CAR-T Cell Expansion",
        "peak_day": "Day 7-14",
        "assay": "Flow cytometry / qPCR",
        "response_correlation": "Cmax >50 cells/μL strongly associated with CR (p<0.001)",
        "kinetics": {
            "expansion": "Days 0-14 (exponential growth)",
            "contraction": "Days 14-28 (decline phase)",
            "persistence": "Day 28+ (plateau if durable response)",
        },
    },
    "cytokine_storm": {
        "name": "CRS Cytokine Panel",
        "peak_day": "Day 1-7",
        "markers": ["IL-6", "IL-10", "IFN-γ", "TNF-α", "IL-1β", "GM-CSF"],
        "assay": "Multiplex cytokine assay (Luminex/MSD)",
        "correlation": "Peak IL-6 >1000 pg/mL associated with Grade ≥3 CRS",
    },
    "b_cell_aplasia": {
        "name": "B-Cell Aplasia",
        "onset": "Day 7-14",
        "duration": "6-12 months (if durable response)",
        "assay": "Flow cytometry (CD19+/CD20+ B-cells)",
        "significance": "Persistence of B-cell aplasia is an on-target PD marker; loss of BCA may indicate CAR-T exhaustion or antigen escape",
    },
    "MRD": {
        "name": "Minimal Residual Disease",
        "sensitivity": "10⁻⁴ to 10⁻⁶",
        "assays": ["Multiparameter flow cytometry (≥10⁻⁴)", "NGS (clonoSEQ, ≥10⁻⁶)", "PCR-based (≥10⁻⁵)"],
        "timepoints": ["Day 28", "Month 3", "Month 6", "Month 12"],
        "correlation": "MRD negativity at Month 3 predicts durable remission (PFS HR 0.15)",
    },
    "ctDNA": {
        "name": "Circulating Tumor DNA",
        "assay": "Targeted NGS panel or ddPCR",
        "significance": "Rapid ctDNA clearance (Day 7-14) associated with deeper responses",
        "timepoints": ["Baseline", "Day 7", "Day 14", "Day 28", "Month 3"],
    },
}


async def biomarker_panel(panel_type: str = "pre_infusion") -> Dict[str, Any]:
    """Get biomarker panel specifications."""
    if panel_type == "pre_infusion":
        return {
            "panel_type": "Pre-Infusion Predictive Panel",
            "total_markers": len(_PRE_INFUSION_PANEL),
            "markers": _PRE_INFUSION_PANEL,
        }
    elif panel_type == "pharmacodynamic":
        return {
            "panel_type": "Post-Infusion Pharmacodynamic Panel",
            "total_markers": len(_PD_BIOMARKERS),
            "markers": _PD_BIOMARKERS,
        }
    return {"error": f"Unknown panel type: {panel_type}"}


async def simulate_cytokine_kinetics(
    crs_grade: int = 2,
    n_days: int = 28,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Simulate cytokine kinetics based on CRS grade."""
    if seed:
        random.seed(seed)

    # Peak multipliers by CRS grade
    peak_mult = {0: 1, 1: 5, 2: 20, 3: 100, 4: 500}
    mult = peak_mult.get(crs_grade, 10)
    peak_day = max(1, random.randint(2, 5))

    cytokines = {}
    for marker, baseline in [("IL6", 5), ("IL10", 3), ("IFNg", 2), ("TNFa", 1), ("CRP", 8), ("ferritin", 200)]:
        trajectory = []
        for day in range(n_days + 1):
            if day <= peak_day:
                # Exponential rise
                val = baseline * (1 + (mult - 1) * (day / peak_day) ** 2)
            elif day <= peak_day + 5:
                # Rapid decline (post-tocilizumab if given)
                decay_factor = 0.5 if crs_grade >= 2 else 0.3
                val = baseline * mult * math.exp(-decay_factor * (day - peak_day))
            else:
                # Gradual return to baseline
                val = baseline * (1 + max(0, mult * 0.05 * math.exp(-0.1 * (day - peak_day - 5))))

            # Add noise
            val *= random.uniform(0.85, 1.15)
            trajectory.append({"day": day, "value": round(max(0, val), 1)})

        cytokines[marker] = {
            "baseline": baseline,
            "peak_value": round(max(t["value"] for t in trajectory), 1),
            "peak_day": peak_day,
            "trajectory": trajectory,
            "unit": "pg/mL" if marker not in ("CRP", "ferritin") else ("mg/L" if marker == "CRP" else "ng/mL"),
        }

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "crs_grade": crs_grade,
        "n_days": n_days,
        "cytokines": cytokines,
    }


async def car_t_expansion_correlation(
    n_patients: int = 80,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Correlate CAR-T expansion kinetics with clinical response."""
    if seed:
        random.seed(seed)

    patients = []
    for i in range(n_patients):
        # CAR-T Cmax (peak expansion)
        cmax = round(random.lognormvariate(math.log(30), 0.8), 1)

        # Response correlates with expansion
        response_prob = min(0.95, 0.1 + 0.8 * (1 - math.exp(-cmax / 50)))
        responded = random.random() < response_prob
        cr = responded and random.random() < (0.3 + 0.4 * min(1, cmax / 100))

        # CRS correlates with expansion
        crs_grade = 0
        if cmax > 20:
            crs_grade = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
        elif cmax > 5:
            crs_grade = random.choices([0, 1, 2], weights=[30, 50, 20])[0]

        # Persistence
        persistent_6mo = cr and random.random() < 0.7

        patients.append({
            "id": i + 1,
            "cmax_cells_per_ul": cmax,
            "peak_day": random.randint(7, 14),
            "response": "CR" if cr else "PR" if responded else "NR",
            "crs_grade": crs_grade,
            "persistent_6mo": persistent_6mo,
        })

    # Correlation analysis
    responders = [p for p in patients if p["response"] != "NR"]
    non_responders = [p for p in patients if p["response"] == "NR"]

    median_cmax_responders = sorted([p["cmax_cells_per_ul"] for p in responders])[len(responders) // 2] if responders else 0
    median_cmax_nr = sorted([p["cmax_cells_per_ul"] for p in non_responders])[len(non_responders) // 2] if non_responders else 0

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "n_patients": n_patients,
        "orr_pct": round(len(responders) / n_patients * 100, 1),
        "cr_pct": round(sum(1 for p in patients if p["response"] == "CR") / n_patients * 100, 1),
        "correlation": {
            "median_cmax_responders": round(median_cmax_responders, 1),
            "median_cmax_non_responders": round(median_cmax_nr, 1),
            "fold_difference": round(median_cmax_responders / max(median_cmax_nr, 0.1), 1),
            "threshold_for_response": round(sorted([p["cmax_cells_per_ul"] for p in patients])[int(n_patients * 0.3)], 1),
        },
        "crs_by_expansion": {
            "low_expansion_crs3plus_pct": round(sum(1 for p in patients if p["cmax_cells_per_ul"] < 20 and p["crs_grade"] >= 3) / max(sum(1 for p in patients if p["cmax_cells_per_ul"] < 20), 1) * 100, 1),
            "high_expansion_crs3plus_pct": round(sum(1 for p in patients if p["cmax_cells_per_ul"] >= 50 and p["crs_grade"] >= 3) / max(sum(1 for p in patients if p["cmax_cells_per_ul"] >= 50), 1) * 100, 1),
        },
        "patients": patients[:20],
    }


async def companion_diagnostic_design(
    target: str = "CD19",
    indication: str = "DLBCL",
) -> Dict[str, Any]:
    """Design companion diagnostic test panel for CAR-T therapy."""
    return {
        "product": f"{target} CAR-T Cell Therapy",
        "indication": indication,
        "cdi_classification": "Complementary diagnostic (not required but recommended)",
        "required_tests": [
            {
                "test": f"{target} Expression by IHC",
                "purpose": "Confirm target antigen expression for treatment eligibility",
                "assay": f"IHC with anti-{target} antibody (clone FMC63 or equivalent)",
                "threshold": "≥20% tumor cells positive",
                "turnaround_days": 3,
                "regulatory_status": "CE-IVD / FDA PMA",
            },
            {
                "test": f"{target} Expression by Flow Cytometry",
                "purpose": "Quantitative target expression assessment",
                "assay": "Multiparameter flow cytometry",
                "threshold": "MFI ratio >2.0",
                "turnaround_days": 1,
                "regulatory_status": "LDT",
            },
        ],
        "recommended_tests": [
            {"test": "PD-L1 TPS", "purpose": "Immune microenvironment characterization", "assay": "IHC 22C3"},
            {"test": "TMB", "purpose": "Mutational burden assessment", "assay": "WES or FoundationOne CDx"},
            {"test": "MSI Status", "purpose": "Mismatch repair deficiency", "assay": "PCR or IHC"},
            {"test": "TP53 Mutation", "purpose": "Prognostic marker (poor outcome if mutated)", "assay": "NGS panel"},
        ],
        "monitoring_tests": [
            {"test": "CAR-T qPCR", "purpose": "Track CAR transgene copies", "timepoints": "D1,3,7,10,14,21,28,M2,3,6,12"},
            {"test": "B-cell count", "purpose": "On-target PD biomarker (aplasia)", "timepoints": "Monthly × 12"},
            {"test": "Immunoglobulin levels", "purpose": "Replacement therapy guidance", "timepoints": "Monthly × 12"},
        ],
    }
