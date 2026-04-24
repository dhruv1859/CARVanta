"""
CARVanta Drug Discovery — Resistance Prediction Engine
==========================================================
Predict and model mechanisms of CAR-T therapy resistance
including antigen loss, immune evasion, T-cell exhaustion,
and tumor microenvironment-mediated suppression.

Features:
- Antigen loss/downregulation modeling
- Lineage switch prediction (B→myeloid)
- T-cell exhaustion trajectory modeling
- Tumor microenvironment resistance scoring
- Checkpoint ligand upregulation prediction
- Trogocytosis-mediated antigen transfer
- Combination resistance prediction
- Resistance mitigation strategy recommendation
"""

import logging
import math
import random
import uuid
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.drug_discovery.resistance")


# ──────────────────────────────────────────────────────────────────────
# Resistance Mechanism Database
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ResistanceMechanism:
    """Represents a known CAR-T resistance mechanism."""
    name: str
    category: str  # antigen_loss, immune_evasion, tme, exhaustion, intrinsic
    frequency_pct: float
    onset_months: Tuple[float, float]  # range
    description: str
    biomarkers: List[str]
    mitigations: List[str]
    literature_refs: int


_RESISTANCE_MECHANISMS: Dict[str, ResistanceMechanism] = {
    "cd19_loss": ResistanceMechanism(
        "CD19 antigen loss", "antigen_loss", 30,
        (1, 12), "Complete loss of CD19 surface expression via biallelic mutations, alternative splicing (exon 2 deletion), or epigenetic silencing",
        ["CD19 flow cytometry (loss)", "CD19 mRNA (decreased)", "Genomic: CD19 mutations/deletions"],
        ["Dual-target CAR (CD19/CD22)", "CD19 re-expression inducers", "Alternative target switch"],
        245,
    ),
    "antigen_downregulation": ResistanceMechanism(
        "Target antigen downregulation", "antigen_loss", 20,
        (2, 18), "Partial reduction of antigen surface density below the threshold for CAR-T activation (~200 molecules/cell)",
        ["Quantitative flow cytometry (qFlow)", "Surface molecule density (molecules/cell)"],
        ["High-affinity scFv", "CAR with lower activation threshold", "Combination with bispecific antibodies"],
        189,
    ),
    "lineage_switch": ResistanceMechanism(
        "Lineage switch (B→myeloid)", "antigen_loss", 5,
        (1, 6), "Transdifferentiation of B-ALL to AML/mixed phenotype, losing B-cell markers including CD19. Associated with MLL rearrangements",
        ["Loss of CD19/CD22/CD20", "Gain of CD33/CD14/MPO", "MLL-r status"],
        ["Multi-lineage target CAR", "Checkpoint combination", "Allogeneic HSCT consolidation"],
        67,
    ),
    "trogocytosis": ResistanceMechanism(
        "Trogocytosis-mediated antigen transfer", "antigen_loss", 15,
        (0.25, 3), "CAR-T cells strip antigen from tumor surface (trogocytosis), temporarily reducing target density and enabling fratricide",
        ["CAR-T cells positive for target antigen", "Reduced tumor antigen density"],
        ["Dasatinib pause (reduces trogocytosis)", "Lower CAR-T dose", "Intermittent dosing"],
        34,
    ),
    "exhaustion_chronic_signaling": ResistanceMechanism(
        "T-cell exhaustion (chronic CAR signaling)", "exhaustion", 40,
        (0.5, 6), "Persistent antigen stimulation drives progressive T-cell dysfunction with upregulation of PD-1, LAG-3, TIM-3, and TIGIT",
        ["PD-1 high", "LAG-3 high", "TIM-3 high", "TIGIT high", "TOX transcription factor upregulation",
         "Loss of IL-2 production", "Reduced cytotoxicity"],
        ["4-1BB costimulation (vs CD28)", "PD-1 checkpoint combination", "REST periods (dasatinib)",
         "CRISPR knockout of exhaustion genes (TOX, NR4A)", "Armored CAR with IL-15 secretion"],
        312,
    ),
    "exhaustion_tonic_signaling": ResistanceMechanism(
        "Tonic signaling-induced exhaustion", "exhaustion", 15,
        (0, 3), "Antigen-independent CAR clustering causes constitutive signaling, driving premature exhaustion before infusion",
        ["CAR+ T-cell phenotype: high PD-1 before infusion", "Reduced expansion in vitro"],
        ["scFv engineering (reduce aggregation)", "4-1BB costimulation", "Regulated CAR expression (Tet-ON)"],
        89,
    ),
    "pd_l1_upregulation": ResistanceMechanism(
        "PD-L1 upregulation by tumor", "immune_evasion", 35,
        (0.5, 12), "Tumor cells upregulate PD-L1 in response to IFN-γ secreted by CAR-T, creating adaptive immune resistance",
        ["PD-L1 IHC (tumor)", "IFN-γ levels (serum)", "CAR-T exhaustion markers"],
        ["Anti-PD-1/PD-L1 combination", "PD-1 dominant-negative receptor on CAR-T",
         "CRISPR PD-1 knockout CAR-T", "Armored CAR secreting anti-PD-L1 scFv"],
        198,
    ),
    "cd58_loss": ResistanceMechanism(
        "CD58 loss (immune synapse disruption)", "immune_evasion", 10,
        (1, 12), "Loss of CD58 disrupts the immune synapse between CAR-T and tumor via CD2-CD58 interaction",
        ["CD58 flow cytometry (loss)", "CD2 binding assay"],
        ["CD2-independent CAR design", "Combination with NK cells"],
        23,
    ),
    "fas_pathway_defect": ResistanceMechanism(
        "Fas/FasL pathway defect", "immune_evasion", 8,
        (2, 18), "Tumor acquires mutations in FAS or downstream apoptosis pathway, resisting CAR-T-mediated killing",
        ["FAS mutations (genomic)", "Caspase-8 expression", "Resistance to FasL-induced apoptosis"],
        ["Perforin/granzyme-dependent killing optimization", "TRAIL pathway activation"],
        45,
    ),
    "tme_immunosuppression": ResistanceMechanism(
        "TME immunosuppression (Tregs, MDSCs, TAMs)", "tme", 30,
        (1, 12), "Immunosuppressive cells in the TME (Tregs, MDSCs, M2 macrophages) inhibit CAR-T function via TGF-β, IL-10, adenosine",
        ["Treg infiltration (CD4+CD25+FoxP3+)", "MDSC frequency", "M2/M1 macrophage ratio",
         "TGF-β levels", "Adenosine levels"],
        ["TGF-β dominant-negative receptor on CAR-T", "Adenosine receptor knockout",
         "IL-12/IL-15 armored CAR", "Oncolytic virus combination"],
        156,
    ),
    "hypoxia": ResistanceMechanism(
        "Tumor hypoxia", "tme", 25,
        (0, 24), "Hypoxic TME reduces CAR-T metabolism and effector function; upregulates HIF-1α in tumor",
        ["HIF-1α expression", "VEGF levels", "Pimonidazole staining"],
        ["HIF-responsive CAR (activated by hypoxia)", "Anti-VEGF combination", "Oxygen-independent CAR design"],
        78,
    ),
    "physical_barrier": ResistanceMechanism(
        "Physical barrier (solid tumor stroma)", "tme", 50,
        (0, 24), "Dense extracellular matrix and fibrotic stroma prevent CAR-T infiltration into solid tumors",
        ["Collagen density (Masson trichrome)", "FAP+ fibroblasts", "CAR-T infiltration (IHC)"],
        ["FAP-targeting CAR-T", "Heparanase-expressing CAR-T", "Local injection", "Oncolytic virus (TME remodeling)"],
        134,
    ),
    "ido_expression": ResistanceMechanism(
        "IDO/TDO tryptophan depletion", "tme", 15,
        (0.5, 12), "Tumor/TME expression of IDO/TDO depletes tryptophan and produces kynurenine, suppressing T-cell function",
        ["IDO1 IHC", "Tryptophan/kynurenine ratio (serum)", "Kynurenine pathway metabolites"],
        ["IDO inhibitor combination (epacadostat)", "Tryptophan supplementation", "IDO-resistant CAR-T"],
        56,
    ),
    "mhc_loss": ResistanceMechanism(
        "MHC-I downregulation", "immune_evasion", 12,
        (2, 18), "Loss of MHC-I prevents endogenous T-cell recognition. Does NOT directly affect CAR-T but prevents bystander killing",
        ["MHC-I (HLA-A,B,C) IHC", "β2-microglobulin expression"],
        ["NK cell combination therapy", "CAR-T designed to work with NK cells", "IFN-γ inducers"],
        67,
    ),
    "apoptosis_resistance": ResistanceMechanism(
        "Intrinsic apoptosis resistance", "intrinsic", 18,
        (0, 24), "Tumor overexpression of anti-apoptotic proteins (BCL-2, MCL-1, BCL-XL) prevents CAR-T-mediated killing",
        ["BCL-2 expression (IHC/WB)", "MCL-1 amplification", "BH3 profiling"],
        ["Venetoclax combination (BCL-2 inhibitor)", "BH3 mimetics", "Enhanced perforin delivery"],
        89,
    ),
}


# ──────────────────────────────────────────────────────────────────────
# Resistance Prediction Functions
# ──────────────────────────────────────────────────────────────────────

def _seed_from(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


async def predict_resistance(
    target: str = "CD19",
    cancer_type: str = "DLBCL",
    car_costim: str = "4-1BB",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Predict resistance mechanisms for a specific CAR-T therapy.
    Scores each mechanism by likelihood and provides mitigation strategies.
    """
    if seed:
        random.seed(seed)

    rng = random.Random(_seed_from(f"{target}_{cancer_type}"))

    scored_mechanisms = []
    for code, mech in _RESISTANCE_MECHANISMS.items():
        # Base frequency adjusted by target and cancer type
        base_freq = mech.frequency_pct

        # Target-specific adjustments
        if "antigen" in mech.category:
            if target == "CD19":
                base_freq *= 1.2  # Well-documented for CD19
            elif target == "BCMA":
                base_freq *= 0.8  # Less antigen loss with BCMA
            elif target in ("HER2", "EGFR"):
                base_freq *= 0.6  # Solid tumor targets

        # Costimulation adjustments
        if "exhaustion" in mech.category:
            if car_costim == "4-1BB":
                base_freq *= 0.6  # 4-1BB protects against exhaustion
            elif car_costim == "CD28":
                base_freq *= 1.3  # CD28 more prone to exhaustion

        # TME adjustments for solid tumors
        if mech.category == "tme":
            if cancer_type in ("NSCLC", "pancreatic", "glioblastoma", "ovarian"):
                base_freq *= 1.5
            elif cancer_type in ("DLBCL", "B-ALL", "MCL"):
                base_freq *= 0.5

        # Add noise
        adjusted_freq = max(1, min(95, base_freq + rng.gauss(0, 5)))

        # Onset prediction
        onset_low, onset_high = mech.onset_months
        predicted_onset = round(rng.uniform(onset_low, onset_high), 1)

        scored_mechanisms.append({
            "code": code,
            "name": mech.name,
            "category": mech.category,
            "likelihood_pct": round(adjusted_freq, 1),
            "predicted_onset_months": predicted_onset,
            "description": mech.description,
            "biomarkers": mech.biomarkers,
            "mitigations": mech.mitigations,
            "literature_refs": mech.literature_refs,
        })

    # Sort by likelihood
    scored_mechanisms.sort(key=lambda x: x["likelihood_pct"], reverse=True)

    # Overall resistance risk
    top_risks = scored_mechanisms[:5]
    overall_risk = 1 - math.prod(1 - m["likelihood_pct"] / 100 for m in top_risks)

    # Category summary
    categories = {}
    for m in scored_mechanisms:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = {"count": 0, "avg_likelihood": 0, "top_mechanism": ""}
        categories[cat]["count"] += 1
        categories[cat]["avg_likelihood"] += m["likelihood_pct"]
    for cat in categories:
        categories[cat]["avg_likelihood"] = round(categories[cat]["avg_likelihood"] / categories[cat]["count"], 1)
        top = max((m for m in scored_mechanisms if m["category"] == cat), key=lambda x: x["likelihood_pct"])
        categories[cat]["top_mechanism"] = top["name"]

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "cancer_type": cancer_type,
        "car_costimulation": car_costim,
        "overall_resistance_risk_pct": round(overall_risk * 100, 1),
        "risk_classification": "high" if overall_risk > 0.6 else "moderate" if overall_risk > 0.3 else "low",
        "total_mechanisms_analyzed": len(scored_mechanisms),
        "top_5_risks": top_risks,
        "category_summary": categories,
        "all_mechanisms": scored_mechanisms,
        "monitoring_recommendations": _generate_monitoring_plan(top_risks),
        "prevention_strategy": _generate_prevention_strategy(top_risks, target),
    }


def _generate_monitoring_plan(top_risks: List[Dict]) -> List[Dict]:
    """Generate a biomarker monitoring plan based on top resistance risks."""
    plan = []
    seen_biomarkers = set()
    for risk in top_risks:
        for biomarker in risk["biomarkers"][:2]:
            if biomarker not in seen_biomarkers:
                seen_biomarkers.add(biomarker)
                plan.append({
                    "biomarker": biomarker,
                    "monitoring_for": risk["name"],
                    "frequency": "Monthly" if risk["likelihood_pct"] > 25 else "Every 3 months",
                    "method": "Flow cytometry" if "flow" in biomarker.lower() else "Blood test" if "serum" in biomarker.lower() else "Biopsy/IHC",
                    "start_timepoint": f"Day {max(14, int(risk['predicted_onset_months'] * 15))}",
                })
    return plan


def _generate_prevention_strategy(top_risks: List[Dict], target: str) -> Dict[str, Any]:
    """Generate a multi-layered prevention strategy."""
    strategies = {
        "preemptive": [],
        "combination": [],
        "engineering": [],
    }

    for risk in top_risks[:3]:
        if risk["category"] == "antigen_loss":
            strategies["preemptive"].append(f"Dual-target CAR to prevent {risk['name']}")
            strategies["engineering"].append("Bispecific or tandem CAR construct")
        elif risk["category"] == "exhaustion":
            strategies["combination"].append("Anti-PD-1 checkpoint inhibitor at Day 28")
            strategies["engineering"].append("4-1BB costimulation with reduced ITAM CAR")
        elif risk["category"] == "tme":
            strategies["combination"].append("TME-remodeling agent (e.g., lenalidomide)")
            strategies["engineering"].append("Armored CAR with IL-15/IL-21 secretion")
        elif risk["category"] == "immune_evasion":
            strategies["combination"].append("NK cell therapy combination")
            strategies["engineering"].append("PD-1 dominant-negative or knockout CAR-T")

    return {
        "preemptive_strategies": list(set(strategies["preemptive"])),
        "combination_strategies": list(set(strategies["combination"])),
        "engineering_strategies": list(set(strategies["engineering"])),
        "overall_recommendation": (
            f"For {target}-targeting CAR-T, employ a multi-layered resistance prevention strategy "
            f"combining engineering solutions with rational combination therapy."
        ),
    }


async def exhaustion_trajectory(
    costim: str = "4-1BB",
    antigen_load: str = "high",
    n_days: int = 90,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Model T-cell exhaustion trajectory over time.
    Tracks exhaustion markers, cytokine production, and killing capacity.
    """
    if seed:
        random.seed(seed)

    # Exhaustion kinetics based on costimulation
    exhaustion_rate = {
        "CD28": 0.035, "4-1BB": 0.015, "ICOS": 0.020,
        "CD28_4-1BB": 0.025, "OX40": 0.018,
    }.get(costim, 0.025)

    # Antigen load modifier
    load_modifier = {"high": 1.5, "moderate": 1.0, "low": 0.6}.get(antigen_load, 1.0)
    exhaustion_rate *= load_modifier

    timepoints = []
    for day in range(n_days + 1):
        if day % max(1, n_days // 50) != 0 and day != n_days:
            continue

        exhaustion_level = 1 - math.exp(-exhaustion_rate * day)
        pd1 = min(95, 10 + exhaustion_level * 85 + random.gauss(0, 3))
        lag3 = min(90, 5 + exhaustion_level * 75 + random.gauss(0, 4))
        tim3 = min(85, 8 + exhaustion_level * 70 + random.gauss(0, 3))
        tigit = min(80, 3 + exhaustion_level * 65 + random.gauss(0, 4))
        il2 = max(0, 90 - exhaustion_level * 80 + random.gauss(0, 5))
        ifng = max(5, 95 - exhaustion_level * 70 + random.gauss(0, 5))
        killing = max(5, 95 - exhaustion_level * 85 + random.gauss(0, 4))
        proliferation = max(0, 90 - exhaustion_level * 90 + random.gauss(0, 5))
        tox_tf = min(95, 5 + exhaustion_level * 80 + random.gauss(0, 3))

        timepoints.append({
            "day": day,
            "exhaustion_level": round(exhaustion_level, 3),
            "markers": {
                "PD-1": round(pd1, 1), "LAG-3": round(lag3, 1),
                "TIM-3": round(tim3, 1), "TIGIT": round(tigit, 1),
                "TOX": round(tox_tf, 1),
            },
            "function": {
                "IL-2_production": round(il2, 1),
                "IFN-γ_production": round(ifng, 1),
                "killing_capacity": round(killing, 1),
                "proliferation": round(proliferation, 1),
            },
        })

    # Find critical timepoints
    half_exhaustion_day = next((tp["day"] for tp in timepoints if tp["exhaustion_level"] >= 0.5), None)
    critical_day = next((tp["day"] for tp in timepoints if tp["function"]["killing_capacity"] < 30), None)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "costimulation": costim,
        "antigen_load": antigen_load,
        "exhaustion_rate": exhaustion_rate,
        "simulation_days": n_days,
        "timepoints": timepoints,
        "critical_events": {
            "half_exhaustion_day": half_exhaustion_day,
            "critical_dysfunction_day": critical_day,
            "window_of_efficacy_days": critical_day or n_days,
        },
        "recommendation": (
            f"With {costim} costimulation and {antigen_load} antigen load, "
            f"CAR-T cells maintain killing capacity for ~{critical_day or '>90'} days. "
            f"{'Consider checkpoint combination at day ' + str(max(14, (half_exhaustion_day or 45) - 7)) if half_exhaustion_day and half_exhaustion_day < 60 else 'Exhaustion trajectory is favorable.'}"
        ),
    }


async def antigen_escape_model(
    target: str = "CD19",
    initial_tumor_cells: int = 1_000_000,
    antigen_negative_fraction: float = 0.001,
    n_days: int = 180,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Model antigen-negative escape under CAR-T selection pressure.
    Simulates clonal evolution of antigen-positive and antigen-negative populations.
    """
    if seed:
        random.seed(seed)

    ag_pos = initial_tumor_cells * (1 - antigen_negative_fraction)
    ag_neg = initial_tumor_cells * antigen_negative_fraction

    # Growth rates
    tumor_growth_rate = 0.03  # per day
    car_t_kill_rate = 0.15    # per day (antigen-positive only)
    car_t_expansion_peak_day = 14
    car_t_contraction_rate = 0.02

    timepoints = []
    for day in range(n_days + 1):
        if day % max(1, n_days // 60) != 0 and day != n_days:
            continue

        # CAR-T efficacy curve (expansion then contraction)
        if day < car_t_expansion_peak_day:
            car_t_efficacy = min(1.0, day / car_t_expansion_peak_day)
        else:
            car_t_efficacy = max(0.05, math.exp(-car_t_contraction_rate * (day - car_t_expansion_peak_day)))

        # Antigen-positive population
        effective_kill = car_t_kill_rate * car_t_efficacy
        ag_pos_growth = ag_pos * (tumor_growth_rate - effective_kill)
        ag_pos = max(0, ag_pos + ag_pos_growth + random.gauss(0, max(1, ag_pos * 0.01)))

        # Antigen-negative population (unaffected by CAR-T)
        ag_neg_growth = ag_neg * tumor_growth_rate
        ag_neg = max(0, ag_neg + ag_neg_growth + random.gauss(0, max(1, ag_neg * 0.01)))

        total = ag_pos + ag_neg
        neg_fraction = ag_neg / max(total, 1)

        timepoints.append({
            "day": day,
            "ag_positive": round(ag_pos),
            "ag_negative": round(ag_neg),
            "total_tumor": round(total),
            "ag_negative_fraction": round(neg_fraction, 4),
            "car_t_efficacy": round(car_t_efficacy, 3),
        })

    # Determine outcome
    final = timepoints[-1]
    nadir = min(timepoints, key=lambda x: x["total_tumor"])

    if final["total_tumor"] < initial_tumor_cells * 0.01:
        outcome = "Complete response"
    elif final["ag_negative_fraction"] > 0.5:
        outcome = "Antigen-negative relapse"
    elif final["total_tumor"] > initial_tumor_cells:
        outcome = "Progressive disease"
    else:
        outcome = "Partial response"

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "initial_burden": initial_tumor_cells,
        "initial_ag_negative_fraction": antigen_negative_fraction,
        "simulation_days": n_days,
        "outcome": outcome,
        "nadir": {"day": nadir["day"], "tumor_cells": nadir["total_tumor"]},
        "final_state": final,
        "timepoints": timepoints,
        "conclusion": (
            f"With {antigen_negative_fraction*100:.1f}% initial antigen-negative cells, "
            f"{'antigen escape drives relapse' if final['ag_negative_fraction'] > 0.3 else 'CAR-T maintains disease control'}. "
            f"Nadir reached at day {nadir['day']}."
        ),
    }


async def get_all_resistance_mechanisms() -> Dict[str, Any]:
    """Get all known CAR-T resistance mechanisms."""
    return {
        "total": len(_RESISTANCE_MECHANISMS),
        "categories": {
            cat: [code for code, m in _RESISTANCE_MECHANISMS.items() if m.category == cat]
            for cat in set(m.category for m in _RESISTANCE_MECHANISMS.values())
        },
        "mechanisms": {
            code: {
                "name": m.name, "category": m.category,
                "frequency_pct": m.frequency_pct,
                "onset_range_months": f"{m.onset_months[0]}-{m.onset_months[1]}",
                "mitigations": m.mitigations[:3],
                "literature_refs": m.literature_refs,
            }
            for code, m in _RESISTANCE_MECHANISMS.items()
        },
    }
