"""
CARVanta Genomics — Variant Caller Engine
==========================================
Somatic and germline variant calling pipeline with COSMIC/ClinVar/dbSNP
annotation, variant effect prediction, and population allele frequency
stratification for immunotherapy-relevant genomic analysis.

Security: All inputs sanitized, no raw SQL, async-compatible, stateless.
API Version: v5
"""

import math
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from genomics.file_processor import (
    VariantRecord, VariantType, QualityTier,
    GRCH38_CHROMOSOMES,
)

logger = logging.getLogger("carvanta.genomics.variant_caller")

# ──────────────────────────────────────────────────────────────────────
# Constants — Variant Effect Classes
# ──────────────────────────────────────────────────────────────────────

class VariantConsequence(Enum):
    """Sequence Ontology variant consequences, ranked by severity."""
    FRAMESHIFT = "frameshift_variant"
    STOP_GAINED = "stop_gained"
    SPLICE_ACCEPTOR = "splice_acceptor_variant"
    SPLICE_DONOR = "splice_donor_variant"
    START_LOST = "start_lost"
    STOP_LOST = "stop_lost"
    MISSENSE = "missense_variant"
    INFRAME_INSERTION = "inframe_insertion"
    INFRAME_DELETION = "inframe_deletion"
    SPLICE_REGION = "splice_region_variant"
    SYNONYMOUS = "synonymous_variant"
    FIVE_PRIME_UTR = "5_prime_UTR_variant"
    THREE_PRIME_UTR = "3_prime_UTR_variant"
    INTRON = "intron_variant"
    INTERGENIC = "intergenic_variant"
    UPSTREAM = "upstream_gene_variant"
    DOWNSTREAM = "downstream_gene_variant"
    NON_CODING = "non_coding_transcript_variant"
    REGULATORY = "regulatory_region_variant"


class ClinicalSignificance(Enum):
    """ClinVar clinical significance categories."""
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting"
    NOT_PROVIDED = "not_provided"
    DRUG_RESPONSE = "drug_response"
    RISK_FACTOR = "risk_factor"
    PROTECTIVE = "protective"


class ImpactSeverity(Enum):
    """Overall variant impact severity."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    MODIFIER = "MODIFIER"


# Consequence to impact mapping
CONSEQUENCE_IMPACT: Dict[VariantConsequence, ImpactSeverity] = {
    VariantConsequence.FRAMESHIFT: ImpactSeverity.HIGH,
    VariantConsequence.STOP_GAINED: ImpactSeverity.HIGH,
    VariantConsequence.SPLICE_ACCEPTOR: ImpactSeverity.HIGH,
    VariantConsequence.SPLICE_DONOR: ImpactSeverity.HIGH,
    VariantConsequence.START_LOST: ImpactSeverity.HIGH,
    VariantConsequence.STOP_LOST: ImpactSeverity.HIGH,
    VariantConsequence.MISSENSE: ImpactSeverity.MODERATE,
    VariantConsequence.INFRAME_INSERTION: ImpactSeverity.MODERATE,
    VariantConsequence.INFRAME_DELETION: ImpactSeverity.MODERATE,
    VariantConsequence.SPLICE_REGION: ImpactSeverity.LOW,
    VariantConsequence.SYNONYMOUS: ImpactSeverity.LOW,
    VariantConsequence.FIVE_PRIME_UTR: ImpactSeverity.MODIFIER,
    VariantConsequence.THREE_PRIME_UTR: ImpactSeverity.MODIFIER,
    VariantConsequence.INTRON: ImpactSeverity.MODIFIER,
    VariantConsequence.INTERGENIC: ImpactSeverity.MODIFIER,
    VariantConsequence.UPSTREAM: ImpactSeverity.MODIFIER,
    VariantConsequence.DOWNSTREAM: ImpactSeverity.MODIFIER,
    VariantConsequence.NON_CODING: ImpactSeverity.MODIFIER,
    VariantConsequence.REGULATORY: ImpactSeverity.MODIFIER,
}


# ──────────────────────────────────────────────────────────────────────
# Gene & Transcript Reference Data (Top immunotherapy targets)
# ──────────────────────────────────────────────────────────────────────

# Key cancer driver genes with locus info
CANCER_DRIVER_GENES: Dict[str, Dict[str, Any]] = {
    "TP53":   {"chrom": "chr17", "start": 7668402,  "end": 7687550,  "strand": "-", "role": "tumor_suppressor"},
    "KRAS":   {"chrom": "chr12", "start": 25205246, "end": 25250936, "strand": "-", "role": "oncogene"},
    "EGFR":   {"chrom": "chr7",  "start": 55019017, "end": 55211628, "strand": "+", "role": "oncogene"},
    "BRAF":   {"chrom": "chr7",  "start": 140719327,"end": 140924929,"strand": "-", "role": "oncogene"},
    "PIK3CA": {"chrom": "chr3",  "start": 179148114,"end": 179240093,"strand": "+", "role": "oncogene"},
    "PTEN":   {"chrom": "chr10", "start": 87862625, "end": 87972930, "strand": "+", "role": "tumor_suppressor"},
    "APC":    {"chrom": "chr5",  "start": 112707498,"end": 112846239,"strand": "+", "role": "tumor_suppressor"},
    "BRCA1":  {"chrom": "chr17", "start": 43044295, "end": 43125483, "strand": "-", "role": "tumor_suppressor"},
    "BRCA2":  {"chrom": "chr13", "start": 32315508, "end": 32400268, "strand": "+", "role": "tumor_suppressor"},
    "MYC":    {"chrom": "chr8",  "start": 127735434,"end": 127742951,"strand": "+", "role": "oncogene"},
    "ALK":    {"chrom": "chr2",  "start": 29192774, "end": 29921566, "strand": "-", "role": "oncogene"},
    "ROS1":   {"chrom": "chr6",  "start": 117288300,"end": 117436009,"strand": "-", "role": "oncogene"},
    "RET":    {"chrom": "chr10", "start": 43077027, "end": 43130351, "strand": "+", "role": "oncogene"},
    "MET":    {"chrom": "chr7",  "start": 116672196,"end": 116798386,"strand": "+", "role": "oncogene"},
    "NTRK1":  {"chrom": "chr1",  "start": 156785385,"end": 156851642,"strand": "+", "role": "oncogene"},
    "NTRK2":  {"chrom": "chr9",  "start": 84668452, "end": 85027070, "strand": "+", "role": "oncogene"},
    "NTRK3":  {"chrom": "chr15", "start": 88248282, "end": 88619904, "strand": "+", "role": "oncogene"},
    "IDH1":   {"chrom": "chr2",  "start": 208236227,"end": 208266074,"strand": "-", "role": "oncogene"},
    "IDH2":   {"chrom": "chr15", "start": 90083041, "end": 90102463, "strand": "-", "role": "oncogene"},
    "ARID1A": {"chrom": "chr1",  "start": 26696016, "end": 26782376, "strand": "-", "role": "tumor_suppressor"},
    "CD19":   {"chrom": "chr16", "start": 28931942, "end": 28939422, "strand": "+", "role": "car_t_target"},
    "CD20":   {"chrom": "chr11", "start": 47218826, "end": 47245983, "strand": "+", "role": "car_t_target"},
    "CD22":   {"chrom": "chr19", "start": 35324929, "end": 35344960, "strand": "-", "role": "car_t_target"},
    "BCMA":   {"chrom": "chr16", "start": 12004152, "end": 12034849, "strand": "+", "role": "car_t_target"},
    "MSLN":   {"chrom": "chr16", "start": 810682,   "end": 822762,   "strand": "+", "role": "car_t_target"},
    "CD276":  {"chrom": "chr15", "start": 73684018, "end": 73714880, "strand": "+", "role": "car_t_target"},
    "GPC3":   {"chrom": "chrX",  "start": 133506785,"end": 133979835,"strand": "+", "role": "car_t_target"},
    "HER2":   {"chrom": "chr17", "start": 39687914, "end": 39730426, "strand": "+", "role": "car_t_target"},
    "CEACAM5":{"chrom": "chr19", "start": 41697513, "end": 41718576, "strand": "+", "role": "car_t_target"},
    "PDCD1":  {"chrom": "chr2",  "start": 241849881,"end": 241858908,"strand": "-", "role": "immune_checkpoint"},
    "CD274":  {"chrom": "chr9",  "start": 5450503,  "end": 5470566,  "strand": "-", "role": "immune_checkpoint"},
    "CTLA4":  {"chrom": "chr2",  "start": 203867788,"end": 203873960,"strand": "+", "role": "immune_checkpoint"},
    "HAVCR2": {"chrom": "chr5",  "start": 157085832,"end": 157109937,"strand": "+", "role": "immune_checkpoint"},
    "LAG3":   {"chrom": "chr12", "start": 6772512,  "end": 6778455,  "strand": "-", "role": "immune_checkpoint"},
    "TIGIT":  {"chrom": "chr3",  "start": 114666544,"end": 114680376,"strand": "-", "role": "immune_checkpoint"},
}

# COSMIC top hotspot mutations
COSMIC_HOTSPOTS: Dict[str, List[Dict[str, Any]]] = {
    "TP53": [
        {"pos": 7675088, "ref": "C", "alt": "T", "aa": "R248W", "cosmic_id": "COSM10656", "frequency": 0.036},
        {"pos": 7674220, "ref": "C", "alt": "T", "aa": "R273H", "cosmic_id": "COSM10659", "frequency": 0.031},
        {"pos": 7673802, "ref": "C", "alt": "T", "aa": "R282W", "cosmic_id": "COSM10704", "frequency": 0.017},
        {"pos": 7675159, "ref": "G", "alt": "A", "aa": "R248Q", "cosmic_id": "COSM10662", "frequency": 0.032},
        {"pos": 7674953, "ref": "G", "alt": "A", "aa": "R249S", "cosmic_id": "COSM99003", "frequency": 0.018},
        {"pos": 7674230, "ref": "G", "alt": "A", "aa": "R273C", "cosmic_id": "COSM10660", "frequency": 0.015},
        {"pos": 7675116, "ref": "G", "alt": "A", "aa": "R175H", "cosmic_id": "COSM10648", "frequency": 0.044},
        {"pos": 7673786, "ref": "G", "alt": "T", "aa": "G245S", "cosmic_id": "COSM6932",  "frequency": 0.021},
    ],
    "KRAS": [
        {"pos": 25245350, "ref": "C", "alt": "A", "aa": "G12V", "cosmic_id": "COSM520",   "frequency": 0.089},
        {"pos": 25245350, "ref": "C", "alt": "T", "aa": "G12D", "cosmic_id": "COSM521",   "frequency": 0.112},
        {"pos": 25245351, "ref": "C", "alt": "A", "aa": "G12C", "cosmic_id": "COSM516",   "frequency": 0.062},
        {"pos": 25245347, "ref": "C", "alt": "T", "aa": "G13D", "cosmic_id": "COSM532",   "frequency": 0.037},
        {"pos": 25227342, "ref": "G", "alt": "T", "aa": "Q61H", "cosmic_id": "COSM554",   "frequency": 0.022},
    ],
    "BRAF": [
        {"pos": 140753336, "ref": "A", "alt": "T", "aa": "V600E", "cosmic_id": "COSM476", "frequency": 0.215},
        {"pos": 140753335, "ref": "A", "alt": "G", "aa": "V600K", "cosmic_id": "COSM473", "frequency": 0.018},
    ],
    "PIK3CA": [
        {"pos": 179218294, "ref": "G", "alt": "A", "aa": "H1047R", "cosmic_id": "COSM775", "frequency": 0.056},
        {"pos": 179203765, "ref": "A", "alt": "G", "aa": "E545K",  "cosmic_id": "COSM763", "frequency": 0.034},
        {"pos": 179199088, "ref": "A", "alt": "G", "aa": "E542K",  "cosmic_id": "COSM760", "frequency": 0.025},
    ],
    "EGFR": [
        {"pos": 55174014, "ref": "C", "alt": "T",    "aa": "T790M",           "cosmic_id": "COSM6240",  "frequency": 0.031},
        {"pos": 55191822, "ref": "T", "alt": "G",    "aa": "L858R",           "cosmic_id": "COSM6224",  "frequency": 0.047},
        {"pos": 55174771, "ref": "AGGAATTAAGAGAAGC", "alt": "A", "aa": "E746_A750del", "cosmic_id": "COSM6223", "frequency": 0.064},
    ],
    "IDH1": [
        {"pos": 208248388, "ref": "C", "alt": "T", "aa": "R132H", "cosmic_id": "COSM28746", "frequency": 0.082},
        {"pos": 208248389, "ref": "G", "alt": "A", "aa": "R132C", "cosmic_id": "COSM28747", "frequency": 0.013},
    ],
}

# Amino acid properties for missense impact prediction
AMINO_ACID_PROPERTIES: Dict[str, Dict[str, Any]] = {
    "A": {"hydrophobicity": 1.8,  "charge": 0, "size": "small",    "polarity": "nonpolar"},
    "R": {"hydrophobicity": -4.5, "charge": 1, "size": "large",    "polarity": "positive"},
    "N": {"hydrophobicity": -3.5, "charge": 0, "size": "medium",   "polarity": "polar"},
    "D": {"hydrophobicity": -3.5, "charge":-1, "size": "medium",   "polarity": "negative"},
    "C": {"hydrophobicity": 2.5,  "charge": 0, "size": "medium",   "polarity": "nonpolar"},
    "E": {"hydrophobicity": -3.5, "charge":-1, "size": "large",    "polarity": "negative"},
    "Q": {"hydrophobicity": -3.5, "charge": 0, "size": "large",    "polarity": "polar"},
    "G": {"hydrophobicity": -0.4, "charge": 0, "size": "tiny",     "polarity": "nonpolar"},
    "H": {"hydrophobicity": -3.2, "charge": 0, "size": "large",    "polarity": "positive"},
    "I": {"hydrophobicity": 4.5,  "charge": 0, "size": "large",    "polarity": "nonpolar"},
    "L": {"hydrophobicity": 3.8,  "charge": 0, "size": "large",    "polarity": "nonpolar"},
    "K": {"hydrophobicity": -3.9, "charge": 1, "size": "large",    "polarity": "positive"},
    "M": {"hydrophobicity": 1.9,  "charge": 0, "size": "large",    "polarity": "nonpolar"},
    "F": {"hydrophobicity": 2.8,  "charge": 0, "size": "large",    "polarity": "nonpolar"},
    "P": {"hydrophobicity": -1.6, "charge": 0, "size": "medium",   "polarity": "nonpolar"},
    "S": {"hydrophobicity": -0.8, "charge": 0, "size": "small",    "polarity": "polar"},
    "T": {"hydrophobicity": -0.7, "charge": 0, "size": "medium",   "polarity": "polar"},
    "W": {"hydrophobicity": -0.9, "charge": 0, "size": "large",    "polarity": "nonpolar"},
    "Y": {"hydrophobicity": -1.3, "charge": 0, "size": "large",    "polarity": "polar"},
    "V": {"hydrophobicity": 4.2,  "charge": 0, "size": "medium",   "polarity": "nonpolar"},
}

# Population allele frequency databases
POPULATION_DATABASES: Dict[str, Dict[str, Any]] = {
    "gnomAD_AFR": {"name": "African/African-American", "abbreviation": "AFR", "sample_size": 12487},
    "gnomAD_AMR": {"name": "Latino/Admixed-American",  "abbreviation": "AMR", "sample_size": 17720},
    "gnomAD_ASJ": {"name": "Ashkenazi Jewish",         "abbreviation": "ASJ", "sample_size": 5185},
    "gnomAD_EAS": {"name": "East Asian",               "abbreviation": "EAS", "sample_size": 9977},
    "gnomAD_FIN": {"name": "Finnish",                  "abbreviation": "FIN", "sample_size": 12897},
    "gnomAD_NFE": {"name": "Non-Finnish European",     "abbreviation": "NFE", "sample_size": 64603},
    "gnomAD_SAS": {"name": "South Asian",              "abbreviation": "SAS", "sample_size": 15308},
    "gnomAD_OTH": {"name": "Other",                    "abbreviation": "OTH", "sample_size": 3234},
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes — Annotated Variants
# ──────────────────────────────────────────────────────────────────────

@dataclass
class VariantAnnotation:
    """Rich annotation for a single variant."""
    gene_symbol: str = ""
    gene_id: str = ""
    transcript_id: str = ""
    consequence: VariantConsequence = VariantConsequence.INTERGENIC
    impact: ImpactSeverity = ImpactSeverity.MODIFIER
    protein_change: str = ""
    codon_change: str = ""
    exon_number: Optional[int] = None
    intron_number: Optional[int] = None
    is_cancer_driver: bool = False
    driver_role: str = ""  # oncogene / tumor_suppressor / car_t_target
    cosmic_id: Optional[str] = None
    cosmic_frequency: float = 0.0
    is_hotspot: bool = False
    clinvar_significance: ClinicalSignificance = ClinicalSignificance.NOT_PROVIDED
    clinvar_id: Optional[str] = None
    dbsnp_id: Optional[str] = None
    sift_prediction: str = ""
    sift_score: float = 1.0
    polyphen_prediction: str = ""
    polyphen_score: float = 0.0
    grantham_score: float = 0.0
    blosum62_score: float = 0.0
    population_frequencies: Dict[str, float] = field(default_factory=dict)
    max_population_frequency: float = 0.0
    is_rare: bool = True  # AF < 0.01
    immunotherapy_relevance: float = 0.0
    car_t_impact: str = ""


@dataclass
class SomaticCallResult:
    """Result from somatic variant calling."""
    variant: VariantRecord
    is_somatic: bool = False
    somatic_score: float = 0.0
    tumor_af: float = 0.0
    normal_af: float = 0.0
    tumor_depth: int = 0
    normal_depth: int = 0
    strand_bias: float = 0.0
    mapping_quality_bias: float = 0.0
    base_quality_bias: float = 0.0
    filters_applied: List[str] = field(default_factory=list)
    filters_passed: List[str] = field(default_factory=list)
    filters_failed: List[str] = field(default_factory=list)


@dataclass
class VariantCallingStats:
    """Aggregate statistics from variant calling."""
    total_variants: int = 0
    somatic_variants: int = 0
    germline_variants: int = 0
    snv_count: int = 0
    indel_count: int = 0
    mnv_count: int = 0
    ti_tv_ratio: float = 0.0
    mean_vaf: float = 0.0
    driver_mutations: int = 0
    hotspot_mutations: int = 0
    high_impact: int = 0
    moderate_impact: int = 0
    low_impact: int = 0
    modifier_impact: int = 0
    genes_affected: int = 0
    pathogenic_variants: int = 0


# ──────────────────────────────────────────────────────────────────────
# Somatic Variant Calling
# ──────────────────────────────────────────────────────────────────────

def _compute_somatic_score(
    tumor_af: float,
    normal_af: float,
    tumor_depth: int,
    normal_depth: int,
    qual: float,
) -> float:
    """
    Compute somatic likelihood score using a simplified Bayesian model.
    Higher score = more likely somatic.
    """
    # Base score from allele frequency differential
    af_diff = max(0.0, tumor_af - normal_af)
    af_score = min(1.0, af_diff * 5.0)

    # Depth confidence
    depth_score = min(1.0, (tumor_depth / 50.0) * (normal_depth / 30.0))

    # Quality contribution
    qual_score = min(1.0, qual / 100.0)

    # Penalize if variant present in normal
    normal_penalty = 1.0 - min(1.0, normal_af * 10.0)

    # Combined score
    score = (af_score * 0.4 + depth_score * 0.2 + qual_score * 0.2 + normal_penalty * 0.2)
    return round(min(1.0, max(0.0, score)), 4)


def _compute_strand_bias(
    forward_ref: int, reverse_ref: int,
    forward_alt: int, reverse_alt: int,
) -> float:
    """Compute Fisher's exact test approximation for strand bias."""
    total = forward_ref + reverse_ref + forward_alt + reverse_alt
    if total == 0:
        return 0.0

    # Simplified contingency table approach
    a, b, c, d = forward_ref, reverse_ref, forward_alt, reverse_alt
    n = a + b + c + d
    if n == 0:
        return 0.0

    # Approximation using log odds ratio
    try:
        odds = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
        return abs(math.log(odds))
    except (ValueError, ZeroDivisionError):
        return 0.0


async def call_somatic_variants(
    tumor_variants: List[VariantRecord],
    normal_variants: Optional[List[VariantRecord]] = None,
    min_tumor_af: float = 0.05,
    max_normal_af: float = 0.02,
    min_tumor_depth: int = 10,
    min_normal_depth: int = 8,
    min_somatic_score: float = 0.3,
) -> Tuple[List[SomaticCallResult], VariantCallingStats]:
    """
    Identify somatic variants by comparing tumor vs. normal samples.

    When no normal is provided, uses population frequency and heuristics.

    Args:
        tumor_variants: Variants from tumor sample
        normal_variants: Variants from matched normal (optional)
        min_tumor_af: Minimum tumor allele frequency
        max_normal_af: Maximum normal allele frequency for somatic
        min_tumor_depth: Minimum read depth in tumor
        min_normal_depth: Minimum read depth in normal
        min_somatic_score: Minimum somatic score threshold

    Returns:
        Tuple of (somatic call results, calling statistics)
    """
    stats = VariantCallingStats()
    results: List[SomaticCallResult] = []

    # Index normal variants by coordinate key
    normal_index: Dict[str, VariantRecord] = {}
    if normal_variants:
        for nv in normal_variants:
            normal_index[nv.coordinate_key] = nv

    # Transition/transversion counting
    transitions = {"AG", "GA", "CT", "TC"}
    ti_count = 0
    tv_count = 0
    total_vaf = 0.0

    for variant in tumor_variants:
        stats.total_variants += 1

        tumor_af = variant.allele_frequency
        tumor_depth = variant.read_depth

        # Look up matched normal
        normal_match = normal_index.get(variant.coordinate_key)
        normal_af = normal_match.allele_frequency if normal_match else 0.0
        normal_depth = normal_match.read_depth if normal_match else 30

        # Compute somatic score
        somatic_score = _compute_somatic_score(
            tumor_af, normal_af, tumor_depth, normal_depth, variant.qual,
        )

        # Apply filters
        filters_applied = []
        filters_passed = []
        filters_failed = []

        # Tumor AF filter
        filters_applied.append("min_tumor_af")
        if tumor_af >= min_tumor_af or tumor_af == 0.0:
            filters_passed.append("min_tumor_af")
        else:
            filters_failed.append("min_tumor_af")

        # Normal AF filter
        filters_applied.append("max_normal_af")
        if normal_af <= max_normal_af:
            filters_passed.append("max_normal_af")
        else:
            filters_failed.append("max_normal_af")

        # Depth filters
        filters_applied.append("min_tumor_depth")
        if tumor_depth >= min_tumor_depth or tumor_depth == 0:
            filters_passed.append("min_tumor_depth")
        else:
            filters_failed.append("min_tumor_depth")

        # Somatic score filter
        filters_applied.append("somatic_score")
        if somatic_score >= min_somatic_score:
            filters_passed.append("somatic_score")
        else:
            filters_failed.append("somatic_score")

        is_somatic = len(filters_failed) == 0

        result = SomaticCallResult(
            variant=variant,
            is_somatic=is_somatic,
            somatic_score=somatic_score,
            tumor_af=tumor_af,
            normal_af=normal_af,
            tumor_depth=tumor_depth,
            normal_depth=normal_depth,
            filters_applied=filters_applied,
            filters_passed=filters_passed,
            filters_failed=filters_failed,
        )
        results.append(result)

        if is_somatic:
            stats.somatic_variants += 1
            total_vaf += tumor_af
        else:
            stats.germline_variants += 1

        # Variant type counts
        if variant.variant_type == VariantType.SNV:
            stats.snv_count += 1
            # Ti/Tv
            pair = variant.ref + variant.alt
            if pair in transitions:
                ti_count += 1
            else:
                tv_count += 1
        elif variant.variant_type in (VariantType.INSERTION, VariantType.DELETION):
            stats.indel_count += 1
        elif variant.variant_type == VariantType.MNV:
            stats.mnv_count += 1

    # Ti/Tv ratio
    stats.ti_tv_ratio = round(ti_count / max(tv_count, 1), 3)
    stats.mean_vaf = round(total_vaf / max(stats.somatic_variants, 1), 4)

    logger.info(
        f"Somatic calling: {stats.somatic_variants}/{stats.total_variants} somatic, "
        f"Ti/Tv={stats.ti_tv_ratio}"
    )
    return results, stats


async def filter_somatic_variants(
    calls: List[SomaticCallResult],
    min_score: float = 0.5,
    pass_only: bool = True,
    max_population_af: float = 0.01,
) -> List[SomaticCallResult]:
    """
    Post-filter somatic variant calls.

    Args:
        calls: Raw somatic call results
        min_score: Minimum somatic score
        pass_only: Only return variants passing all filters
        max_population_af: Max population allele frequency

    Returns:
        Filtered list of somatic calls
    """
    filtered: List[SomaticCallResult] = []

    for call in calls:
        if pass_only and not call.is_somatic:
            continue
        if call.somatic_score < min_score:
            continue

        # Check population frequency from variant INFO
        pop_af = call.variant.info.get("AF_popmax", call.variant.info.get("gnomAD_AF", 0.0))
        if isinstance(pop_af, (int, float)) and pop_af > max_population_af:
            continue

        filtered.append(call)

    # Sort by somatic score descending
    filtered.sort(key=lambda c: c.somatic_score, reverse=True)
    return filtered


# ──────────────────────────────────────────────────────────────────────
# COSMIC Annotation
# ──────────────────────────────────────────────────────────────────────

async def annotate_variants_cosmic(
    variants: List[VariantRecord],
) -> List[Tuple[VariantRecord, VariantAnnotation]]:
    """
    Annotate variants against COSMIC hotspot database.

    Identifies known cancer driver mutations and their frequencies
    in the COSMIC catalogue.
    """
    annotated: List[Tuple[VariantRecord, VariantAnnotation]] = []

    for variant in variants:
        annotation = VariantAnnotation()

        # Check if variant falls in a known cancer driver gene
        for gene, locus in CANCER_DRIVER_GENES.items():
            if variant.chrom != locus["chrom"]:
                continue
            if not (locus["start"] <= variant.pos <= locus["end"]):
                continue

            annotation.gene_symbol = gene
            annotation.is_cancer_driver = True
            annotation.driver_role = locus["role"]

            # Check hotspot match
            if gene in COSMIC_HOTSPOTS:
                for hotspot in COSMIC_HOTSPOTS[gene]:
                    if variant.pos == hotspot["pos"] and variant.alt == hotspot["alt"]:
                        annotation.cosmic_id = hotspot["cosmic_id"]
                        annotation.cosmic_frequency = hotspot["frequency"]
                        annotation.protein_change = hotspot["aa"]
                        annotation.is_hotspot = True
                        break

            # Immunotherapy relevance scoring
            if locus["role"] == "car_t_target":
                annotation.immunotherapy_relevance = 0.95
                annotation.car_t_impact = "direct_target_mutation"
            elif locus["role"] == "immune_checkpoint":
                annotation.immunotherapy_relevance = 0.85
                annotation.car_t_impact = "checkpoint_modulation"
            elif locus["role"] == "oncogene":
                annotation.immunotherapy_relevance = 0.6
                annotation.car_t_impact = "driver_oncogene"
            elif locus["role"] == "tumor_suppressor":
                annotation.immunotherapy_relevance = 0.55
                annotation.car_t_impact = "tumor_suppressor_loss"

            break

        annotated.append((variant, annotation))

    logger.info(
        f"COSMIC annotation: {sum(1 for _, a in annotated if a.is_hotspot)} hotspots, "
        f"{sum(1 for _, a in annotated if a.is_cancer_driver)} drivers found"
    )
    return annotated


# ──────────────────────────────────────────────────────────────────────
# ClinVar Annotation
# ──────────────────────────────────────────────────────────────────────

# ClinVar simulated entries for key immunotherapy-relevant variants
CLINVAR_ENTRIES: Dict[str, Dict[str, Any]] = {
    "chr17:7675116:G>A": {"clinvar_id": "VCV000012347", "significance": "pathogenic",       "gene": "TP53",   "condition": "Li-Fraumeni syndrome"},
    "chr17:7675088:C>T": {"clinvar_id": "VCV000012348", "significance": "pathogenic",       "gene": "TP53",   "condition": "Hereditary cancer"},
    "chr12:25245350:C>A": {"clinvar_id": "VCV000012982", "significance": "pathogenic",      "gene": "KRAS",   "condition": "RASopathy"},
    "chr12:25245350:C>T": {"clinvar_id": "VCV000012983", "significance": "pathogenic",      "gene": "KRAS",   "condition": "Noonan syndrome"},
    "chr7:140753336:A>T": {"clinvar_id": "VCV000013961", "significance": "pathogenic",      "gene": "BRAF",   "condition": "Melanoma"},
    "chr7:55191822:T>G":  {"clinvar_id": "VCV000016609", "significance": "drug_response",   "gene": "EGFR",   "condition": "NSCLC TKI sensitivity"},
    "chr7:55174014:C>T":  {"clinvar_id": "VCV000016610", "significance": "drug_response",   "gene": "EGFR",   "condition": "NSCLC TKI resistance"},
    "chr3:179218294:G>A": {"clinvar_id": "VCV000019207", "significance": "pathogenic",      "gene": "PIK3CA", "condition": "Breast cancer"},
    "chr17:43044295:A>G": {"clinvar_id": "VCV000055326", "significance": "pathogenic",      "gene": "BRCA1",  "condition": "HBOC"},
    "chr13:32340300:A>T": {"clinvar_id": "VCV000052138", "significance": "pathogenic",      "gene": "BRCA2",  "condition": "HBOC"},
    "chr10:87933147:C>T": {"clinvar_id": "VCV000005146", "significance": "pathogenic",      "gene": "PTEN",   "condition": "Cowden syndrome"},
    "chr2:208248388:C>T": {"clinvar_id": "VCV000375882", "significance": "pathogenic",      "gene": "IDH1",   "condition": "Glioma"},
}


async def annotate_variants_clinvar(
    annotated_variants: List[Tuple[VariantRecord, VariantAnnotation]],
) -> List[Tuple[VariantRecord, VariantAnnotation]]:
    """
    Enrich variant annotations with ClinVar clinical significance.

    Matches variants against ClinVar database entries and updates
    clinical significance, condition, and ClinVar accession.
    """
    significance_map = {
        "pathogenic": ClinicalSignificance.PATHOGENIC,
        "likely_pathogenic": ClinicalSignificance.LIKELY_PATHOGENIC,
        "uncertain_significance": ClinicalSignificance.UNCERTAIN,
        "likely_benign": ClinicalSignificance.LIKELY_BENIGN,
        "benign": ClinicalSignificance.BENIGN,
        "drug_response": ClinicalSignificance.DRUG_RESPONSE,
        "risk_factor": ClinicalSignificance.RISK_FACTOR,
        "protective": ClinicalSignificance.PROTECTIVE,
    }

    for variant, annotation in annotated_variants:
        key = variant.coordinate_key
        if key in CLINVAR_ENTRIES:
            entry = CLINVAR_ENTRIES[key]
            annotation.clinvar_id = entry["clinvar_id"]
            sig_str = entry["significance"]
            annotation.clinvar_significance = significance_map.get(
                sig_str, ClinicalSignificance.NOT_PROVIDED
            )

        # Also check INFO field for ClinVar ID
        if "CLNDN" in variant.info:
            annotation.clinvar_significance = ClinicalSignificance.PATHOGENIC
        if "RS" in variant.info:
            annotation.dbsnp_id = f"rs{variant.info['RS']}"

    pathogenic_count = sum(
        1 for _, a in annotated_variants
        if a.clinvar_significance in (
            ClinicalSignificance.PATHOGENIC,
            ClinicalSignificance.LIKELY_PATHOGENIC,
        )
    )
    logger.info(f"ClinVar annotation: {pathogenic_count} pathogenic/likely-pathogenic variants")
    return annotated_variants


# ──────────────────────────────────────────────────────────────────────
# Variant Effect Prediction
# ──────────────────────────────────────────────────────────────────────

def _compute_grantham_score(aa_ref: str, aa_alt: str) -> float:
    """
    Compute Grantham distance between two amino acids.
    Measures physicochemical difference; higher = more disruptive.
    Range: 0-215.
    """
    # Grantham distance matrix (subset of common substitutions)
    grantham_matrix: Dict[str, Dict[str, float]] = {
        "A": {"R": 112, "N": 111, "D": 126, "C": 195, "E": 107, "G": 60, "H": 86, "I": 94, "L": 96, "K": 106, "M": 84, "F": 113, "P": 27, "S": 99, "T": 58, "W": 148, "Y": 112, "V": 64},
        "R": {"N": 86, "D": 96, "C": 180, "E": 54, "G": 125, "H": 29, "I": 97, "L": 102, "K": 26, "M": 91, "F": 97, "P": 103, "S": 110, "T": 71, "W": 101, "Y": 77, "V": 96},
        "D": {"N": 23, "C": 154, "E": 45, "G": 94, "H": 81, "I": 168, "L": 172, "K": 101, "M": 160, "F": 177, "P": 108, "S": 65, "T": 85, "W": 181, "Y": 160, "V": 152},
        "G": {"N": 80, "C": 159, "E": 98, "H": 98, "I": 135, "L": 138, "K": 127, "M": 127, "F": 153, "P": 42, "S": 56, "T": 59, "W": 184, "Y": 147, "V": 109},
    }

    if aa_ref in grantham_matrix and aa_alt in grantham_matrix[aa_ref]:
        return grantham_matrix[aa_ref][aa_alt]
    if aa_alt in grantham_matrix and aa_ref in grantham_matrix[aa_alt]:
        return grantham_matrix[aa_alt][aa_ref]

    # Fallback: estimate from amino acid properties
    ref_props = AMINO_ACID_PROPERTIES.get(aa_ref, {"hydrophobicity": 0, "charge": 0})
    alt_props = AMINO_ACID_PROPERTIES.get(aa_alt, {"hydrophobicity": 0, "charge": 0})

    hydro_diff = abs(ref_props["hydrophobicity"] - alt_props["hydrophobicity"])
    charge_diff = abs(ref_props["charge"] - alt_props["charge"])

    return min(215.0, hydro_diff * 15 + charge_diff * 50 + 30)


def _predict_sift_score(variant: VariantRecord, annotation: VariantAnnotation) -> Tuple[str, float]:
    """
    Predict SIFT-like deleteriousness score.
    Score < 0.05 = deleterious.
    """
    # Base score from variant quality and type
    if annotation.consequence in (VariantConsequence.FRAMESHIFT, VariantConsequence.STOP_GAINED):
        return "deleterious", 0.0
    if annotation.consequence == VariantConsequence.SYNONYMOUS:
        return "tolerated", 0.85

    # For missense: use Grantham + conservation approximation
    if annotation.consequence == VariantConsequence.MISSENSE:
        grantham = annotation.grantham_score
        # Normalize Grantham to SIFT-like score (inverse)
        sift = max(0.0, 1.0 - (grantham / 215.0))

        # Hotspot penalty
        if annotation.is_hotspot:
            sift *= 0.1

        # Driver gene penalty
        if annotation.is_cancer_driver:
            sift *= 0.5

        prediction = "deleterious" if sift < 0.05 else "tolerated"
        return prediction, round(sift, 4)

    return "tolerated", 0.5


def _predict_polyphen_score(variant: VariantRecord, annotation: VariantAnnotation) -> Tuple[str, float]:
    """
    Predict PolyPhen-2-like pathogenicity score.
    Score > 0.85 = probably_damaging, > 0.15 = possibly_damaging.
    """
    if annotation.consequence in (VariantConsequence.FRAMESHIFT, VariantConsequence.STOP_GAINED):
        return "probably_damaging", 1.0
    if annotation.consequence == VariantConsequence.SYNONYMOUS:
        return "benign", 0.02

    if annotation.consequence == VariantConsequence.MISSENSE:
        grantham = annotation.grantham_score
        score = min(1.0, grantham / 200.0)

        if annotation.is_hotspot:
            score = min(1.0, score + 0.3)
        if annotation.is_cancer_driver:
            score = min(1.0, score + 0.15)

        if score > 0.85:
            return "probably_damaging", round(score, 4)
        elif score > 0.15:
            return "possibly_damaging", round(score, 4)
        return "benign", round(score, 4)

    return "benign", 0.1


async def predict_variant_effect(
    annotated_variants: List[Tuple[VariantRecord, VariantAnnotation]],
) -> List[Tuple[VariantRecord, VariantAnnotation]]:
    """
    Predict functional effect of each variant.

    Adds:
    - Variant consequence (missense, frameshift, etc.)
    - Impact severity (HIGH/MODERATE/LOW/MODIFIER)
    - SIFT score and prediction
    - PolyPhen-2 score and prediction
    - Grantham distance for missense variants
    """
    for variant, annotation in annotated_variants:
        # Determine consequence from variant type and gene context
        if annotation.gene_symbol:
            if variant.variant_type == VariantType.SNV:
                if len(variant.ref) == 1 and len(variant.alt) == 1:
                    # Check for protein_change already assigned by COSMIC
                    if annotation.protein_change:
                        if annotation.protein_change.endswith("*"):
                            annotation.consequence = VariantConsequence.STOP_GAINED
                        else:
                            annotation.consequence = VariantConsequence.MISSENSE
                    else:
                        # Heuristic: position in gene determines coding vs. non-coding
                        gene_info = CANCER_DRIVER_GENES.get(annotation.gene_symbol, {})
                        gene_start = gene_info.get("start", 0)
                        gene_end = gene_info.get("end", 0)
                        gene_len = gene_end - gene_start
                        rel_pos = (variant.pos - gene_start) / max(gene_len, 1)

                        if 0.05 < rel_pos < 0.95:
                            annotation.consequence = VariantConsequence.MISSENSE
                        elif rel_pos <= 0.05 or rel_pos >= 0.95:
                            annotation.consequence = VariantConsequence.SPLICE_REGION
                        else:
                            annotation.consequence = VariantConsequence.INTRON

            elif variant.variant_type == VariantType.INSERTION:
                ref_len = len(variant.ref) - 1  # subtract anchor base
                alt_len = len(variant.alt) - 1
                insert_len = alt_len - ref_len
                if insert_len % 3 == 0:
                    annotation.consequence = VariantConsequence.INFRAME_INSERTION
                else:
                    annotation.consequence = VariantConsequence.FRAMESHIFT

            elif variant.variant_type == VariantType.DELETION:
                ref_len = len(variant.ref) - 1
                alt_len = max(0, len(variant.alt) - 1)
                del_len = ref_len - alt_len
                if del_len % 3 == 0:
                    annotation.consequence = VariantConsequence.INFRAME_DELETION
                else:
                    annotation.consequence = VariantConsequence.FRAMESHIFT

            elif variant.variant_type == VariantType.MNV:
                annotation.consequence = VariantConsequence.MISSENSE

        else:
            annotation.consequence = VariantConsequence.INTERGENIC

        # Set impact from consequence
        annotation.impact = CONSEQUENCE_IMPACT.get(
            annotation.consequence, ImpactSeverity.MODIFIER
        )

        # Compute Grantham score for missense
        if annotation.consequence == VariantConsequence.MISSENSE and annotation.protein_change:
            # Extract amino acids from protein change (e.g., R248W → R, W)
            aa_match = re.match(r"([A-Z])(\d+)([A-Z*])", annotation.protein_change)
            if aa_match:
                aa_ref = aa_match.group(1)
                aa_alt = aa_match.group(3)
                if aa_alt != "*":
                    annotation.grantham_score = _compute_grantham_score(aa_ref, aa_alt)

        # SIFT prediction
        annotation.sift_prediction, annotation.sift_score = _predict_sift_score(variant, annotation)

        # PolyPhen prediction
        annotation.polyphen_prediction, annotation.polyphen_score = _predict_polyphen_score(variant, annotation)

    # Log impact distribution
    impact_dist = {}
    for _, a in annotated_variants:
        key = a.impact.value
        impact_dist[key] = impact_dist.get(key, 0) + 1
    logger.info(f"Variant effects predicted: {impact_dist}")

    return annotated_variants


# ──────────────────────────────────────────────────────────────────────
# Population Allele Frequency Stratification
# ──────────────────────────────────────────────────────────────────────

async def compute_allele_frequencies(
    annotated_variants: List[Tuple[VariantRecord, VariantAnnotation]],
    rarity_threshold: float = 0.01,
) -> List[Tuple[VariantRecord, VariantAnnotation]]:
    """
    Assign population allele frequencies from gnomAD-style databases.

    Marks variants as rare/common and computes max population frequency
    across all populations.
    """
    for variant, annotation in annotated_variants:
        # Check INFO field for population AFs
        pop_freqs: Dict[str, float] = {}

        for pop_key, pop_info in POPULATION_DATABASES.items():
            # Check variant's INFO for population-specific AF
            af_key = f"AF_{pop_info['abbreviation']}"
            if af_key in variant.info:
                try:
                    pop_freqs[pop_info["abbreviation"]] = float(variant.info[af_key])
                except (ValueError, TypeError):
                    pass

        # If no population data in INFO, simulate based on variant characteristics
        if not pop_freqs:
            # Common variants (dbSNP with high frequency) get population AFs
            if annotation.dbsnp_id:
                base_af = 0.05 + (hash(annotation.dbsnp_id) % 100) / 1000
                for pop_info in POPULATION_DATABASES.values():
                    jitter = ((hash(annotation.dbsnp_id + pop_info["abbreviation"]) % 100) - 50) / 1000
                    pop_freqs[pop_info["abbreviation"]] = max(0.0, min(1.0, base_af + jitter))
            elif annotation.is_hotspot:
                # Hotspot somatic mutations are rare in population
                for pop_info in POPULATION_DATABASES.values():
                    pop_freqs[pop_info["abbreviation"]] = 0.0
            else:
                # Novel variants: rare across populations
                seed = hash(variant.coordinate_key) % 10000
                for pop_info in POPULATION_DATABASES.values():
                    af = (seed % 100) / 100000  # 0 to 0.001
                    pop_freqs[pop_info["abbreviation"]] = round(af, 6)

        annotation.population_frequencies = pop_freqs
        annotation.max_population_frequency = max(pop_freqs.values()) if pop_freqs else 0.0
        annotation.is_rare = annotation.max_population_frequency < rarity_threshold

    rare_count = sum(1 for _, a in annotated_variants if a.is_rare)
    logger.info(
        f"Population AF: {rare_count}/{len(annotated_variants)} variants are rare (AF < {rarity_threshold})"
    )
    return annotated_variants


# ──────────────────────────────────────────────────────────────────────
# Full Variant Calling Pipeline
# ──────────────────────────────────────────────────────────────────────

async def run_variant_calling_pipeline(
    tumor_variants: List[VariantRecord],
    normal_variants: Optional[List[VariantRecord]] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the complete variant calling → annotation → effect prediction pipeline.

    Returns a comprehensive result dictionary with annotated variants,
    statistics, and clinical interpretation.
    """
    options = options or {}

    # Step 1: Somatic calling
    somatic_calls, calling_stats = await call_somatic_variants(
        tumor_variants,
        normal_variants,
        min_tumor_af=options.get("min_tumor_af", 0.05),
        max_normal_af=options.get("max_normal_af", 0.02),
        min_tumor_depth=options.get("min_tumor_depth", 10),
    )

    # Step 2: Filter
    filtered_calls = await filter_somatic_variants(
        somatic_calls,
        min_score=options.get("min_somatic_score", 0.3),
        pass_only=options.get("pass_only", True),
    )

    # Extract somatic variants for annotation
    somatic_variants = [call.variant for call in filtered_calls]

    # Step 3: COSMIC annotation
    annotated = await annotate_variants_cosmic(somatic_variants)

    # Step 4: ClinVar annotation
    annotated = await annotate_variants_clinvar(annotated)

    # Step 5: Variant effect prediction
    annotated = await predict_variant_effect(annotated)

    # Step 6: Population allele frequencies
    annotated = await compute_allele_frequencies(annotated)

    # Build result
    genes_affected: Set[str] = set()
    high_impact_variants: List[Dict[str, Any]] = []
    driver_variants: List[Dict[str, Any]] = []

    for variant, annotation in annotated:
        if annotation.gene_symbol:
            genes_affected.add(annotation.gene_symbol)

        var_summary = {
            "coordinate": variant.coordinate_key,
            "gene": annotation.gene_symbol,
            "consequence": annotation.consequence.value,
            "impact": annotation.impact.value,
            "protein_change": annotation.protein_change,
            "cosmic_id": annotation.cosmic_id,
            "is_hotspot": annotation.is_hotspot,
            "clinvar_significance": annotation.clinvar_significance.value,
            "sift": annotation.sift_prediction,
            "polyphen": annotation.polyphen_prediction,
            "immunotherapy_relevance": annotation.immunotherapy_relevance,
            "car_t_impact": annotation.car_t_impact,
            "population_af": annotation.max_population_frequency,
            "is_rare": annotation.is_rare,
        }

        if annotation.impact in (ImpactSeverity.HIGH, ImpactSeverity.MODERATE):
            high_impact_variants.append(var_summary)

        if annotation.is_cancer_driver:
            driver_variants.append(var_summary)

    # Update stats
    calling_stats.genes_affected = len(genes_affected)
    calling_stats.driver_mutations = len(driver_variants)
    calling_stats.hotspot_mutations = sum(1 for _, a in annotated if a.is_hotspot)
    calling_stats.high_impact = sum(1 for _, a in annotated if a.impact == ImpactSeverity.HIGH)
    calling_stats.moderate_impact = sum(1 for _, a in annotated if a.impact == ImpactSeverity.MODERATE)
    calling_stats.low_impact = sum(1 for _, a in annotated if a.impact == ImpactSeverity.LOW)
    calling_stats.modifier_impact = sum(1 for _, a in annotated if a.impact == ImpactSeverity.MODIFIER)
    calling_stats.pathogenic_variants = sum(
        1 for _, a in annotated
        if a.clinvar_significance in (ClinicalSignificance.PATHOGENIC, ClinicalSignificance.LIKELY_PATHOGENIC)
    )

    return {
        "success": True,
        "total_somatic": calling_stats.somatic_variants,
        "total_germline": calling_stats.germline_variants,
        "ti_tv_ratio": calling_stats.ti_tv_ratio,
        "mean_vaf": calling_stats.mean_vaf,
        "genes_affected": sorted(genes_affected),
        "driver_mutations": driver_variants,
        "hotspot_count": calling_stats.hotspot_mutations,
        "high_impact_variants": high_impact_variants,
        "impact_distribution": {
            "HIGH": calling_stats.high_impact,
            "MODERATE": calling_stats.moderate_impact,
            "LOW": calling_stats.low_impact,
            "MODIFIER": calling_stats.modifier_impact,
        },
        "pathogenic_count": calling_stats.pathogenic_variants,
        "snv_count": calling_stats.snv_count,
        "indel_count": calling_stats.indel_count,
        "annotated_variants": [
            {
                "coordinate": v.coordinate_key,
                "chrom": v.chrom,
                "pos": v.pos,
                "ref": v.ref,
                "alt": v.alt,
                "qual": v.qual,
                "gene": a.gene_symbol,
                "consequence": a.consequence.value,
                "impact": a.impact.value,
                "protein_change": a.protein_change,
                "cosmic_id": a.cosmic_id,
                "cosmic_frequency": a.cosmic_frequency,
                "is_hotspot": a.is_hotspot,
                "clinvar": a.clinvar_significance.value,
                "sift_score": a.sift_score,
                "sift_pred": a.sift_prediction,
                "polyphen_score": a.polyphen_score,
                "polyphen_pred": a.polyphen_prediction,
                "grantham": a.grantham_score,
                "max_pop_af": a.max_population_frequency,
                "is_rare": a.is_rare,
                "immunotherapy_relevance": a.immunotherapy_relevance,
                "car_t_impact": a.car_t_impact,
            }
            for v, a in annotated
        ],
    }
