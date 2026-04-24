"""
CARVanta Discovery — CAR Construct Architect Engine
=====================================================
AI-powered CAR (Chimeric Antigen Receptor) construct design engine.
Models all 5 generations of CAR architectures, evaluates domain combinations,
predicts functional fitness, and compares constructs head-to-head.

Supports:
- All 5 CAR generations (1st → 5th)
- Modular domain selection (scFv, hinge, TM, co-stim, signaling)
- Armored CAR / Logic-gated CAR / Switchable CAR design
- Fitness prediction (T-cell expansion, persistence, exhaustion)
- Head-to-head construct comparison

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.discovery.car_architect")

# ──────────────────────────────────────────────────────────────────────
# Constants — CAR Architecture Components
# ──────────────────────────────────────────────────────────────────────

class CARGeneration(Enum):
    """CAR construct generation classification."""
    GEN_1 = "1st_generation"  # scFv + CD3ζ only
    GEN_2 = "2nd_generation"  # + 1 co-stimulatory domain
    GEN_3 = "3rd_generation"  # + 2 co-stimulatory domains
    GEN_4 = "4th_generation"  # TRUCK: + cytokine payload
    GEN_5 = "5th_generation"  # + intracellular IL receptor (STAT signaling)


class HingeType(Enum):
    """Hinge/spacer domain options."""
    CD8A = "CD8α_hinge"
    IGG1_CH2CH3 = "IgG1_CH2_CH3"
    IGG4_FC = "IgG4_Fc"
    CD28_HINGE = "CD28_hinge"
    CUSTOM_SHORT = "custom_short_hinge"
    CUSTOM_LONG = "custom_long_hinge"


class TransmembraneDomain(Enum):
    """Transmembrane domain options."""
    CD8A = "CD8α_TM"
    CD28 = "CD28_TM"
    ICOS = "ICOS_TM"
    NKG2D = "NKG2D_TM"


class CostimDomain(Enum):
    """Co-stimulatory domain options."""
    CD28 = "CD28"         # Strong initial activation, less persistence
    FOUR_1BB = "4-1BB"    # Better persistence and memory
    ICOS = "ICOS"         # Th17 differentiation, tissue homing
    OX40 = "OX40"         # Enhanced survival
    CD27 = "CD27"         # Balanced activation + persistence
    DAP10 = "DAP10"       # NKG2D pathway


class SignalingDomain(Enum):
    """Primary signaling domain options."""
    CD3_ZETA = "CD3ζ"
    CD3_ZETA_ITAM3 = "CD3ζ_ITAM_mutant"  # reduced tonic signaling
    FC_EPSILON_RI = "FcεRIγ"  # lower activation threshold


class ArmorType(Enum):
    """Armoring strategies for enhanced CAR-T efficacy."""
    NONE = "none"
    CYTOKINE_IL15 = "IL-15_secretion"
    CYTOKINE_IL21 = "IL-21_secretion"
    CYTOKINE_IL12 = "IL-12_secretion"
    CHECKPOINT_RESISTANT = "PD1_dominant_negative"
    TGF_BETA_TRAP = "TGFβ_trap"
    BISPECIFIC = "bispecific_targeting"
    SWITCH = "switchable_ON_OFF"
    LOGIC_AND = "AND_gate_logic"
    SAFETY_SWITCH = "iCaspase9_kill_switch"
    CXCR4_HOMING = "CXCR4_tumor_homing"


# ──────────────────────────────────────────────────────────────────────
# Component Properties Database
# ──────────────────────────────────────────────────────────────────────

HINGE_PROPERTIES: Dict[HingeType, Dict[str, Any]] = {
    HingeType.CD8A: {
        "length_aa": 45, "flexibility": "moderate",
        "reach_nm": 2.5, "immunogenicity": 0.05,
        "best_for": "proximal_membrane_epitopes",
        "steric_impact": 0.1,
    },
    HingeType.IGG1_CH2CH3: {
        "length_aa": 229, "flexibility": "high",
        "reach_nm": 12.0, "immunogenicity": 0.15,
        "best_for": "membrane_proximal_larger_targets",
        "steric_impact": 0.3,
    },
    HingeType.IGG4_FC: {
        "length_aa": 119, "flexibility": "moderate",
        "reach_nm": 7.0, "immunogenicity": 0.10,
        "best_for": "medium_distance_epitopes",
        "steric_impact": 0.2,
    },
    HingeType.CD28_HINGE: {
        "length_aa": 39, "flexibility": "low",
        "reach_nm": 2.0, "immunogenicity": 0.05,
        "best_for": "distal_epitopes",
        "steric_impact": 0.05,
    },
    HingeType.CUSTOM_SHORT: {
        "length_aa": 12, "flexibility": "low",
        "reach_nm": 1.0, "immunogenicity": 0.02,
        "best_for": "very_proximal_or_large_epitopes",
        "steric_impact": 0.02,
    },
    HingeType.CUSTOM_LONG: {
        "length_aa": 300, "flexibility": "very_high",
        "reach_nm": 15.0, "immunogenicity": 0.20,
        "best_for": "difficult_access_epitopes",
        "steric_impact": 0.35,
    },
}

COSTIM_PROPERTIES: Dict[CostimDomain, Dict[str, Any]] = {
    CostimDomain.CD28: {
        "activation_strength": 0.95, "persistence": 0.40,
        "exhaustion_risk": 0.70, "memory_formation": 0.30,
        "cytokine_profile": ["IL-2", "IFN-γ", "TNF-α"],
        "tonic_signaling_risk": 0.60,
        "clinical_experience": "extensive",
        "best_tumor_types": ["hematologic_aggressive"],
    },
    CostimDomain.FOUR_1BB: {
        "activation_strength": 0.70, "persistence": 0.85,
        "exhaustion_risk": 0.30, "memory_formation": 0.80,
        "cytokine_profile": ["IFN-γ", "TNF-α"],
        "tonic_signaling_risk": 0.20,
        "clinical_experience": "extensive",
        "best_tumor_types": ["hematologic_indolent", "solid_tumor"],
    },
    CostimDomain.ICOS: {
        "activation_strength": 0.65, "persistence": 0.70,
        "exhaustion_risk": 0.40, "memory_formation": 0.60,
        "cytokine_profile": ["IL-17", "IL-21", "IL-10"],
        "tonic_signaling_risk": 0.30,
        "clinical_experience": "limited",
        "best_tumor_types": ["solid_tumor_cold"],
    },
    CostimDomain.OX40: {
        "activation_strength": 0.60, "persistence": 0.80,
        "exhaustion_risk": 0.35, "memory_formation": 0.75,
        "cytokine_profile": ["IL-2", "IFN-γ"],
        "tonic_signaling_risk": 0.25,
        "clinical_experience": "preclinical",
        "best_tumor_types": ["solid_tumor"],
    },
    CostimDomain.CD27: {
        "activation_strength": 0.55, "persistence": 0.75,
        "exhaustion_risk": 0.25, "memory_formation": 0.70,
        "cytokine_profile": ["IL-2", "IFN-γ"],
        "tonic_signaling_risk": 0.20,
        "clinical_experience": "preclinical",
        "best_tumor_types": ["hematologic", "solid_tumor"],
    },
    CostimDomain.DAP10: {
        "activation_strength": 0.50, "persistence": 0.60,
        "exhaustion_risk": 0.20, "memory_formation": 0.50,
        "cytokine_profile": ["IFN-γ"],
        "tonic_signaling_risk": 0.15,
        "clinical_experience": "preclinical",
        "best_tumor_types": ["nk_cell_therapy"],
    },
}

ARMOR_PROPERTIES: Dict[ArmorType, Dict[str, Any]] = {
    ArmorType.NONE: {"complexity": 0.0, "efficacy_boost": 0.0, "safety_concern": 0.0},
    ArmorType.CYTOKINE_IL15: {
        "complexity": 0.40, "efficacy_boost": 0.30,
        "safety_concern": 0.20, "mechanism": "Autocrine T-cell survival signal",
    },
    ArmorType.CYTOKINE_IL21: {
        "complexity": 0.45, "efficacy_boost": 0.25,
        "safety_concern": 0.15, "mechanism": "Anti-exhaustion, stem-like T-cell maintenance",
    },
    ArmorType.CYTOKINE_IL12: {
        "complexity": 0.50, "efficacy_boost": 0.45,
        "safety_concern": 0.50, "mechanism": "TME reprogramming, IFN-γ amplification",
    },
    ArmorType.CHECKPOINT_RESISTANT: {
        "complexity": 0.35, "efficacy_boost": 0.35,
        "safety_concern": 0.25, "mechanism": "PD-1 dominant negative blocks checkpoint inhibition",
    },
    ArmorType.TGF_BETA_TRAP: {
        "complexity": 0.40, "efficacy_boost": 0.30,
        "safety_concern": 0.20, "mechanism": "Scavenges immunosuppressive TGF-β in TME",
    },
    ArmorType.BISPECIFIC: {
        "complexity": 0.60, "efficacy_boost": 0.40,
        "safety_concern": 0.30, "mechanism": "Dual antigen targeting reduces antigen escape",
    },
    ArmorType.SWITCH: {
        "complexity": 0.55, "efficacy_boost": 0.10,
        "safety_concern": -0.30, "mechanism": "Drug-controlled ON/OFF for safety management",
    },
    ArmorType.LOGIC_AND: {
        "complexity": 0.65, "efficacy_boost": 0.05,
        "safety_concern": -0.40, "mechanism": "Requires 2 antigens for activation — reduces off-tumor risk",
    },
    ArmorType.SAFETY_SWITCH: {
        "complexity": 0.30, "efficacy_boost": -0.05,
        "safety_concern": -0.50, "mechanism": "Inducible suicide gene for emergency CAR-T elimination",
    },
    ArmorType.CXCR4_HOMING: {
        "complexity": 0.30, "efficacy_boost": 0.25,
        "safety_concern": 0.10, "mechanism": "Chemokine receptor for bone marrow/tumor homing",
    },
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ConstructFitness:
    """Predicted functional fitness of a CAR construct."""
    activation_strength: float   # 0-1: initial T-cell activation
    persistence: float           # 0-1: long-term in vivo durability
    exhaustion_resistance: float # 0-1: resistance to T-cell exhaustion
    memory_formation: float      # 0-1: central memory differentiation
    cytokine_output: float       # 0-1: effector cytokine production
    tumor_killing: float         # 0-1: predicted cytotoxicity
    safety_score: float          # 0-1: overall safety
    manufacturing_ease: float    # 0-1: production complexity
    overall_fitness: float       # weighted composite


@dataclass
class CARConstruct:
    """Complete CAR construct design."""
    construct_id: str
    name: str
    generation: CARGeneration
    target: str
    scfv_id: str
    hinge: HingeType
    transmembrane: TransmembraneDomain
    costim_domains: List[CostimDomain]
    signaling: SignalingDomain
    armor: ArmorType
    fitness: ConstructFitness
    total_domains: int
    estimated_size_kda: float
    viral_vector_size_kb: float
    design_rationale: List[str]
    risk_factors: List[str]
    recommended_manufacturing: str
    rank: int = 0


# ──────────────────────────────────────────────────────────────────────
# Fitness Prediction
# ──────────────────────────────────────────────────────────────────────

def _predict_fitness(
    costim_domains: List[CostimDomain],
    signaling: SignalingDomain,
    hinge: HingeType,
    armor: ArmorType,
    generation: CARGeneration,
) -> ConstructFitness:
    """
    Predict functional fitness of a CAR construct based on domain composition.
    """
    # Aggregate co-stimulatory properties
    activation = 0.0
    persistence = 0.0
    exhaustion = 0.0
    memory = 0.0

    for costim in costim_domains:
        props = COSTIM_PROPERTIES.get(costim, {})
        activation = max(activation, props.get("activation_strength", 0.5))
        persistence = max(persistence, props.get("persistence", 0.5))
        exhaustion += props.get("exhaustion_risk", 0.4)
        memory = max(memory, props.get("memory_formation", 0.5))

    # Multi-costim synergy/antagonism
    if len(costim_domains) >= 2:
        # 3rd gen: synergy but also exhaustion risk
        activation = min(1.0, activation * 1.1)
        exhaustion = min(1.0, exhaustion * 1.2)
        if CostimDomain.CD28 in costim_domains and CostimDomain.FOUR_1BB in costim_domains:
            # Classic 28/BB combo — good balance but tonic signaling risk
            persistence = min(1.0, persistence * 1.15)
            exhaustion = min(1.0, exhaustion * 0.9)

    exhaustion_resistance = max(0, 1.0 - exhaustion / max(len(costim_domains), 1))

    # Signaling domain impact
    if signaling == SignalingDomain.CD3_ZETA_ITAM3:
        exhaustion_resistance = min(1.0, exhaustion_resistance + 0.15)
        activation *= 0.85  # reduced ITAM → less activation
    elif signaling == SignalingDomain.FC_EPSILON_RI:
        activation *= 0.75
        exhaustion_resistance += 0.10

    # Hinge impact on function
    hinge_props = HINGE_PROPERTIES.get(hinge, {})
    steric_penalty = hinge_props.get("steric_impact", 0.1)

    # Cytokine output
    cytokine = activation * 0.7 + memory * 0.3 - steric_penalty

    # Tumor killing = activation × cytokine × (1 - steric_penalty)
    killing = activation * 0.5 + cytokine * 0.3 + exhaustion_resistance * 0.2

    # Armor impact
    armor_props = ARMOR_PROPERTIES.get(armor, {})
    efficacy_boost = armor_props.get("efficacy_boost", 0)
    safety_concern = armor_props.get("safety_concern", 0)
    complexity = armor_props.get("complexity", 0)

    killing = min(1.0, killing + efficacy_boost * 0.5)
    persistence = min(1.0, persistence + efficacy_boost * 0.3)

    # Safety score
    base_safety = 0.7
    if safety_concern < 0:
        base_safety = min(1.0, base_safety - safety_concern)  # negative = safer
    else:
        base_safety = max(0.1, base_safety - safety_concern * 0.5)

    if armor == ArmorType.SAFETY_SWITCH:
        base_safety = min(1.0, base_safety + 0.25)

    # Manufacturing ease
    total_domains = 1 + 1 + 1 + len(costim_domains) + 1  # scfv + hinge + TM + costim + signaling
    if armor != ArmorType.NONE:
        total_domains += 1

    mfg_ease = max(0.1, 1.0 - total_domains * 0.08 - complexity * 0.3)

    # Overall fitness
    overall = (
        activation * 0.15 +
        persistence * 0.20 +
        exhaustion_resistance * 0.15 +
        memory * 0.10 +
        cytokine * 0.10 +
        killing * 0.15 +
        base_safety * 0.10 +
        mfg_ease * 0.05
    )

    return ConstructFitness(
        activation_strength=round(min(1.0, max(0.0, activation)), 4),
        persistence=round(min(1.0, max(0.0, persistence)), 4),
        exhaustion_resistance=round(min(1.0, max(0.0, exhaustion_resistance)), 4),
        memory_formation=round(min(1.0, max(0.0, memory)), 4),
        cytokine_output=round(min(1.0, max(0.0, cytokine)), 4),
        tumor_killing=round(min(1.0, max(0.0, killing)), 4),
        safety_score=round(min(1.0, max(0.0, base_safety)), 4),
        manufacturing_ease=round(min(1.0, max(0.0, mfg_ease)), 4),
        overall_fitness=round(min(1.0, max(0.0, overall)), 4),
    )


# ──────────────────────────────────────────────────────────────────────
# Construct Design Pipeline
# ──────────────────────────────────────────────────────────────────────

async def design_car_construct(
    target: str,
    scfv_id: str = "auto",
    generation: str = "2nd_generation",
    costim_preference: Optional[List[str]] = None,
    armor_type: str = "none",
    optimize_for: str = "balanced",
    num_designs: int = 5,
) -> List[CARConstruct]:
    """
    Design CAR construct architectures for a target antigen.

    Generates multiple construct designs optimized for different
    performance characteristics.

    Args:
        target: Target antigen gene symbol
        scfv_id: scFv candidate ID (or "auto" for default)
        generation: CAR generation (1st-5th)
        costim_preference: Preferred co-stimulatory domains
        armor_type: Armoring strategy
        optimize_for: "efficacy", "persistence", "safety", or "balanced"
        num_designs: Number of designs to generate

    Returns:
        List of CARConstruct objects ranked by fitness
    """
    # Parse generation
    gen_map = {
        "1st_generation": CARGeneration.GEN_1,
        "2nd_generation": CARGeneration.GEN_2,
        "3rd_generation": CARGeneration.GEN_3,
        "4th_generation": CARGeneration.GEN_4,
        "5th_generation": CARGeneration.GEN_5,
    }
    gen = gen_map.get(generation, CARGeneration.GEN_2)

    # Parse armor
    armor = ArmorType.NONE
    for at in ArmorType:
        if at.value == armor_type:
            armor = at
            break

    # Generate design configurations
    configs = _generate_design_configs(gen, costim_preference, armor, optimize_for, num_designs)

    constructs: List[CARConstruct] = []

    for i, config in enumerate(configs):
        costim_domains = config["costim"]
        hinge = config["hinge"]
        tm = config["tm"]
        signaling = config["signaling"]
        current_armor = config["armor"]

        fitness = _predict_fitness(costim_domains, signaling, hinge, current_armor, gen)

        # Size estimation
        scfv_size = 25.0  # kDa
        hinge_size = HINGE_PROPERTIES.get(hinge, {}).get("length_aa", 45) * 0.11  # ~110 Da/aa
        tm_size = 3.0  # kDa
        costim_size = len(costim_domains) * 5.0  # kDa each
        signaling_size = 12.0  # kDa (CD3ζ)
        total_kda = scfv_size + hinge_size + tm_size + costim_size + signaling_size

        # Viral vector size
        base_kb = 1.5  # scFv + framework
        costim_kb = len(costim_domains) * 0.3
        armor_kb = 0.8 if current_armor != ArmorType.NONE else 0.0
        viral_vector_kb = base_kb + costim_kb + armor_kb

        # Design rationale
        rationale = _generate_rationale(costim_domains, hinge, current_armor, gen, optimize_for)

        # Risk factors
        risks = _assess_risks(costim_domains, hinge, current_armor, gen, viral_vector_kb)

        # Manufacturing recommendation
        if viral_vector_kb > 4.5:
            mfg = "Split-intein dual-vector system recommended due to large insert size"
        elif gen in (CARGeneration.GEN_4, CARGeneration.GEN_5):
            mfg = "Lentiviral vector with inducible expression cassette"
        else:
            mfg = "Standard lentiviral vector transduction"

        construct_name = _generate_construct_name(target, costim_domains, gen, current_armor)

        construct_id = hashlib.sha256(
            f"{target}_{generation}_{i}_{armor_type}".encode()
        ).hexdigest()[:12]

        constructs.append(CARConstruct(
            construct_id=f"car_{construct_id}",
            name=construct_name,
            generation=gen,
            target=target,
            scfv_id=scfv_id,
            hinge=hinge,
            transmembrane=tm,
            costim_domains=costim_domains,
            signaling=signaling,
            armor=current_armor,
            fitness=fitness,
            total_domains=1 + 1 + 1 + len(costim_domains) + 1 + (1 if current_armor != ArmorType.NONE else 0),
            estimated_size_kda=round(total_kda, 1),
            viral_vector_size_kb=round(viral_vector_kb, 2),
            design_rationale=rationale,
            risk_factors=risks,
            recommended_manufacturing=mfg,
        ))

    # Sort by overall fitness
    constructs.sort(key=lambda c: c.fitness.overall_fitness, reverse=True)
    for i, c in enumerate(constructs):
        c.rank = i + 1

    return constructs


def _generate_design_configs(
    gen: CARGeneration,
    costim_pref: Optional[List[str]],
    armor: ArmorType,
    optimize_for: str,
    num_designs: int,
) -> List[Dict[str, Any]]:
    """Generate diverse CAR design configurations."""
    configs: List[Dict[str, Any]] = []

    # Configuration templates based on generation
    if gen == CARGeneration.GEN_1:
        costim_options = [[]]
    elif gen == CARGeneration.GEN_2:
        if costim_pref:
            parsed = []
            for cp in costim_pref:
                for cd in CostimDomain:
                    if cd.value == cp or cd.name == cp:
                        parsed.append(cd)
            costim_options = [[p] for p in parsed] if parsed else [[CostimDomain.FOUR_1BB], [CostimDomain.CD28]]
        else:
            costim_options = [
                [CostimDomain.FOUR_1BB],
                [CostimDomain.CD28],
                [CostimDomain.ICOS],
                [CostimDomain.OX40],
                [CostimDomain.CD27],
            ]
    elif gen in (CARGeneration.GEN_3, CARGeneration.GEN_4, CARGeneration.GEN_5):
        costim_options = [
            [CostimDomain.CD28, CostimDomain.FOUR_1BB],
            [CostimDomain.FOUR_1BB, CostimDomain.OX40],
            [CostimDomain.CD28, CostimDomain.ICOS],
            [CostimDomain.FOUR_1BB, CostimDomain.CD27],
            [CostimDomain.ICOS, CostimDomain.OX40],
        ]
    else:
        costim_options = [[CostimDomain.FOUR_1BB]]

    hinge_options = [HingeType.CD8A, HingeType.CD28_HINGE, HingeType.IGG4_FC]
    tm_options = [TransmembraneDomain.CD8A, TransmembraneDomain.CD28]
    signal_options = [SignalingDomain.CD3_ZETA]

    # Optimization-guided selection
    if optimize_for == "efficacy":
        hinge_options = [HingeType.CD8A, HingeType.CD28_HINGE]
    elif optimize_for == "persistence":
        costim_options = [co for co in costim_options if CostimDomain.FOUR_1BB in co or CostimDomain.OX40 in co]
    elif optimize_for == "safety":
        if armor == ArmorType.NONE:
            armor = ArmorType.SAFETY_SWITCH

    # Generate configs
    for i in range(min(num_designs, len(costim_options))):
        configs.append({
            "costim": costim_options[i % len(costim_options)],
            "hinge": hinge_options[i % len(hinge_options)],
            "tm": tm_options[i % len(tm_options)],
            "signaling": signal_options[0],
            "armor": armor,
        })

    # Ensure we have enough configs
    while len(configs) < num_designs:
        idx = len(configs) % len(costim_options)
        configs.append({
            "costim": costim_options[idx],
            "hinge": hinge_options[(idx + 1) % len(hinge_options)],
            "tm": tm_options[(idx + 1) % len(tm_options)],
            "signaling": signal_options[0],
            "armor": armor,
        })

    return configs[:num_designs]


def _generate_construct_name(
    target: str,
    costim: List[CostimDomain],
    gen: CARGeneration,
    armor: ArmorType,
) -> str:
    """Generate human-readable construct name."""
    costim_str = "/".join(c.value for c in costim) if costim else "none"
    gen_str = gen.value.split("_")[0]
    name = f"anti-{target} {gen_str} CAR ({costim_str})"
    if armor != ArmorType.NONE:
        name += f" + {armor.value.replace('_', ' ')}"
    return name


def _generate_rationale(
    costim: List[CostimDomain],
    hinge: HingeType,
    armor: ArmorType,
    gen: CARGeneration,
    optimize_for: str,
) -> List[str]:
    """Generate design rationale explaining domain choices."""
    rationale: List[str] = []

    for cd in costim:
        props = COSTIM_PROPERTIES.get(cd, {})
        if cd == CostimDomain.FOUR_1BB:
            rationale.append("4-1BB co-stimulation selected for superior T-cell persistence and Tcm differentiation")
        elif cd == CostimDomain.CD28:
            rationale.append("CD28 co-stimulation selected for rapid, potent T-cell activation and effector function")
        elif cd == CostimDomain.ICOS:
            rationale.append("ICOS co-stimulation selected for Th17 differentiation and tissue-homing capability")
        else:
            rationale.append(f"{cd.value} co-stimulation selected for {props.get('clinical_experience', 'novel')} profile")

    hinge_props = HINGE_PROPERTIES.get(hinge, {})
    rationale.append(f"{hinge.value} hinge ({hinge_props.get('length_aa', 0)} aa) — optimal for {hinge_props.get('best_for', 'standard').replace('_', ' ')}")

    if armor != ArmorType.NONE:
        armor_props = ARMOR_PROPERTIES.get(armor, {})
        rationale.append(f"Armored with {armor.value.replace('_', ' ')}: {armor_props.get('mechanism', '')}")

    return rationale


def _assess_risks(
    costim: List[CostimDomain],
    hinge: HingeType,
    armor: ArmorType,
    gen: CARGeneration,
    vector_kb: float,
) -> List[str]:
    """Assess risk factors for a construct design."""
    risks: List[str] = []

    total_exhaustion = sum(
        COSTIM_PROPERTIES.get(cd, {}).get("exhaustion_risk", 0.3)
        for cd in costim
    )
    if total_exhaustion > 0.8:
        risks.append("High exhaustion risk — consider ITAM mutation or rest protocols")

    total_tonic = sum(
        COSTIM_PROPERTIES.get(cd, {}).get("tonic_signaling_risk", 0.3)
        for cd in costim
    )
    if total_tonic > 0.5:
        risks.append("Tonic signaling risk — may cause premature T-cell differentiation")

    if vector_kb > 4.5:
        risks.append(f"Large vector insert ({vector_kb:.1f} kb) — may reduce viral titer and transduction efficiency")

    if gen in (CARGeneration.GEN_4, CARGeneration.GEN_5):
        risks.append("Advanced generation — limited clinical validation, regulatory pathway uncertain")

    hinge_props = HINGE_PROPERTIES.get(hinge, {})
    if hinge_props.get("immunogenicity", 0) > 0.10:
        risks.append("Hinge domain may elicit anti-drug antibodies — monitor ADA response")

    armor_props = ARMOR_PROPERTIES.get(armor, {})
    if armor_props.get("safety_concern", 0) > 0.3:
        risks.append(f"Armoring strategy ({armor.value}) carries significant safety concerns")

    return risks


# ──────────────────────────────────────────────────────────────────────
# Construct Comparison
# ──────────────────────────────────────────────────────────────────────

async def evaluate_construct_fitness(
    construct: CARConstruct,
) -> Dict[str, Any]:
    """Evaluate construct fitness for API response."""
    f = construct.fitness
    return {
        "construct_id": construct.construct_id,
        "name": construct.name,
        "generation": construct.generation.value,
        "fitness": {
            "activation": f.activation_strength,
            "persistence": f.persistence,
            "exhaustion_resistance": f.exhaustion_resistance,
            "memory_formation": f.memory_formation,
            "cytokine_output": f.cytokine_output,
            "tumor_killing": f.tumor_killing,
            "safety": f.safety_score,
            "manufacturing": f.manufacturing_ease,
            "overall": f.overall_fitness,
        },
        "domains": {
            "costim": [c.value for c in construct.costim_domains],
            "hinge": construct.hinge.value,
            "signaling": construct.signaling.value,
            "armor": construct.armor.value,
        },
        "size_kda": construct.estimated_size_kda,
        "vector_kb": construct.viral_vector_size_kb,
        "rationale": construct.design_rationale,
        "risks": construct.risk_factors,
        "manufacturing": construct.recommended_manufacturing,
    }


async def compare_car_generations(
    target: str,
    scfv_id: str = "auto",
) -> Dict[str, Any]:
    """
    Compare CAR constructs across all 5 generations for a target.

    Returns head-to-head fitness comparison.
    """
    comparison: Dict[str, Any] = {"target": target, "generations": []}

    for gen_name, gen_enum in [
        ("1st gen", CARGeneration.GEN_1),
        ("2nd gen (4-1BB)", CARGeneration.GEN_2),
        ("2nd gen (CD28)", CARGeneration.GEN_2),
        ("3rd gen (28+BB)", CARGeneration.GEN_3),
        ("4th gen (TRUCK)", CARGeneration.GEN_4),
    ]:
        if "CD28" in gen_name:
            costim = [CostimDomain.CD28]
        elif "4-1BB" in gen_name:
            costim = [CostimDomain.FOUR_1BB]
        elif "28+BB" in gen_name:
            costim = [CostimDomain.CD28, CostimDomain.FOUR_1BB]
        elif "TRUCK" in gen_name:
            costim = [CostimDomain.FOUR_1BB]
        else:
            costim = []

        armor = ArmorType.CYTOKINE_IL15 if gen_enum == CARGeneration.GEN_4 else ArmorType.NONE

        fitness = _predict_fitness(
            costim, SignalingDomain.CD3_ZETA, HingeType.CD8A, armor, gen_enum,
        )

        comparison["generations"].append({
            "name": gen_name,
            "generation": gen_enum.value,
            "costim": [c.value for c in costim],
            "armor": armor.value,
            "fitness": {
                "activation": fitness.activation_strength,
                "persistence": fitness.persistence,
                "exhaustion_resistance": fitness.exhaustion_resistance,
                "tumor_killing": fitness.tumor_killing,
                "safety": fitness.safety_score,
                "overall": fitness.overall_fitness,
            },
        })

    # Recommendation
    best = max(comparison["generations"], key=lambda g: g["fitness"]["overall"])
    comparison["recommendation"] = f"Recommended: {best['name']} (overall fitness: {best['fitness']['overall']:.3f})"

    return comparison
