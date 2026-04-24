"""
CARVanta Genomics — Gene Expression Profiling Engine
=======================================================
Analyze gene expression signatures relevant to CAR-T therapy,
including cell-of-origin classification, proliferation indices,
and therapy response prediction.

Features:
- Cell-of-origin (COO) classification for DLBCL (ABC vs GCB vs unclassified)
- Proliferation index scoring (Ki-67 molecular correlate)
- Gene expression-based subtyping (NMF/consensus clustering)
- CAR-T target antigen expression quantification
- Immune gene signature scoring (Hallmark, MSigDB)
- Drug resistance gene expression panels
- Molecular response predictor for CAR-T therapy
- Expression-based survival risk scoring
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.genomics.expression_profiler")


# ──────────────────────────────────────────────────────────────────────
# Gene Expression Signature Databases
# ──────────────────────────────────────────────────────────────────────

_COO_CLASSIFIER = {
    "GCB_signature": {
        "genes": ["LMO2", "MYBL1", "MME", "BCL6", "SERPINA9", "ASB13", "NEK6", "ITPKB"],
        "description": "Germinal center B-cell signature — favorable prognosis",
        "car_t_response": "GCB-DLBCL generally has better CD19 CAR-T response rates",
    },
    "ABC_signature": {
        "genes": ["IRF4", "FOXP1", "TNFRSF13B", "SH3BP5", "PIM1", "CCND2", "BLNK", "CYB5R2"],
        "description": "Activated B-cell signature — inferior prognosis with R-CHOP",
        "car_t_response": "ABC-DLBCL shows comparable CAR-T response to GCB in recent data (axi-cel)",
    },
    "MHG_signature": {
        "genes": ["MYC", "BCL2", "BCL6", "TP53", "CDKN2A", "E2F1", "MCM2", "CCNE1"],
        "description": "Molecular high-grade / double-hit signature — worst prognosis",
        "car_t_response": "MHG/DHL DLBCL has reduced CAR-T CR rate; consider bispecific or dual-target CAR",
    },
}

_TARGET_EXPRESSION = {
    "CD19": {"gene": "CD19", "normal_tpm": 85.0, "tumor_range": [10, 200], "threshold_low": 20,
             "clinical_note": "CD19 expression >20 TPM generally sufficient for CAR-T targeting"},
    "BCMA": {"gene": "TNFRSF17", "normal_tpm": 5.0, "tumor_range": [1, 150], "threshold_low": 5,
             "clinical_note": "BCMA expression variable in MM; sBCMA shedding may reduce surface levels"},
    "CD22": {"gene": "CD22", "normal_tpm": 60.0, "tumor_range": [5, 180], "threshold_low": 15,
             "clinical_note": "CD22 often maintained when CD19 is lost — dual target strategy"},
    "GPRC5D": {"gene": "GPRC5D", "normal_tpm": 2.0, "tumor_range": [0.5, 80], "threshold_low": 3,
               "clinical_note": "GPRC5D expression more stable than BCMA; less shedding"},
    "CD20": {"gene": "MS4A1", "normal_tpm": 90.0, "tumor_range": [15, 250], "threshold_low": 25,
             "clinical_note": "CD20 maintained in most B-NHL; bispecific CD20xCD3 alternative to CAR-T"},
    "CD38": {"gene": "CD38", "normal_tpm": 30.0, "tumor_range": [5, 200], "threshold_low": 10,
             "clinical_note": "CD38 target for daratumumab; CAR-CD38 constructs in development"},
    "CD138": {"gene": "SDC1", "normal_tpm": 10.0, "tumor_range": [2, 150], "threshold_low": 8,
              "clinical_note": "CD138/Syndecan-1 highly expressed on MM plasma cells"},
    "GPC3": {"gene": "GPC3", "normal_tpm": 0.5, "tumor_range": [0.1, 100], "threshold_low": 2,
             "clinical_note": "GPC3 overexpressed in HCC; tumor-specific CAR-T target"},
    "MSLN": {"gene": "MSLN", "normal_tpm": 1.0, "tumor_range": [0.2, 120], "threshold_low": 3,
             "clinical_note": "Mesothelin expressed in mesothelioma, ovarian, pancreatic cancers"},
    "EGFR": {"gene": "EGFR", "normal_tpm": 15.0, "tumor_range": [5, 300], "threshold_low": 20,
             "clinical_note": "EGFR/EGFRvIII targeting for solid tumor CAR-T"},
}

_IMMUNE_SIGNATURES = {
    "interferon_gamma": {
        "genes": ["IFNG", "STAT1", "IRF1", "CXCL9", "CXCL10", "CXCL11", "IDO1", "HLA-DRA"],
        "significance": "IFNγ response signature — predictive of immunotherapy response",
        "car_t_note": "High IFNγ signature indicates pre-existing immune activation; favorable for CAR-T",
    },
    "t_cell_inflamed": {
        "genes": ["CD8A", "GZMA", "GZMB", "PRF1", "CXCL9", "CXCL10", "CD274", "CTLA4"],
        "significance": "T-cell inflamed phenotype — hot tumor microenvironment",
        "car_t_note": "Pre-existing T-cell infiltration suggests favorable CAR-T trafficking",
    },
    "tgf_beta": {
        "genes": ["TGFB1", "TGFB2", "TGFB3", "TGFBR1", "TGFBR2", "SMAD2", "SMAD3", "SMAD4"],
        "significance": "TGF-β pathway — immunosuppressive when upregulated",
        "car_t_note": "High TGF-β impairs CAR-T effector function; armored CAR-T constructs recommended",
    },
    "proliferation": {
        "genes": ["MKI67", "TOP2A", "PCNA", "MCM2", "MCM6", "CDK1", "CCNB1", "BUB1"],
        "significance": "Proliferation index — correlates with tumor growth rate",
        "car_t_note": "High proliferation may outpace CAR-T killing; bridging therapy recommended",
    },
    "angiogenesis": {
        "genes": ["VEGFA", "VEGFB", "FLT1", "KDR", "PECAM1", "CDH5", "ANGPT1", "ANGPT2"],
        "significance": "Angiogenesis signature — correlates with vascular density",
        "car_t_note": "High angiogenesis in solid tumors impairs CAR-T trafficking; anti-VEGF combo may help",
    },
    "wnt_target": {
        "genes": ["AXIN2", "LEF1", "TCF7", "MYC", "CCND1", "BIRC5", "LGR5", "ASCL2"],
        "significance": "WNT target genes — β-catenin pathway activity",
        "car_t_note": "WNT activation associated with T-cell exclusion from tumors",
    },
}


async def cell_of_origin_classification(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Classify DLBCL cell-of-origin by gene expression profiling.

    Uses Hans algorithm equivalent (IHC surrogate) and molecular
    GEP-based classification to assign GCB vs ABC vs unclassified.
    """
    if seed:
        random.seed(seed)

    # Simulate gene expression for COO signatures
    signature_scores = {}
    for sig_name, sig_data in _COO_CLASSIFIER.items():
        gene_expressions = {}
        for gene in sig_data["genes"]:
            expr = round(random.gauss(50, 25), 1)
            expr = max(0.1, expr)
            gene_expressions[gene] = expr

        score = round(sum(gene_expressions.values()) / len(gene_expressions), 2)
        signature_scores[sig_name] = {
            "score": score,
            "genes": gene_expressions,
            "description": sig_data["description"],
            "car_t_response": sig_data["car_t_response"],
        }

    # Determine COO
    gcb_score = signature_scores["GCB_signature"]["score"]
    abc_score = signature_scores["ABC_signature"]["score"]
    mhg_score = signature_scores["MHG_signature"]["score"]

    if mhg_score > gcb_score and mhg_score > abc_score:
        coo = "MHG (Molecular High-Grade)"
        prognosis = "poor"
    elif gcb_score > abc_score * 1.2:
        coo = "GCB (Germinal Center B-cell)"
        prognosis = "favorable"
    elif abc_score > gcb_score * 1.2:
        coo = "ABC (Activated B-cell)"
        prognosis = "intermediate"
    else:
        coo = "Unclassified"
        prognosis = "intermediate"

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "classification": coo,
        "prognosis": prognosis,
        "signature_scores": signature_scores,
        "hans_algorithm": {
            "CD10": random.random() < 0.6,
            "BCL6": random.random() < 0.7,
            "MUM1": random.random() < 0.5,
            "hans_classification": coo.split(" ")[0],
        },
        "car_t_implications": {
            "expected_response": "CR ~58% (GCB) vs ~52% (ABC) with axi-cel" if cancer_type == "DLBCL" else "Variable",
            "recommendation": (
                "GCB type detected — favorable CAR-T candidate."
                if "GCB" in coo else
                "ABC/MHG type — CAR-T efficacy comparable but monitor for early relapse."
            ),
        },
    }


async def target_expression_panel(
    targets: Optional[List[str]] = None,
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Quantify expression of CAR-T target antigens.

    Measures RNA expression (TPM) and predicts surface protein
    levels for candidate CAR-T targets to guide target selection.
    """
    if seed:
        random.seed(seed)

    if not targets:
        targets = ["CD19", "BCMA", "CD22", "GPRC5D", "CD20"]

    results = []
    for target in targets:
        target_upper = target.upper()
        info = _TARGET_EXPRESSION.get(target_upper, {
            "gene": target, "normal_tpm": 50, "tumor_range": [5, 150],
            "threshold_low": 10, "clinical_note": "No specific clinical data"
        })

        # Simulate expression
        tpm = round(random.uniform(info["tumor_range"][0], info["tumor_range"][1]), 1)
        log2_fc = round(math.log2(max(tpm, 0.1) / max(info["normal_tpm"], 0.1)), 2)

        # Surface protein prediction (rough correlation with RNA)
        protein_predicted = "high" if tpm > info["threshold_low"] * 3 else "moderate" if tpm > info["threshold_low"] else "low"

        results.append({
            "target": target_upper,
            "gene": info["gene"],
            "tpm": tpm,
            "log2_fold_change": log2_fc,
            "expression_category": "high" if tpm > info["threshold_low"] * 3 else "adequate" if tpm > info["threshold_low"] else "low",
            "above_threshold": tpm >= info["threshold_low"],
            "predicted_surface_protein": protein_predicted,
            "car_t_eligible": tpm >= info["threshold_low"],
            "clinical_note": info["clinical_note"],
        })

    # Rank targets by expression
    results.sort(key=lambda x: x["tpm"], reverse=True)

    eligible = [r for r in results if r["car_t_eligible"]]
    best_target = eligible[0]["target"] if eligible else "None"

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "targets_assessed": len(results),
        "eligible_targets": len(eligible),
        "best_target": best_target,
        "expression_panel": results,
        "dual_target_recommendation": (
            f"{eligible[0]['target']} + {eligible[1]['target']}" if len(eligible) >= 2 else "Insufficient targets for dual approach"
        ),
    }


async def immune_signature_scoring(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Score multiple immune gene signatures.

    Evaluates IFNγ response, T-cell inflammation, TGF-β,
    proliferation, angiogenesis, and WNT pathway activity.
    """
    if seed:
        random.seed(seed)

    results = []
    for sig_name, sig_data in _IMMUNE_SIGNATURES.items():
        gene_expr = {}
        for gene in sig_data["genes"]:
            gene_expr[gene] = round(max(0.1, random.gauss(50, 30)), 1)

        score = round(sum(gene_expr.values()) / len(gene_expr), 2)
        zscore = round((score - 50) / 15, 2)

        results.append({
            "signature": sig_name,
            "score": score,
            "zscore": zscore,
            "category": "high" if zscore > 0.5 else "low" if zscore < -0.5 else "intermediate",
            "genes": gene_expr,
            "significance": sig_data["significance"],
            "car_t_note": sig_data["car_t_note"],
        })

    # Overall immune score
    ifng = next((r for r in results if r["signature"] == "interferon_gamma"), None)
    tcell = next((r for r in results if r["signature"] == "t_cell_inflamed"), None)
    tgfb = next((r for r in results if r["signature"] == "tgf_beta"), None)

    immune_composite = round(
        (ifng["zscore"] if ifng else 0) +
        (tcell["zscore"] if tcell else 0) -
        (tgfb["zscore"] if tgfb else 0),
        2
    )

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "signatures": results,
        "composite_immune_score": immune_composite,
        "immune_phenotype": (
            "immune-hot" if immune_composite > 1 else
            "immune-cold" if immune_composite < -1 else
            "immune-intermediate"
        ),
        "car_t_prediction": (
            "Favorable immune microenvironment for CAR-T infiltration and activity."
            if immune_composite > 0 else
            "Immunosuppressive features detected; consider armored CAR-T or combination approach."
        ),
    }
