"""
CARVanta – Genomic Profiling Engine
=====================================
Comprehensive genomic analysis for CAR-T therapy optimization.
Integrates with:
  - Somatic mutation profiling (TP53, MYC, BCL2, BCL6)
  - Copy number variation analysis
  - Gene expression signatures
  - Immune microenvironment characterization
  - Neoantigen prediction
  - Clonal heterogeneity assessment
  - Pharmacogenomic markers
  - Minimal residual disease (MRD) tracking
  - HLA typing for allogeneic considerations

Provides actionable genomic insights for treatment selection.
"""

import math
import random
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# Genomic Data Models
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SomaticMutation:
    """A somatic mutation with clinical annotation."""
    gene: str
    variant: str  # e.g., "R248W", "del17p"
    type: str  # missense, nonsense, frameshift, splice, deletion, amplification
    vaf: float  # variant allele frequency (0-1)
    tier: int  # 1=actionable, 2=potentially actionable, 3=VUS, 4=benign
    clinical_significance: str
    car_t_impact: str  # favorable, unfavorable, neutral
    evidence_level: str  # A, B, C, D


@dataclass
class CopyNumberVariation:
    """Copy number alteration."""
    gene: str
    alteration: str  # gain, loss, amplification, deletion
    copy_number: float  # estimated copies
    significance: str
    car_t_impact: str


@dataclass
class GeneExpressionSignature:
    """Gene expression-based classification."""
    signature_name: str
    classification: str
    score: float
    prognosis: str
    car_t_relevance: str


@dataclass
class GenomicProfile:
    """Complete genomic profile for a patient."""
    patient_id: str = ""
    cancer_type: str = "DLBCL"
    mutations: List[SomaticMutation] = field(default_factory=list)
    cnvs: List[CopyNumberVariation] = field(default_factory=list)
    expression_signatures: List[GeneExpressionSignature] = field(default_factory=list)
    tmb: float = 0.0  # tumor mutational burden (mut/Mb)
    msi_status: str = "MSS"  # MSS, MSI-L, MSI-H
    pd_l1_expression: float = 0.0  # 0-100 TPS
    immune_phenotype: str = "cold"  # hot, cold, excluded, desert


# ═══════════════════════════════════════════════════════════════════════════════
# Known CAR-T-Relevant Genes Database
# ═══════════════════════════════════════════════════════════════════════════════

CART_RELEVANT_GENES = {
    # Tumor suppressors — mutations often reduce CAR-T efficacy
    "TP53": {
        "role": "tumor_suppressor",
        "common_mutations": ["R175H", "R248W", "R273H", "Y220C", "G245S", "del17p"],
        "car_t_impact": "unfavorable",
        "impact_mechanism": "Reduced apoptotic response to CAR-T killing; chemo-resistant clones persist",
        "evidence": "A",
        "frequency_dlbcl": 0.21,
        "frequency_all": 0.08,
        "frequency_mcl": 0.28,
        "frequency_mm": 0.10,
        "pfs_hazard_ratio": 2.1,
    },
    "CDKN2A": {
        "role": "tumor_suppressor",
        "common_mutations": ["deletion", "p16 loss"],
        "car_t_impact": "unfavorable",
        "impact_mechanism": "Cell cycle deregulation; proliferative advantage for resistant clones",
        "evidence": "B",
        "frequency_dlbcl": 0.30,
        "frequency_all": 0.35,
        "frequency_mcl": 0.25,
        "frequency_mm": 0.05,
        "pfs_hazard_ratio": 1.6,
    },

    # Oncogenes — may drive resistance
    "MYC": {
        "role": "oncogene",
        "common_mutations": ["rearrangement", "amplification"],
        "car_t_impact": "unfavorable",
        "impact_mechanism": "Rapid proliferation outpaces CAR-T killing; associated with double-hit",
        "evidence": "A",
        "frequency_dlbcl": 0.12,
        "frequency_all": 0.05,
        "frequency_mcl": 0.08,
        "frequency_mm": 0.15,
        "pfs_hazard_ratio": 2.4,
    },
    "BCL2": {
        "role": "oncogene",
        "common_mutations": ["rearrangement", "t(14;18)", "overexpression"],
        "car_t_impact": "moderately_unfavorable",
        "impact_mechanism": "Anti-apoptotic; tumor cells resist CAR-T-mediated killing",
        "evidence": "B",
        "frequency_dlbcl": 0.25,
        "frequency_all": 0.02,
        "frequency_mcl": 0.05,
        "frequency_mm": 0.03,
        "pfs_hazard_ratio": 1.5,
    },
    "BCL6": {
        "role": "oncogene",
        "common_mutations": ["rearrangement"],
        "car_t_impact": "neutral",
        "impact_mechanism": "GCB subtype marker; generally neutral for CAR-T",
        "evidence": "C",
        "frequency_dlbcl": 0.30,
        "frequency_all": 0.01,
        "frequency_mcl": 0.02,
        "frequency_mm": 0.01,
        "pfs_hazard_ratio": 1.0,
    },

    # Immune evasion — directly affect CAR-T targeting
    "CD19": {
        "role": "target_antigen",
        "common_mutations": ["exon2_splice", "truncation", "loss"],
        "car_t_impact": "highly_unfavorable",
        "impact_mechanism": "Loss of target antigen → primary resistance or relapse",
        "evidence": "A",
        "frequency_dlbcl": 0.05,
        "frequency_all": 0.15,
        "frequency_mcl": 0.03,
        "frequency_mm": 0.0,
        "pfs_hazard_ratio": 5.0,
    },
    "CD22": {
        "role": "alternative_target",
        "common_mutations": ["downregulation", "splice_variant"],
        "car_t_impact": "context_dependent",
        "impact_mechanism": "Alternative target if CD19 lost; reduced efficacy if downregulated",
        "evidence": "B",
        "frequency_dlbcl": 0.08,
        "frequency_all": 0.10,
        "frequency_mcl": 0.05,
        "frequency_mm": 0.0,
        "pfs_hazard_ratio": 1.8,
    },
    "BCMA": {
        "role": "target_antigen",
        "common_mutations": ["biallelic_loss", "downregulation"],
        "car_t_impact": "highly_unfavorable",
        "impact_mechanism": "Loss of BCMA → resistance in multiple myeloma CAR-T",
        "evidence": "A",
        "frequency_dlbcl": 0.0,
        "frequency_all": 0.0,
        "frequency_mcl": 0.0,
        "frequency_mm": 0.06,
        "pfs_hazard_ratio": 4.5,
    },

    # Immune checkpoint / TME
    "B2M": {
        "role": "immune_evasion",
        "common_mutations": ["loss", "truncation"],
        "car_t_impact": "unfavorable",
        "impact_mechanism": "Loss of MHC-I presentation; reduced immune recognition",
        "evidence": "B",
        "frequency_dlbcl": 0.15,
        "frequency_all": 0.03,
        "frequency_mcl": 0.05,
        "frequency_mm": 0.05,
        "pfs_hazard_ratio": 1.7,
    },
    "CD58": {
        "role": "immune_evasion",
        "common_mutations": ["loss", "truncation", "downregulation"],
        "car_t_impact": "unfavorable",
        "impact_mechanism": "Disrupts immune synapse formation between T-cell and tumor",
        "evidence": "B",
        "frequency_dlbcl": 0.21,
        "frequency_all": 0.05,
        "frequency_mcl": 0.08,
        "frequency_mm": 0.02,
        "pfs_hazard_ratio": 1.9,
    },

    # T-cell exhaustion / TME modifiers
    "ARID1A": {
        "role": "chromatin_remodeling",
        "common_mutations": ["loss_of_function"],
        "car_t_impact": "context_dependent",
        "impact_mechanism": "Affects chromatin accessibility; may alter TME immune infiltration",
        "evidence": "C",
        "frequency_dlbcl": 0.08,
        "frequency_all": 0.02,
        "frequency_mcl": 0.05,
        "frequency_mm": 0.03,
        "pfs_hazard_ratio": 1.3,
    },
    "NOTCH1": {
        "role": "signaling",
        "common_mutations": ["activating", "gain_of_function"],
        "car_t_impact": "context_dependent",
        "impact_mechanism": "NOTCH signaling in T-cells can enhance or exhaust CAR-T cells",
        "evidence": "C",
        "frequency_dlbcl": 0.08,
        "frequency_all": 0.50,
        "frequency_mcl": 0.12,
        "frequency_mm": 0.02,
        "pfs_hazard_ratio": 1.2,
    },
    "EZH2": {
        "role": "epigenetic",
        "common_mutations": ["Y641F", "Y641N", "gain_of_function"],
        "car_t_impact": "potentially_favorable",
        "impact_mechanism": "EZH2 mutations may increase immunogenicity in GCB-DLBCL",
        "evidence": "B",
        "frequency_dlbcl": 0.22,
        "frequency_all": 0.01,
        "frequency_mcl": 0.02,
        "frequency_mm": 0.01,
        "pfs_hazard_ratio": 0.85,
    },
    "CREBBP": {
        "role": "epigenetic",
        "common_mutations": ["loss_of_function", "truncation"],
        "car_t_impact": "moderately_unfavorable",
        "impact_mechanism": "Disrupts MHC-II expression; reduces antigen presentation",
        "evidence": "B",
        "frequency_dlbcl": 0.18,
        "frequency_all": 0.15,
        "frequency_mcl": 0.05,
        "frequency_mm": 0.02,
        "pfs_hazard_ratio": 1.4,
    },
}


# Molecular subtypes
DLBCL_SUBTYPES = {
    "GCB": {
        "description": "Germinal Center B-cell like",
        "frequency": 0.45,
        "prognosis": "favorable",
        "car_t_response": "good",
        "typical_mutations": ["EZH2", "BCL2", "CREBBP", "KMT2D"],
        "expected_orr_modifier": 1.1,
    },
    "ABC": {
        "description": "Activated B-cell like",
        "frequency": 0.35,
        "prognosis": "unfavorable",
        "car_t_response": "moderate",
        "typical_mutations": ["MYD88", "CD79B", "CARD11", "TNFAIP3"],
        "expected_orr_modifier": 0.9,
    },
    "Unclassified": {
        "description": "Not classified",
        "frequency": 0.20,
        "prognosis": "intermediate",
        "car_t_response": "variable",
        "typical_mutations": [],
        "expected_orr_modifier": 1.0,
    },
}

GENETIC_CLUSTERS = {
    "MCD": {"genes": ["MYD88_L265P", "CD79B"], "prognosis": "poor", "frequency": 0.12},
    "BN2": {"genes": ["BCL6", "NOTCH2"], "prognosis": "favorable", "frequency": 0.15},
    "N1": {"genes": ["NOTCH1"], "prognosis": "poor", "frequency": 0.05},
    "EZB": {"genes": ["EZH2", "BCL2"], "prognosis": "favorable", "frequency": 0.20},
    "ST2": {"genes": ["SGK1", "TET2"], "prognosis": "favorable", "frequency": 0.08},
    "A53": {"genes": ["TP53_mutant", "aneuploidy"], "prognosis": "very_poor", "frequency": 0.10},
}


# ═══════════════════════════════════════════════════════════════════════════════
# Genomic Analysis Functions
# ═══════════════════════════════════════════════════════════════════════════════

def generate_genomic_profile(
    cancer_type: str = "DLBCL",
    patient_age: int = 55,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate a realistic genomic profile for simulation.
    Uses cancer-type-specific mutation frequencies.
    """
    rng = random.Random(seed or hash(f"{cancer_type}_{patient_age}"))

    cancer_key = _normalize_cancer(cancer_type)
    mutations = []
    cnvs = []

    # Generate mutations based on frequency
    for gene, info in CART_RELEVANT_GENES.items():
        freq_key = f"frequency_{cancer_key}"
        frequency = info.get(freq_key, info.get("frequency_dlbcl", 0.05))

        if rng.random() < frequency:
            variant = rng.choice(info["common_mutations"])
            vaf = round(rng.uniform(0.05, 0.65), 3)

            mut = SomaticMutation(
                gene=gene,
                variant=variant,
                type=_infer_mutation_type(variant),
                vaf=vaf,
                tier=1 if info["evidence"] == "A" else 2 if info["evidence"] == "B" else 3,
                clinical_significance=info["car_t_impact"],
                car_t_impact=info["car_t_impact"],
                evidence_level=info["evidence"],
            )
            mutations.append(mut)

            # Some mutations also manifest as CNVs
            if variant in ("deletion", "amplification", "loss", "del17p"):
                cnv = CopyNumberVariation(
                    gene=gene,
                    alteration=variant,
                    copy_number=0 if "del" in variant or "loss" in variant else rng.uniform(3, 8),
                    significance=info["car_t_impact"],
                    car_t_impact=info["car_t_impact"],
                )
                cnvs.append(cnv)

    # TMB calculation
    tmb = round(rng.gauss(6.5, 3.0), 1)
    tmb = max(0.5, tmb)

    # MSI status
    msi = "MSS"
    if rng.random() < 0.03:
        msi = "MSI-H"
    elif rng.random() < 0.08:
        msi = "MSI-L"

    # PD-L1
    pd_l1 = round(rng.gauss(15, 20), 1)
    pd_l1 = max(0, min(100, pd_l1))

    # Immune phenotype
    if pd_l1 > 50:
        immune_pheno = "hot"
    elif pd_l1 > 20:
        immune_pheno = rng.choice(["hot", "excluded"])
    elif pd_l1 > 5:
        immune_pheno = rng.choice(["excluded", "cold"])
    else:
        immune_pheno = rng.choice(["cold", "desert"])

    # Expression signatures
    signatures = _generate_expression_signatures(cancer_key, mutations, rng)

    # Molecular subtype (DLBCL)
    subtype_info = {}
    if cancer_key == "dlbcl":
        subtype = _classify_dlbcl_subtype(mutations, rng)
        subtype_info = {
            "subtype": subtype,
            "classification": DLBCL_SUBTYPES[subtype]["description"],
            "prognosis": DLBCL_SUBTYPES[subtype]["prognosis"],
            "car_t_response_modifier": DLBCL_SUBTYPES[subtype]["expected_orr_modifier"],
        }

    # Genetic cluster
    cluster = _identify_genetic_cluster(mutations)

    # Double-hit / triple-hit assessment
    double_hit = _assess_double_hit(mutations, cnvs)

    # CAR-T resistance risk
    resistance = _assess_resistance_risk(mutations, cnvs, cancer_key)

    # Actionable findings
    actionable = _get_actionable_findings(mutations, cnvs, cancer_key)

    return {
        "cancer_type": cancer_type,
        "mutations": [
            {
                "gene": m.gene,
                "variant": m.variant,
                "type": m.type,
                "vaf": m.vaf,
                "tier": m.tier,
                "clinical_significance": m.clinical_significance,
                "car_t_impact": m.car_t_impact,
                "evidence_level": m.evidence_level,
            }
            for m in mutations
        ],
        "copy_number_variations": [
            {
                "gene": c.gene,
                "alteration": c.alteration,
                "copy_number": round(c.copy_number, 1),
                "car_t_impact": c.car_t_impact,
            }
            for c in cnvs
        ],
        "expression_signatures": [
            {
                "name": s.signature_name,
                "classification": s.classification,
                "score": round(s.score, 3),
                "prognosis": s.prognosis,
                "car_t_relevance": s.car_t_relevance,
            }
            for s in signatures
        ],
        "tumor_mutational_burden": tmb,
        "tmb_category": "high" if tmb > 10 else "intermediate" if tmb > 5 else "low",
        "msi_status": msi,
        "pd_l1_expression": round(pd_l1, 1),
        "immune_phenotype": immune_pheno,
        "molecular_subtype": subtype_info,
        "genetic_cluster": cluster,
        "double_hit_assessment": double_hit,
        "resistance_risk": resistance,
        "actionable_findings": actionable,
        "total_mutations_detected": len(mutations),
        "tier1_mutations": len([m for m in mutations if m.tier == 1]),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def analyze_resistance_mechanisms(
    cancer_type: str = "DLBCL",
    target_antigen: str = "CD19",
    mutations: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Analyze potential CAR-T resistance mechanisms based on genomic profile.
    Returns risk assessment for each resistance pathway.
    """
    resistance_pathways = []

    # 1. Antigen loss/escape
    antigen_loss_risk = 0.15  # baseline
    if mutations:
        for mut in mutations:
            if mut.get("gene", "").upper() == target_antigen.upper():
                antigen_loss_risk = 0.85
                break
            if mut.get("gene") in ("CD58", "B2M"):
                antigen_loss_risk += 0.1

    resistance_pathways.append({
        "pathway": "Antigen Loss/Escape",
        "risk_score": round(min(1.0, antigen_loss_risk), 3),
        "risk_level": _risk_level(antigen_loss_risk),
        "mechanism": f"{target_antigen} downregulation, splice variants, or lineage switch",
        "monitoring": f"Serial {target_antigen} expression by flow cytometry",
        "mitigation": [
            f"Dual-target CAR-T ({target_antigen} + alternative target)",
            "Tandem/bivalent CAR design",
            "Bispecific antibody bridge",
        ],
    })

    # 2. T-cell exhaustion
    exhaustion_risk = 0.3
    if mutations:
        tp53_mutated = any(m.get("gene") == "TP53" for m in mutations)
        if tp53_mutated:
            exhaustion_risk += 0.2
    resistance_pathways.append({
        "pathway": "T-cell Exhaustion",
        "risk_score": round(min(1.0, exhaustion_risk), 3),
        "risk_level": _risk_level(exhaustion_risk),
        "mechanism": "Chronic antigen stimulation → PD-1/LAG-3/TIM-3 upregulation",
        "monitoring": "T-cell persistence monitoring by qPCR, exhaustion markers by flow",
        "mitigation": [
            "PD-1 checkpoint inhibitor combination",
            "Armored CAR-T with PD-1 disruption",
            "Rest period with drug holiday",
        ],
    })

    # 3. Immune evasion / TME suppression
    evasion_risk = 0.25
    if mutations:
        if any(m.get("gene") in ("B2M", "CD58", "CREBBP") for m in mutations):
            evasion_risk += 0.25
    resistance_pathways.append({
        "pathway": "Immune Microenvironment Suppression",
        "risk_score": round(min(1.0, evasion_risk), 3),
        "risk_level": _risk_level(evasion_risk),
        "mechanism": "Tumor-associated macrophages, MDSCs, Tregs suppress CAR-T function",
        "monitoring": "TME profiling, cytokine panel, T-reg quantification",
        "mitigation": [
            "CAR-T with cytokine secretion (armored CAR)",
            "Anti-CD47 combination",
            "Oncolytic virus pre-conditioning",
        ],
    })

    # 4. Clonal evolution
    clonal_risk = 0.2
    if mutations:
        high_vaf_count = sum(1 for m in mutations if m.get("vaf", 0) > 0.4)
        if high_vaf_count >= 2:
            clonal_risk += 0.15
    resistance_pathways.append({
        "pathway": "Clonal Evolution",
        "risk_score": round(min(1.0, clonal_risk), 3),
        "risk_level": _risk_level(clonal_risk),
        "mechanism": "Selection of pre-existing resistant clones under CAR-T pressure",
        "monitoring": "ctDNA monitoring, serial NGS for clonal dynamics",
        "mitigation": [
            "Multi-target CAR-T approach",
            "Early intensification based on MRD",
            "Maintenance therapy post-CAR-T",
        ],
    })

    # 5. Tumor cell-intrinsic resistance
    intrinsic_risk = 0.2
    if mutations:
        if any(m.get("gene") in ("TP53", "MYC") for m in mutations):
            intrinsic_risk += 0.3
        if any(m.get("gene") == "BCL2" for m in mutations):
            intrinsic_risk += 0.15
    resistance_pathways.append({
        "pathway": "Tumor Intrinsic Resistance",
        "risk_score": round(min(1.0, intrinsic_risk), 3),
        "risk_level": _risk_level(intrinsic_risk),
        "mechanism": "Anti-apoptotic signaling (BCL2), proliferative advantage (MYC)",
        "monitoring": "Response assessment imaging, PET/CT, ctDNA kinetics",
        "mitigation": [
            "Venetoclax combination (BCL2 inhibitor)",
            "Bridging therapy for tumor debulking",
            "Dose-intensified CAR-T approach",
        ],
    })

    # Overall resistance profile
    avg_risk = sum(p["risk_score"] for p in resistance_pathways) / len(resistance_pathways)

    return {
        "target_antigen": target_antigen,
        "cancer_type": cancer_type,
        "resistance_pathways": resistance_pathways,
        "overall_resistance_risk": round(avg_risk, 3),
        "overall_risk_level": _risk_level(avg_risk),
        "highest_risk_pathway": max(resistance_pathways, key=lambda p: p["risk_score"])["pathway"],
        "recommended_strategy": _recommend_resistance_strategy(resistance_pathways),
    }


def predict_mrd_trajectory(
    days: int = 180,
    cancer_type: str = "DLBCL",
    initial_burden: float = 50.0,
    treatment_response: str = "CR",
    genomic_risk: str = "standard",
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Simulate minimal residual disease trajectory post-CAR-T.
    Models MRD kinetics using bi-exponential decay with stochastic fluctuations.
    """
    rng = random.Random(seed or 42)

    # Response-dependent decay rate
    decay_rates = {
        "CR": 0.08,   # Complete response — fast clearance
        "PR": 0.04,   # Partial response
        "SD": 0.01,   # Stable disease
        "PD": -0.02,  # Progressive disease (growing)
    }
    base_decay = decay_rates.get(treatment_response, 0.04)

    # Genomic risk modifier
    risk_modifiers = {
        "standard": 1.0,
        "intermediate": 0.8,
        "high": 0.5,
        "very_high": 0.3,
    }
    risk_mod = risk_modifiers.get(genomic_risk, 1.0)
    effective_decay = base_decay * risk_mod

    # Simulate daily MRD values
    mrd_values = []
    relapse_day = None
    mrd_negative_day = None
    current_mrd = initial_burden

    for day in range(days):
        # Bi-exponential decay: fast initial + slow residual
        fast_component = math.exp(-effective_decay * day) * 0.7
        slow_component = math.exp(-effective_decay * 0.2 * day) * 0.3
        base_value = initial_burden * (fast_component + slow_component)

        # Add stochastic noise
        noise = rng.gauss(0, base_value * 0.05)
        current_mrd = max(0, base_value + noise)

        # Check for relapse (MRD starts rising after initial decline)
        if day > 60 and current_mrd > mrd_values[-1] * 1.5 and relapse_day is None:
            if genomic_risk in ("high", "very_high") and rng.random() < 0.3:
                relapse_day = day
                effective_decay = -0.03  # Switch to growth

        # MRD negativity threshold (10^-4)
        if current_mrd < 0.01 and mrd_negative_day is None:
            mrd_negative_day = day

        mrd_values.append(round(current_mrd, 6))

    # Calculate kinetics
    nadir_value = min(mrd_values)
    nadir_day = mrd_values.index(nadir_value)
    final_mrd = mrd_values[-1]
    is_mrd_negative = final_mrd < 0.01

    return {
        "trajectory": mrd_values[::max(1, days // 120)],  # Downsample
        "days_simulated": days,
        "initial_burden": initial_burden,
        "treatment_response": treatment_response,
        "genomic_risk": genomic_risk,
        "nadir_value": round(nadir_value, 6),
        "nadir_day": nadir_day,
        "final_mrd": round(final_mrd, 6),
        "is_mrd_negative": is_mrd_negative,
        "mrd_negative_day": mrd_negative_day,
        "relapse_detected": relapse_day is not None,
        "relapse_day": relapse_day,
        "clearance_rate": round(effective_decay * risk_mod, 4),
        "monitoring_recommendations": _mrd_monitoring_recs(is_mrd_negative, relapse_day),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_cancer(cancer_type: str) -> str:
    """Normalize cancer type to a key."""
    ct = cancer_type.upper()
    if "DLBCL" in ct or "DIFFUSE LARGE" in ct:
        return "dlbcl"
    if "ALL" in ct or "ACUTE LYMPHO" in ct:
        return "all"
    if "MCL" in ct or "MANTLE" in ct:
        return "mcl"
    if "MYELOMA" in ct or "MM" in ct:
        return "mm"
    return "dlbcl"


def _infer_mutation_type(variant: str) -> str:
    """Infer mutation type from variant description."""
    v = variant.lower()
    if "del" in v or "loss" in v:
        return "deletion"
    if "amp" in v:
        return "amplification"
    if "rearrangement" in v or "t(" in v:
        return "translocation"
    if "splice" in v:
        return "splice_site"
    if "truncat" in v:
        return "nonsense"
    if "overexp" in v or "gain" in v or "activat" in v:
        return "gain_of_function"
    if "downreg" in v:
        return "expression_change"
    return "missense"


def _risk_level(score: float) -> str:
    """Convert numeric risk to category."""
    if score > 0.7:
        return "high"
    if score > 0.4:
        return "moderate"
    if score > 0.2:
        return "low"
    return "very_low"


def _generate_expression_signatures(
    cancer_key: str,
    mutations: List[SomaticMutation],
    rng: random.Random,
) -> List[GeneExpressionSignature]:
    """Generate gene expression signatures based on mutations and cancer type."""
    signatures = []

    # Proliferation signature
    proliferation_score = rng.gauss(0.5, 0.2)
    if any(m.gene == "MYC" for m in mutations):
        proliferation_score += 0.3
    proliferation_score = max(0, min(1, proliferation_score))
    signatures.append(GeneExpressionSignature(
        signature_name="Proliferation Index",
        classification="high" if proliferation_score > 0.6 else "low",
        score=proliferation_score,
        prognosis="unfavorable" if proliferation_score > 0.7 else "favorable",
        car_t_relevance="High proliferation may outpace CAR-T killing",
    ))

    # Immune signature
    immune_score = rng.gauss(0.4, 0.2)
    if any(m.gene in ("B2M", "CD58") for m in mutations):
        immune_score -= 0.2
    immune_score = max(0, min(1, immune_score))
    signatures.append(GeneExpressionSignature(
        signature_name="Immune Infiltration Score",
        classification="inflamed" if immune_score > 0.5 else "non-inflamed",
        score=immune_score,
        prognosis="favorable" if immune_score > 0.5 else "unfavorable",
        car_t_relevance="Pre-existing immune infiltration may support CAR-T homing",
    ))

    # Stromal signature
    stromal_score = rng.gauss(0.35, 0.15)
    stromal_score = max(0, min(1, stromal_score))
    signatures.append(GeneExpressionSignature(
        signature_name="Stromal/Fibrosis Score",
        classification="fibrotic" if stromal_score > 0.5 else "non-fibrotic",
        score=stromal_score,
        prognosis="unfavorable" if stromal_score > 0.6 else "neutral",
        car_t_relevance="Dense stroma may impede CAR-T cell infiltration",
    ))

    # Apoptosis resistance
    apoptosis_score = rng.gauss(0.3, 0.15)
    if any(m.gene == "BCL2" for m in mutations):
        apoptosis_score += 0.3
    if any(m.gene == "TP53" for m in mutations):
        apoptosis_score += 0.2
    apoptosis_score = max(0, min(1, apoptosis_score))
    signatures.append(GeneExpressionSignature(
        signature_name="Apoptosis Resistance",
        classification="resistant" if apoptosis_score > 0.5 else "sensitive",
        score=apoptosis_score,
        prognosis="unfavorable" if apoptosis_score > 0.5 else "favorable",
        car_t_relevance="Apoptosis-resistant tumors may not respond to CAR-T killing",
    ))

    return signatures


def _classify_dlbcl_subtype(
    mutations: List[SomaticMutation],
    rng: random.Random,
) -> str:
    """Classify DLBCL subtype based on mutation profile."""
    gcb_genes = {"EZH2", "BCL2", "CREBBP", "KMT2D", "TNFRSF14"}
    abc_genes = {"MYD88", "CD79B", "CARD11", "TNFAIP3", "PIM1"}

    mut_genes = {m.gene for m in mutations}

    gcb_count = len(mut_genes & gcb_genes)
    abc_count = len(mut_genes & abc_genes)

    if gcb_count > abc_count:
        return "GCB"
    elif abc_count > gcb_count:
        return "ABC"
    else:
        return rng.choice(["GCB", "ABC", "Unclassified"])


def _identify_genetic_cluster(mutations: List[SomaticMutation]) -> Dict[str, Any]:
    """Identify genetic cluster based on co-occurring mutations."""
    mut_genes = {m.gene for m in mutations}

    for cluster_name, cluster_info in GENETIC_CLUSTERS.items():
        cluster_genes = set(g.split("_")[0] for g in cluster_info["genes"])
        overlap = mut_genes & cluster_genes
        if len(overlap) >= 1:
            return {
                "cluster": cluster_name,
                "matching_genes": list(overlap),
                "prognosis": cluster_info["prognosis"],
                "frequency": cluster_info["frequency"],
            }

    return {"cluster": "Unclassified", "matching_genes": [], "prognosis": "intermediate", "frequency": 0.30}


def _assess_double_hit(
    mutations: List[SomaticMutation],
    cnvs: List[CopyNumberVariation],
) -> Dict[str, Any]:
    """Assess double-hit/triple-hit lymphoma status."""
    mut_genes = {m.gene for m in mutations}
    cnv_genes = {c.gene for c in cnvs}
    all_altered = mut_genes | cnv_genes

    myc = "MYC" in all_altered
    bcl2 = "BCL2" in all_altered
    bcl6 = "BCL6" in all_altered

    if myc and bcl2 and bcl6:
        status = "Triple-hit"
    elif myc and (bcl2 or bcl6):
        status = "Double-hit"
    elif myc:
        status = "MYC-rearranged (single-hit)"
    else:
        status = "Non-double-hit"

    is_double_hit = status in ("Double-hit", "Triple-hit")

    return {
        "status": status,
        "is_double_hit": is_double_hit,
        "myc_altered": myc,
        "bcl2_altered": bcl2,
        "bcl6_altered": bcl6,
        "prognosis": "very_poor" if is_double_hit else "standard",
        "car_t_impact": "Significantly reduced long-term PFS" if is_double_hit else "Standard expectations",
        "recommendation": (
            "Consider intensive bridging + early consolidation strategies"
            if is_double_hit else "Proceed with standard CAR-T approach"
        ),
    }


def _assess_resistance_risk(
    mutations: List[SomaticMutation],
    cnvs: List[CopyNumberVariation],
    cancer_key: str,
) -> Dict[str, Any]:
    """Calculate overall CAR-T resistance risk from genomic features."""
    risk_score = 0.0
    risk_factors = []

    for m in mutations:
        gene_info = CART_RELEVANT_GENES.get(m.gene, {})
        hr = gene_info.get("pfs_hazard_ratio", 1.0)
        if hr > 1.5:
            contribution = min(0.2, (hr - 1.0) * 0.1)
            risk_score += contribution
            risk_factors.append({
                "gene": m.gene,
                "variant": m.variant,
                "hazard_ratio": hr,
                "contribution": round(contribution, 3),
            })

    risk_score = min(1.0, risk_score)

    return {
        "overall_risk": round(risk_score, 3),
        "risk_level": _risk_level(risk_score),
        "risk_factors": risk_factors,
        "predicted_pfs_modifier": round(max(0.3, 1.0 - risk_score), 3),
    }


def _get_actionable_findings(
    mutations: List[SomaticMutation],
    cnvs: List[CopyNumberVariation],
    cancer_key: str,
) -> List[Dict[str, Any]]:
    """Extract actionable genomic findings."""
    findings = []

    for m in mutations:
        if m.tier <= 2:
            gene_info = CART_RELEVANT_GENES.get(m.gene, {})
            action = {
                "gene": m.gene,
                "variant": m.variant,
                "tier": m.tier,
                "car_t_impact": m.car_t_impact,
                "recommendation": "",
            }

            if m.gene == "TP53":
                action["recommendation"] = "Consider dose-intensified approach; venetoclax combination may help"
            elif m.gene == "CD19":
                action["recommendation"] = "High risk of antigen escape; consider CD22 or dual-target CAR-T"
            elif m.gene == "BCL2":
                action["recommendation"] = "Venetoclax combination post-CAR-T may enhance tumor killing"
            elif m.gene == "MYC":
                action["recommendation"] = "Aggressive bridging recommended; monitor for early relapse"
            elif m.gene == "B2M":
                action["recommendation"] = "MHC-I loss detected; CAR-T may still work (MHC-independent killing)"
            elif m.gene == "EZH2":
                action["recommendation"] = "Favorable marker in GCB-DLBCL; may enhance immunogenicity"
            else:
                action["recommendation"] = f"Monitor {m.gene} status during treatment"

            findings.append(action)

    return findings


def _recommend_resistance_strategy(pathways: List[Dict]) -> str:
    """Generate overall resistance mitigation strategy."""
    highest = max(pathways, key=lambda p: p["risk_score"])
    if highest["risk_score"] > 0.6:
        return f"Primary concern: {highest['pathway']}. Recommend proactive mitigation with {highest['mitigation'][0]}."
    elif highest["risk_score"] > 0.3:
        return f"Moderate concern for {highest['pathway']}. Enhanced monitoring recommended."
    return "Standard risk profile. Proceed with standard monitoring protocols."


def _mrd_monitoring_recs(is_mrd_negative: bool, relapse_day: Optional[int]) -> List[str]:
    """Generate MRD monitoring recommendations."""
    recs = ["ctDNA monitoring monthly for Year 1, then quarterly"]
    if is_mrd_negative:
        recs.append("MRD-negative: Continue surveillance, consider treatment de-escalation")
    else:
        recs.append("MRD-positive: Consider consolidation therapy")
    if relapse_day:
        recs.append(f"Molecular relapse detected at Day {relapse_day} — consider re-treatment")
    recs.append("Flow cytometry for antigen expression at each assessment")
    return recs
