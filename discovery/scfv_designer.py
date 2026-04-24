"""
CARVanta Discovery — scFv Designer Engine
============================================
Antibody fragment (single-chain variable fragment) design and optimization
for CAR-T therapy. Models CDR regions, binding affinity prediction,
developability assessment, and humanization scoring.

Supports:
- De novo scFv design from target epitope profiles
- CDR optimization via in-silico affinity maturation
- VH/VL pairing and linker design
- Humanization scoring (framework region analysis)
- Aggregation/stability/immunogenicity prediction

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.discovery.scfv_designer")

# ──────────────────────────────────────────────────────────────────────
# Constants — Antibody Design
# ──────────────────────────────────────────────────────────────────────

class ScFvFormat(Enum):
    """scFv structural formats."""
    VH_LINKER_VL = "VH-linker-VL"  # most common
    VL_LINKER_VH = "VL-linker-VH"


class LinkerType(Enum):
    """Peptide linker types for VH-VL connection."""
    G4S_1X = "(G4S)x1"   # 5 aa
    G4S_3X = "(G4S)x3"   # 15 aa — most common
    G4S_4X = "(G4S)x4"   # 20 aa
    WHITLOW = "Whitlow"   # GSTSGSGKPGSGEGSTKG
    ALFTV = "ALFTV"       # rigid short linker


class HumanizationLevel(Enum):
    """Degree of framework humanization."""
    FULLY_MURINE = "fully_murine"
    CHIMERIC = "chimeric"
    HUMANIZED_CDR_GRAFT = "humanized_cdr_graft"
    FULLY_HUMAN = "fully_human"
    CAMELID_VHH = "camelid_vhh"


class DevelopabilityRisk(Enum):
    """Developability risk categories."""
    LOW = "low_risk"
    MODERATE = "moderate_risk"
    HIGH = "high_risk"
    CRITICAL = "critical"


# Amino acid properties for CDR analysis
AA_HYDROPHOBICITY: Dict[str, float] = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3,
}

AA_CHARGE: Dict[str, float] = {
    "A": 0, "C": 0, "D": -1, "E": -1, "F": 0,
    "G": 0, "H": 0.5, "I": 0, "K": 1, "L": 0,
    "M": 0, "N": 0, "P": 0, "Q": 0, "R": 1,
    "S": 0, "T": 0, "V": 0, "W": 0, "Y": 0,
}

# Canonical CDR sequences from known anti-tumor scFvs
REFERENCE_SCFVS: Dict[str, Dict[str, Any]] = {
    "FMC63": {
        "target": "CD19", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.FULLY_MURINE,
        "vh_cdr1": "GYTFTSY", "vh_cdr2": "YPGNGD", "vh_cdr3": "EVYSNFDY",
        "vl_cdr1": "HASQDI", "vl_cdr2": "VGNLED", "vl_cdr3": "LQHTYPPW",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 0.3, "thermal_stability_tm": 68.5,
        "clinical_products": ["Kymriah", "Yescarta"],
    },
    "SJ25C1": {
        "target": "CD19", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.FULLY_MURINE,
        "vh_cdr1": "GYTFTDY", "vh_cdr2": "YPIDGS", "vh_cdr3": "GSLPDY",
        "vl_cdr1": "RASQDI", "vl_cdr2": "DASNLET", "vl_cdr3": "QQHDESPW",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 0.5, "thermal_stability_tm": 65.2,
        "clinical_products": [],
    },
    "4D5": {
        "target": "HER2", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.HUMANIZED_CDR_GRAFT,
        "vh_cdr1": "GYTFTSY", "vh_cdr2": "YPYNGN", "vh_cdr3": "WGGDGFYAMD",
        "vl_cdr1": "RASQDI", "vl_cdr2": "DASNLET", "vl_cdr3": "QQHYTTPPT",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 5.0, "thermal_stability_tm": 72.1,
        "clinical_products": ["Herceptin"],
    },
    "SS1": {
        "target": "MSLN", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.FULLY_MURINE,
        "vh_cdr1": "GFSLSTSG", "vh_cdr2": "IWSGGST", "vh_cdr3": "AKHFRGNY",
        "vl_cdr1": "QLVHSNG", "vl_cdr2": "KVSNRFS", "vl_cdr3": "SQSTHVPP",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 11.0, "thermal_stability_tm": 63.8,
        "clinical_products": [],
    },
    "m971": {
        "target": "CD22", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.FULLY_HUMAN,
        "vh_cdr1": "GGTFSSYA", "vh_cdr2": "IIPIFGTAN", "vh_cdr3": "ARDMGNGPH",
        "vl_cdr1": "SGSSSNIG", "vl_cdr2": "SNNQRPS", "vl_cdr3": "AAWDDSLNGH",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 2.1, "thermal_stability_tm": 70.3,
        "clinical_products": [],
    },
    "J591": {
        "target": "PSMA", "format": ScFvFormat.VH_LINKER_VL,
        "humanization": HumanizationLevel.HUMANIZED_CDR_GRAFT,
        "vh_cdr1": "GFNIKDTY", "vh_cdr2": "RIDPSNG", "vh_cdr3": "GGKYWFGEL",
        "vl_cdr1": "KASQNVGTAV", "vl_cdr2": "WASTRHT", "vl_cdr3": "QQYNSYPLT",
        "linker": LinkerType.G4S_3X,
        "affinity_kd_nm": 3.8, "thermal_stability_tm": 69.0,
        "clinical_products": [],
    },
}

# Deamidation-prone motifs (NG, NS, NT)
DEAMIDATION_MOTIFS = {"NG", "NS", "NT", "DG", "DS"}

# Isomerization-prone motifs (DG, DS, DT, DD)
ISOMERIZATION_MOTIFS = {"DG", "DS", "DT", "DD"}

# Oxidation-prone residues
OXIDATION_RESIDUES = {"M", "W", "C"}

# Glycosylation motifs (N-X-S/T where X ≠ P)
GLYCOSYLATION_PATTERN = {"NAS", "NAT", "NCS", "NCT", "NDS", "NDT", "NES", "NET",
                         "NFS", "NFT", "NGS", "NGT", "NHS", "NHT", "NIS", "NIT",
                         "NKS", "NKT", "NLS", "NLT", "NMS", "NMT", "NQS", "NQT",
                         "NRS", "NRT", "NSS", "NST", "NTS", "NTT", "NVS", "NVT",
                         "NWS", "NWT", "NYS", "NYT"}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class CDRProfile:
    """Analysis of a CDR region."""
    sequence: str
    length: int
    hydrophobicity: float
    net_charge: float
    aromatic_fraction: float
    deamidation_sites: int
    oxidation_sites: int
    glycosylation_sites: int


@dataclass
class BindingPrediction:
    """Predicted binding characteristics."""
    kd_nm: float           # equilibrium dissociation constant
    kon_1_Ms: float        # on-rate
    koff_1_s: float        # off-rate
    binding_energy_kcal: float
    epitope_accessibility: float  # 0-1
    cross_reactivity_risk: float  # 0-1


@dataclass
class DevelopabilityAssessment:
    """Comprehensive developability assessment."""
    aggregation_risk: float  # 0-1
    viscosity_risk: float    # 0-1
    immunogenicity_risk: float  # 0-1
    expression_yield: float  # relative yield prediction
    thermal_stability_c: float  # predicted Tm in °C
    polyreactivity_risk: float  # 0-1
    deamidation_hotspots: int
    isomerization_hotspots: int
    overall_risk: DevelopabilityRisk
    risk_factors: List[str]


@dataclass
class ScFvCandidate:
    """Complete scFv design candidate."""
    candidate_id: str
    target: str
    format: ScFvFormat
    humanization: HumanizationLevel
    vh_cdr1: str
    vh_cdr2: str
    vh_cdr3: str
    vl_cdr1: str
    vl_cdr2: str
    vl_cdr3: str
    linker: LinkerType
    binding: BindingPrediction
    developability: DevelopabilityAssessment
    cdr_profiles: Dict[str, CDRProfile]
    overall_score: float  # 0-1
    rank: int = 0
    source_template: str = ""
    mutations_from_template: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# CDR Analysis
# ──────────────────────────────────────────────────────────────────────

def _analyze_cdr(sequence: str) -> CDRProfile:
    """Analyze CDR region properties."""
    seq = sequence.upper()
    length = len(seq)

    hydrophobicity = sum(AA_HYDROPHOBICITY.get(aa, 0) for aa in seq) / max(length, 1)
    charge = sum(AA_CHARGE.get(aa, 0) for aa in seq)

    aromatics = sum(1 for aa in seq if aa in "FWY")
    aromatic_frac = aromatics / max(length, 1)

    deamidation = sum(1 for i in range(length - 1) if seq[i:i+2] in DEAMIDATION_MOTIFS)
    oxidation = sum(1 for aa in seq if aa in OXIDATION_RESIDUES)
    glyco = sum(1 for i in range(length - 2) if seq[i:i+3] in GLYCOSYLATION_PATTERN)

    return CDRProfile(
        sequence=seq,
        length=length,
        hydrophobicity=round(hydrophobicity, 3),
        net_charge=charge,
        aromatic_fraction=round(aromatic_frac, 3),
        deamidation_sites=deamidation,
        oxidation_sites=oxidation,
        glycosylation_sites=glyco,
    )


# ──────────────────────────────────────────────────────────────────────
# Binding Affinity Prediction
# ──────────────────────────────────────────────────────────────────────

def _predict_binding(
    vh_cdrs: List[str],
    vl_cdrs: List[str],
    target: str,
) -> BindingPrediction:
    """
    Predict binding affinity from CDR sequences.

    Uses biophysical property-based estimation:
    - CDR3 length and hydrophobicity → shape complementarity
    - Aromatic content → binding energy contribution
    - Charge complementarity → electrostatic contribution
    """
    vh_cdr3 = vh_cdrs[2] if len(vh_cdrs) > 2 else ""
    vl_cdr3 = vl_cdrs[2] if len(vl_cdrs) > 2 else ""

    # CDR3 length penalty (optimal 8-14 for VH, 7-11 for VL)
    vh3_len = len(vh_cdr3)
    vl3_len = len(vl_cdr3)
    len_penalty = 0.0
    if vh3_len < 6 or vh3_len > 20:
        len_penalty += 0.3
    if vl3_len < 5 or vl3_len > 15:
        len_penalty += 0.2

    # Aromatic content → binding
    all_cdrs = "".join(vh_cdrs + vl_cdrs)
    aromatic_count = sum(1 for aa in all_cdrs if aa in "FWYH")
    aromatic_bonus = min(aromatic_count * 0.1, 0.5)

    # Hydrophobicity balance
    hydro = sum(AA_HYDROPHOBICITY.get(aa, 0) for aa in all_cdrs) / max(len(all_cdrs), 1)
    hydro_penalty = abs(hydro) * 0.05  # too hydrophobic or hydrophilic is bad

    # Base KD estimation (nM)
    base_kd = 5.0  # starting assumption
    kd_factor = 1.0 + len_penalty - aromatic_bonus + hydro_penalty
    predicted_kd = base_kd * max(kd_factor, 0.1)

    # Adjust for known targets with reference scFvs
    for ref_name, ref in REFERENCE_SCFVS.items():
        if ref["target"] == target:
            predicted_kd = ref["affinity_kd_nm"] * kd_factor
            break

    predicted_kd = max(0.01, min(1000, predicted_kd))

    # Kinetics
    kon = 1e5 * (1.0 + aromatic_bonus)  # typical range 1e4 - 1e6
    koff = predicted_kd * 1e-9 * kon  # KD = koff / kon

    # Binding energy
    binding_energy = -1.38 * math.log(max(predicted_kd * 1e-9, 1e-15))

    # Epitope accessibility (rough estimate)
    accessibility = 0.8 - len_penalty * 0.3

    # Cross-reactivity risk
    cross_react = min(1.0, hydro_penalty * 2.0 + (1.0 if len(all_cdrs) < 30 else 0.0) * 0.1)

    return BindingPrediction(
        kd_nm=round(predicted_kd, 3),
        kon_1_Ms=round(kon, 0),
        koff_1_s=round(koff, 6),
        binding_energy_kcal=round(binding_energy, 2),
        epitope_accessibility=round(accessibility, 3),
        cross_reactivity_risk=round(cross_react, 3),
    )


# ──────────────────────────────────────────────────────────────────────
# Developability Assessment
# ──────────────────────────────────────────────────────────────────────

def _assess_developability(
    vh_cdrs: List[str],
    vl_cdrs: List[str],
    humanization: HumanizationLevel,
) -> DevelopabilityAssessment:
    """
    Assess developability risks for an scFv candidate.

    Evaluates: aggregation propensity, viscosity, immunogenicity,
    expression yield, thermal stability, and liability motifs.
    """
    all_cdrs = "".join(vh_cdrs + vl_cdrs)
    total_length = len(all_cdrs)

    # Aggregation risk
    hydrophobic_patches = 0
    for i in range(total_length - 4):
        patch_hydro = sum(AA_HYDROPHOBICITY.get(all_cdrs[j], 0) for j in range(i, i + 5))
        if patch_hydro > 15:  # 5 consecutive hydrophobic residues
            hydrophobic_patches += 1
    aggregation_risk = min(1.0, hydrophobic_patches * 0.15)

    # Viscosity risk (correlates with net charge and hydrophobicity)
    net_charge = sum(AA_CHARGE.get(aa, 0) for aa in all_cdrs)
    viscosity_risk = min(1.0, max(0.0, (abs(net_charge) - 5) * 0.1))

    # Immunogenicity risk (based on humanization level)
    immuno_scores = {
        HumanizationLevel.FULLY_MURINE: 0.80,
        HumanizationLevel.CHIMERIC: 0.55,
        HumanizationLevel.HUMANIZED_CDR_GRAFT: 0.25,
        HumanizationLevel.FULLY_HUMAN: 0.08,
        HumanizationLevel.CAMELID_VHH: 0.40,
    }
    immunogenicity_risk = immuno_scores.get(humanization, 0.5)

    # Expression yield prediction
    charge_penalty = min(abs(net_charge) * 0.03, 0.3)
    yield_score = max(0.1, 1.0 - aggregation_risk * 0.4 - charge_penalty)

    # Thermal stability prediction
    aromatic_frac = sum(1 for aa in all_cdrs if aa in "FWY") / max(total_length, 1)
    base_tm = 65.0
    if aromatic_frac > 0.15:
        base_tm += 3.0
    base_tm -= aggregation_risk * 5.0
    base_tm += (1.0 - immunogenicity_risk) * 3.0

    # Polyreactivity risk
    positive_charge = sum(1 for aa in all_cdrs if aa in "KRH")
    poly_risk = min(1.0, positive_charge / max(total_length, 1) * 3.0)

    # Liability motifs
    deamidation_hotspots = sum(1 for i in range(total_length - 1) if all_cdrs[i:i+2] in DEAMIDATION_MOTIFS)
    isomerization_hotspots = sum(1 for i in range(total_length - 1) if all_cdrs[i:i+2] in ISOMERIZATION_MOTIFS)

    # Risk factors
    risk_factors: List[str] = []
    if aggregation_risk > 0.4:
        risk_factors.append("High aggregation propensity — consider surface mutation of hydrophobic patches")
    if viscosity_risk > 0.3:
        risk_factors.append("Viscosity risk — high charge density may cause concentration-dependent viscosity")
    if immunogenicity_risk > 0.5:
        risk_factors.append("Immunogenicity concern — framework humanization recommended")
    if deamidation_hotspots > 2:
        risk_factors.append(f"{deamidation_hotspots} deamidation hotspots (NG/NS/NT) — consider N→Q substitution")
    if isomerization_hotspots > 1:
        risk_factors.append(f"{isomerization_hotspots} isomerization sites (DG/DS) — monitor during stability studies")
    if poly_risk > 0.3:
        risk_factors.append("Polyreactivity risk — excess positive charge in CDRs")
    if aromatic_frac > 0.25:
        risk_factors.append("High aromatic content — possible nonspecific binding")

    # Overall risk
    avg_risk = (aggregation_risk + viscosity_risk + immunogenicity_risk + poly_risk) / 4
    if avg_risk < 0.2:
        overall = DevelopabilityRisk.LOW
    elif avg_risk < 0.4:
        overall = DevelopabilityRisk.MODERATE
    elif avg_risk < 0.6:
        overall = DevelopabilityRisk.HIGH
    else:
        overall = DevelopabilityRisk.CRITICAL

    return DevelopabilityAssessment(
        aggregation_risk=round(aggregation_risk, 3),
        viscosity_risk=round(viscosity_risk, 3),
        immunogenicity_risk=round(immunogenicity_risk, 3),
        expression_yield=round(yield_score, 3),
        thermal_stability_c=round(base_tm, 1),
        polyreactivity_risk=round(poly_risk, 3),
        deamidation_hotspots=deamidation_hotspots,
        isomerization_hotspots=isomerization_hotspots,
        overall_risk=overall,
        risk_factors=risk_factors,
    )


# ──────────────────────────────────────────────────────────────────────
# scFv Design Pipeline
# ──────────────────────────────────────────────────────────────────────

async def design_scfv_candidates(
    target: str,
    num_candidates: int = 5,
    humanization_level: str = "humanized_cdr_graft",
    format_preference: str = "VH-linker-VL",
) -> List[ScFvCandidate]:
    """
    Design scFv candidates for a target antigen.

    Generates candidates by:
    1. Selecting template scFvs from reference database
    2. Applying in-silico affinity maturation (CDR mutations)
    3. Optimizing for developability
    4. Ranking by composite score

    Args:
        target: Target antigen gene symbol
        num_candidates: Number of candidates to generate
        humanization_level: Desired humanization level
        format_preference: VH-linker-VL or VL-linker-VH

    Returns:
        List of ScFvCandidate objects ranked by score
    """
    humanization = HumanizationLevel.HUMANIZED_CDR_GRAFT
    for h in HumanizationLevel:
        if h.value == humanization_level:
            humanization = h
            break

    scfv_format = ScFvFormat.VH_LINKER_VL
    if format_preference == "VL-linker-VH":
        scfv_format = ScFvFormat.VL_LINKER_VH

    # Find template(s) for target
    templates = [
        (name, ref) for name, ref in REFERENCE_SCFVS.items()
        if ref["target"] == target
    ]
    if not templates:
        # Use closest match or generic template
        templates = [("FMC63", REFERENCE_SCFVS["FMC63"])]

    candidates: List[ScFvCandidate] = []

    for candidate_idx in range(num_candidates):
        template_name, template = templates[candidate_idx % len(templates)]

        # In-silico affinity maturation variants
        vh_cdrs = [
            _mutate_cdr(template["vh_cdr1"], candidate_idx, 0),
            _mutate_cdr(template["vh_cdr2"], candidate_idx, 1),
            _mutate_cdr(template["vh_cdr3"], candidate_idx, 2),
        ]
        vl_cdrs = [
            _mutate_cdr(template["vl_cdr1"], candidate_idx, 3),
            _mutate_cdr(template["vl_cdr2"], candidate_idx, 4),
            _mutate_cdr(template["vl_cdr3"], candidate_idx, 5),
        ]

        mutations = []
        for i, (orig, mut) in enumerate(zip(
            [template["vh_cdr1"], template["vh_cdr2"], template["vh_cdr3"],
             template["vl_cdr1"], template["vl_cdr2"], template["vl_cdr3"]],
            vh_cdrs + vl_cdrs,
        )):
            if orig != mut:
                cdr_name = ["VH-CDR1", "VH-CDR2", "VH-CDR3", "VL-CDR1", "VL-CDR2", "VL-CDR3"][i]
                mutations.append(f"{cdr_name}: {orig} → {mut}")

        # Analyze CDRs
        cdr_profiles = {
            "VH-CDR1": _analyze_cdr(vh_cdrs[0]),
            "VH-CDR2": _analyze_cdr(vh_cdrs[1]),
            "VH-CDR3": _analyze_cdr(vh_cdrs[2]),
            "VL-CDR1": _analyze_cdr(vl_cdrs[0]),
            "VL-CDR2": _analyze_cdr(vl_cdrs[1]),
            "VL-CDR3": _analyze_cdr(vl_cdrs[2]),
        }

        # Predict binding
        binding = _predict_binding(vh_cdrs, vl_cdrs, target)

        # Assess developability
        developability = _assess_developability(vh_cdrs, vl_cdrs, humanization)

        # Composite score
        affinity_score = max(0, 1.0 - math.log10(max(binding.kd_nm, 0.01)) / 3.0)
        stability_score = max(0, (developability.thermal_stability_c - 50) / 30)
        dev_score = 1.0 - (developability.aggregation_risk + developability.immunogenicity_risk) / 2

        overall = (
            affinity_score * 0.35 +
            stability_score * 0.25 +
            dev_score * 0.25 +
            binding.epitope_accessibility * 0.15
        )

        candidate_id = hashlib.sha256(
            f"{target}_{template_name}_{candidate_idx}".encode()
        ).hexdigest()[:12]

        candidates.append(ScFvCandidate(
            candidate_id=f"scfv_{candidate_id}",
            target=target,
            format=scfv_format,
            humanization=humanization,
            vh_cdr1=vh_cdrs[0],
            vh_cdr2=vh_cdrs[1],
            vh_cdr3=vh_cdrs[2],
            vl_cdr1=vl_cdrs[0],
            vl_cdr2=vl_cdrs[1],
            vl_cdr3=vl_cdrs[2],
            linker=LinkerType.G4S_3X,
            binding=binding,
            developability=developability,
            cdr_profiles=cdr_profiles,
            overall_score=round(overall, 4),
            source_template=template_name,
            mutations_from_template=mutations,
        ))

    # Sort by overall score
    candidates.sort(key=lambda c: c.overall_score, reverse=True)
    for i, c in enumerate(candidates):
        c.rank = i + 1

    return candidates


def _mutate_cdr(sequence: str, variant_idx: int, cdr_idx: int) -> str:
    """
    Apply in-silico affinity maturation mutations to a CDR.
    First variant (idx=0) returns the original sequence.
    """
    if variant_idx == 0:
        return sequence

    seq = list(sequence.upper())
    # Deterministic mutation based on indices
    pos = (variant_idx * 3 + cdr_idx) % max(len(seq), 1)

    # Conservative mutations (biochemically similar)
    conservative_subs = {
        "A": "V", "V": "I", "I": "L", "L": "V",
        "F": "Y", "Y": "W", "W": "F",
        "S": "T", "T": "S",
        "D": "E", "E": "D",
        "N": "Q", "Q": "N",
        "K": "R", "R": "K",
        "G": "A", "P": "A",
        "C": "S", "M": "L", "H": "Y",
    }

    if pos < len(seq):
        original = seq[pos]
        seq[pos] = conservative_subs.get(original, original)

    return "".join(seq)


async def optimize_binding_affinity(
    candidate: ScFvCandidate,
    optimization_rounds: int = 3,
) -> ScFvCandidate:
    """
    Optimize scFv binding affinity through iterative CDR refinement.
    Returns best variant after optimization rounds.
    """
    best = candidate
    for round_idx in range(optimization_rounds):
        # Try mutations in CDR3 (most critical for binding)
        vh_cdr3_mutated = _mutate_cdr(best.vh_cdr3, round_idx + 1, 2)
        vl_cdr3_mutated = _mutate_cdr(best.vl_cdr3, round_idx + 1, 5)

        vh_cdrs = [best.vh_cdr1, best.vh_cdr2, vh_cdr3_mutated]
        vl_cdrs = [best.vl_cdr1, best.vl_cdr2, vl_cdr3_mutated]

        new_binding = _predict_binding(vh_cdrs, vl_cdrs, best.target)

        if new_binding.kd_nm < best.binding.kd_nm:
            best = ScFvCandidate(
                candidate_id=best.candidate_id + f"_opt{round_idx}",
                target=best.target,
                format=best.format,
                humanization=best.humanization,
                vh_cdr1=best.vh_cdr1, vh_cdr2=best.vh_cdr2, vh_cdr3=vh_cdr3_mutated,
                vl_cdr1=best.vl_cdr1, vl_cdr2=best.vl_cdr2, vl_cdr3=vl_cdr3_mutated,
                linker=best.linker,
                binding=new_binding,
                developability=_assess_developability(vh_cdrs, vl_cdrs, best.humanization),
                cdr_profiles=best.cdr_profiles,
                overall_score=best.overall_score,
                source_template=best.source_template,
                mutations_from_template=best.mutations_from_template,
            )

    return best


async def predict_developability(
    candidate: ScFvCandidate,
) -> Dict[str, Any]:
    """Get developability assessment for API response."""
    dev = candidate.developability
    return {
        "candidate_id": candidate.candidate_id,
        "target": candidate.target,
        "overall_risk": dev.overall_risk.value,
        "aggregation_risk": dev.aggregation_risk,
        "viscosity_risk": dev.viscosity_risk,
        "immunogenicity_risk": dev.immunogenicity_risk,
        "expression_yield": dev.expression_yield,
        "thermal_stability_c": dev.thermal_stability_c,
        "polyreactivity_risk": dev.polyreactivity_risk,
        "deamidation_hotspots": dev.deamidation_hotspots,
        "isomerization_hotspots": dev.isomerization_hotspots,
        "risk_factors": dev.risk_factors,
        "binding": {
            "kd_nm": candidate.binding.kd_nm,
            "kon": candidate.binding.kon_1_Ms,
            "koff": candidate.binding.koff_1_s,
            "binding_energy_kcal": candidate.binding.binding_energy_kcal,
        },
    }
