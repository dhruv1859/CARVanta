"""
CARVanta Trials — API Router
================================
REST API endpoints for Module 4: Clinical Trial Matcher.
Provides trial search, patient matching, eligibility checking,
proximity analysis, and outcome prediction endpoints.

Security: Rate-limited, input-sanitized, API v5.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.trials_router")

router = APIRouter(prefix="/api/v5/trials", tags=["Clinical Trial Matcher"])


# ──────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────

class TrialSearchRequest(BaseModel):
    query: str = Field("", max_length=500)
    target: Optional[str] = Field(None, max_length=20)
    phase: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=30)
    disease: Optional[str] = Field(None, max_length=50)
    country: Optional[str] = Field(None, max_length=50)
    max_results: int = Field(20, ge=1, le=50)


class PatientProfileRequest(BaseModel):
    patient_id: str = Field("", max_length=32)
    age: int = Field(50, ge=0, le=120)
    gender: str = Field("All", max_length=10)
    ecog_status: int = Field(1, ge=0, le=4)
    cancer_type: str = Field("", max_length=100)
    cancer_subtype: str = Field("", max_length=100)
    prior_therapies: int = Field(0, ge=0, le=20)
    target_antigens_expressed: List[str] = Field(default_factory=list)
    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    latitude: float = Field(0.0)
    longitude: float = Field(0.0)
    willing_to_travel_km: float = Field(500.0, ge=0, le=20000)
    comorbidities: List[str] = Field(default_factory=list)
    organ_function: Dict[str, str] = Field(default_factory=dict)
    prior_car_t: bool = Field(False)


class MatchRequest(BaseModel):
    patient: PatientProfileRequest
    max_results: int = Field(15, ge=1, le=50)
    min_score: float = Field(0.2, ge=0, le=1)
    include_ineligible: bool = Field(False)


class EligibilityRequest(BaseModel):
    patient: PatientProfileRequest
    nct_id: str = Field(..., max_length=20)


class ProximityRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    nct_id: str = Field(..., max_length=20)


class NearbyRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    max_distance_km: float = Field(500, ge=10, le=20000)
    target: Optional[str] = Field(None, max_length=20)
    max_results: int = Field(20, ge=1, le=50)


class OutcomeRequest(BaseModel):
    nct_id: str = Field(..., max_length=20)
    patient: Optional[PatientProfileRequest] = None


# ──────────────────────────────────────────────────────────────────────
# Trial Search Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/search", summary="Search immunotherapy clinical trials")
async def search_trials(request: TrialSearchRequest) -> Dict[str, Any]:
    """Search 500+ indexed immunotherapy clinical trials with multi-field filtering."""
    from trials.clinicaltrials_sync import search_trials as do_search
    return await do_search(
        query=request.query, target=request.target, phase=request.phase,
        status=request.status, disease=request.disease, country=request.country,
        max_results=request.max_results,
    )


@router.get("/detail/{nct_id}", summary="Get trial details by NCT ID")
async def get_trial(nct_id: str) -> Dict[str, Any]:
    """Get comprehensive details for a specific trial."""
    from trials.clinicaltrials_sync import get_trial_by_id
    trial = await get_trial_by_id(nct_id)
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")
    return trial


@router.get("/statistics", summary="Get trial database statistics")
async def trial_statistics() -> Dict[str, Any]:
    """Get aggregate statistics about the trial database."""
    from trials.clinicaltrials_sync import get_trial_statistics
    return await get_trial_statistics()


# ──────────────────────────────────────────────────────────────────────
# Patient Matching Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/match", summary="Match patient to clinical trials")
async def match_patient(request: MatchRequest) -> Dict[str, Any]:
    """AI-powered patient-to-trial matching based on genomic profile, disease, and location."""
    from trials.matcher import match_patient_to_trials, PatientProfile
    patient = PatientProfile(
        patient_id=request.patient.patient_id, age=request.patient.age,
        gender=request.patient.gender, ecog_status=request.patient.ecog_status,
        cancer_type=request.patient.cancer_type, cancer_subtype=request.patient.cancer_subtype,
        prior_therapies=request.patient.prior_therapies,
        target_antigens_expressed=request.patient.target_antigens_expressed,
        biomarkers=request.patient.biomarkers,
        latitude=request.patient.latitude, longitude=request.patient.longitude,
        willing_to_travel_km=request.patient.willing_to_travel_km,
        comorbidities=request.patient.comorbidities,
        organ_function=request.patient.organ_function,
        prior_car_t=request.patient.prior_car_t,
    )
    return await match_patient_to_trials(
        patient, max_results=request.max_results,
        min_score=request.min_score, include_ineligible=request.include_ineligible,
    )


# ──────────────────────────────────────────────────────────────────────
# Eligibility Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/eligibility", summary="Check patient eligibility for a trial")
async def check_eligibility(request: EligibilityRequest) -> Dict[str, Any]:
    """Comprehensive 12-dimension eligibility pre-screening."""
    from trials.eligibility_checker import check_eligibility as do_check
    patient_dict = request.patient.dict()
    return await do_check(patient_dict, request.nct_id)


# ──────────────────────────────────────────────────────────────────────
# Proximity Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/proximity", summary="Analyze trial site proximity")
async def analyze_proximity(request: ProximityRequest) -> Dict[str, Any]:
    """Analyze geographic proximity to all sites of a trial."""
    from trials.geo_proximity import analyze_trial_proximity
    return await analyze_trial_proximity(request.latitude, request.longitude, request.nct_id)


@router.post("/nearby", summary="Find nearest recruiting trials")
async def find_nearby(request: NearbyRequest) -> Dict[str, Any]:
    """Find nearest recruiting trials within a distance radius."""
    from trials.geo_proximity import find_nearest_trials
    return await find_nearest_trials(
        request.latitude, request.longitude,
        max_distance_km=request.max_distance_km,
        target=request.target, max_results=request.max_results,
    )


# ──────────────────────────────────────────────────────────────────────
# Outcome Prediction Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/outcome", summary="Predict trial outcomes")
async def predict_outcome(request: OutcomeRequest) -> Dict[str, Any]:
    """Predict expected outcomes for a trial based on historical data."""
    from trials.outcome_predictor import predict_trial_outcomes
    patient_dict = request.patient.dict() if request.patient else None
    return await predict_trial_outcomes(request.nct_id, patient_dict)


class CompareOutcomesRequest(BaseModel):
    nct_ids: List[str] = Field(..., max_length=5)


@router.post("/compare-outcomes", summary="Compare outcomes across trials")
async def compare_outcomes(request: CompareOutcomesRequest) -> Dict[str, Any]:
    """Compare predicted outcomes across multiple trials."""
    from trials.outcome_predictor import compare_trial_outcomes
    return await compare_trial_outcomes(request.nct_ids)


# ──────────────────────────────────────────────────────────────────────
# Patient Stratification Endpoints
# ──────────────────────────────────────────────────────────────────────

class StratifyRequest(BaseModel):
    cancer_type: str = Field("DLBCL", max_length=30)
    age: int = Field(55, ge=0, le=120)
    stage: str = Field("IV", max_length=10)
    ecog: int = Field(1, ge=0, le=4)
    ldh_elevated: bool = Field(True)
    extranodal_sites: int = Field(1, ge=0, le=10)
    biomarkers: Dict[str, Any] = Field(default_factory=dict)
    prior_therapies: int = Field(2, ge=0, le=20)


@router.post("/stratify", summary="Stratify patient risk")
async def stratify_patient(req: StratifyRequest) -> Dict[str, Any]:
    """Stratify patient into risk group using disease-specific models (IPI, R-ISS, NCCN)."""
    from trials.stratification import stratify_patient as do_stratify
    return await do_stratify(
        cancer_type=req.cancer_type, age=req.age, stage=req.stage,
        ecog=req.ecog, ldh_elevated=req.ldh_elevated,
        extranodal_sites=req.extranodal_sites, biomarkers=req.biomarkers,
        prior_therapies=req.prior_therapies,
    )


@router.get("/cohort/{cancer_type}", summary="Generate synthetic cohort")
async def generate_cohort(cancer_type: str, n_patients: int = Query(100, ge=10, le=500)) -> Dict[str, Any]:
    """Generate a synthetic patient cohort for trial simulation."""
    from trials.stratification import generate_synthetic_cohort
    return await generate_synthetic_cohort(cancer_type=cancer_type, n_patients=n_patients)


@router.get("/kaplan-meier/{cancer_type}", summary="Kaplan-Meier survival estimate")
async def kaplan_meier(
    cancer_type: str,
    treatment: str = Query("CAR-T"),
    n_patients: int = Query(100, ge=20, le=500),
) -> Dict[str, Any]:
    """Generate Kaplan-Meier survival estimates from simulated data."""
    from trials.stratification import kaplan_meier_estimate
    return await kaplan_meier_estimate(cancer_type=cancer_type, treatment=treatment, n_patients=n_patients)


# ──────────────────────────────────────────────────────────────────────
# Site Network Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/sites/feasibility", summary="Site feasibility analysis")
async def site_feasibility(
    target: str = Query("CD19"),
    cancer_type: str = Query("DLBCL"),
    phase: str = Query("Phase 2"),
    enrollment: int = Query(100, ge=10, le=1000),
) -> Dict[str, Any]:
    """Score and rank trial sites by feasibility."""
    from trials.site_network import site_feasibility as do_feasibility
    return await do_feasibility(target_antigen=target, cancer_type=cancer_type, phase=phase, target_enrollment=enrollment)


@router.get("/sites/enrollment-forecast", summary="Monte Carlo enrollment forecast")
async def enrollment_forecast(
    n_sites: int = Query(10, ge=2, le=50),
    target: int = Query(100, ge=10, le=1000),
    months: int = Query(24, ge=6, le=60),
) -> Dict[str, Any]:
    """Monte Carlo simulation of enrollment timelines."""
    from trials.site_network import enrollment_forecast as do_forecast
    return await do_forecast(n_sites=n_sites, target_enrollment=target, months=months)


@router.get("/sites/recruitment-funnel", summary="Patient recruitment funnel")
async def recruitment_funnel(screening: int = Query(200, ge=50, le=1000)) -> Dict[str, Any]:
    """Model screen-to-complete patient funnel with stage-by-stage attrition."""
    from trials.site_network import recruitment_funnel as do_funnel
    return await do_funnel(screening_target=screening)


@router.get("/sites/diversity", summary="Diversity compliance check")
async def diversity_compliance(n_patients: int = Query(100, ge=20, le=500)) -> Dict[str, Any]:
    """Check FDA diversity and inclusion plan compliance."""
    from trials.site_network import diversity_compliance as do_diversity
    return await do_diversity(n_patients=n_patients)


# ──────────────────────────────────────────────────────────────────────
# Regulatory Intelligence Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/regulatory/comparison", summary="Compare regulatory pathways")
async def regulatory_comparison() -> Dict[str, Any]:
    """Compare FDA, EMA, PMDA, NMPA regulatory pathways."""
    from trials.regulatory import regulatory_comparison as do_comparison
    return await do_comparison()


@router.get("/regulatory/ind-checklist", summary="IND readiness checklist")
async def ind_checklist(
    target: str = Query("CD19"),
    indication: str = Query("DLBCL"),
) -> Dict[str, Any]:
    """Generate IND application readiness checklist."""
    from trials.regulatory import ind_checklist as do_checklist
    return await do_checklist(target=target, indication=indication)


@router.get("/regulatory/bla-timeline", summary="BLA timeline estimate")
async def bla_timeline(
    target: str = Query("CD19"),
    designation: str = Query("RMAT"),
) -> Dict[str, Any]:
    """Estimate BLA submission and approval timeline."""
    from trials.regulatory import bla_timeline as do_timeline
    return await do_timeline(target=target, designation=designation)


@router.get("/regulatory/rems", summary="REMS program design")
async def rems_design(target: str = Query("CD19")) -> Dict[str, Any]:
    """Design a Risk Evaluation and Mitigation Strategy (REMS) program."""
    from trials.regulatory import rems_design as do_rems
    return await do_rems(target=target)


# ──────────────────────────────────────────────────────────────────────
# Protocol Generator Endpoints
# ──────────────────────────────────────────────────────────────────────

class ProtocolRequest(BaseModel):
    indication: str = Field("DLBCL", max_length=50)
    target: str = Field("CD19", max_length=20)
    phase: str = Field("Phase 1/2", max_length=20)
    car_generation: str = Field("2nd", max_length=10)
    costimulation: str = Field("4-1BB", max_length=20)


@router.post("/protocol/generate", summary="Generate clinical trial protocol")
async def generate_protocol(req: ProtocolRequest) -> Dict[str, Any]:
    """Generate a complete ICH-GCP compliant trial protocol synopsis."""
    from trials.protocol_generator import generate_full_protocol, ProtocolConfig
    config = ProtocolConfig(
        indication=req.indication, target=req.target, phase=req.phase,
        car_generation=req.car_generation, costimulation=req.costimulation,
    )
    return await generate_full_protocol(config)


@router.get("/protocol/boin-decision", summary="BOIN dose escalation decision")
async def boin_decision(
    n_treated: int = Query(..., ge=1, le=100),
    n_dlt: int = Query(..., ge=0, le=100),
    target_dlt_rate: float = Query(0.25, ge=0.1, le=0.5),
) -> Dict[str, Any]:
    """Compute BOIN escalation/de-escalation decision from observed DLT data."""
    from trials.protocol_generator import compute_boin_decision
    return await compute_boin_decision(n_treated=n_treated, n_dlt=n_dlt, target_dlt_rate=target_dlt_rate)


@router.get("/protocol/sample-size", summary="Sample size calculator")
async def sample_size(
    design: str = Query("simon_two_stage"),
    p0: float = Query(0.25, ge=0.01, le=0.99),
    p1: float = Query(0.50, ge=0.02, le=0.99),
    alpha: float = Query(0.05, ge=0.001, le=0.2),
    power: float = Query(0.90, ge=0.5, le=0.99),
) -> Dict[str, Any]:
    """Calculate sample size for various clinical trial designs."""
    from trials.protocol_generator import sample_size_calculator
    return await sample_size_calculator(design=design, p0=p0, p1=p1, alpha=alpha, power=power)


@router.get("/protocol/dlt-library", summary="DLT definition library")
async def dlt_library() -> Dict[str, Any]:
    """Get CAR-T-specific DLT definitions and management guidelines."""
    from trials.protocol_generator import _DLT_LIBRARY
    return {"total": len(_DLT_LIBRARY), "definitions": _DLT_LIBRARY}


# ──────────────────────────────────────────────────────────────────────
# Site Analytics Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/sites/network", summary="Global CAR-T site network")
async def site_network(region: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Get the global CAR-T treatment center network."""
    from trials.site_analytics import get_site_network
    return await get_site_network(region=region)


@router.get("/sites/enrollment-projection", summary="Enrollment timeline projection")
async def enrollment_projection(
    indication: str = Query("DLBCL"),
    target_enrollment: int = Query(100, ge=10, le=500),
    n_sites: int = Query(15, ge=2, le=50),
    n_months: int = Query(24, ge=6, le=60),
) -> Dict[str, Any]:
    """Monte Carlo-based enrollment timeline projection."""
    from trials.site_analytics import enrollment_projection
    return await enrollment_projection(
        target_enrollment=target_enrollment, n_sites=n_sites,
        indication=indication, n_months=n_months,
    )


@router.get("/sites/competitive-enrollment", summary="Competitive enrollment landscape")
async def competitive_enrollment(indication: str = Query("DLBCL")) -> Dict[str, Any]:
    """Analyze competing trial enrollment landscape."""
    from trials.site_analytics import competitive_enrollment
    return await competitive_enrollment(indication=indication)


# ──────────────────────────────────────────────────────────────────────
# Safety Monitoring Endpoints
# ──────────────────────────────────────────────────────────────────────

class CRSGradingRequest(BaseModel):
    temperature: float = Field(39.0, ge=35, le=43)
    systolic_bp: Optional[float] = Field(None, ge=40, le=250)
    on_vasopressor: bool = Field(False)
    n_vasopressors: int = Field(0, ge=0, le=5)
    spo2: float = Field(95.0, ge=50, le=100)
    o2_device: str = Field("none", max_length=30)
    on_mechanical_vent: bool = Field(False)


@router.post("/safety/grade-crs", summary="Grade CRS severity")
async def grade_crs(req: CRSGradingRequest) -> Dict[str, Any]:
    """Grade Cytokine Release Syndrome using ASTCT 2019 criteria."""
    from trials.safety_monitoring import grade_crs as do_grade
    return await do_grade(
        temperature=req.temperature, systolic_bp=req.systolic_bp,
        on_vasopressor=req.on_vasopressor, n_vasopressors=req.n_vasopressors,
        spo2=req.spo2, o2_device=req.o2_device, on_mechanical_vent=req.on_mechanical_vent,
    )


class ICEScoreRequest(BaseModel):
    orientation_year: bool = Field(True)
    orientation_month: bool = Field(True)
    orientation_city: bool = Field(True)
    orientation_hospital: bool = Field(True)
    naming_3_objects: int = Field(3, ge=0, le=3)
    follows_commands: bool = Field(True)
    can_write: bool = Field(True)
    attention_counting: bool = Field(True)


@router.post("/safety/ice-score", summary="Calculate ICE score & grade ICANS")
async def ice_score(req: ICEScoreRequest) -> Dict[str, Any]:
    """Calculate Immune Effector Cell-Associated Encephalopathy score."""
    from trials.safety_monitoring import calculate_ice_score
    return await calculate_ice_score(
        orientation_year=req.orientation_year, orientation_month=req.orientation_month,
        orientation_city=req.orientation_city, orientation_hospital=req.orientation_hospital,
        naming_3_objects=req.naming_3_objects, follows_commands=req.follows_commands,
        can_write=req.can_write, attention_counting=req.attention_counting,
    )


@router.get("/safety/signals", summary="Safety signal detection")
async def safety_signals(n_patients: int = Query(50, ge=10, le=500)) -> Dict[str, Any]:
    """Detect safety signals using disproportionality analysis (PRR)."""
    from trials.safety_monitoring import safety_signal_detection
    return await safety_signal_detection(n_patients=n_patients)


@router.get("/safety/dsmb-report", summary="DSMB safety report")
async def dsmb_report(n_patients: int = Query(50, ge=10, le=500)) -> Dict[str, Any]:
    """Generate Data Safety Monitoring Board summary report."""
    from trials.safety_monitoring import generate_dsmb_report
    return await generate_dsmb_report(n_patients=n_patients)


@router.get("/safety/tocilizumab-protocol", summary="Tocilizumab protocol")
async def tocilizumab_protocol() -> Dict[str, Any]:
    """Get tocilizumab administration protocol for CRS management."""
    from trials.safety_monitoring import tocilizumab_protocol as do_protocol
    return await do_protocol()


# ──────────────────────────────────────────────────────────────────────
# Biomarker Correlator Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/biomarkers/panel", summary="Biomarker panel specs")
async def biomarker_panel(panel_type: str = Query("pre_infusion")) -> Dict[str, Any]:
    """Get pre-infusion or pharmacodynamic biomarker panel specifications."""
    from trials.biomarker_correlator import biomarker_panel as do_panel
    return await do_panel(panel_type=panel_type)


@router.get("/biomarkers/cytokine-kinetics", summary="Cytokine kinetics simulation")
async def cytokine_kinetics(crs_grade: int = Query(2, ge=0, le=4), n_days: int = Query(28, ge=7, le=60)) -> Dict[str, Any]:
    """Simulate cytokine kinetics based on CRS grade."""
    from trials.biomarker_correlator import simulate_cytokine_kinetics
    return await simulate_cytokine_kinetics(crs_grade=crs_grade, n_days=n_days)


@router.get("/biomarkers/expansion-correlation", summary="CAR-T expansion correlation")
async def expansion_correlation(n_patients: int = Query(80, ge=20, le=300)) -> Dict[str, Any]:
    """Correlate CAR-T cell expansion with clinical response."""
    from trials.biomarker_correlator import car_t_expansion_correlation
    return await car_t_expansion_correlation(n_patients=n_patients)


@router.get("/biomarkers/companion-dx", summary="Companion diagnostic design")
async def companion_dx(target: str = Query("CD19"), indication: str = Query("DLBCL")) -> Dict[str, Any]:
    """Design companion diagnostic test panel."""
    from trials.biomarker_correlator import companion_diagnostic_design
    return await companion_diagnostic_design(target=target, indication=indication)


# ──────────────────────────────────────────────────────────────────────
# Patient Journey Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/journey/stages", summary="Patient journey stages")
async def journey_stages() -> Dict[str, Any]:
    """Get all patient journey stages with descriptions."""
    from trials.patient_journey import get_journey_stages
    return await get_journey_stages()


@router.get("/journey/simulate", summary="Simulate patient journey")
async def journey_simulate(
    cancer_type: str = Query("DLBCL"), target: str = Query("CD19"),
) -> Dict[str, Any]:
    """Simulate a patient's journey through a CAR-T trial."""
    from trials.patient_journey import simulate_patient_journey
    return await simulate_patient_journey(cancer_type=cancer_type, target=target)


@router.get("/journey/screen-failures", summary="Screen failure analysis")
async def screen_failures(n_patients: int = Query(200, ge=50, le=1000)) -> Dict[str, Any]:
    """Analyze screen failure rates and root causes."""
    from trials.patient_journey import screen_failure_analysis
    return await screen_failure_analysis(n_patients=n_patients)


@router.get("/journey/pre-screening", summary="Pre-screening checklist")
async def pre_screening(cancer_type: str = Query("DLBCL"), target: str = Query("CD19")) -> Dict[str, Any]:
    """Generate pre-screening eligibility checklist."""
    from trials.patient_journey import pre_screening_checklist
    return await pre_screening_checklist(cancer_type=cancer_type, target=target)


# ──────────────────────────────────────────────────────────────────────
# Real-World Evidence Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/rwe/historical-outcomes", summary="Historical CAR-T outcomes")
async def historical_outcomes(indication: str = Query("DLBCL")) -> Dict[str, Any]:
    """Get published historical outcomes for comparison (ZUMA-1, JULIET, KarMMa, etc.)."""
    from trials.real_world_evidence import get_historical_outcomes
    return await get_historical_outcomes(indication=indication)


@router.get("/rwe/external-control", summary="Generate external control arm")
async def external_control(
    indication: str = Query("DLBCL"),
    comparator: str = Query("standard_of_care"),
    n_patients: int = Query(100, ge=20, le=500),
) -> Dict[str, Any]:
    """Generate synthetic external control arm from published data."""
    from trials.real_world_evidence import generate_external_control_arm
    return await generate_external_control_arm(indication=indication, comparator=comparator, n_patients=n_patients)


@router.get("/rwe/treatment-effect", summary="Treatment effect estimation")
async def treatment_effect(
    indication: str = Query("DLBCL"),
    experimental: str = Query("axi_cel"),
    comparator: str = Query("standard_of_care"),
) -> Dict[str, Any]:
    """Estimate treatment effect (HR, OR, NNT) between arms."""
    from trials.real_world_evidence import treatment_effect_estimation
    return await treatment_effect_estimation(indication=indication, experimental=experimental, comparator=comparator)


@router.get("/rwe/hta-package", summary="HTA evidence package")
async def hta_package(
    indication: str = Query("DLBCL"),
    target: str = Query("CD19"),
    price: int = Query(373000, ge=50000, le=1000000),
) -> Dict[str, Any]:
    """Generate health technology assessment evidence package (ICER/NICE/ASCO)."""
    from trials.real_world_evidence import hta_evidence_package
    return await hta_evidence_package(indication=indication, target=target, list_price_usd=price)


# ──────────────────────────────────────────────────────────────────────
# Module Status
# ──────────────────────────────────────────────────────────────────────

@router.get("/status", summary="Trial Matcher module status")
async def module_status() -> Dict[str, Any]:
    """Health check and capability listing."""
    return {
        "module": "Clinical Trial Matcher",
        "status": "operational",
        "engines": {
            "trial_search": "operational",
            "patient_matcher": "operational",
            "eligibility_checker": "operational",
            "geo_proximity": "operational",
            "outcome_predictor": "operational",
            "stratification": "operational",
            "site_network": "operational",
            "site_analytics": "operational",
            "regulatory_intelligence": "operational",
            "protocol_generator": "operational",
            "safety_monitoring": "operational",
            "biomarker_correlator": "operational",
            "patient_journey": "operational",
            "real_world_evidence": "operational",
        },
        "total_engines": 14,
        "total_endpoints": 47,
        "trial_database_size": "500+ indexed trials",
        "api_prefix": "/api/v5/trials",
    }

