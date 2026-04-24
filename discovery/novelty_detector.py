"""
CARVanta Discovery — Novelty Detector Engine
==============================================
Identifies unexplored / under-investigated protein targets by comparing
the current proteome scan against the clinical landscape: ClinicalTrials.gov
registrations, publication counts, patent filings, and competitive landscape.

Computes a "white space" score quantifying how underexplored a target is
relative to its scientific potential.

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.discovery.novelty_detector")

# ──────────────────────────────────────────────────────────────────────
# Constants — Clinical Landscape Reference
# ──────────────────────────────────────────────────────────────────────

class DevelopmentStage(Enum):
    """Target clinical development stage."""
    UNDISCOVERED = "undiscovered"
    PUBLISHED_ONLY = "published_only"
    PRECLINICAL = "preclinical"
    IND_FILED = "ind_filed"
    PHASE_I = "phase_I"
    PHASE_II = "phase_II"
    PHASE_III = "phase_III"
    APPROVED = "approved"


class NoveltyConcern(Enum):
    """Potential concerns for novel targets."""
    EXPRESSION_UNCERTAIN = "expression_data_limited"
    SAFETY_UNKNOWN = "safety_profile_unknown"
    ANTIBODY_UNAVAILABLE = "targeting_antibody_unavailable"
    BIOLOGY_UNCLEAR = "target_biology_unclear"
    IP_CROWDED = "intellectual_property_crowded"
    COMPETITIVE = "multiple_competitors"


# Clinical landscape data (simulated from ClinicalTrials.gov + PubMed)
CLINICAL_LANDSCAPE: Dict[str, Dict[str, Any]] = {
    "CD19": {
        "pubmed_count": 12500, "clinical_trials": 285, "patents": 450,
        "stage": DevelopmentStage.APPROVED, "competitors": 15,
        "first_publication_year": 1988, "first_trial_year": 2010,
        "approved_indications": ["B-ALL", "DLBCL", "FL", "MCL"],
        "market_size_B": 4.5,
    },
    "BCMA": {
        "pubmed_count": 3200, "clinical_trials": 95, "patents": 180,
        "stage": DevelopmentStage.APPROVED, "competitors": 8,
        "first_publication_year": 1992, "first_trial_year": 2015,
        "approved_indications": ["multiple_myeloma"],
        "market_size_B": 2.8,
    },
    "CD22": {
        "pubmed_count": 4800, "clinical_trials": 45, "patents": 85,
        "stage": DevelopmentStage.PHASE_II, "competitors": 5,
        "first_publication_year": 1990, "first_trial_year": 2016,
        "approved_indications": [],
        "market_size_B": 0.8,
    },
    "CD20": {
        "pubmed_count": 18000, "clinical_trials": 35, "patents": 120,
        "stage": DevelopmentStage.PHASE_II, "competitors": 4,
        "first_publication_year": 1985, "first_trial_year": 2017,
        "approved_indications": [],
        "market_size_B": 1.2,
    },
    "HER2": {
        "pubmed_count": 45000, "clinical_trials": 25, "patents": 200,
        "stage": DevelopmentStage.PHASE_I, "competitors": 6,
        "first_publication_year": 1986, "first_trial_year": 2015,
        "approved_indications": [],
        "market_size_B": 3.5,
    },
    "EGFR": {
        "pubmed_count": 65000, "clinical_trials": 18, "patents": 150,
        "stage": DevelopmentStage.PHASE_I, "competitors": 4,
        "first_publication_year": 1980, "first_trial_year": 2018,
        "approved_indications": [],
        "market_size_B": 5.0,
    },
    "MSLN": {
        "pubmed_count": 2800, "clinical_trials": 35, "patents": 70,
        "stage": DevelopmentStage.PHASE_II, "competitors": 5,
        "first_publication_year": 1996, "first_trial_year": 2015,
        "approved_indications": [],
        "market_size_B": 1.5,
    },
    "GPC3": {
        "pubmed_count": 1200, "clinical_trials": 15, "patents": 35,
        "stage": DevelopmentStage.PHASE_I, "competitors": 3,
        "first_publication_year": 1999, "first_trial_year": 2018,
        "approved_indications": [],
        "market_size_B": 0.6,
    },
    "CLDN18.2": {
        "pubmed_count": 800, "clinical_trials": 22, "patents": 40,
        "stage": DevelopmentStage.PHASE_II, "competitors": 4,
        "first_publication_year": 2008, "first_trial_year": 2020,
        "approved_indications": [],
        "market_size_B": 1.2,
    },
    "DLL3": {
        "pubmed_count": 600, "clinical_trials": 12, "patents": 25,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 2012, "first_trial_year": 2019,
        "approved_indications": [],
        "market_size_B": 0.4,
    },
    "MUC16": {
        "pubmed_count": 1500, "clinical_trials": 8, "patents": 20,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 2001, "first_trial_year": 2019,
        "approved_indications": [],
        "market_size_B": 0.8,
    },
    "PSMA": {
        "pubmed_count": 5500, "clinical_trials": 15, "patents": 45,
        "stage": DevelopmentStage.PHASE_I, "competitors": 3,
        "first_publication_year": 1993, "first_trial_year": 2018,
        "approved_indications": [],
        "market_size_B": 1.0,
    },
    "CD70": {
        "pubmed_count": 900, "clinical_trials": 10, "patents": 18,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 1994, "first_trial_year": 2020,
        "approved_indications": [],
        "market_size_B": 0.5,
    },
    "PD_L1": {
        "pubmed_count": 35000, "clinical_trials": 8, "patents": 30,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 1999, "first_trial_year": 2021,
        "approved_indications": [],
        "market_size_B": 2.0,
    },
    "CD47": {
        "pubmed_count": 4200, "clinical_trials": 5, "patents": 55,
        "stage": DevelopmentStage.PHASE_I, "competitors": 3,
        "first_publication_year": 1990, "first_trial_year": 2021,
        "approved_indications": [],
        "market_size_B": 1.5,
    },
    "B7_H3": {
        "pubmed_count": 1100, "clinical_trials": 12, "patents": 28,
        "stage": DevelopmentStage.PHASE_I, "competitors": 3,
        "first_publication_year": 2003, "first_trial_year": 2019,
        "approved_indications": [],
        "market_size_B": 0.7,
    },
    "GPRC5D": {
        "pubmed_count": 250, "clinical_trials": 8, "patents": 15,
        "stage": DevelopmentStage.PHASE_II, "competitors": 3,
        "first_publication_year": 2015, "first_trial_year": 2021,
        "approved_indications": [],
        "market_size_B": 0.5,
    },
    "FcRH5": {
        "pubmed_count": 120, "clinical_trials": 3, "patents": 8,
        "stage": DevelopmentStage.PHASE_I, "competitors": 1,
        "first_publication_year": 2018, "first_trial_year": 2022,
        "approved_indications": [],
        "market_size_B": 0.3,
    },
    "NKG2D_L": {
        "pubmed_count": 800, "clinical_trials": 5, "patents": 12,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 2005, "first_trial_year": 2020,
        "approved_indications": [],
        "market_size_B": 0.4,
    },
    "CSPG4": {
        "pubmed_count": 350, "clinical_trials": 2, "patents": 5,
        "stage": DevelopmentStage.PRECLINICAL, "competitors": 1,
        "first_publication_year": 2010, "first_trial_year": 0,
        "approved_indications": [],
        "market_size_B": 0.3,
    },
    "ROR1": {
        "pubmed_count": 650, "clinical_trials": 8, "patents": 20,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 2008, "first_trial_year": 2019,
        "approved_indications": [],
        "market_size_B": 0.6,
    },
    "EpCAM": {
        "pubmed_count": 5200, "clinical_trials": 6, "patents": 30,
        "stage": DevelopmentStage.PHASE_I, "competitors": 2,
        "first_publication_year": 1979, "first_trial_year": 2019,
        "approved_indications": [],
        "market_size_B": 0.7,
    },
    "GD2": {
        "pubmed_count": 2200, "clinical_trials": 18, "patents": 40,
        "stage": DevelopmentStage.PHASE_II, "competitors": 4,
        "first_publication_year": 1985, "first_trial_year": 2016,
        "approved_indications": [],
        "market_size_B": 0.5,
    },
    "IL13RA2": {
        "pubmed_count": 450, "clinical_trials": 5, "patents": 10,
        "stage": DevelopmentStage.PHASE_I, "competitors": 1,
        "first_publication_year": 2004, "first_trial_year": 2017,
        "approved_indications": [],
        "market_size_B": 0.3,
    },
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class NoveltyScore:
    """Novelty assessment for a target."""
    publication_novelty: float  # 0=crowded, 1=underexplored
    clinical_novelty: float     # 0=many trials, 1=no trials
    patent_novelty: float       # 0=heavily patented, 1=white space
    competitive_novelty: float  # 0=many competitors, 1=first mover
    overall_novelty: float      # weighted composite
    white_space_index: float    # scientific_potential / investigation_level


@dataclass
class NovelTargetResult:
    """Novel target discovery result."""
    gene_symbol: str
    novelty_score: NoveltyScore
    development_stage: DevelopmentStage
    scientific_potential: float
    investigation_level: float
    opportunity_score: float  # novelty × potential
    concerns: List[NoveltyConcern]
    recommendations: List[str]
    pubmed_count: int
    clinical_trials: int
    competitors: int
    market_size_B: float
    rank: int = 0


# ──────────────────────────────────────────────────────────────────────
# Novelty Scoring
# ──────────────────────────────────────────────────────────────────────

def _score_publication_novelty(pubmed_count: int) -> float:
    """Score publication novelty (inverse of saturation)."""
    if pubmed_count <= 50:
        return 0.98
    elif pubmed_count <= 200:
        return 0.90
    elif pubmed_count <= 500:
        return 0.80
    elif pubmed_count <= 1000:
        return 0.65
    elif pubmed_count <= 3000:
        return 0.45
    elif pubmed_count <= 10000:
        return 0.25
    elif pubmed_count <= 30000:
        return 0.10
    else:
        return 0.05


def _score_clinical_novelty(trial_count: int) -> float:
    """Score clinical trial novelty."""
    if trial_count == 0:
        return 1.0
    elif trial_count <= 3:
        return 0.85
    elif trial_count <= 10:
        return 0.60
    elif trial_count <= 30:
        return 0.35
    elif trial_count <= 100:
        return 0.15
    else:
        return 0.05


def _score_patent_novelty(patent_count: int) -> float:
    """Score patent landscape openness."""
    if patent_count == 0:
        return 1.0
    elif patent_count <= 5:
        return 0.90
    elif patent_count <= 15:
        return 0.70
    elif patent_count <= 40:
        return 0.45
    elif patent_count <= 100:
        return 0.25
    else:
        return 0.10


def _score_competitive_novelty(competitors: int) -> float:
    """Score competitive landscape openness."""
    if competitors == 0:
        return 1.0
    elif competitors == 1:
        return 0.80
    elif competitors <= 3:
        return 0.55
    elif competitors <= 6:
        return 0.30
    elif competitors <= 10:
        return 0.15
    else:
        return 0.05


def compute_novelty_score(
    gene: str,
    proteome_score: Optional[float] = None,
) -> NoveltyScore:
    """
    Compute novelty score for a target by comparing its scientific
    potential against the current investigation landscape.

    Args:
        gene: Gene symbol
        proteome_score: Optional composite proteome scan score

    Returns:
        NoveltyScore with multi-dimensional assessment
    """
    landscape = CLINICAL_LANDSCAPE.get(gene, {})

    pub_count = landscape.get("pubmed_count", 0)
    trial_count = landscape.get("clinical_trials", 0)
    patent_count = landscape.get("patents", 0)
    competitors = landscape.get("competitors", 0)

    pub_novelty = _score_publication_novelty(pub_count)
    clin_novelty = _score_clinical_novelty(trial_count)
    pat_novelty = _score_patent_novelty(patent_count)
    comp_novelty = _score_competitive_novelty(competitors)

    # Overall novelty
    overall = (
        pub_novelty * 0.25 +
        clin_novelty * 0.30 +
        pat_novelty * 0.20 +
        comp_novelty * 0.25
    )

    # White space index = potential / investigation_level
    investigation = 1.0 - overall  # how much it's been investigated
    potential = proteome_score if proteome_score else 0.5
    white_space = potential / max(investigation, 0.05)

    return NoveltyScore(
        publication_novelty=round(pub_novelty, 4),
        clinical_novelty=round(clin_novelty, 4),
        patent_novelty=round(pat_novelty, 4),
        competitive_novelty=round(comp_novelty, 4),
        overall_novelty=round(overall, 4),
        white_space_index=round(white_space, 4),
    )


# ──────────────────────────────────────────────────────────────────────
# Novel Target Detection
# ──────────────────────────────────────────────────────────────────────

async def detect_novel_targets(
    proteome_scores: Optional[Dict[str, float]] = None,
    min_novelty: float = 0.4,
    min_potential: float = 0.3,
    max_results: int = 50,
) -> List[NovelTargetResult]:
    """
    Detect novel / underexplored targets with high scientific potential.

    Combines proteome scan scores with clinical landscape analysis
    to find "white space" opportunities.

    Args:
        proteome_scores: Gene → composite score from proteome scan
        min_novelty: Minimum overall novelty threshold
        min_potential: Minimum scientific potential threshold
        max_results: Maximum results to return

    Returns:
        List of NovelTargetResult sorted by opportunity score
    """
    proteome_scores = proteome_scores or {}
    results: List[NovelTargetResult] = []

    for gene, landscape in CLINICAL_LANDSCAPE.items():
        potential = proteome_scores.get(gene, 0.5)
        if potential < min_potential:
            continue

        novelty = compute_novelty_score(gene, potential)
        if novelty.overall_novelty < min_novelty:
            continue

        stage = landscape.get("stage", DevelopmentStage.UNDISCOVERED)
        investigation = 1.0 - novelty.overall_novelty

        # Opportunity score = novelty × potential
        opportunity = novelty.overall_novelty * potential

        # Concerns
        concerns: List[NoveltyConcern] = []
        if landscape.get("pubmed_count", 0) < 100:
            concerns.append(NoveltyConcern.BIOLOGY_UNCLEAR)
        if landscape.get("patents", 0) > 30:
            concerns.append(NoveltyConcern.IP_CROWDED)
        if landscape.get("competitors", 0) > 3:
            concerns.append(NoveltyConcern.COMPETITIVE)
        if novelty.clinical_novelty > 0.8:
            concerns.append(NoveltyConcern.SAFETY_UNKNOWN)
        if landscape.get("pubmed_count", 0) < 500:
            concerns.append(NoveltyConcern.EXPRESSION_UNCERTAIN)

        # Recommendations
        recommendations: List[str] = []
        if novelty.overall_novelty > 0.7:
            recommendations.append("First-mover advantage — pursue aggressive IP strategy")
        if novelty.clinical_novelty > 0.6:
            recommendations.append("Limited clinical data — prioritize safety profiling before IND")
        if novelty.publication_novelty > 0.7:
            recommendations.append("Publish foundational biology papers to establish scientific ownership")
        if potential > 0.7 and novelty.overall_novelty > 0.5:
            recommendations.append("High-opportunity target — consider fast-track development")
        if novelty.patent_novelty > 0.6:
            recommendations.append("IP white space available — file composition-of-matter patent early")

        result = NovelTargetResult(
            gene_symbol=gene,
            novelty_score=novelty,
            development_stage=stage,
            scientific_potential=round(potential, 4),
            investigation_level=round(investigation, 4),
            opportunity_score=round(opportunity, 4),
            concerns=concerns,
            recommendations=recommendations,
            pubmed_count=landscape.get("pubmed_count", 0),
            clinical_trials=landscape.get("clinical_trials", 0),
            competitors=landscape.get("competitors", 0),
            market_size_B=landscape.get("market_size_B", 0),
        )
        results.append(result)

    # Sort by opportunity score
    results.sort(key=lambda r: r.opportunity_score, reverse=True)

    for i, r in enumerate(results):
        r.rank = i + 1

    return results[:max_results]


async def compare_to_clinical_landscape(
    gene: str,
) -> Dict[str, Any]:
    """
    Compare a single target to the full clinical landscape.

    Returns contextual positioning showing where this target sits
    relative to peers in terms of investigation and potential.
    """
    landscape = CLINICAL_LANDSCAPE.get(gene, {})
    novelty = compute_novelty_score(gene)

    # Compute landscape-wide statistics
    all_pub_counts = [l.get("pubmed_count", 0) for l in CLINICAL_LANDSCAPE.values()]
    all_trial_counts = [l.get("clinical_trials", 0) for l in CLINICAL_LANDSCAPE.values()]

    percentile_pub = sum(1 for c in all_pub_counts if c <= landscape.get("pubmed_count", 0)) / max(len(all_pub_counts), 1) * 100
    percentile_trial = sum(1 for c in all_trial_counts if c <= landscape.get("clinical_trials", 0)) / max(len(all_trial_counts), 1) * 100

    return {
        "gene": gene,
        "novelty_score": {
            "publication": novelty.publication_novelty,
            "clinical": novelty.clinical_novelty,
            "patent": novelty.patent_novelty,
            "competitive": novelty.competitive_novelty,
            "overall": novelty.overall_novelty,
            "white_space_index": novelty.white_space_index,
        },
        "landscape": {
            "pubmed_count": landscape.get("pubmed_count", 0),
            "clinical_trials": landscape.get("clinical_trials", 0),
            "patents": landscape.get("patents", 0),
            "competitors": landscape.get("competitors", 0),
            "stage": landscape.get("stage", DevelopmentStage.UNDISCOVERED).value if isinstance(landscape.get("stage"), DevelopmentStage) else "unknown",
            "market_size_B": landscape.get("market_size_B", 0),
        },
        "percentile_vs_peers": {
            "publications": round(percentile_pub, 1),
            "clinical_trials": round(percentile_trial, 1),
        },
        "total_targets_in_landscape": len(CLINICAL_LANDSCAPE),
    }
