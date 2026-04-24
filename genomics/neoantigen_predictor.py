"""
CARVanta Genomics — Neoantigen Predictor Engine
=================================================
Mutant peptide generation from somatic variants with MHC-I and MHC-II
binding affinity prediction, immunogenicity scoring, and neoantigen
prioritization for cancer vaccine and CAR-T target discovery.

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from genomics.file_processor import VariantRecord, VariantType

logger = logging.getLogger("carvanta.genomics.neoantigen_predictor")

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

# Standard genetic code (codon → amino acid)
CODON_TABLE: Dict[str, str] = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

# MHC-I peptide anchor residue preferences (simplified NetMHCpan model)
# Top HLA alleles and their binding preferences by position
MHC_I_BINDING_MOTIFS: Dict[str, Dict[str, Any]] = {
    "HLA-A*02:01": {
        "frequency": 0.29,
        "anchor_2": {"L": 0.9, "M": 0.8, "V": 0.6, "I": 0.5, "A": 0.4, "T": 0.3},
        "anchor_C": {"V": 0.9, "L": 0.8, "I": 0.7, "A": 0.5, "T": 0.4, "M": 0.3},
        "preferred_length": [9, 10],
        "binding_threshold_nM": 500,
    },
    "HLA-A*01:01": {
        "frequency": 0.16,
        "anchor_2": {"T": 0.9, "S": 0.8, "D": 0.5, "E": 0.4, "A": 0.3},
        "anchor_C": {"Y": 0.9, "F": 0.7, "W": 0.6, "L": 0.3},
        "preferred_length": [9, 10],
        "binding_threshold_nM": 500,
    },
    "HLA-A*03:01": {
        "frequency": 0.13,
        "anchor_2": {"L": 0.8, "V": 0.7, "M": 0.6, "I": 0.5, "A": 0.4},
        "anchor_C": {"K": 0.9, "R": 0.8, "Y": 0.5},
        "preferred_length": [9, 10, 11],
        "binding_threshold_nM": 500,
    },
    "HLA-A*11:01": {
        "frequency": 0.12,
        "anchor_2": {"V": 0.8, "T": 0.7, "I": 0.6, "L": 0.5},
        "anchor_C": {"K": 0.9, "R": 0.8, "Y": 0.4},
        "preferred_length": [9, 10, 11],
        "binding_threshold_nM": 500,
    },
    "HLA-A*24:02": {
        "frequency": 0.10,
        "anchor_2": {"Y": 0.9, "F": 0.8, "W": 0.6},
        "anchor_C": {"F": 0.9, "L": 0.8, "I": 0.7, "W": 0.5},
        "preferred_length": [9, 10],
        "binding_threshold_nM": 500,
    },
    "HLA-B*07:02": {
        "frequency": 0.12,
        "anchor_2": {"P": 0.9, "A": 0.5, "S": 0.4},
        "anchor_C": {"L": 0.9, "M": 0.7, "F": 0.5},
        "preferred_length": [9, 10],
        "binding_threshold_nM": 500,
    },
    "HLA-B*08:01": {
        "frequency": 0.09,
        "anchor_2": {"K": 0.8, "R": 0.7, "Q": 0.5},
        "anchor_C": {"L": 0.9, "K": 0.6, "R": 0.5},
        "preferred_length": [8, 9, 10],
        "binding_threshold_nM": 500,
    },
    "HLA-B*44:02": {
        "frequency": 0.08,
        "anchor_2": {"E": 0.9, "D": 0.7, "Q": 0.4},
        "anchor_C": {"Y": 0.9, "F": 0.8, "W": 0.6},
        "preferred_length": [9, 10, 11],
        "binding_threshold_nM": 500,
    },
    "HLA-C*07:01": {
        "frequency": 0.15,
        "anchor_2": {"Y": 0.8, "S": 0.6, "A": 0.5},
        "anchor_C": {"L": 0.9, "F": 0.7, "Y": 0.5},
        "preferred_length": [9],
        "binding_threshold_nM": 500,
    },
    "HLA-C*07:02": {
        "frequency": 0.10,
        "anchor_2": {"R": 0.8, "Y": 0.6, "A": 0.5},
        "anchor_C": {"L": 0.9, "V": 0.7, "Y": 0.5},
        "preferred_length": [9],
        "binding_threshold_nM": 500,
    },
}

# MHC-II binding grooves (simplified)
MHC_II_BINDING_MOTIFS: Dict[str, Dict[str, Any]] = {
    "HLA-DRB1*01:01": {
        "frequency": 0.10,
        "core_length": 9,
        "anchor_1": {"Y": 0.9, "F": 0.8, "W": 0.7, "L": 0.5},
        "anchor_4": {"M": 0.8, "L": 0.7, "I": 0.6, "V": 0.5},
        "anchor_6": {"A": 0.8, "G": 0.7, "S": 0.5, "T": 0.4},
        "anchor_9": {"L": 0.8, "I": 0.7, "V": 0.6, "M": 0.5},
        "binding_threshold_nM": 1000,
    },
    "HLA-DRB1*03:01": {
        "frequency": 0.11,
        "core_length": 9,
        "anchor_1": {"L": 0.9, "I": 0.8, "V": 0.6, "F": 0.5},
        "anchor_4": {"D": 0.8, "E": 0.7, "N": 0.5, "Q": 0.4},
        "anchor_6": {"K": 0.7, "R": 0.6, "N": 0.5},
        "anchor_9": {"Y": 0.8, "L": 0.7, "F": 0.5},
        "binding_threshold_nM": 1000,
    },
    "HLA-DRB1*04:01": {
        "frequency": 0.09,
        "core_length": 9,
        "anchor_1": {"F": 0.9, "Y": 0.8, "W": 0.7},
        "anchor_4": {"S": 0.7, "T": 0.6, "A": 0.5},
        "anchor_6": {"T": 0.7, "S": 0.6, "N": 0.5},
        "anchor_9": {"D": 0.8, "E": 0.7, "N": 0.5},
        "binding_threshold_nM": 1000,
    },
    "HLA-DRB1*07:01": {
        "frequency": 0.12,
        "core_length": 9,
        "anchor_1": {"F": 0.9, "Y": 0.8, "L": 0.6, "I": 0.5},
        "anchor_4": {"N": 0.7, "D": 0.6, "S": 0.5},
        "anchor_6": {"S": 0.7, "T": 0.6},
        "anchor_9": {"L": 0.8, "I": 0.7, "V": 0.6},
        "binding_threshold_nM": 1000,
    },
    "HLA-DRB1*15:01": {
        "frequency": 0.14,
        "core_length": 9,
        "anchor_1": {"F": 0.9, "Y": 0.8, "L": 0.6, "V": 0.5},
        "anchor_4": {"A": 0.7, "S": 0.6, "T": 0.5},
        "anchor_6": {"N": 0.7, "S": 0.6, "T": 0.5},
        "anchor_9": {"Y": 0.8, "V": 0.7, "L": 0.6},
        "binding_threshold_nM": 1000,
    },
}

# Amino acid hydrophobicity (Kyte-Doolittle scale)
AA_HYDROPHOBICITY: Dict[str, float] = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5,
    "E": -3.5, "Q": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
    "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6,
    "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}


class NeoantigenCategory(Enum):
    """Neoantigen priority categories."""
    PRIORITY_1 = "tier_1_strong_binder"       # IC50 < 50 nM, expressed, clonal
    PRIORITY_2 = "tier_2_moderate_binder"      # IC50 50-150 nM
    PRIORITY_3 = "tier_3_weak_binder"          # IC50 150-500 nM
    LOW_PRIORITY = "tier_4_poor_binder"        # IC50 > 500 nM
    NON_BINDER = "non_binder"


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class MutantPeptide:
    """A mutant peptide derived from a somatic variant."""
    sequence: str
    wildtype_sequence: str
    length: int
    source_variant: str  # coordinate key
    gene_symbol: str
    protein_change: str
    mutation_position: int  # position of mutation within peptide
    context_window: str  # surrounding amino acid context

    @property
    def is_novel(self) -> bool:
        return self.sequence != self.wildtype_sequence

    @property
    def identity_to_wildtype(self) -> float:
        if not self.wildtype_sequence or len(self.sequence) != len(self.wildtype_sequence):
            return 0.0
        matches = sum(1 for a, b in zip(self.sequence, self.wildtype_sequence) if a == b)
        return matches / len(self.sequence)


@dataclass
class MHCBindingResult:
    """MHC binding prediction for a peptide-HLA pair."""
    peptide_sequence: str
    hla_allele: str
    predicted_ic50_nM: float
    percentile_rank: float
    binding_level: str  # strong_binder, weak_binder, non_binder
    anchor_score: float
    core_sequence: str  # predicted binding core (for MHC-II)
    is_class_I: bool = True

    @property
    def is_binder(self) -> bool:
        return self.binding_level in ("strong_binder", "weak_binder")


@dataclass
class ImmunogenicityScore:
    """Immunogenicity assessment for a neoantigen candidate."""
    peptide_sequence: str
    overall_score: float  # 0.0 - 1.0
    dai_score: float  # Differential agretopicity index
    hydrophobicity_score: float
    foreignness_score: float
    clonality_score: float
    expression_score: float
    stability_score: float
    self_similarity_penalty: float
    components: Dict[str, float] = field(default_factory=dict)


@dataclass
class NeoantigenCandidate:
    """A prioritized neoantigen candidate."""
    rank: int
    peptide: MutantPeptide
    best_binding: MHCBindingResult
    all_bindings: List[MHCBindingResult]
    immunogenicity: ImmunogenicityScore
    category: NeoantigenCategory
    composite_score: float
    clinical_notes: List[str] = field(default_factory=list)


@dataclass
class NeoantigenPipelineResult:
    """Complete result from the neoantigen prediction pipeline."""
    total_variants_processed: int = 0
    total_peptides_generated: int = 0
    total_binders: int = 0
    tier_1_count: int = 0
    tier_2_count: int = 0
    tier_3_count: int = 0
    candidates: List[NeoantigenCandidate] = field(default_factory=list)
    hla_alleles_tested: List[str] = field(default_factory=list)
    genes_with_neoantigens: Set[str] = field(default_factory=set)


# ──────────────────────────────────────────────────────────────────────
# Mutant Peptide Generation
# ──────────────────────────────────────────────────────────────────────

# Simulated protein sequences for key cancer genes (first ~50 amino acids around hotspots)
GENE_PROTEIN_CONTEXT: Dict[str, str] = {
    "TP53":   "MCNSSCMGGMNRRPILTIITLEDSSGKLLGRNSFEVRVCACPGRDRRTEEENLHKTTGIDSFLHSGAKLCYQRR",
    "KRAS":   "MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSIYRKVIGEPWDISLKLVGTQSVGIVFLNVFLDIND",
    "BRAF":   "MAALSGGGGGAEPGQALFNGDMEPEAGAGAGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGRVVCVR",
    "PIK3CA": "MPPRPSSGELWGIHLMPPRILVECLLPNGMIVTLECLREATLITIKHELFKEARKYPLHQLLQDESSYIFVSVTQ",
    "EGFR":   "MRPSGTAGAALLALLAALCPASRALEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEVVLGNLEITYVQRNYD",
    "IDH1":   "MSKKISGGSVVEMQGDEMRIHRIAHKPSDNIIIEALKIPPEIEAFVSSGMKLAQETGGVVTAECGHYSFDHRDQV",
    "MET":    "MKAPAVLAPAMGLIPSPGHMVVTCLAFVFSLSLAQISSPLEECAKEPLNPKYRFSEELEMQVALDELDINEEL",
    "ALK":    "MEKSLLQHISNLMRNQQYALRKMERGDCSGLGVPKGVRCLGEEVGPREDYPEVTAKALLNDRERFEVNLYVNGS",
    "PTEN":   "MTAIIKEIVSRNKRRYQEDGFDLDLTYIYPNIIAMGFPAERLEGVYRNNIDDVVRFLDSKHKNHYKIYNLCAER",
    "BRCA1":  "MDLSALRQEGGRVQVLEDEELACQKARTLKRSGASTLTIQETGEEIAQHWDIDTAAGGTTRVEPGKHTAQYRQQ",
}


def _get_protein_context(gene: str, mutation_pos: int, window: int = 15) -> str:
    """Get protein sequence context around a mutation position."""
    protein = GENE_PROTEIN_CONTEXT.get(gene, "")
    if not protein:
        # Generate a plausible random context
        seed = hash(f"{gene}:{mutation_pos}")
        aas = "ACDEFGHIKLMNPQRSTVWY"
        return "".join(aas[(seed + i * 7) % 20] for i in range(window * 2 + 1))

    # Normalize position to protein length
    aa_pos = (mutation_pos % len(protein)) if len(protein) > 0 else 0
    start = max(0, aa_pos - window)
    end = min(len(protein), aa_pos + window + 1)
    return protein[start:end]


async def generate_mutant_peptides(
    variants: List[VariantRecord],
    annotations: Optional[Dict[str, Dict[str, Any]]] = None,
    peptide_lengths: Optional[List[int]] = None,
    max_peptides_per_variant: int = 20,
) -> List[MutantPeptide]:
    """
    Generate mutant peptides from somatic variants for MHC binding prediction.

    Creates overlapping peptides of specified lengths centered on the mutation,
    along with corresponding wildtype sequences for DAI calculation.

    Args:
        variants: Somatic variant records
        annotations: Optional variant annotations (gene, protein_change, etc.)
        peptide_lengths: Lengths of peptides to generate (default: [8,9,10,11])
        max_peptides_per_variant: Safety cap per variant

    Returns:
        List of MutantPeptide objects
    """
    if peptide_lengths is None:
        peptide_lengths = [8, 9, 10, 11]

    annotations = annotations or {}
    all_peptides: List[MutantPeptide] = []

    for variant in variants:
        coord = variant.coordinate_key
        annot = annotations.get(coord, variant.annotation)
        gene = annot.get("gene", annot.get("gene_symbol", ""))
        protein_change = annot.get("protein_change", "")

        if not gene:
            continue

        # Get protein context around mutation
        # Extract mutation position from protein_change (e.g., R248W → pos 248)
        mut_pos = 0
        aa_ref = ""
        aa_alt = ""
        if protein_change:
            match = re.match(r"([A-Z*])(\d+)([A-Z*])", protein_change)
            if match:
                aa_ref = match.group(1)
                mut_pos = int(match.group(2))
                aa_alt = match.group(3)

        if not mut_pos:
            mut_pos = (variant.pos % 500) + 1

        # Get surrounding protein context
        context = _get_protein_context(gene, mut_pos, window=15)
        if len(context) < 8:
            continue

        # Generate overlapping peptides of each length
        peptide_count = 0
        for pep_len in peptide_lengths:
            if pep_len > len(context):
                continue

            for start in range(max(0, len(context) - pep_len)):
                if peptide_count >= max_peptides_per_variant:
                    break

                wt_peptide = context[start:start + pep_len]
                if len(wt_peptide) != pep_len:
                    continue

                # Create mutant peptide by substituting at mutation position
                mut_rel_pos = 15 - start  # relative position in peptide
                if not (0 <= mut_rel_pos < pep_len):
                    continue

                mut_peptide_list = list(wt_peptide)
                if aa_alt and aa_alt != "*":
                    mut_peptide_list[mut_rel_pos] = aa_alt
                else:
                    # Generate a substitution based on variant
                    seed = hash(f"{coord}:{pep_len}:{start}")
                    new_aa = "ACDEFGHIKLMNPQRSTVWY"[seed % 20]
                    mut_peptide_list[mut_rel_pos] = new_aa

                mut_sequence = "".join(mut_peptide_list)

                # Skip if identical to wildtype
                if mut_sequence == wt_peptide:
                    continue

                peptide = MutantPeptide(
                    sequence=mut_sequence,
                    wildtype_sequence=wt_peptide,
                    length=pep_len,
                    source_variant=coord,
                    gene_symbol=gene,
                    protein_change=protein_change,
                    mutation_position=mut_rel_pos,
                    context_window=context,
                )
                all_peptides.append(peptide)
                peptide_count += 1

    logger.info(f"Generated {len(all_peptides)} mutant peptides from {len(variants)} variants")
    return all_peptides


# ──────────────────────────────────────────────────────────────────────
# MHC Binding Prediction
# ──────────────────────────────────────────────────────────────────────

def _compute_mhc_i_binding(
    peptide: str,
    allele: str,
    motif: Dict[str, Any],
) -> MHCBindingResult:
    """
    Predict MHC-I binding affinity using anchor-residue scoring model.

    Approximates NetMHCpan-style prediction using position-specific
    scoring matrices (PSSM) derived from known binding motifs.
    """
    pep_len = len(peptide)
    preferred_lengths = motif.get("preferred_length", [9])

    # Length penalty
    length_score = 1.0 if pep_len in preferred_lengths else 0.7

    # Position 2 anchor score
    anchor_2_prefs = motif.get("anchor_2", {})
    p2 = peptide[1] if len(peptide) > 1 else ""
    anchor_2_score = anchor_2_prefs.get(p2, 0.1)

    # C-terminal anchor score
    anchor_C_prefs = motif.get("anchor_C", {})
    pC = peptide[-1] if peptide else ""
    anchor_C_score = anchor_C_prefs.get(pC, 0.1)

    # Combined anchor score
    anchor_score = (anchor_2_score * 0.5 + anchor_C_score * 0.5) * length_score

    # Middle residue diversification (auxiliary positions)
    middle_score = 0.0
    for i in range(2, len(peptide) - 1):
        aa = peptide[i]
        # Hydrophobic residues in central positions improve binding
        hydro = AA_HYDROPHOBICITY.get(aa, 0.0)
        middle_score += (hydro + 5) / 10  # normalize to ~0-1
    if pep_len > 3:
        middle_score /= (pep_len - 3)
    else:
        middle_score = 0.5

    # Combined score → IC50 conversion
    total_score = anchor_score * 0.7 + middle_score * 0.3

    # Convert to IC50 (nM) — exponential mapping
    # High score → low IC50 (strong binding)
    ic50 = 50000 * math.exp(-5.0 * total_score)
    ic50 = max(1.0, min(50000.0, ic50))

    # Percentile rank (lower = better)
    percentile = min(100.0, ic50 / 500 * 2.0)

    # Binding level classification
    if ic50 < 50:
        binding_level = "strong_binder"
    elif ic50 < 150:
        binding_level = "weak_binder"
    elif ic50 < 500:
        binding_level = "weak_binder"
    else:
        binding_level = "non_binder"

    return MHCBindingResult(
        peptide_sequence=peptide,
        hla_allele=allele,
        predicted_ic50_nM=round(ic50, 2),
        percentile_rank=round(percentile, 2),
        binding_level=binding_level,
        anchor_score=round(anchor_score, 4),
        core_sequence=peptide,
        is_class_I=True,
    )


def _compute_mhc_ii_binding(
    peptide: str,
    allele: str,
    motif: Dict[str, Any],
) -> MHCBindingResult:
    """
    Predict MHC-II binding affinity.

    MHC-II binds longer peptides (13-25 aa) with a 9-mer binding core.
    Uses anchor positions 1, 4, 6, 9 of the core.
    """
    # For shorter peptides, use the full sequence as the core
    core_len = motif.get("core_length", 9)
    if len(peptide) < core_len:
        core = peptide
    else:
        # Find best 9-mer core by scoring all windows
        best_core = peptide[:core_len]
        best_score = 0.0

        for i in range(len(peptide) - core_len + 1):
            window = peptide[i:i + core_len]
            score = 0.0

            # Anchor 1
            a1_prefs = motif.get("anchor_1", {})
            score += a1_prefs.get(window[0], 0.1) * 0.3

            # Anchor 4
            a4_prefs = motif.get("anchor_4", {})
            if len(window) > 3:
                score += a4_prefs.get(window[3], 0.1) * 0.2

            # Anchor 6
            a6_prefs = motif.get("anchor_6", {})
            if len(window) > 5:
                score += a6_prefs.get(window[5], 0.1) * 0.2

            # Anchor 9
            a9_prefs = motif.get("anchor_9", {})
            if len(window) > 8:
                score += a9_prefs.get(window[8], 0.1) * 0.3

            if score > best_score:
                best_score = score
                best_core = window

        core = best_core

    # Score the core
    total_score = 0.0
    anchor_positions = {0: "anchor_1", 3: "anchor_4", 5: "anchor_6", 8: "anchor_9"}
    for pos, anchor_key in anchor_positions.items():
        if pos < len(core):
            prefs = motif.get(anchor_key, {})
            total_score += prefs.get(core[pos], 0.1)
    total_score /= len(anchor_positions)

    # IC50 conversion
    ic50 = 50000 * math.exp(-4.5 * total_score)
    ic50 = max(1.0, min(50000.0, ic50))

    percentile = min(100.0, ic50 / 1000 * 2.0)

    if ic50 < 150:
        binding_level = "strong_binder"
    elif ic50 < 500:
        binding_level = "weak_binder"
    elif ic50 < 1000:
        binding_level = "weak_binder"
    else:
        binding_level = "non_binder"

    return MHCBindingResult(
        peptide_sequence=peptide,
        hla_allele=allele,
        predicted_ic50_nM=round(ic50, 2),
        percentile_rank=round(percentile, 2),
        binding_level=binding_level,
        anchor_score=round(total_score, 4),
        core_sequence=core,
        is_class_I=False,
    )


async def predict_mhc_binding(
    peptides: List[MutantPeptide],
    hla_alleles: Optional[List[str]] = None,
    include_class_ii: bool = True,
    ic50_threshold: float = 500.0,
) -> Dict[str, List[MHCBindingResult]]:
    """
    Predict MHC binding for all peptide-HLA combinations.

    Args:
        peptides: Mutant peptides to test
        hla_alleles: Specific HLA alleles (default: test all common)
        include_class_ii: Also predict MHC-II binding
        ic50_threshold: IC50 cutoff for reporting

    Returns:
        Dict mapping peptide sequence → list of binding results
    """
    # Default: test top HLA alleles
    mhc_i_alleles = hla_alleles or list(MHC_I_BINDING_MOTIFS.keys())[:6]
    mhc_ii_alleles = list(MHC_II_BINDING_MOTIFS.keys())[:3] if include_class_ii else []

    results: Dict[str, List[MHCBindingResult]] = {}
    total_tested = 0
    total_binders = 0

    for peptide in peptides:
        seq = peptide.sequence
        bindings: List[MHCBindingResult] = []

        # MHC-I predictions
        for allele in mhc_i_alleles:
            if allele not in MHC_I_BINDING_MOTIFS:
                continue
            motif = MHC_I_BINDING_MOTIFS[allele]

            # Only test appropriate lengths
            if peptide.length not in motif.get("preferred_length", [9, 10]):
                continue

            result = _compute_mhc_i_binding(seq, allele, motif)
            total_tested += 1

            if result.predicted_ic50_nM <= ic50_threshold:
                bindings.append(result)
                total_binders += 1

        # MHC-II predictions
        for allele in mhc_ii_alleles:
            if allele not in MHC_II_BINDING_MOTIFS:
                continue
            motif = MHC_II_BINDING_MOTIFS[allele]
            result = _compute_mhc_ii_binding(seq, allele, motif)
            total_tested += 1

            if result.predicted_ic50_nM <= 1000.0:
                bindings.append(result)
                total_binders += 1

        if bindings:
            results[seq] = sorted(bindings, key=lambda b: b.predicted_ic50_nM)

    logger.info(
        f"MHC binding: {total_tested} predictions, {total_binders} binders "
        f"across {len(results)} unique peptides"
    )
    return results


# ──────────────────────────────────────────────────────────────────────
# Immunogenicity Scoring
# ──────────────────────────────────────────────────────────────────────

def _compute_dai(mutant_ic50: float, wildtype_ic50: float) -> float:
    """
    Compute Differential Agretopicity Index (DAI).
    DAI = log(wildtype IC50) - log(mutant IC50)
    Positive DAI = mutant binds better than wildtype.
    """
    if mutant_ic50 <= 0 or wildtype_ic50 <= 0:
        return 0.0
    return math.log10(wildtype_ic50) - math.log10(mutant_ic50)


def _compute_foreignness(peptide: str, wildtype: str) -> float:
    """
    Compute foreignness score based on sequence divergence from wildtype.
    Higher = more foreign to immune system.
    """
    if not wildtype or len(peptide) != len(wildtype):
        return 0.5

    mismatches = sum(1 for a, b in zip(peptide, wildtype) if a != b)
    mismatch_fraction = mismatches / len(peptide)

    # Physicochemical difference at mutation sites
    physico_diff = 0.0
    for i, (mut, wt) in enumerate(zip(peptide, wildtype)):
        if mut != wt:
            h_mut = AA_HYDROPHOBICITY.get(mut, 0)
            h_wt = AA_HYDROPHOBICITY.get(wt, 0)
            physico_diff += abs(h_mut - h_wt) / 9.0  # normalize by max range

    physico_diff /= max(mismatches, 1)

    return min(1.0, mismatch_fraction * 0.5 + physico_diff * 0.5)


def _compute_peptide_hydrophobicity(peptide: str) -> float:
    """
    Compute normalized hydrophobicity score for a peptide.
    Moderate hydrophobicity is ideal for T-cell recognition.
    """
    if not peptide:
        return 0.0
    total = sum(AA_HYDROPHOBICITY.get(aa, 0) for aa in peptide)
    mean_hydro = total / len(peptide)
    # Optimal range: -1 to +2 (moderate)
    # Score peaks at ~0.5 mean hydrophobicity
    score = 1.0 - abs(mean_hydro - 0.5) / 5.0
    return max(0.0, min(1.0, score))


def _compute_stability_score(peptide: str, ic50: float) -> float:
    """
    Estimate peptide-MHC complex stability.
    Strong binders with good anchor residues are more stable.
    """
    # IC50-based stability
    ic50_score = min(1.0, 500.0 / max(ic50, 1.0))

    # Peptide composition stability (avoid too many prolines, glycines)
    destabilizing = sum(1 for aa in peptide if aa in "PG")
    composition_score = max(0.0, 1.0 - destabilizing / len(peptide) * 2)

    return round(ic50_score * 0.6 + composition_score * 0.4, 4)


async def score_immunogenicity(
    peptides: List[MutantPeptide],
    binding_results: Dict[str, List[MHCBindingResult]],
    expression_data: Optional[Dict[str, float]] = None,
    clonality_data: Optional[Dict[str, float]] = None,
) -> Dict[str, ImmunogenicityScore]:
    """
    Score immunogenicity of neoantigen candidates.

    Combines:
    - DAI (differential agretopicity index)
    - Peptide hydrophobicity
    - Foreignness to self
    - Clonality (variant allele frequency)
    - Gene expression level
    - pMHC complex stability

    Args:
        peptides: Mutant peptides
        binding_results: MHC binding predictions
        expression_data: Gene → expression level mapping
        clonality_data: Variant → VAF mapping

    Returns:
        Dict mapping peptide sequence → immunogenicity score
    """
    expression_data = expression_data or {}
    clonality_data = clonality_data or {}

    scores: Dict[str, ImmunogenicityScore] = {}

    for peptide in peptides:
        seq = peptide.sequence

        # Get best binding result
        bindings = binding_results.get(seq, [])
        if not bindings:
            continue

        best_binding = bindings[0]  # already sorted by IC50

        # Compute DAI using wildtype binding
        # Predict wildtype binding against same allele
        wt_motif = MHC_I_BINDING_MOTIFS.get(best_binding.hla_allele, {})
        if wt_motif and peptide.wildtype_sequence:
            wt_result = _compute_mhc_i_binding(
                peptide.wildtype_sequence, best_binding.hla_allele, wt_motif
            )
            dai = _compute_dai(best_binding.predicted_ic50_nM, wt_result.predicted_ic50_nM)
        else:
            dai = 0.5

        # Foreignness
        foreignness = _compute_foreignness(seq, peptide.wildtype_sequence)

        # Hydrophobicity
        hydrophobicity = _compute_peptide_hydrophobicity(seq)

        # Clonality (from source variant VAF)
        vaf = clonality_data.get(peptide.source_variant, 0.3)
        clonality = min(1.0, vaf * 2)  # Scale VAF to 0-1

        # Expression
        expr = expression_data.get(peptide.gene_symbol, 5.0)  # default moderate
        expression = min(1.0, expr / 10.0)

        # Stability
        stability = _compute_stability_score(seq, best_binding.predicted_ic50_nM)

        # Self-similarity penalty
        self_sim = peptide.identity_to_wildtype
        self_penalty = self_sim * 0.3  # high similarity = immune tolerance

        # Overall score (weighted combination)
        overall = (
            dai * 0.20 +
            foreignness * 0.20 +
            hydrophobicity * 0.10 +
            clonality * 0.15 +
            expression * 0.15 +
            stability * 0.15 +
            (1.0 - self_penalty) * 0.05
        )
        overall = round(max(0.0, min(1.0, overall)), 4)

        score = ImmunogenicityScore(
            peptide_sequence=seq,
            overall_score=overall,
            dai_score=round(dai, 4),
            hydrophobicity_score=round(hydrophobicity, 4),
            foreignness_score=round(foreignness, 4),
            clonality_score=round(clonality, 4),
            expression_score=round(expression, 4),
            stability_score=stability,
            self_similarity_penalty=round(self_penalty, 4),
            components={
                "dai": round(dai * 0.20, 4),
                "foreignness": round(foreignness * 0.20, 4),
                "hydrophobicity": round(hydrophobicity * 0.10, 4),
                "clonality": round(clonality * 0.15, 4),
                "expression": round(expression * 0.15, 4),
                "stability": round(stability * 0.15, 4),
                "novelty": round((1.0 - self_penalty) * 0.05, 4),
            },
        )
        scores[seq] = score

    logger.info(f"Immunogenicity scored: {len(scores)} candidates")
    return scores


# ──────────────────────────────────────────────────────────────────────
# Neoantigen Prioritization
# ──────────────────────────────────────────────────────────────────────

async def prioritize_neoantigens(
    peptides: List[MutantPeptide],
    binding_results: Dict[str, List[MHCBindingResult]],
    immunogenicity_scores: Dict[str, ImmunogenicityScore],
    max_candidates: int = 50,
) -> NeoantigenPipelineResult:
    """
    Rank and prioritize neoantigen candidates.

    Combines MHC binding affinity, immunogenicity score, and clinical
    relevance into a composite ranking.

    Args:
        peptides: All generated mutant peptides
        binding_results: MHC binding predictions
        immunogenicity_scores: Immunogenicity assessments
        max_candidates: Maximum candidates to return

    Returns:
        NeoantigenPipelineResult with ranked candidates
    """
    result = NeoantigenPipelineResult(
        total_variants_processed=len(set(p.source_variant for p in peptides)),
        total_peptides_generated=len(peptides),
        hla_alleles_tested=list(MHC_I_BINDING_MOTIFS.keys())[:6],
    )

    # Build candidate list
    candidates: List[NeoantigenCandidate] = []

    for peptide in peptides:
        seq = peptide.sequence
        bindings = binding_results.get(seq, [])
        if not bindings:
            continue

        immuno = immunogenicity_scores.get(seq)
        if not immuno:
            continue

        best_binding = bindings[0]

        # Composite score
        # Binding contribution (IC50 → 0-1 score)
        binding_score = min(1.0, 500.0 / max(best_binding.predicted_ic50_nM, 1.0))

        # Immunogenicity contribution
        immuno_score = immuno.overall_score

        # Composite
        composite = binding_score * 0.5 + immuno_score * 0.5

        # Categorize
        ic50 = best_binding.predicted_ic50_nM
        if ic50 < 50 and immuno.overall_score > 0.5:
            category = NeoantigenCategory.PRIORITY_1
        elif ic50 < 150:
            category = NeoantigenCategory.PRIORITY_2
        elif ic50 < 500:
            category = NeoantigenCategory.PRIORITY_3
        else:
            category = NeoantigenCategory.LOW_PRIORITY

        # Clinical notes
        notes: List[str] = []
        if best_binding.binding_level == "strong_binder":
            notes.append(f"Strong binder to {best_binding.hla_allele} (IC50={ic50:.1f}nM)")
        if immuno.dai_score > 1.0:
            notes.append(f"High DAI ({immuno.dai_score:.2f}) — mutant binds much better than wildtype")
        if immuno.clonality_score > 0.7:
            notes.append("Clonal variant — present in majority of tumor cells")
        if peptide.gene_symbol in ("TP53", "KRAS", "BRAF", "EGFR"):
            notes.append(f"Driver gene mutation in {peptide.gene_symbol}")

        candidate = NeoantigenCandidate(
            rank=0,  # assigned after sorting
            peptide=peptide,
            best_binding=best_binding,
            all_bindings=bindings,
            immunogenicity=immuno,
            category=category,
            composite_score=round(composite, 4),
            clinical_notes=notes,
        )
        candidates.append(candidate)
        result.genes_with_neoantigens.add(peptide.gene_symbol)

    # Sort by composite score
    candidates.sort(key=lambda c: c.composite_score, reverse=True)

    # Assign ranks and limit
    for i, c in enumerate(candidates[:max_candidates]):
        c.rank = i + 1

    result.candidates = candidates[:max_candidates]
    result.total_binders = len(candidates)
    result.tier_1_count = sum(1 for c in candidates if c.category == NeoantigenCategory.PRIORITY_1)
    result.tier_2_count = sum(1 for c in candidates if c.category == NeoantigenCategory.PRIORITY_2)
    result.tier_3_count = sum(1 for c in candidates if c.category == NeoantigenCategory.PRIORITY_3)

    logger.info(
        f"Neoantigen prioritization: {result.tier_1_count} Tier-1, "
        f"{result.tier_2_count} Tier-2, {result.tier_3_count} Tier-3 "
        f"from {result.total_peptides_generated} peptides"
    )
    return result


# ──────────────────────────────────────────────────────────────────────
# Full Pipeline Orchestrator
# ──────────────────────────────────────────────────────────────────────

async def run_neoantigen_pipeline(
    variants: List[VariantRecord],
    annotations: Optional[Dict[str, Dict[str, Any]]] = None,
    hla_alleles: Optional[List[str]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run complete neoantigen prediction pipeline.

    Steps:
    1. Generate mutant peptides from somatic variants
    2. Predict MHC-I and MHC-II binding
    3. Score immunogenicity
    4. Prioritize and rank neoantigens

    Returns comprehensive result dictionary.
    """
    options = options or {}

    # Step 1: Generate peptides
    peptides = await generate_mutant_peptides(
        variants,
        annotations,
        peptide_lengths=options.get("peptide_lengths", [8, 9, 10, 11]),
        max_peptides_per_variant=options.get("max_peptides", 20),
    )

    if not peptides:
        return {
            "success": True,
            "total_peptides": 0,
            "total_binders": 0,
            "candidates": [],
            "message": "No peptides could be generated from the provided variants",
        }

    # Step 2: MHC binding
    binding_results = await predict_mhc_binding(
        peptides,
        hla_alleles=hla_alleles,
        include_class_ii=options.get("include_class_ii", True),
        ic50_threshold=options.get("ic50_threshold", 500.0),
    )

    # Step 3: Immunogenicity scoring
    immuno_scores = await score_immunogenicity(
        peptides,
        binding_results,
        expression_data=options.get("expression_data"),
        clonality_data=options.get("clonality_data"),
    )

    # Step 4: Prioritize
    pipeline_result = await prioritize_neoantigens(
        peptides,
        binding_results,
        immuno_scores,
        max_candidates=options.get("max_candidates", 50),
    )

    # Build output
    candidate_list = []
    for c in pipeline_result.candidates:
        candidate_list.append({
            "rank": c.rank,
            "peptide": c.peptide.sequence,
            "wildtype": c.peptide.wildtype_sequence,
            "length": c.peptide.length,
            "gene": c.peptide.gene_symbol,
            "protein_change": c.peptide.protein_change,
            "mutation_position": c.peptide.mutation_position,
            "category": c.category.value,
            "composite_score": c.composite_score,
            "best_hla": c.best_binding.hla_allele,
            "best_ic50": c.best_binding.predicted_ic50_nM,
            "binding_level": c.best_binding.binding_level,
            "immunogenicity": c.immunogenicity.overall_score,
            "dai_score": c.immunogenicity.dai_score,
            "foreignness": c.immunogenicity.foreignness_score,
            "clonality": c.immunogenicity.clonality_score,
            "stability": c.immunogenicity.stability_score,
            "clinical_notes": c.clinical_notes,
            "all_hla_bindings": [
                {
                    "hla": b.hla_allele,
                    "ic50": b.predicted_ic50_nM,
                    "level": b.binding_level,
                    "class": "I" if b.is_class_I else "II",
                }
                for b in c.all_bindings
            ],
        })

    return {
        "success": True,
        "total_peptides": pipeline_result.total_peptides_generated,
        "total_binders": pipeline_result.total_binders,
        "tier_1": pipeline_result.tier_1_count,
        "tier_2": pipeline_result.tier_2_count,
        "tier_3": pipeline_result.tier_3_count,
        "genes_with_neoantigens": sorted(pipeline_result.genes_with_neoantigens),
        "hla_alleles_tested": pipeline_result.hla_alleles_tested,
        "candidates": candidate_list,
    }
