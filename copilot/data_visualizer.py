"""
CARVanta Copilot — Data Visualizer
=====================================
Server-side data visualization and chart configuration generator
for the Research Copilot. Creates chart specifications for the
frontend to render interactive plots.

Features:
- Survival curve (Kaplan-Meier) configurations
- Waterfall plot data for treatment response
- Spider plot data for tumor dynamics
- Swimmer lane chart data
- Forest plot for subgroup analysis
- Heatmap configurations for biomarker correlation
- Network graph data for pathway analysis
- Volcano plot for differential expression

Output: JSON chart specifications compatible with Recharts/D3.
"""

import logging
import math
import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.copilot.data_visualizer")


async def generate_survival_curve(
    n_patients: int = 50,
    product: str = "axi-cel",
    cancer_type: str = "DLBCL",
    follow_up_months: int = 24,
) -> Dict[str, Any]:
    """Generate Kaplan-Meier survival curve data."""
    random.seed(42)

    # Median PFS/OS by product (months)
    medians = {
        "axi-cel": {"pfs": 14.7, "os": 25.8},
        "liso-cel": {"pfs": 12.1, "os": 23.4},
        "tisa-cel": {"pfs": 8.3, "os": 18.0},
        "brexu-cel": {"pfs": 11.6, "os": 22.1},
        "ide-cel": {"pfs": 8.8, "os": 20.2},
        "cilta-cel": {"pfs": 27.0, "os": 36.0},
    }
    med = medians.get(product, {"pfs": 10, "os": 20})

    # Generate events
    pfs_data = []
    os_data = []
    for t in range(0, follow_up_months + 1):
        pfs_surv = math.exp(-0.693 / med["pfs"] * t) * 100
        os_surv = math.exp(-0.693 / med["os"] * t) * 100
        # Add noise
        pfs_surv = max(0, min(100, pfs_surv + random.gauss(0, 2)))
        os_surv = max(0, min(100, os_surv + random.gauss(0, 1.5)))
        pfs_data.append({"month": t, "survival_pct": round(pfs_surv, 1), "at_risk": max(0, n_patients - int(t * n_patients / follow_up_months * 0.3))})
        os_data.append({"month": t, "survival_pct": round(os_surv, 1), "at_risk": max(0, n_patients - int(t * n_patients / follow_up_months * 0.15))})

    return {
        "chart_type": "kaplan_meier",
        "title": f"Progression-Free & Overall Survival — {product.upper()} in {cancer_type}",
        "series": [
            {"name": "PFS", "color": "#3b82f6", "data": pfs_data, "median_months": med["pfs"]},
            {"name": "OS", "color": "#22c55e", "data": os_data, "median_months": med["os"]},
        ],
        "x_axis": {"label": "Months", "max": follow_up_months},
        "y_axis": {"label": "Survival (%)", "max": 100},
        "annotations": [
            {"type": "horizontal_line", "y": 50, "label": "Median", "dash": True},
        ],
        "n_patients": n_patients,
    }


async def generate_waterfall_plot(
    n_patients: int = 30,
    product: str = "axi-cel",
) -> Dict[str, Any]:
    """Generate waterfall plot data for treatment response."""
    random.seed(42)
    responses = []
    cr_rate = 0.54 if product == "axi-cel" else 0.40

    for i in range(n_patients):
        r = random.random()
        if r < cr_rate:
            change = random.uniform(-100, -75)
            category = "CR"
        elif r < cr_rate + 0.25:
            change = random.uniform(-74, -30)
            category = "PR"
        elif r < cr_rate + 0.35:
            change = random.uniform(-29, 20)
            category = "SD"
        else:
            change = random.uniform(21, 80)
            category = "PD"
        responses.append({
            "patient": f"Pt-{i+1:03d}",
            "change_pct": round(change, 1),
            "category": category,
            "color": {"CR": "#22c55e", "PR": "#3b82f6", "SD": "#f59e0b", "PD": "#ef4444"}[category],
        })

    responses.sort(key=lambda x: x["change_pct"])

    return {
        "chart_type": "waterfall",
        "title": f"Best Overall Response — {product.upper()}",
        "data": responses,
        "summary": {
            "CR": sum(1 for r in responses if r["category"] == "CR"),
            "PR": sum(1 for r in responses if r["category"] == "PR"),
            "SD": sum(1 for r in responses if r["category"] == "SD"),
            "PD": sum(1 for r in responses if r["category"] == "PD"),
            "ORR_pct": round(sum(1 for r in responses if r["category"] in ("CR", "PR")) / n_patients * 100, 1),
        },
        "x_axis": {"label": "Patients"},
        "y_axis": {"label": "Change from Baseline (%)", "range": [-100, 100]},
        "threshold_lines": [
            {"y": -30, "label": "PR threshold", "color": "#3b82f6"},
            {"y": 20, "label": "PD threshold", "color": "#ef4444"},
        ],
    }


async def generate_spider_plot(
    n_patients: int = 10,
    timepoints: int = 6,
) -> Dict[str, Any]:
    """Generate spider plot data for tumor dynamics over time."""
    random.seed(42)
    patients = []

    for i in range(n_patients):
        trajectory = []
        val = 0
        responder = random.random() < 0.7
        for t in range(timepoints + 1):
            if responder:
                val = max(-100, val + random.gauss(-15, 8))
            else:
                val = min(100, val + random.gauss(10, 12))
            trajectory.append({"month": t * 2, "change_pct": round(val, 1)})
        patients.append({
            "patient": f"Pt-{i+1:03d}",
            "responder": responder,
            "color": "#22c55e" if responder else "#ef4444",
            "data": trajectory,
        })

    return {
        "chart_type": "spider",
        "title": "Tumor Burden Change Over Time",
        "patients": patients,
        "x_axis": {"label": "Months"},
        "y_axis": {"label": "Change from Baseline (%)"},
    }


async def generate_forest_plot(
    product: str = "axi-cel",
) -> Dict[str, Any]:
    """Generate forest plot for subgroup analysis."""
    subgroups = [
        {"group": "Overall", "hr": 0.42, "ci_low": 0.31, "ci_high": 0.57, "n": 307, "weight": 100},
        {"group": "Age <65", "hr": 0.38, "ci_low": 0.26, "ci_high": 0.55, "n": 210, "weight": 68},
        {"group": "Age ≥65", "hr": 0.52, "ci_low": 0.33, "ci_high": 0.82, "n": 97, "weight": 32},
        {"group": "Male", "hr": 0.40, "ci_low": 0.27, "ci_high": 0.59, "n": 185, "weight": 60},
        {"group": "Female", "hr": 0.45, "ci_low": 0.29, "ci_high": 0.70, "n": 122, "weight": 40},
        {"group": "ECOG 0", "hr": 0.35, "ci_low": 0.22, "ci_high": 0.56, "n": 145, "weight": 47},
        {"group": "ECOG 1", "hr": 0.50, "ci_low": 0.34, "ci_high": 0.74, "n": 162, "weight": 53},
        {"group": "Stage III", "hr": 0.39, "ci_low": 0.25, "ci_high": 0.61, "n": 128, "weight": 42},
        {"group": "Stage IV", "hr": 0.46, "ci_low": 0.32, "ci_high": 0.66, "n": 179, "weight": 58},
        {"group": "High LDH", "hr": 0.55, "ci_low": 0.38, "ci_high": 0.80, "n": 140, "weight": 46},
        {"group": "Normal LDH", "hr": 0.32, "ci_low": 0.20, "ci_high": 0.51, "n": 167, "weight": 54},
        {"group": "≤2 Prior Lines", "hr": 0.36, "ci_low": 0.23, "ci_high": 0.56, "n": 115, "weight": 37},
        {"group": ">2 Prior Lines", "hr": 0.48, "ci_low": 0.34, "ci_high": 0.68, "n": 192, "weight": 63},
    ]

    return {
        "chart_type": "forest",
        "title": f"Subgroup Analysis — {product.upper()} vs SOC",
        "subgroups": subgroups,
        "reference_line": 1.0,
        "favors_left": f"Favors {product.upper()}",
        "favors_right": "Favors SOC",
        "x_axis": {"label": "Hazard Ratio", "scale": "log", "range": [0.1, 2.0]},
    }


async def generate_heatmap(
    biomarkers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generate biomarker correlation heatmap."""
    if not biomarkers:
        biomarkers = ["IL-6", "IFNγ", "TNFα", "IL-2", "IL-10", "CRP", "Ferritin", "LDH", "ALC", "CD4/CD8"]

    random.seed(42)
    matrix = []
    for i, b1 in enumerate(biomarkers):
        row = []
        for j, b2 in enumerate(biomarkers):
            if i == j:
                row.append(1.0)
            elif i > j:
                row.append(matrix[j][i])  # symmetry
            else:
                row.append(round(random.uniform(-0.8, 0.95), 2))
        matrix.append(row)

    return {
        "chart_type": "heatmap",
        "title": "Biomarker Correlation Matrix",
        "labels": biomarkers,
        "matrix": matrix,
        "color_scale": {"min": -1, "max": 1, "colors": ["#3b82f6", "#f8fafc", "#ef4444"]},
    }


async def generate_volcano_plot(
    n_genes: int = 200,
) -> Dict[str, Any]:
    """Generate volcano plot for differential gene expression."""
    random.seed(42)
    genes = []
    gene_names = [f"GENE{i}" for i in range(1, n_genes + 1)]
    # Add some known immune genes
    known = ["CD19", "CD22", "BCMA", "PD1", "PDL1", "CTLA4", "LAG3", "TIM3", "TIGIT", "CD28"]
    gene_names[:len(known)] = known

    for name in gene_names:
        log2fc = random.gauss(0, 1.5)
        pval = 10 ** (-abs(log2fc) * random.uniform(0.5, 3))
        neg_log10_p = -math.log10(max(pval, 1e-50))
        significant = abs(log2fc) > 1.0 and neg_log10_p > 2
        genes.append({
            "gene": name,
            "log2FC": round(log2fc, 3),
            "neg_log10_pval": round(neg_log10_p, 2),
            "significant": significant,
            "color": "#ef4444" if log2fc > 1 and significant else "#3b82f6" if log2fc < -1 and significant else "#94a3b8",
        })

    return {
        "chart_type": "volcano",
        "title": "Differential Gene Expression — CAR-T Responders vs Non-Responders",
        "data": genes,
        "thresholds": {"log2FC": 1.0, "neg_log10_pval": 2.0},
        "x_axis": {"label": "log₂(Fold Change)"},
        "y_axis": {"label": "-log₁₀(p-value)"},
        "summary": {
            "upregulated": sum(1 for g in genes if g["log2FC"] > 1 and g["significant"]),
            "downregulated": sum(1 for g in genes if g["log2FC"] < -1 and g["significant"]),
            "total_significant": sum(1 for g in genes if g["significant"]),
        },
    }
