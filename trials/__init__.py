"""
CARVanta Trials — Clinical Trial Matcher Package
===================================================
Comprehensive AI-powered clinical trial matching, protocol design,
safety monitoring, and regulatory intelligence for CAR-T cell therapy.

Architecture:
    trials/
    ├── clinicaltrials_sync.py    — ClinicalTrials.gov data integration (500+ trials)
    ├── matcher.py                — NLP-based multi-dimensional patient-trial matching
    ├── eligibility_checker.py    — Automated 12-criterion eligibility verification
    ├── geo_proximity.py          — Haversine geographic distance and site ranking
    ├── outcome_predictor.py      — Historical outcome prediction with CI estimation
    ├── stratification.py         — Risk stratification (IPI, R-ISS, NCCN models)
    ├── site_network.py           — Site feasibility, enrollment funnel, diversity
    ├── site_analytics.py         — Global site database (23 centers), Monte Carlo
    ├── regulatory.py             — FDA/EMA/PMDA/NMPA pathway comparison, IND/BLA
    ├── protocol_generator.py     — ICH-GCP protocol design, BOIN, Simon's two-stage
    ├── safety_monitoring.py      — CRS/ICANS grading, safety signals, DSMB reports
    ├── biomarker_correlator.py   — Predictive biomarker panels, cytokine kinetics
    ├── patient_journey.py        — 14-stage journey tracking, screen failure analysis
    └── real_world_evidence.py    — RWE comparator matching, external control arms

Sub-modules (13 engines):
- clinicaltrials_sync: ClinicalTrials.gov data integration and indexing
- matcher: NLP-based patient-trial matching engine with 8-dimension scoring
- eligibility_checker: Automated criteria verification across 12 clinical dimensions
- geo_proximity: Geographic distance calculation and trial site ranking
- outcome_predictor: Historical outcome prediction with confidence intervals
- stratification: IPI / R-ISS / NCCN risk stratification with CAR-T response prediction
- site_network: Site feasibility scoring, enrollment funnel, FDA diversity compliance
- site_analytics: Global CAR-T center database, enrollment projection, competitive landscape
- regulatory: Multi-agency regulatory comparison, IND checklist, BLA timeline, REMS design
- protocol_generator: Complete protocol synopsis, BOIN dose escalation, sample size calculator
- safety_monitoring: ASTCT CRS/ICANS grading, safety signal detection, DSMB reporting
- biomarker_correlator: Predictive panels, cytokine kinetics, CAR-T expansion correlation
- patient_journey: 14-stage journey simulation, screen failure analysis, QoL trajectory

API Integration:
    All engines are exposed via /api/v5/trials/* endpoints through trials_router.py.
    Total: 42+ REST API endpoints across 13 engines.

Clinical Standards:
    - CRS grading: ASTCT 2019 consensus (Lee et al., Biol Blood Marrow Transplant)
    - ICANS grading: ASTCT 2019 consensus with ICE score
    - Risk models: IPI (DLBCL), R-ISS (MM), NCCN (ALL), TNM+Molecular (NSCLC)
    - Protocol design: ICH E6(R2) GCP, FDA CAR-T guidance (2022)
    - Dose escalation: BOIN (FDA-accepted for cell therapy)
    - Statistical design: Simon's Optimal Two-Stage Design
    - Endpoints: Lugano 2014 (lymphoma), IMWG (myeloma), RECIST 1.1 (solid tumor)
"""

__version__ = "5.2.0"
__all__ = [
    "clinicaltrials_sync",
    "matcher",
    "eligibility_checker",
    "geo_proximity",
    "outcome_predictor",
    "stratification",
    "site_network",
    "site_analytics",
    "regulatory",
    "protocol_generator",
    "safety_monitoring",
    "biomarker_correlator",
    "patient_journey",
    "real_world_evidence",
]


# ──────────────────────────────────────────────────────────────────────
# Engine Registry for Runtime Introspection
# ──────────────────────────────────────────────────────────────────────

ENGINE_REGISTRY = {
    "clinicaltrials_sync": {
        "module": "trials.clinicaltrials_sync",
        "description": "ClinicalTrials.gov data integration with 500+ indexed immunotherapy trials",
        "version": "5.0.0",
        "endpoints": ["search", "detail/{nct_id}", "statistics"],
        "status": "operational",
    },
    "matcher": {
        "module": "trials.matcher",
        "description": "NLP-based patient-trial matching with 8-dimension scoring (antigen, disease, biomarker, geography, prior therapy, organ function, age, performance status)",
        "version": "5.0.0",
        "endpoints": ["match"],
        "status": "operational",
    },
    "eligibility_checker": {
        "module": "trials.eligibility_checker",
        "description": "Automated 12-criterion eligibility pre-screening with pass/fail and reason codes",
        "version": "5.0.0",
        "endpoints": ["eligibility"],
        "status": "operational",
    },
    "geo_proximity": {
        "module": "trials.geo_proximity",
        "description": "Haversine geographic distance calculation and trial site proximity ranking",
        "version": "5.0.0",
        "endpoints": ["proximity", "nearby"],
        "status": "operational",
    },
    "outcome_predictor": {
        "module": "trials.outcome_predictor",
        "description": "Historical outcome prediction with 95% CI for response, survival, and toxicity",
        "version": "5.0.0",
        "endpoints": ["outcome", "compare-outcomes"],
        "status": "operational",
    },
    "stratification": {
        "module": "trials.stratification",
        "description": "Disease-specific risk stratification (IPI, R-ISS, NCCN) with CAR-T response prediction",
        "version": "5.1.0",
        "endpoints": ["stratify", "cohort/{cancer_type}", "kaplan-meier/{cancer_type}"],
        "status": "operational",
    },
    "site_network": {
        "module": "trials.site_network",
        "description": "Site feasibility assessment, enrollment funnel modeling, and FDA diversity compliance",
        "version": "5.1.0",
        "endpoints": ["sites/feasibility", "sites/enrollment-forecast", "sites/recruitment-funnel", "sites/diversity"],
        "status": "operational",
    },
    "site_analytics": {
        "module": "trials.site_analytics",
        "description": "Global CAR-T treatment center database (23 centers), Monte Carlo enrollment projection, competitive landscape",
        "version": "5.2.0",
        "endpoints": ["sites/network", "sites/enrollment-projection", "sites/competitive-enrollment"],
        "status": "operational",
    },
    "regulatory": {
        "module": "trials.regulatory",
        "description": "Multi-agency regulatory comparison (FDA/EMA/PMDA/NMPA), IND readiness checklist, BLA timeline, REMS design",
        "version": "5.1.0",
        "endpoints": ["regulatory/comparison", "regulatory/ind-checklist", "regulatory/bla-timeline", "regulatory/rems"],
        "status": "operational",
    },
    "protocol_generator": {
        "module": "trials.protocol_generator",
        "description": "ICH-GCP compliant protocol synopsis generation with BOIN dose escalation, Simon's two-stage design, DLT library, study schedule",
        "version": "5.2.0",
        "endpoints": ["protocol/generate", "protocol/boin-decision", "protocol/sample-size", "protocol/dlt-library"],
        "status": "operational",
    },
    "safety_monitoring": {
        "module": "trials.safety_monitoring",
        "description": "ASTCT CRS/ICANS grading algorithm, ICE score calculator, safety signal detection (PRR), DSMB report generation",
        "version": "5.2.0",
        "endpoints": ["safety/grade-crs", "safety/ice-score", "safety/signals", "safety/dsmb-report", "safety/tocilizumab-protocol"],
        "status": "operational",
    },
    "biomarker_correlator": {
        "module": "trials.biomarker_correlator",
        "description": "Pre-infusion predictive panel (8 biomarkers), PD biomarker tracking, cytokine kinetics simulation, expansion-response correlation",
        "version": "5.2.0",
        "endpoints": ["biomarkers/panel", "biomarkers/cytokine-kinetics", "biomarkers/expansion-correlation", "biomarkers/companion-dx"],
        "status": "operational",
    },
    "patient_journey": {
        "module": "trials.patient_journey",
        "description": "14-stage patient journey simulation (referral → LTFU), screen failure analysis, QoL trajectory, pre-screening checklist",
        "version": "5.2.0",
        "endpoints": ["journey/stages", "journey/simulate", "journey/screen-failures", "journey/pre-screening"],
        "status": "operational",
    },
    "real_world_evidence": {
        "module": "trials.real_world_evidence",
        "description": "Published CAR-T outcomes database (ZUMA-1, JULIET, TRANSCEND, KarMMa, CARTITUDE-1), external control arm generation, propensity score matching, treatment effect estimation (HR, OR, NNT), HTA evidence package",
        "version": "5.2.0",
        "endpoints": ["rwe/historical-outcomes", "rwe/external-control", "rwe/treatment-effect", "rwe/hta-package"],
        "status": "operational",
        "data_sources": [
            "SCHOLAR-1 (Crump et al., Blood 2017)",
            "ZUMA-1 (Neelapu et al., NEJM 2017)",
            "JULIET (Schuster et al., NEJM 2019)",
            "TRANSCEND NHL 001 (Abramson et al., Lancet 2020)",
            "ELIANA (Maude et al., NEJM 2018)",
            "KarMMa (Munshi et al., NEJM 2021)",
            "CARTITUDE-1 (Berdeja et al., Lancet 2021)",
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────
# Package Introspection Utilities
# ──────────────────────────────────────────────────────────────────────

def get_engine_info(engine_name: str) -> dict:
    """Get information about a specific engine.

    Args:
        engine_name: Name of engine (e.g. 'safety_monitoring')

    Returns:
        Engine metadata dict including module path, description,
        version, endpoints, and status. Returns error dict if
        engine not found.
    """
    return ENGINE_REGISTRY.get(engine_name, {"error": f"Engine '{engine_name}' not found"})


def list_engines() -> list:
    """List all registered engines with their status.

    Returns:
        List of dicts with name, description, status, and
        endpoint count for each registered engine.
    """
    return [
        {
            "name": name,
            "description": info["description"],
            "status": info["status"],
            "version": info.get("version", "5.0.0"),
            "endpoints": len(info["endpoints"]),
            "endpoint_list": info["endpoints"],
        }
        for name, info in ENGINE_REGISTRY.items()
    ]


def get_total_endpoints() -> int:
    """Get total number of API endpoints across all engines."""
    return sum(len(info["endpoints"]) for info in ENGINE_REGISTRY.values())


def get_package_summary() -> dict:
    """Get a complete summary of the trials package.

    Returns:
        Dict with total engines, endpoints, version, and
        per-engine breakdown.
    """
    engines = list_engines()
    return {
        "package": "carvanta.trials",
        "version": __version__,
        "total_engines": len(engines),
        "total_endpoints": get_total_endpoints(),
        "all_operational": all(e["status"] == "operational" for e in engines),
        "engines": engines,
        "clinical_standards": {
            "crs_grading": "ASTCT 2019 Consensus (Lee et al.)",
            "icans_grading": "ASTCT 2019 Consensus with ICE Score",
            "risk_models": ["IPI (DLBCL)", "R-ISS (MM)", "NCCN (ALL)", "TNM+Molecular (NSCLC)"],
            "protocol_design": "ICH E6(R2) GCP, FDA CAR-T Guidance (2022)",
            "dose_escalation": "BOIN (FDA-accepted for cell therapy)",
            "statistical_design": "Simon's Optimal Two-Stage Design",
            "response_criteria": ["Lugano 2014 (lymphoma)", "IMWG (myeloma)", "RECIST 1.1 (solid)"],
        },
    }

