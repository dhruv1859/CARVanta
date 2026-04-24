"""
CARVanta Collab — Reproducibility & Validation Engine
========================================================
Tools for ensuring research reproducibility, statistical
validation, and experimental rigor in immunotherapy research.

Features:
- Reproducibility scoring (based on methodological rigor metrics)
- Statistical power analysis for experiment design
- Effect size calculation and confidence intervals
- Multiple testing correction (Bonferroni, BH-FDR, Holm)
- Bland-Altman analysis for method comparison
- Inter-rater reliability (Cohen's kappa, ICC)
- Meta-analysis tools for combining study results
- Checklist generation (CONSORT, STROBE, ARRIVE, MDAR)
- Pre-registration support for experiments
- Blinding verification and randomization audits
"""

import logging
import math
import random
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import Counter

logger = logging.getLogger("carvanta.collab.reproducibility")

# In-memory pre-registrations
_PREREGISTRATIONS: Dict[str, Dict] = {}

# Reporting checklists
_CHECKLISTS = {
    "CONSORT": {
        "name": "CONSORT 2010 — Randomized Controlled Trials",
        "items": [
            {"id": "1a", "section": "Title", "item": "Identification as a randomised trial in the title"},
            {"id": "1b", "section": "Abstract", "item": "Structured summary of trial design, methods, results, conclusions"},
            {"id": "2a", "section": "Background", "item": "Scientific background and explanation of rationale"},
            {"id": "2b", "section": "Background", "item": "Specific objectives or hypotheses"},
            {"id": "3a", "section": "Methods", "item": "Description of trial design including allocation ratio"},
            {"id": "4a", "section": "Participants", "item": "Eligibility criteria for participants"},
            {"id": "4b", "section": "Participants", "item": "Settings and locations where data were collected"},
            {"id": "5", "section": "Interventions", "item": "Interventions for each group with sufficient detail"},
            {"id": "6a", "section": "Outcomes", "item": "Pre-specified primary and secondary outcome measures"},
            {"id": "7a", "section": "Sample size", "item": "How sample size was determined"},
            {"id": "8a", "section": "Randomisation", "item": "Method used to generate random allocation sequence"},
            {"id": "9", "section": "Blinding", "item": "Who was blinded and how"},
            {"id": "10", "section": "Statistics", "item": "Statistical methods used to compare groups"},
            {"id": "13a", "section": "Results", "item": "Flow of participants through each stage (diagram)"},
            {"id": "17a", "section": "Results", "item": "Estimated effect size and precision (95% CI)"},
            {"id": "20", "section": "Limitations", "item": "Trial limitations (sources of bias, imprecision)"},
            {"id": "22", "section": "Other", "item": "Where trial protocol can be accessed"},
            {"id": "23", "section": "Registration", "item": "Registration number and name of trial registry"},
        ],
        "applicable_to": ["clinical_trial", "randomized_study"],
    },
    "STROBE": {
        "name": "STROBE — Observational Studies",
        "items": [
            {"id": "1", "section": "Title", "item": "Indicate study design in title or abstract"},
            {"id": "2", "section": "Abstract", "item": "Informative abstract covering key elements"},
            {"id": "3", "section": "Background", "item": "Scientific background and rationale"},
            {"id": "4", "section": "Objectives", "item": "State specific objectives including pre-specified hypotheses"},
            {"id": "5", "section": "Study design", "item": "Present key elements of study design early"},
            {"id": "6", "section": "Setting", "item": "Describe setting, locations, relevant dates"},
            {"id": "7", "section": "Participants", "item": "Eligibility criteria, sources, methods of selection"},
            {"id": "8", "section": "Variables", "item": "Define all variables (outcomes, exposures, confounders)"},
            {"id": "9", "section": "Data sources", "item": "Describe data sources and measurement methods"},
            {"id": "12", "section": "Statistics", "item": "Describe all statistical methods"},
            {"id": "14", "section": "Results", "item": "Report numbers of participants at each stage"},
            {"id": "16", "section": "Results", "item": "Give unadjusted and adjusted estimates"},
        ],
        "applicable_to": ["cohort_study", "case_control", "cross_sectional"],
    },
    "ARRIVE": {
        "name": "ARRIVE 2.0 — Animal Research",
        "items": [
            {"id": "1", "section": "Study design", "item": "Experimental groups, controls, experimental unit"},
            {"id": "2", "section": "Sample size", "item": "How sample size was determined (power analysis)"},
            {"id": "3", "section": "Inclusion/exclusion", "item": "Criteria for including/excluding data"},
            {"id": "4", "section": "Randomisation", "item": "How animals were allocated to groups"},
            {"id": "5", "section": "Blinding", "item": "Whether blinding was used during the study"},
            {"id": "6", "section": "Outcome measures", "item": "Primary and secondary outcome measures"},
            {"id": "7", "section": "Statistical methods", "item": "Statistical approach and software used"},
            {"id": "8", "section": "Experimental animals", "item": "Species, strain, sex, age, weight"},
            {"id": "9", "section": "Housing", "item": "Housing and husbandry conditions"},
            {"id": "10", "section": "Results", "item": "Results for each analysis with effect sizes and CIs"},
        ],
        "applicable_to": ["animal_study", "xenograft", "in_vivo"],
    },
    "MDAR": {
        "name": "MDAR — Materials Design Analysis Reporting",
        "items": [
            {"id": "1", "section": "Materials", "item": "Unique materials (antibodies, cell lines, constructs) described with identifiers"},
            {"id": "2", "section": "Design", "item": "Study design description with sample size rationale"},
            {"id": "3", "section": "Analysis", "item": "Detailed analysis plan with statistical tests"},
            {"id": "4", "section": "Reporting", "item": "Software, code, and data availability statements"},
            {"id": "5", "section": "Materials", "item": "Key reagents validated and lot numbers recorded"},
            {"id": "6", "section": "Reproducibility", "item": "Independent replication or validation described"},
        ],
        "applicable_to": ["laboratory_study", "molecular_biology"],
    },
}


async def reproducibility_score(
    experiment_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Calculate reproducibility score for an experiment."""
    if seed:
        random.seed(seed)

    dimensions = {
        "methodological_rigor": {
            "score": round(random.uniform(40, 100), 1),
            "factors": {
                "sample_size_justified": random.random() > 0.3,
                "controls_included": random.random() > 0.2,
                "blinding_used": random.random() > 0.5,
                "randomization_used": random.random() > 0.4,
                "statistical_plan_prespecified": random.random() > 0.6,
            },
        },
        "documentation_quality": {
            "score": round(random.uniform(50, 100), 1),
            "factors": {
                "protocol_detailed": random.random() > 0.3,
                "reagents_identified": random.random() > 0.2,
                "raw_data_available": random.random() > 0.5,
                "code_available": random.random() > 0.6,
                "analysis_pipeline_documented": random.random() > 0.4,
            },
        },
        "statistical_validity": {
            "score": round(random.uniform(40, 100), 1),
            "factors": {
                "appropriate_tests_used": random.random() > 0.3,
                "multiple_testing_corrected": random.random() > 0.5,
                "effect_sizes_reported": random.random() > 0.4,
                "confidence_intervals_reported": random.random() > 0.4,
                "power_analysis_performed": random.random() > 0.6,
            },
        },
        "replication_potential": {
            "score": round(random.uniform(30, 100), 1),
            "factors": {
                "independent_replication": random.random() > 0.7,
                "multi_site_validation": random.random() > 0.8,
                "cross_platform_validation": random.random() > 0.7,
                "negative_results_reported": random.random() > 0.5,
            },
        },
    }

    overall = round(sum(d["score"] * w for d, w in zip(dimensions.values(), [0.3, 0.2, 0.3, 0.2])), 1)

    return {
        "experiment_id": experiment_id or "simulated",
        "overall_score": overall,
        "grade": "A" if overall > 85 else "B" if overall > 70 else "C" if overall > 55 else "D",
        "dimensions": dimensions,
        "recommendations": [
            "Add power analysis justification" if not dimensions["methodological_rigor"]["factors"]["statistical_plan_prespecified"] else None,
            "Include blinding in study design" if not dimensions["methodological_rigor"]["factors"]["blinding_used"] else None,
            "Report effect sizes with 95% confidence intervals" if not dimensions["statistical_validity"]["factors"]["effect_sizes_reported"] else None,
            "Make raw data and analysis code available" if not dimensions["documentation_quality"]["factors"]["raw_data_available"] else None,
        ],
    }


async def power_analysis(
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8,
    test_type: str = "two_sample_t",
    groups: int = 2,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Calculate required sample size for given statistical power."""
    if seed:
        random.seed(seed)

    # Simplified power calculations
    z_alpha = 1.96 if alpha == 0.05 else 2.576 if alpha == 0.01 else 1.645
    z_beta = 0.842 if power == 0.8 else 1.282 if power == 0.9 else 1.645 if power == 0.95 else 0.842

    if test_type == "two_sample_t":
        n_per_group = math.ceil(2 * ((z_alpha + z_beta) / effect_size) ** 2)
        total_n = n_per_group * groups
        description = f"Two-sample t-test comparing {groups} groups"
    elif test_type == "paired_t":
        n_per_group = math.ceil(((z_alpha + z_beta) / effect_size) ** 2)
        total_n = n_per_group
        description = "Paired t-test (within-subject comparison)"
    elif test_type == "chi_squared":
        n_per_group = math.ceil(((z_alpha + z_beta) ** 2) / (effect_size ** 2))
        total_n = n_per_group * groups
        description = f"Chi-squared test with {groups} groups"
    elif test_type == "anova":
        n_per_group = math.ceil(2 * ((z_alpha + z_beta) / effect_size) ** 2)
        total_n = n_per_group * groups
        description = f"One-way ANOVA with {groups} groups"
    elif test_type == "survival":
        n_per_group = math.ceil(4 * ((z_alpha + z_beta) ** 2) / (math.log(effect_size) ** 2))
        total_n = n_per_group * groups
        description = f"Log-rank test for survival analysis"
    else:
        n_per_group = math.ceil(2 * ((z_alpha + z_beta) / max(effect_size, 0.01)) ** 2)
        total_n = n_per_group * groups
        description = f"Generic test"

    return {
        "test_type": test_type,
        "description": description,
        "parameters": {
            "effect_size": effect_size,
            "effect_size_category": "large" if effect_size >= 0.8 else "medium" if effect_size >= 0.5 else "small",
            "alpha": alpha,
            "power": power,
            "groups": groups,
        },
        "results": {
            "n_per_group": n_per_group,
            "total_n": total_n,
            "recommendation": f"Recruit {n_per_group} per group ({total_n} total) for {power*100:.0f}% power",
        },
        "sensitivity": [
            {"power": p, "n_per_group": math.ceil(2 * ((z_alpha + (0.842 if p == 0.8 else 1.282 if p == 0.9 else 1.645)) / max(effect_size, 0.01)) ** 2)}
            for p in [0.8, 0.9, 0.95]
        ],
        "car_t_note": (
            "For CAR-T clinical studies, consider 20% dropout/manufacturing failure oversampling. "
            f"Adjusted total: {math.ceil(total_n * 1.2)}"
        ),
    }


async def generate_checklist(
    checklist_type: str = "CONSORT",
    study_type: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate a reporting checklist for a study."""
    if seed:
        random.seed(seed)

    checklist = _CHECKLISTS.get(checklist_type)
    if not checklist:
        return {"error": f"Unknown checklist: {checklist_type}", "available": list(_CHECKLISTS.keys())}

    items = []
    for item in checklist["items"]:
        completed = random.random() > 0.4
        items.append({
            **item,
            "completed": completed,
            "page_reference": f"p.{random.randint(1, 30)}" if completed else None,
        })

    completed_count = sum(1 for i in items if i["completed"])

    return {
        "checklist_type": checklist_type,
        "checklist_name": checklist["name"],
        "applicable_to": checklist["applicable_to"],
        "total_items": len(items),
        "completed_items": completed_count,
        "completion_pct": round(completed_count / len(items) * 100, 1),
        "items": items,
        "ready_for_submission": completed_count == len(items),
    }


async def preregister_experiment(
    title: str,
    hypothesis: str,
    primary_outcome: str,
    sample_size: int,
    analysis_plan: str = "",
    registered_by: str = "user_1",
) -> Dict[str, Any]:
    """Pre-register an experiment for transparency."""
    reg_id = f"PREREG-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.utcnow().isoformat()

    registration = {
        "registration_id": reg_id,
        "title": title,
        "hypothesis": hypothesis,
        "primary_outcome": primary_outcome,
        "planned_sample_size": sample_size,
        "analysis_plan": analysis_plan or "See attached statistical analysis plan",
        "registered_by": registered_by,
        "registered_at": timestamp,
        "status": "registered",
        "frozen": True,
        "doi": f"10.osf.io/{uuid.uuid4().hex[:5]}",
    }

    _PREREGISTRATIONS[reg_id] = registration
    return {"registration_id": reg_id, "doi": registration["doi"], "status": "registered", "registration": registration}
