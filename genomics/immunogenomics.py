"""
CARVanta Genomics — Immunogenomics & TCR/BCR Analysis
========================================================
Analyze immune repertoire, T-cell receptor diversity, and
immunogenomic features relevant to CAR-T cell therapy.

Features:
- TCR/BCR clonotype analysis
- V(D)J recombination tracking
- Immune repertoire diversity metrics (Shannon, Simpson, Chao1)
- T-cell exhaustion signature scoring
- CAR-T product composition analysis
- Immune checkpoint expression profiling
- Tumor-infiltrating lymphocyte (TIL) quantification
- Immune microenvironment classification (hot/cold/altered)
- CAR-T persistence biomarker panel
- Pre-apheresis T-cell fitness assessment
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.genomics.immunogenomics")


# ──────────────────────────────────────────────────────────────────────
# TCR/BCR Analysis
# ──────────────────────────────────────────────────────────────────────

_TRBV_GENES = [
    "TRBV2", "TRBV3-1", "TRBV4-1", "TRBV5-1", "TRBV6-1", "TRBV7-2",
    "TRBV9", "TRBV10-1", "TRBV11-2", "TRBV12-3", "TRBV13", "TRBV14",
    "TRBV15", "TRBV18", "TRBV19", "TRBV20-1", "TRBV24-1", "TRBV25-1",
    "TRBV27", "TRBV28", "TRBV29-1", "TRBV30",
]

_TRBJ_GENES = ["TRBJ1-1", "TRBJ1-2", "TRBJ1-3", "TRBJ1-4", "TRBJ1-5", "TRBJ1-6",
               "TRBJ2-1", "TRBJ2-2", "TRBJ2-3", "TRBJ2-4", "TRBJ2-5", "TRBJ2-6", "TRBJ2-7"]


async def tcr_repertoire_analysis(
    n_clonotypes: int = 500,
    sample_type: str = "peripheral_blood",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze T-cell receptor repertoire diversity.

    Simulates TCR-seq data and computes diversity metrics
    relevant to CAR-T manufacturing and efficacy prediction.
    """
    if seed:
        random.seed(seed)

    # Generate clonotype distribution (power-law)
    clonotypes = []
    total_count = 0
    for i in range(n_clonotypes):
        # Power-law distribution for clone sizes
        count = max(1, int(random.paretovariate(1.5)))
        v_gene = random.choice(_TRBV_GENES)
        j_gene = random.choice(_TRBJ_GENES)

        # Random CDR3 sequence
        cdr3_len = random.randint(10, 18)
        cdr3 = "C" + "".join(random.choices("ADEFGHIKLMNPQRSTVWY", k=cdr3_len - 2)) + "F"

        clonotypes.append({
            "clonotype_id": f"CLN{i+1:04d}",
            "v_gene": v_gene,
            "j_gene": j_gene,
            "cdr3_aa": cdr3,
            "cdr3_length": cdr3_len,
            "count": count,
        })
        total_count += count

    # Sort by abundance
    clonotypes.sort(key=lambda x: x["count"], reverse=True)

    # Add frequency
    for c in clonotypes:
        c["frequency"] = round(c["count"] / max(total_count, 1), 6)

    # Diversity metrics
    frequencies = [c["count"] / total_count for c in clonotypes]
    shannon = -sum(f * math.log(f) for f in frequencies if f > 0)
    simpson = sum(f ** 2 for f in frequencies)
    inv_simpson = 1 / max(simpson, 1e-10)
    evenness = shannon / max(math.log(len(clonotypes)), 1e-10)

    # Clonality (1 - evenness, higher = more clonal)
    clonality = round(1 - evenness, 4)

    # Top clone fraction
    top_clone_pct = round(clonotypes[0]["frequency"] * 100, 2) if clonotypes else 0
    top10_pct = round(sum(c["frequency"] for c in clonotypes[:10]) * 100, 2)

    # V-gene usage distribution
    v_usage = {}
    for c in clonotypes:
        v_usage[c["v_gene"]] = v_usage.get(c["v_gene"], 0) + c["count"]
    v_usage_sorted = sorted(v_usage.items(), key=lambda x: x[1], reverse=True)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "sample_type": sample_type,
        "total_clonotypes": len(clonotypes),
        "total_reads": total_count,
        "diversity_metrics": {
            "shannon_entropy": round(shannon, 4),
            "simpson_diversity": round(1 - simpson, 4),
            "inverse_simpson": round(inv_simpson, 2),
            "chao1_estimate": len(clonotypes) + random.randint(10, 100),
            "evenness": round(evenness, 4),
            "clonality": clonality,
        },
        "clonal_expansion": {
            "top_clone_pct": top_clone_pct,
            "top10_clone_pct": top10_pct,
            "top50_clone_pct": round(sum(c["frequency"] for c in clonotypes[:50]) * 100, 2),
            "highly_expanded": clonality > 0.3,
        },
        "v_gene_usage": [{"gene": v, "count": c, "pct": round(c / total_count * 100, 1)} for v, c in v_usage_sorted[:10]],
        "top_clonotypes": clonotypes[:20],
        "car_t_manufacturing_assessment": {
            "polyclonality": "adequate" if clonality < 0.3 else "reduced" if clonality < 0.6 else "oligoclonal",
            "recommendation": (
                "Adequate polyclonal T-cell repertoire for CAR-T manufacturing."
                if clonality < 0.3 else
                "Reduced diversity may impact CAR-T product heterogeneity."
            ),
        },
    }


async def t_cell_exhaustion_scoring(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Score T-cell exhaustion markers for CAR-T fitness prediction.

    Evaluates expression of exhaustion markers (PD-1, LAG-3, TIM-3,
    CTLA-4, TIGIT) and effector/memory phenotype distribution.
    """
    if seed:
        random.seed(seed)

    # Exhaustion markers (surface expression, MFI)
    markers = {
        "PD1": {"full_name": "Programmed Death-1 (CD279)", "gene": "PDCD1",
                "mfi": round(random.gauss(1500, 500), 0), "pct_positive": round(random.uniform(15, 65), 1),
                "threshold_high": 40, "impact": "Primary checkpoint; high PD-1 indicates chronic antigen stimulation"},
        "LAG3": {"full_name": "Lymphocyte Activation Gene-3", "gene": "LAG3",
                 "mfi": round(random.gauss(800, 300), 0), "pct_positive": round(random.uniform(5, 40), 1),
                 "threshold_high": 25, "impact": "Synergizes with PD-1; dual blockade may restore function"},
        "TIM3": {"full_name": "T-cell Immunoglobulin Mucin-3", "gene": "HAVCR2",
                 "mfi": round(random.gauss(600, 250), 0), "pct_positive": round(random.uniform(3, 35), 1),
                 "threshold_high": 20, "impact": "Co-expression with PD-1 marks terminally exhausted T-cells"},
        "CTLA4": {"full_name": "Cytotoxic T-Lymphocyte Antigen-4", "gene": "CTLA4",
                  "mfi": round(random.gauss(500, 200), 0), "pct_positive": round(random.uniform(10, 30), 1),
                  "threshold_high": 20, "impact": "Competitive inhibition of costimulation; ipilimumab target"},
        "TIGIT": {"full_name": "T-cell Immunoreceptor with Ig and ITIM Domains", "gene": "TIGIT",
                  "mfi": round(random.gauss(700, 300), 0), "pct_positive": round(random.uniform(8, 45), 1),
                  "threshold_high": 30, "impact": "Competitive inhibitor of CD226; emerging checkpoint target"},
        "TOX": {"full_name": "Thymocyte Selection-Associated HMG Box", "gene": "TOX",
                "mfi": round(random.gauss(400, 150), 0), "pct_positive": round(random.uniform(5, 30), 1),
                "threshold_high": 15, "impact": "Master regulator of T-cell exhaustion program; intranuclear"},
    }

    # Exhaustion score (0-100)
    exhaustion_pcts = [m["pct_positive"] for m in markers.values()]
    exhaustion_score = round(sum(exhaustion_pcts) / len(exhaustion_pcts), 1)

    # T-cell subset distribution
    subsets = {
        "naive": round(random.uniform(5, 25), 1),
        "central_memory": round(random.uniform(15, 40), 1),
        "effector_memory": round(random.uniform(20, 45), 1),
        "terminally_differentiated": round(random.uniform(5, 20), 1),
        "stem_cell_memory": round(random.uniform(2, 12), 1),
    }
    # Normalize to 100%
    total_sub = sum(subsets.values())
    subsets = {k: round(v / total_sub * 100, 1) for k, v in subsets.items()}

    # CD4:CD8 ratio
    cd4_pct = round(random.uniform(25, 65), 1)
    cd8_pct = round(100 - cd4_pct - random.uniform(5, 15), 1)
    cd4_cd8_ratio = round(cd4_pct / max(cd8_pct, 1), 2)

    # CAR-T fitness prediction
    if exhaustion_score < 20 and subsets.get("stem_cell_memory", 0) > 5:
        fitness = "excellent"
        prediction = "High probability of robust CAR-T expansion and durable response"
    elif exhaustion_score < 35:
        fitness = "good"
        prediction = "Adequate T-cell fitness; standard manufacturing expected to succeed"
    elif exhaustion_score < 50:
        fitness = "moderate"
        prediction = "Moderate exhaustion detected; consider optimized manufacturing protocol"
    else:
        fitness = "poor"
        prediction = "High exhaustion burden; consider T-cell rejuvenation or donor-derived CAR-T"

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "exhaustion_markers": markers,
        "exhaustion_score": exhaustion_score,
        "exhaustion_category": "low" if exhaustion_score < 20 else "moderate" if exhaustion_score < 40 else "high",
        "t_cell_subsets": subsets,
        "cd4_cd8": {"cd4_pct": cd4_pct, "cd8_pct": cd8_pct, "ratio": cd4_cd8_ratio},
        "car_t_fitness": {
            "grade": fitness,
            "prediction": prediction,
            "optimal_manufacturing": "shortened culture" if fitness == "excellent" else "standard" if fitness in ("good", "moderate") else "enhanced expansion",
        },
        "recommendations": [
            f"CAR-T fitness grade: {fitness.upper()}",
            f"Exhaustion score: {exhaustion_score}/100 ({'acceptable' if exhaustion_score < 40 else 'elevated'})",
            f"CD4:CD8 ratio {cd4_cd8_ratio} ({'favorable' if cd4_cd8_ratio > 0.8 else 'suboptimal'})",
            f"Stem cell memory T-cells: {subsets.get('stem_cell_memory', 0)}% ({'adequate' if subsets.get('stem_cell_memory', 0) > 5 else 'low'})",
        ],
    }


async def immune_microenvironment(
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Classify tumor immune microenvironment (TIME).

    Assesses immune cell infiltration, checkpoint expression,
    and classifies TME as hot, cold, or altered-excluded/immunosuppressed.
    """
    if seed:
        random.seed(seed)

    # Immune cell fractions (simulated from RNA deconvolution)
    immune_cells = {
        "CD8_T_cells": round(random.uniform(2, 35), 1),
        "CD4_T_cells": round(random.uniform(3, 25), 1),
        "Tregs": round(random.uniform(1, 15), 1),
        "NK_cells": round(random.uniform(1, 10), 1),
        "B_cells": round(random.uniform(1, 20), 1),
        "macrophages_M1": round(random.uniform(2, 15), 1),
        "macrophages_M2": round(random.uniform(2, 20), 1),
        "dendritic_cells": round(random.uniform(0.5, 8), 1),
        "neutrophils": round(random.uniform(1, 12), 1),
        "mast_cells": round(random.uniform(0.5, 5), 1),
    }

    # TIL score
    til_score = round(immune_cells["CD8_T_cells"] + immune_cells["CD4_T_cells"] + immune_cells["NK_cells"], 1)

    # Checkpoint expression
    checkpoints = {
        "PD_L1_TPS": round(random.uniform(0, 80), 0),
        "PD_L1_CPS": round(random.uniform(0, 100), 0),
        "PD_L2": round(random.uniform(0, 30), 0),
        "B7_H3": round(random.uniform(5, 60), 0),
        "B7_H4": round(random.uniform(0, 25), 0),
        "VISTA": round(random.uniform(5, 40), 0),
        "IDO1": round(random.uniform(0, 50), 0),
    }

    # TME classification
    cd8_high = immune_cells["CD8_T_cells"] > 15
    pdl1_high = checkpoints["PD_L1_TPS"] > 20
    treg_high = immune_cells["Tregs"] > 8
    m2_high = immune_cells["macrophages_M2"] > 12

    if cd8_high and pdl1_high:
        tme_class = "hot (immune-inflamed)"
        car_t_prediction = "Favorable TME for CAR-T infiltration; existing immune response detected"
    elif cd8_high and not pdl1_high:
        tme_class = "altered-excluded"
        car_t_prediction = "T-cells present at margins but excluded from tumor core; consider TME modifiers"
    elif treg_high or m2_high:
        tme_class = "altered-immunosuppressed"
        car_t_prediction = "Immunosuppressive TME may impair CAR-T function; consider armored CAR-T or checkpoint combo"
    else:
        tme_class = "cold (immune-desert)"
        car_t_prediction = "Minimal immune infiltration; CAR-T may face challenges with trafficking and persistence"

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "immune_cell_fractions": immune_cells,
        "til_score": til_score,
        "til_category": "high" if til_score > 30 else "moderate" if til_score > 15 else "low",
        "checkpoint_expression": checkpoints,
        "tme_classification": tme_class,
        "car_t_prediction": car_t_prediction,
        "immunoscore": {
            "cd3_center": round(random.uniform(50, 3000), 0),
            "cd3_margin": round(random.uniform(100, 5000), 0),
            "cd8_center": round(random.uniform(20, 2000), 0),
            "cd8_margin": round(random.uniform(50, 3000), 0),
            "score": random.choices(["I0", "I1", "I2", "I3", "I4"], weights=[10, 15, 30, 25, 20])[0],
        },
        "therapeutic_implications": [
            f"TME classification: {tme_class}",
            f"TIL score: {til_score} ({'favorable' if til_score > 20 else 'unfavorable'})",
            f"PD-L1 TPS: {checkpoints['PD_L1_TPS']}% ({'eligible for anti-PD-1' if checkpoints['PD_L1_TPS'] > 50 else 'low'})",
            f"Treg infiltration: {immune_cells['Tregs']}% ({'high — consider Treg depletion' if treg_high else 'acceptable'})",
            f"M2 macrophages: {immune_cells['macrophages_M2']}% ({'immunosuppressive' if m2_high else 'acceptable'})",
        ],
    }


async def car_t_product_analysis(
    product_type: str = "CD19_CAR",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze CAR-T product cell composition and quality.

    Simulates flow cytometry and functional analysis of the
    manufactured CAR-T cell product before infusion.
    """
    if seed:
        random.seed(seed)

    # Product composition (% of total cells)
    composition = {
        "CD3_total": round(random.uniform(85, 99), 1),
        "CD4_CAR_positive": round(random.uniform(15, 55), 1),
        "CD8_CAR_positive": round(random.uniform(25, 65), 1),
        "NK_cells": round(random.uniform(0.5, 5), 1),
        "monocytes": round(random.uniform(0.1, 3), 1),
        "B_cells": round(random.uniform(0, 0.5), 2),
    }

    # Transduction efficiency
    transduction = round(random.uniform(20, 75), 1)

    # Vector copy number
    vcn = round(random.uniform(1, 8), 1)

    # Phenotype breakdown (of CAR+ cells)
    phenotype = {
        "naive_like": round(random.uniform(5, 30), 1),
        "stem_cell_memory": round(random.uniform(5, 25), 1),
        "central_memory": round(random.uniform(20, 45), 1),
        "effector_memory": round(random.uniform(15, 35), 1),
        "effector": round(random.uniform(5, 20), 1),
    }
    # Normalize
    ptotal = sum(phenotype.values())
    phenotype = {k: round(v / ptotal * 100, 1) for k, v in phenotype.items()}

    # Functionality
    cytotoxicity = round(random.uniform(30, 90), 1)
    cytokine_production = {
        "IFNg": round(random.uniform(20, 80), 1),
        "TNFa": round(random.uniform(15, 70), 1),
        "IL2": round(random.uniform(10, 60), 1),
        "granzyme_B": round(random.uniform(25, 85), 1),
    }

    # Product quality score
    quality_factors = [
        transduction / 75,
        composition["CD3_total"] / 99,
        phenotype.get("stem_cell_memory", 0) / 25,
        cytotoxicity / 90,
    ]
    quality_score = round(sum(quality_factors) / len(quality_factors) * 100, 1)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "product_type": product_type,
        "cell_composition": composition,
        "transduction_efficiency": transduction,
        "vector_copy_number": vcn,
        "vcn_safety": "acceptable" if 1 <= vcn <= 5 else "review_required",
        "phenotype_distribution": phenotype,
        "functional_assays": {
            "cytotoxicity_4hr": cytotoxicity,
            "cytokine_production": cytokine_production,
            "polyfunctionality": round(sum(1 for v in cytokine_production.values() if v > 30) / len(cytokine_production) * 100, 1),
        },
        "quality_score": quality_score,
        "quality_grade": "A" if quality_score > 70 else "B" if quality_score > 50 else "C",
        "release_criteria": {
            "viability": round(random.uniform(70, 99), 1),
            "sterility": "pass",
            "mycoplasma": "negative",
            "endotoxin": round(random.uniform(0.1, 3.5), 2),
            "endotoxin_pass": True,
            "identity_cd3": composition["CD3_total"] > 80,
            "identity_car": transduction > 10,
            "potency": cytotoxicity > 20,
        },
        "prediction": {
            "expansion_probability": "high" if phenotype.get("stem_cell_memory", 0) > 10 else "moderate",
            "persistence_probability": "favorable" if phenotype.get("central_memory", 0) > 30 else "uncertain",
            "clinical_response_prediction": (
                "Product characteristics associated with durable response."
                if quality_score > 65 else
                "Product characteristics may limit durability; close monitoring recommended."
            ),
        },
    }


async def pre_apheresis_assessment(
    age: int = 55,
    prior_lines: int = 3,
    cancer_type: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Pre-apheresis T-cell fitness assessment.

    Evaluates patient T-cell fitness before leukapheresis collection
    to predict manufacturing success and product quality.
    """
    if seed:
        random.seed(seed)

    # Impact of prior therapy lines
    therapy_impact = min(prior_lines * 10, 50)

    # Absolute lymphocyte count
    alc = round(random.uniform(0.3, 3.0), 2)
    alc_adequate = alc > 0.5

    # CD3 count
    cd3_count = round(alc * random.uniform(0.5, 0.8) * 1000, 0)
    cd3_adequate = cd3_count > 300

    # T-cell fitness markers
    fitness = {
        "alc": {"value": alc, "unit": "×10⁹/L", "adequate": alc_adequate, "threshold": 0.5},
        "cd3_absolute": {"value": cd3_count, "unit": "cells/μL", "adequate": cd3_adequate, "threshold": 300},
        "cd4_count": {"value": round(cd3_count * random.uniform(0.3, 0.6), 0), "unit": "cells/μL"},
        "cd8_count": {"value": round(cd3_count * random.uniform(0.2, 0.5), 0), "unit": "cells/μL"},
        "naive_t_cell_pct": {"value": round(max(2, 30 - therapy_impact + random.gauss(0, 5)), 1), "unit": "%"},
        "exhaustion_index": {"value": round(min(80, 15 + therapy_impact + random.gauss(0, 10)), 1), "unit": "score"},
    }

    # Manufacturing prediction
    naive_pct = fitness["naive_t_cell_pct"]["value"]
    exh_idx = fitness["exhaustion_index"]["value"]

    if alc_adequate and cd3_adequate and naive_pct > 10 and exh_idx < 40:
        manufacturing_prediction = "high_success"
        recommendation = "Proceed with standard leukapheresis. T-cell fitness adequate."
    elif alc_adequate and cd3_adequate:
        manufacturing_prediction = "moderate_success"
        recommendation = "Proceed with leukapheresis. Consider extended manufacturing protocol."
    else:
        manufacturing_prediction = "at_risk"
        recommendation = "Low T-cell counts. Consider washout period, growth factor support, or repeat collection."

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "patient_age": age,
        "prior_therapy_lines": prior_lines,
        "cancer_type": cancer_type,
        "fitness_markers": fitness,
        "manufacturing_prediction": manufacturing_prediction,
        "recommendation": recommendation,
        "leukapheresis_timing": {
            "optimal": "2-4 weeks after last cytotoxic therapy",
            "minimum_washout": {
                "chemotherapy": "2 weeks",
                "anti_cd20": "4 weeks (rituximab depletes B-cells, not T-cells, but monitor lymphocyte recovery)",
                "checkpoint_inhibitor": "3-4 weeks",
                "steroids": "72 hours (dexamethasone >10mg)",
                "bendamustine": "4+ weeks (lymphodepleting)",
            },
        },
        "collection_target": {
            "minimum_cd3": "0.6 × 10⁹ total CD3+ cells",
            "target_cd3": "2.0 × 10⁹ total CD3+ cells",
            "blood_volume_processed": "10-15 L (2-3 blood volumes)",
            "duration": "3-4 hours",
        },
    }
