"""
CARVanta Trials — NLP-Based Patient-Trial Matching Engine
==========================================================
AI-powered matching system that compares patient genomic profiles,
disease characteristics, and biomarkers against trial eligibility
criteria to produce ranked match scores.

Matching Dimensions:
1. Target antigen concordance (patient tumor expresses trial target)
2. Disease type match (cancer type alignment)
3. Biomarker compatibility (required biomarker presence)
4. Prior therapy alignment (treatment history vs requirements)
5. Age/performance status eligibility
6. Geographic accessibility

Output: Ranked list of trials with multi-dimensional match scores,
eligibility assessment, and match rationale.

Security: Stateless, async, PII-free (profile data not persisted).
API Version: v5
"""

import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.trials.matcher")

# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class PatientProfile:
    """Patient profile for trial matching."""
    patient_id: str = ""
    age: int = 50
    gender: str = "All"
    ecog_status: int = 1
    cancer_type: str = ""
    cancer_subtype: str = ""
    stage: str = "IV"
    histology: str = ""
    prior_therapies: int = 0
    prior_therapy_types: List[str] = field(default_factory=list)
    biomarkers: Dict[str, Any] = field(default_factory=dict)
    target_antigens_expressed: List[str] = field(default_factory=list)
    hla_type: List[str] = field(default_factory=list)
    tmb: Optional[float] = None
    msi_status: str = "MSS"
    mutations: List[str] = field(default_factory=list)
    location: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    willing_to_travel_km: float = 500.0
    comorbidities: List[str] = field(default_factory=list)
    organ_function: Dict[str, str] = field(default_factory=dict)
    prior_car_t: bool = False


@dataclass
class MatchDimension:
    """Single dimension of a trial match score."""
    dimension: str
    score: float  # 0.0 to 1.0
    weight: float
    rationale: str
    is_disqualifying: bool = False


@dataclass
class TrialMatch:
    """Patient-trial match result."""
    nct_id: str
    trial_title: str
    target_antigen: str
    phase: str
    status: str
    overall_score: float
    dimensions: List[MatchDimension]
    eligible: bool
    eligibility_issues: List[str]
    nearest_site: Optional[Dict[str, Any]] = None
    distance_km: Optional[float] = None
    rank: int = 0


# ──────────────────────────────────────────────────────────────────────
# Matching Weights
# ──────────────────────────────────────────────────────────────────────

_MATCH_WEIGHTS = {
    "target_antigen": 0.30,
    "disease_type": 0.25,
    "biomarker_compat": 0.15,
    "prior_therapy": 0.10,
    "age_ecog": 0.08,
    "geographic": 0.07,
    "trial_phase": 0.05,
}

# Disease type mappings
_DISEASE_ALIASES: Dict[str, List[str]] = {
    "ALL": ["acute lymphoblastic leukemia", "b-all", "t-all", "b-cell all", "lymphoblastic"],
    "AML": ["acute myeloid leukemia", "myeloid", "aml"],
    "CLL": ["chronic lymphocytic leukemia", "cll", "sll"],
    "DLBCL": ["diffuse large b-cell lymphoma", "dlbcl", "lbcl", "large b-cell"],
    "FL": ["follicular lymphoma", "fl", "indolent"],
    "MCL": ["mantle cell lymphoma", "mcl"],
    "MM": ["multiple myeloma", "myeloma", "mm", "plasma cell"],
    "HL": ["hodgkin", "hodgkin lymphoma", "hl"],
    "NSCLC": ["non-small cell lung", "nsclc", "lung adenocarcinoma", "squamous lung"],
    "SCLC": ["small cell lung", "sclc", "neuroendocrine"],
    "BREAST": ["breast cancer", "triple negative", "tnbc", "her2+", "breast"],
    "OVARIAN": ["ovarian", "fallopian", "peritoneal"],
    "PANCREATIC": ["pancreatic", "pancreas", "pdac"],
    "GBM": ["glioblastoma", "gbm", "brain tumor", "glioma"],
    "HCC": ["hepatocellular", "liver cancer", "hcc"],
    "MESOTHELIOMA": ["mesothelioma", "pleural"],
    "GASTRIC": ["gastric", "stomach", "gastroesophageal"],
    "RENAL": ["renal", "kidney", "rcc", "clear cell"],
    "PROSTATE": ["prostate", "crpc", "castration-resistant"],
}

# Target antigen synonyms
_TARGET_SYNONYMS: Dict[str, List[str]] = {
    "CD19": ["cd19", "fmc63"],
    "CD22": ["cd22"],
    "BCMA": ["bcma", "tnfrsf17", "b-cell maturation antigen"],
    "HER2": ["her2", "erbb2", "her-2", "neu"],
    "MSLN": ["msln", "mesothelin"],
    "GPC3": ["gpc3", "glypican-3", "glypican3"],
    "DLL3": ["dll3", "delta-like 3"],
    "EGFR": ["egfr", "egfr806", "her1"],
    "PSMA": ["psma", "folh1"],
    "CD47": ["cd47", "don't eat me"],
    "PD_L1": ["pd-l1", "pdl1", "cd274"],
    "B7_H3": ["b7-h3", "b7h3", "cd276"],
    "EpCAM": ["epcam", "cd326", "epithelial cell adhesion"],
    "GPRC5D": ["gprc5d"],
    "CD70": ["cd70"],
    "NKG2D": ["nkg2d", "nkg2dl"],
    "CLDN18.2": ["claudin", "cldn18", "claudin 18.2"],
}


# ──────────────────────────────────────────────────────────────────────
# Matching Functions
# ──────────────────────────────────────────────────────────────────────

def _match_target_antigen(patient: PatientProfile, trial_target: str) -> MatchDimension:
    """Score target antigen concordance."""
    expressed = [t.upper() for t in patient.target_antigens_expressed]
    trial_t = trial_target.upper().replace("-", "_")

    # Direct match
    if trial_t in expressed:
        return MatchDimension("target_antigen", 1.0, _MATCH_WEIGHTS["target_antigen"],
                              f"Patient tumor expresses {trial_t}, matching trial target.")

    # Check synonyms
    for canonical, aliases in _TARGET_SYNONYMS.items():
        if canonical.upper() == trial_t:
            if any(a.upper() in expressed or canonical.upper() in expressed for a in aliases):
                return MatchDimension("target_antigen", 0.9, _MATCH_WEIGHTS["target_antigen"],
                                      f"Patient expresses synonym of {trial_t}.")

    # Bispecific: partial match
    if "/" in trial_target:
        parts = trial_target.split("/")
        matches = sum(1 for p in parts if p.upper() in expressed)
        if matches > 0:
            score = matches / len(parts) * 0.8
            return MatchDimension("target_antigen", score, _MATCH_WEIGHTS["target_antigen"],
                                  f"Patient expresses {matches}/{len(parts)} targets in bispecific trial.")

    # No expression data available
    if not patient.target_antigens_expressed:
        return MatchDimension("target_antigen", 0.3, _MATCH_WEIGHTS["target_antigen"],
                              "Target expression status unknown; tissue testing recommended.")

    return MatchDimension("target_antigen", 0.0, _MATCH_WEIGHTS["target_antigen"],
                          f"Patient tumor does not express {trial_t}.", is_disqualifying=True)


def _match_disease_type(patient: PatientProfile, trial_disease: str, trial_conditions: List[str]) -> MatchDimension:
    """Score disease type concordance."""
    patient_cancer = patient.cancer_type.lower()
    patient_subtype = patient.cancer_subtype.lower()

    # Direct match
    if trial_disease.lower() in patient_cancer or patient_cancer in trial_disease.lower():
        return MatchDimension("disease_type", 1.0, _MATCH_WEIGHTS["disease_type"],
                              f"Direct disease match: {trial_disease}.")

    # Alias matching
    for key, aliases in _DISEASE_ALIASES.items():
        if any(a in patient_cancer or a in patient_subtype for a in aliases):
            if key.lower() == trial_disease.lower() or any(key.lower() in c.lower() for c in trial_conditions):
                return MatchDimension("disease_type", 0.95, _MATCH_WEIGHTS["disease_type"],
                                      f"Disease matches via alias: {key}.")

    # Condition-level matching
    for cond in trial_conditions:
        if any(term in patient_cancer for term in cond.lower().split()):
            return MatchDimension("disease_type", 0.7, _MATCH_WEIGHTS["disease_type"],
                                  f"Partial disease match with trial condition: {cond}.")

    # Solid tumor basket trial
    if trial_disease.lower() in ["solid_tumor", "solid tumor"]:
        solid_types = ["breast", "lung", "colon", "prostate", "ovarian", "pancreatic", "gastric", "renal", "liver"]
        if any(s in patient_cancer for s in solid_types):
            return MatchDimension("disease_type", 0.6, _MATCH_WEIGHTS["disease_type"],
                                  "Basket trial accepting multiple solid tumor types.")

    return MatchDimension("disease_type", 0.0, _MATCH_WEIGHTS["disease_type"],
                          f"Disease mismatch: patient has {patient.cancer_type}, trial requires {trial_disease}.", is_disqualifying=True)


def _match_biomarkers(patient: PatientProfile, required_biomarkers: List[str]) -> MatchDimension:
    """Score biomarker compatibility."""
    if not required_biomarkers:
        return MatchDimension("biomarker_compat", 0.8, _MATCH_WEIGHTS["biomarker_compat"],
                              "No specific biomarkers required.")

    patient_markers = {k.upper(): v for k, v in patient.biomarkers.items()}
    patient_targets = [t.upper() for t in patient.target_antigens_expressed]
    met = 0
    issues: List[str] = []

    for req in required_biomarkers:
        req_upper = req.upper().replace("+", "").strip()
        if req_upper in patient_markers or req_upper in patient_targets:
            met += 1
        elif any(req_upper in t for t in patient_targets):
            met += 1
        else:
            issues.append(f"Missing biomarker: {req}")

    score = met / len(required_biomarkers) if required_biomarkers else 0.8
    rationale = f"Met {met}/{len(required_biomarkers)} biomarker requirements."
    if issues:
        rationale += " " + "; ".join(issues[:3])

    return MatchDimension("biomarker_compat", score, _MATCH_WEIGHTS["biomarker_compat"],
                          rationale, is_disqualifying=score == 0)


def _match_prior_therapy(patient: PatientProfile, required_prior: int, trial_target: str) -> MatchDimension:
    """Score prior therapy alignment."""
    if patient.prior_therapies >= required_prior:
        score = 1.0
        rationale = f"Patient has {patient.prior_therapies} prior lines (≥{required_prior} required)."
    elif patient.prior_therapies == required_prior - 1:
        score = 0.5
        rationale = f"Patient has {patient.prior_therapies} prior lines, {required_prior} required. May qualify after next line."
    else:
        score = 0.1
        rationale = f"Patient has {patient.prior_therapies} prior lines, but {required_prior} required."

    # Check for prior same-target CAR-T (usually excluded)
    if patient.prior_car_t:
        score *= 0.3
        rationale += " Prior CAR-T therapy may be exclusionary."

    return MatchDimension("prior_therapy", score, _MATCH_WEIGHTS["prior_therapy"], rationale)


def _match_age_ecog(patient: PatientProfile, min_age: int, max_age: int, max_ecog: int) -> MatchDimension:
    """Score age and performance status eligibility."""
    issues: List[str] = []
    score = 1.0

    if patient.age < min_age:
        score -= 0.5
        issues.append(f"Patient age {patient.age} below minimum {min_age}")
    if patient.age > max_age:
        score -= 0.5
        issues.append(f"Patient age {patient.age} above maximum {max_age}")
    if patient.ecog_status > max_ecog:
        score -= 0.4
        issues.append(f"Patient ECOG {patient.ecog_status} exceeds maximum {max_ecog}")

    score = max(0.0, score)
    rationale = f"Age {patient.age}, ECOG {patient.ecog_status}."
    if issues:
        rationale += " Issues: " + "; ".join(issues)
    else:
        rationale += " Within eligibility criteria."

    return MatchDimension("age_ecog", score, _MATCH_WEIGHTS["age_ecog"],
                          rationale, is_disqualifying=score < 0.3)


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points on Earth in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _match_geographic(patient: PatientProfile, sites: list) -> Tuple[MatchDimension, Optional[Dict[str, Any]], Optional[float]]:
    """Score geographic accessibility."""
    if not patient.latitude or not patient.longitude or not sites:
        return (MatchDimension("geographic", 0.5, _MATCH_WEIGHTS["geographic"],
                               "Patient location unknown; cannot assess proximity."), None, None)

    nearest = None
    min_dist = float('inf')
    for site in sites:
        if hasattr(site, 'latitude') and site.latitude:
            dist = _haversine_distance(patient.latitude, patient.longitude, site.latitude, site.longitude)
            if dist < min_dist:
                min_dist = dist
                nearest = site

    if nearest is None:
        return (MatchDimension("geographic", 0.3, _MATCH_WEIGHTS["geographic"],
                               "No site coordinates available."), None, None)

    if min_dist <= 50:
        score = 1.0
    elif min_dist <= 200:
        score = 0.8
    elif min_dist <= 500:
        score = 0.6
    elif min_dist <= 1000:
        score = 0.4
    elif min_dist <= patient.willing_to_travel_km:
        score = 0.3
    else:
        score = 0.1

    site_info = {"facility": nearest.facility, "city": nearest.city, "country": nearest.country,
                 "latitude": nearest.latitude, "longitude": nearest.longitude}

    rationale = f"Nearest site: {nearest.facility} ({nearest.city}), {min_dist:.0f} km away."
    return (MatchDimension("geographic", score, _MATCH_WEIGHTS["geographic"], rationale), site_info, round(min_dist, 1))


def _match_trial_phase(phase: str) -> MatchDimension:
    """Score trial phase (later phases generally preferred)."""
    phase_scores = {
        "Phase 3": 1.0, "Phase 2/Phase 3": 0.9, "Phase 2": 0.8,
        "Phase 1/Phase 2": 0.7, "Phase 1": 0.5, "Early Phase 1": 0.3,
    }
    score = phase_scores.get(phase, 0.5)
    return MatchDimension("trial_phase", score, _MATCH_WEIGHTS["trial_phase"],
                          f"Trial is {phase}. Later phases have more efficacy data.")


# ──────────────────────────────────────────────────────────────────────
# Main Matching Pipeline
# ──────────────────────────────────────────────────────────────────────

async def match_patient_to_trials(
    patient: PatientProfile,
    max_results: int = 15,
    min_score: float = 0.2,
    include_ineligible: bool = False,
) -> Dict[str, Any]:
    """
    Match a patient to clinical trials across all dimensions.
    Returns ranked list of trial matches with scores and rationale.
    """
    from trials.clinicaltrials_sync import get_trial_database
    trials = await get_trial_database()

    matches: List[TrialMatch] = []

    for trial in trials:
        # Skip non-recruiting unless include_ineligible
        if "Recruiting" not in trial.status and not include_ineligible:
            if trial.status not in ["Enrolling by invitation", "Not yet recruiting"]:
                continue

        # Compute all dimensions
        dims: List[MatchDimension] = []
        dims.append(_match_target_antigen(patient, trial.target_antigen))
        dims.append(_match_disease_type(patient, trial.disease_category, trial.conditions))
        dims.append(_match_biomarkers(patient, trial.eligibility.required_biomarkers))
        dims.append(_match_prior_therapy(patient, trial.eligibility.prior_therapies_required, trial.target_antigen))
        dims.append(_match_age_ecog(patient, trial.eligibility.min_age, trial.eligibility.max_age, trial.eligibility.ecog_max))
        geo_dim, nearest_site, distance = _match_geographic(patient, trial.sites)
        dims.append(geo_dim)
        dims.append(_match_trial_phase(trial.phase))

        # Overall weighted score
        overall = sum(d.score * d.weight for d in dims) / sum(d.weight for d in dims)
        disqualifiers = [d for d in dims if d.is_disqualifying]
        eligible = len(disqualifiers) == 0
        issues = [d.rationale for d in disqualifiers]

        if not include_ineligible and not eligible:
            continue
        if overall < min_score:
            continue

        matches.append(TrialMatch(
            nct_id=trial.nct_id, trial_title=trial.title,
            target_antigen=trial.target_antigen, phase=trial.phase, status=trial.status,
            overall_score=round(overall, 4), dimensions=dims,
            eligible=eligible, eligibility_issues=issues,
            nearest_site=nearest_site, distance_km=distance,
        ))

    # Rank by score
    matches.sort(key=lambda m: m.overall_score, reverse=True)
    for i, m in enumerate(matches):
        m.rank = i + 1

    matches = matches[:max_results]

    return {
        "patient_id": patient.patient_id,
        "total_matches": len(matches),
        "eligible_count": sum(1 for m in matches if m.eligible),
        "matches": [
            {
                "rank": m.rank, "nct_id": m.nct_id, "title": m.trial_title,
                "target": m.target_antigen, "phase": m.phase, "status": m.status,
                "overall_score": m.overall_score, "eligible": m.eligible,
                "eligibility_issues": m.eligibility_issues,
                "nearest_site": m.nearest_site, "distance_km": m.distance_km,
                "dimensions": [
                    {"dimension": d.dimension, "score": round(d.score, 3), "weight": d.weight, "rationale": d.rationale}
                    for d in m.dimensions
                ],
            }
            for m in matches
        ],
    }
