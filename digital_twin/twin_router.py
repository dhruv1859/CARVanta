"""
CARVanta – Digital Twin API Router v5
==========================================
Complete API layer for the Patient Digital Twin module.
Exposes endpoints for all 10 engines:
  1. Immune Simulation
  2. CRS Risk Assessment
  3. Cancer-Specific Profiles
  4. PK/PD Engine
  5. Treatment Protocols / Products
  6. Biomarker Predictor
  7. Treatment Optimizer
  8. Genomic Profiler
  9. Adverse Event Model
  10. Patient Outcomes & Population Simulator
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

# ─── Core engines ───────────────────────────────────────────────────────────────
from digital_twin.immune_sim import (
    simulate_immune_dynamics,
    compare_targets,
    predict_crs_risk,
)
from digital_twin.tumor_models import (
    simulate_with_cancer_profile,
    get_cancer_profiles_summary,
)
from digital_twin.pk_pd_engine import (
    simulate_car_t_pk,
    get_lymphodepletion_options,
)
from digital_twin.treatment_protocols import (
    predict_outcome_for_product,
    compare_products as compare_products_protocol,
    get_products_for_cancer,
    get_all_products_summary,
)
from digital_twin.biomarker_predictor import (
    generate_complete_biomarker_report,
)

# ─── New engines ────────────────────────────────────────────────────────────────
from digital_twin.treatment_optimizer import (
    optimize_treatment,
    compare_treatments,
    get_all_products_detail,
    PatientProfile,
)
from digital_twin.genomic_profiler import (
    generate_genomic_profile,
    analyze_resistance_mechanisms,
    predict_mrd_trajectory,
)
from digital_twin.adverse_event_model import (
    predict_adverse_events,
    simulate_crs_kinetics,
    predict_cytopenia_recovery,
)
from digital_twin.patient_outcomes import (
    simulate_cohort_outcomes,
    analyze_individual_outcome,
    compare_to_benchmark,
    TRIAL_BENCHMARKS,
)
from digital_twin.population_simulator import (
    run_population_simulation,
    run_sensitivity_analysis,
    compare_products as compare_products_population,
)
from digital_twin.report_generator import (
    generate_patient_report,
    render_report_html,
)
from digital_twin.realworld_evidence import (
    generate_registry_data,
    compare_rwe_vs_trial,
    post_market_surveillance,
    health_technology_assessment,
)


router = APIRouter(prefix="/api/v5/twin", tags=["Digital Twin"])


# ═══════════════════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════════════════

class SimulationRequest(BaseModel):
    patient_age: int = 55
    patient_weight: float = 70.0
    cancer_type: str = "B-cell Lymphoma"
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    t_cell_dose: float = 1e8
    antigen_expression: float = 0.7
    prior_car_t: bool = False
    lymphodepletion: bool = True
    alc: Optional[float] = None
    ldh: Optional[float] = None
    days: int = 365


class TargetComparison(BaseModel):
    name: str
    expression: float = 0.7


class CompareRequest(BaseModel):
    targets: List[TargetComparison]
    patient_age: int = 55
    patient_weight: float = 70.0
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    prior_car_t: bool = False
    lymphodepletion: bool = True
    alc: Optional[float] = None
    ldh: Optional[float] = None
    days: int = 365


class CRSRiskRequest(BaseModel):
    tumor_burden: float = 50.0
    cancer_stage: str = "III"
    ldh: Optional[float] = None
    il6_baseline: Optional[float] = None
    crp_baseline: Optional[float] = None
    ferritin_baseline: Optional[float] = None
    prior_car_t: bool = False
    patient_age: int = 55


class CancerSimRequest(BaseModel):
    cancer_type: str = "DLBCL"
    days: int = 365
    tumor_burden_mm: float = 50.0
    patient_age: int = 55
    antigen_target: Optional[str] = None
    prior_lines: int = 2
    ecog_status: int = 1


class ProductRequest(BaseModel):
    product_key: str = "axi-cel"
    patient_age: int = 55
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    prior_lines: int = 3
    ecog: int = 1
    ldh: Optional[float] = None
    crp: Optional[float] = None
    bridging_therapy: bool = False


class BiomarkerRequest(BaseModel):
    days: int = 90
    cancer_type: str = "DLBCL"
    car_t_target: str = "CD19"
    crs_severity: float = 0.5
    patient_age: int = 55


class PKRequest(BaseModel):
    days: int = 60
    infusion_dose: float = 1e8
    patient_weight: float = 70.0
    tumor_burden_ml: float = 50.0
    cancer_category: str = "hematologic"
    lymphodepletion: bool = True


# ─── New request models ────────────────────────────────────────────────────────

class TreatmentOptimizerRequest(BaseModel):
    age: int = 55
    weight_kg: float = 70.0
    cancer_type: str = "DLBCL"
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    prior_lines: int = 2
    prior_car_t: bool = False
    ecog_status: int = 1
    comorbidities: List[str] = Field(default_factory=list)
    ldh: Optional[float] = None
    crp: Optional[float] = None
    ferritin: Optional[float] = None
    alc: Optional[float] = None
    platelet_count: Optional[float] = None
    tp53_mutated: bool = False
    myc_rearranged: bool = False
    double_hit: bool = False


class GenomicProfileRequest(BaseModel):
    cancer_type: str = "DLBCL"
    patient_age: int = 55
    seed: Optional[int] = None


class ResistanceAnalysisRequest(BaseModel):
    cancer_type: str = "DLBCL"
    target_antigen: str = "CD19"
    mutations: Optional[List[dict]] = None


class MRDRequest(BaseModel):
    days: int = 180
    cancer_type: str = "DLBCL"
    initial_burden: float = 50.0
    treatment_response: str = "CR"
    genomic_risk: str = "standard"
    seed: Optional[int] = None


class AdverseEventRequest(BaseModel):
    patient_age: int = 55
    cancer_type: str = "DLBCL"
    tumor_burden_mm: float = 50.0
    car_t_product: str = "axi-cel"
    dose_cells: float = 1e8
    prior_car_t: bool = False
    ecog: int = 1
    ldh: Optional[float] = None
    crp: Optional[float] = None
    ferritin: Optional[float] = None
    il6: Optional[float] = None
    alc: Optional[float] = None
    platelets: Optional[float] = None
    comorbidities: Optional[List[str]] = None


class CRSKineticsRequest(BaseModel):
    patient_age: int = 55
    tumor_burden_mm: float = 50.0
    costimulatory: str = "CD28"
    days: int = 30
    seed: Optional[int] = None


class CytopeniaRecoveryRequest(BaseModel):
    patient_age: int = 55
    baseline_anc: float = 4.0
    baseline_platelets: float = 200.0
    baseline_hgb: float = 12.0
    lymphodepletion: str = "flu_cy"
    crs_severity: float = 0.5
    days: int = 120
    seed: Optional[int] = None


class CohortOutcomeRequest(BaseModel):
    n_patients: int = Field(default=50, ge=10, le=500)
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    follow_up_months: int = 24
    seed: Optional[int] = None


class IndividualOutcomeRequest(BaseModel):
    patient_age: int = 55
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    tumor_burden_mm: float = 50.0
    prior_lines: int = 3
    seed: Optional[int] = None


class BenchmarkCompareRequest(BaseModel):
    product: str = "axi-cel"
    cancer_type: str = "DLBCL"
    observed_orr: float = 75.0
    observed_cr: float = 50.0
    observed_g3_crs: float = 10.0
    cohort_size: int = 50


class PopulationSimRequest(BaseModel):
    n_patients: int = Field(default=500, ge=50, le=5000)
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    follow_up_months: int = 24
    seed: Optional[int] = None


class SensitivityRequest(BaseModel):
    parameter: str = "tumor_burden"
    values: Optional[List[float]] = None
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    n_simulations: int = Field(default=200, ge=50, le=1000)
    seed: Optional[int] = None


class ProductComparePopRequest(BaseModel):
    cancer_type: str = "DLBCL"
    products: Optional[List[str]] = None
    n_simulations: int = Field(default=300, ge=50, le=1000)
    seed: Optional[int] = None


class TreatmentCompareRequest(BaseModel):
    product_keys: List[str] = Field(default=["axi-cel", "liso-cel"])
    age: int = 55
    cancer_type: str = "DLBCL"
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50.0
    prior_lines: int = 3


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Core Simulation Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/simulate")
def run_simulation(req: SimulationRequest):
    """Run a full CAR-T treatment simulation for a patient."""
    result = simulate_immune_dynamics(
        days=req.days, tumor_burden=req.tumor_burden_mm,
        t_cell_dose=req.t_cell_dose, cancer_stage=req.cancer_stage,
        prior_car_t=req.prior_car_t, lymphodepletion=req.lymphodepletion,
        antigen_expression=req.antigen_expression,
        patient_age=req.patient_age, patient_weight=req.patient_weight,
        alc=req.alc, ldh=req.ldh, noise_seed=42,
    )

    timeline = result["timeline"]
    total_days = len(timeline["days"])
    step = max(1, total_days // 120)
    sampled = {k: [v[i] for i in range(0, total_days, step)] for k, v in timeline.items()}

    response = {"timeline": sampled, "summary": result["summary"], "parameters": result["parameters"]}

    # ── LLM Insight ──
    try:
        from features.llm_insight import generate_digital_twin_insight, is_llm_available
        if is_llm_available():
            patient_data = {
                "age": req.patient_age, "weight": req.patient_weight,
                "cancer_type": req.cancer_type, "ecog": "N/A",
                "prior_lines": "N/A", "target_antigen": "N/A",
            }
            sim_data = result.get("summary", {})
            insight = generate_digital_twin_insight(patient_data, sim_data)
            if insight:
                response["ai_insight"] = insight
                response["ai_insight_source"] = "llm"
    except Exception as e:
        print(f"[CARVanta] Twin LLM insight error: {e}")

    return response


@router.post("/compare")
def compare_treatment_targets(req: CompareRequest):
    """Compare treatment outcomes across multiple antigen targets."""
    targets = [{"name": t.name, "expression": t.expression} for t in req.targets]
    patient_params = {
        "tumor_burden": req.tumor_burden_mm, "cancer_stage": req.cancer_stage,
        "prior_car_t": req.prior_car_t, "lymphodepletion": req.lymphodepletion,
        "patient_age": req.patient_age, "patient_weight": req.patient_weight,
        "alc": req.alc, "ldh": req.ldh,
    }
    return compare_targets(targets, patient_params, days=req.days)


@router.post("/crs-risk")
def crs_risk_assessment(req: CRSRiskRequest):
    """Predict CRS risk for a patient."""
    return predict_crs_risk(
        tumor_burden=req.tumor_burden, cancer_stage=req.cancer_stage,
        ldh=req.ldh, il6_baseline=req.il6_baseline,
        crp_baseline=req.crp_baseline, ferritin_baseline=req.ferritin_baseline,
        prior_car_t=req.prior_car_t, patient_age=req.patient_age,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Cancer-Specific Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/simulate-cancer")
def simulate_cancer_specific(req: CancerSimRequest):
    """Simulate using cancer-specific tumor models."""
    return simulate_with_cancer_profile(
        cancer_type=req.cancer_type, days=req.days,
        tumor_burden_mm=req.tumor_burden_mm, patient_age=req.patient_age,
        antigen_target=req.antigen_target, prior_lines=req.prior_lines,
        ecog_status=req.ecog_status,
    )


@router.get("/cancer-profiles")
def list_cancer_profiles():
    """List all available cancer profiles."""
    return get_cancer_profiles_summary()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PK/PD Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/pk-simulation")
def run_pk_simulation(req: PKRequest):
    """Simulate CAR-T cell pharmacokinetics."""
    return simulate_car_t_pk(
        days=req.days, infusion_dose=req.infusion_dose,
        patient_weight=req.patient_weight, tumor_burden_ml=req.tumor_burden_ml,
        cancer_category=req.cancer_category, lymphodepletion=req.lymphodepletion,
    )


@router.get("/lymphodepletion-options")
def list_lymphodepletion_options():
    """List available lymphodepletion regimens."""
    return get_lymphodepletion_options()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CAR-T Product Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/predict-product-outcome")
def predict_product(req: ProductRequest):
    """Predict personalized outcome for a specific CAR-T product."""
    return predict_outcome_for_product(
        product_key=req.product_key, patient_age=req.patient_age,
        cancer_stage=req.cancer_stage, tumor_burden_mm=req.tumor_burden_mm,
        prior_lines=req.prior_lines, ecog=req.ecog,
        ldh=req.ldh, crp=req.crp, bridging_therapy=req.bridging_therapy,
    )


@router.get("/products")
def list_products():
    """List all CAR-T products."""
    return get_all_products_summary()


@router.get("/products/{cancer_type}")
def products_for_cancer(cancer_type: str):
    """List CAR-T products for a specific cancer type."""
    return get_products_for_cancer(cancer_type)


@router.get("/products-detailed")
def list_products_detailed():
    """List all CAR-T products with complete clinical data."""
    return get_all_products_detail()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Biomarker Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/biomarkers")
def predict_biomarker_trajectory(req: BiomarkerRequest):
    """Generate comprehensive biomarker trajectory predictions."""
    return generate_complete_biomarker_report(
        days=req.days, cancer_type=req.cancer_type,
        car_t_target=req.car_t_target, crs_severity=req.crs_severity,
        patient_age=req.patient_age,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Treatment Optimizer Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/optimize-treatment")
def optimize_treatment_endpoint(req: TreatmentOptimizerRequest):
    """Generate AI-optimized treatment recommendation for a patient."""
    profile = PatientProfile(
        age=req.age, weight_kg=req.weight_kg,
        cancer_type=req.cancer_type, cancer_stage=req.cancer_stage,
        tumor_burden_mm=req.tumor_burden_mm, prior_lines=req.prior_lines,
        prior_car_t=req.prior_car_t, ecog_status=req.ecog_status,
        comorbidities=req.comorbidities, ldh=req.ldh, crp=req.crp,
        ferritin=req.ferritin, alc=req.alc, platelet_count=req.platelet_count,
        tp53_mutated=req.tp53_mutated, myc_rearranged=req.myc_rearranged,
        double_hit=req.double_hit,
    )
    return optimize_treatment(profile)


@router.post("/compare-treatments")
def compare_treatments_endpoint(req: TreatmentCompareRequest):
    """Head-to-head comparison of CAR-T products for a patient."""
    profile = PatientProfile(
        age=req.age, cancer_type=req.cancer_type,
        cancer_stage=req.cancer_stage, tumor_burden_mm=req.tumor_burden_mm,
        prior_lines=req.prior_lines,
    )
    return compare_treatments(profile, req.product_keys)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Genomic Profiler Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/genomic-profile")
def generate_genomic_profile_endpoint(req: GenomicProfileRequest):
    """Generate a comprehensive genomic profile for treatment planning."""
    result = generate_genomic_profile(
        cancer_type=req.cancer_type,
        patient_age=req.patient_age,
        seed=req.seed,
    )
    try:
        from features.llm_insight import generate_genomic_insight, is_llm_available
        if is_llm_available():
            insight = generate_genomic_insight(result)
            if insight:
                result["ai_insight"] = insight
                result["ai_insight_source"] = "llm"
    except Exception as e:
        print(f"[CARVanta] Genomic LLM insight error: {e}")
    return result


@router.post("/resistance-analysis")
def analyze_resistance_endpoint(req: ResistanceAnalysisRequest):
    """Analyze CAR-T resistance mechanisms based on genomic data."""
    return analyze_resistance_mechanisms(
        cancer_type=req.cancer_type,
        target_antigen=req.target_antigen,
        mutations=req.mutations,
    )


@router.post("/mrd-trajectory")
def predict_mrd_endpoint(req: MRDRequest):
    """Predict minimal residual disease trajectory post-CAR-T."""
    return predict_mrd_trajectory(
        days=req.days, cancer_type=req.cancer_type,
        initial_burden=req.initial_burden,
        treatment_response=req.treatment_response,
        genomic_risk=req.genomic_risk, seed=req.seed,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Adverse Event Model Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/predict-adverse-events")
def predict_ae_endpoint(req: AdverseEventRequest):
    """Predict comprehensive adverse event profile for a CAR-T treatment."""
    result = predict_adverse_events(
        patient_age=req.patient_age, cancer_type=req.cancer_type,
        tumor_burden_mm=req.tumor_burden_mm, car_t_product=req.car_t_product,
        dose_cells=req.dose_cells, prior_car_t=req.prior_car_t,
        ecog=req.ecog, ldh=req.ldh, crp=req.crp, ferritin=req.ferritin,
        il6=req.il6, alc=req.alc, platelets=req.platelets,
        comorbidities=req.comorbidities,
    )
    try:
        from features.llm_insight import generate_adverse_event_insight, is_llm_available
        if is_llm_available():
            ae_data = {"product": req.car_t_product, "target": "N/A",
                       "total_patients": "simulated", "events": result.get("events", []),
                       "crs_severe_rate": result.get("crs_severe_pct", 0),
                       "icans_severe_rate": result.get("icans_severe_pct", 0)}
            insight = generate_adverse_event_insight(ae_data)
            if insight:
                result["ai_insight"] = insight
                result["ai_insight_source"] = "llm"
    except Exception as e:
        print(f"[CARVanta] AE LLM insight error: {e}")
    return result


@router.post("/crs-kinetics")
def simulate_crs_kinetics_endpoint(req: CRSKineticsRequest):
    """Simulate CRS cytokine kinetics (IL-6, IFN-γ, TNF-α, temperature)."""
    return simulate_crs_kinetics(
        patient_age=req.patient_age,
        tumor_burden_mm=req.tumor_burden_mm,
        costimulatory=req.costimulatory,
        days=req.days, seed=req.seed,
    )


@router.post("/cytopenia-recovery")
def predict_cytopenia_endpoint(req: CytopeniaRecoveryRequest):
    """Model hematologic recovery trajectory post-CAR-T."""
    return predict_cytopenia_recovery(
        patient_age=req.patient_age,
        baseline_anc=req.baseline_anc,
        baseline_platelets=req.baseline_platelets,
        baseline_hgb=req.baseline_hgb,
        lymphodepletion=req.lymphodepletion,
        crs_severity=req.crs_severity,
        days=req.days, seed=req.seed,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Patient Outcomes Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/simulate-cohort")
def simulate_cohort_endpoint(req: CohortOutcomeRequest):
    """Simulate a cohort of patient outcomes with KM curves."""
    return simulate_cohort_outcomes(
        n_patients=req.n_patients, cancer_type=req.cancer_type,
        product=req.product, follow_up_months=req.follow_up_months,
        seed=req.seed,
    )


@router.post("/individual-outcome")
def individual_outcome_endpoint(req: IndividualOutcomeRequest):
    """Simulate detailed individual patient outcome."""
    return analyze_individual_outcome(
        patient_age=req.patient_age, cancer_type=req.cancer_type,
        product=req.product, tumor_burden_mm=req.tumor_burden_mm,
        prior_lines=req.prior_lines, seed=req.seed,
    )


@router.post("/benchmark-compare")
def benchmark_compare_endpoint(req: BenchmarkCompareRequest):
    """Compare observed outcomes to clinical trial benchmarks."""
    return compare_to_benchmark(
        product=req.product, cancer_type=req.cancer_type,
        observed_orr=req.observed_orr, observed_cr=req.observed_cr,
        observed_g3_crs=req.observed_g3_crs, cohort_size=req.cohort_size,
    )


@router.get("/trial-benchmarks")
def list_trial_benchmarks():
    """List all available clinical trial benchmarks."""
    return TRIAL_BENCHMARKS


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Population Simulator Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/population-simulation")
def population_simulation_endpoint(req: PopulationSimRequest):
    """Run Monte Carlo population-level simulation."""
    return run_population_simulation(
        n_patients=req.n_patients, cancer_type=req.cancer_type,
        product=req.product, follow_up_months=req.follow_up_months,
        seed=req.seed,
    )


@router.post("/sensitivity-analysis")
def sensitivity_analysis_endpoint(req: SensitivityRequest):
    """Run sensitivity analysis by varying a parameter."""
    return run_sensitivity_analysis(
        parameter=req.parameter, values=req.values,
        cancer_type=req.cancer_type, product=req.product,
        n_simulations=req.n_simulations, seed=req.seed,
    )


@router.post("/compare-products-population")
def compare_products_population_endpoint(req: ProductComparePopRequest):
    """Population-level head-to-head comparison of CAR-T products."""
    return compare_products_population(
        cancer_type=req.cancer_type, products=req.products,
        n_simulations=req.n_simulations, seed=req.seed,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Report Generator Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class ReportRequest(BaseModel):
    patient_age: int = 55
    sex: str = "M"
    cancer_type: str = "DLBCL"
    cancer_stage: str = "III"
    tumor_burden_mm: float = 50
    ecog: int = 1
    product: str = "axi-cel"
    prior_lines: int = 3
    ldh: Optional[float] = None
    ferritin: Optional[float] = None
    tp53_mutated: bool = False
    double_hit: bool = False
    format: str = "json"  # "json" or "html"
    seed: Optional[int] = None


@router.post("/generate-report")
def generate_report_endpoint(req: ReportRequest):
    """Generate a comprehensive clinical simulation report."""
    report = generate_patient_report(
        patient_age=req.patient_age, sex=req.sex,
        cancer_type=req.cancer_type, cancer_stage=req.cancer_stage,
        tumor_burden_mm=req.tumor_burden_mm, ecog=req.ecog,
        product=req.product, prior_lines=req.prior_lines,
        ldh=req.ldh, ferritin=req.ferritin,
        tp53_mutated=req.tp53_mutated, double_hit=req.double_hit,
        seed=req.seed,
    )
    if req.format == "html":
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=render_report_html(report))
    return report


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Real-World Evidence Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

class RegistryRequest(BaseModel):
    n_patients: int = 200
    cancer_type: str = "DLBCL"
    product: str = "axi-cel"
    time_period_months: int = 24
    seed: Optional[int] = None

class RWECompareRequest(BaseModel):
    product: str = "axi-cel"
    cancer_type: str = "DLBCL"
    rwe_n: int = 200
    seed: Optional[int] = None

class SurveillanceRequest(BaseModel):
    product: str = "axi-cel"
    n_patients: int = 500
    monitoring_months: int = 36
    seed: Optional[int] = None

class HTARequest(BaseModel):
    product: str = "axi-cel"
    cancer_type: str = "DLBCL"
    comparator: str = "salvage_chemotherapy"
    time_horizon_years: int = 5
    seed: Optional[int] = None


@router.post("/rwe-registry")
def rwe_registry_endpoint(req: RegistryRequest):
    """Generate simulated registry data for real-world evidence."""
    return generate_registry_data(
        n_patients=req.n_patients, cancer_type=req.cancer_type,
        product=req.product, time_period_months=req.time_period_months,
        seed=req.seed,
    )


@router.post("/rwe-vs-trial")
def rwe_vs_trial_endpoint(req: RWECompareRequest):
    """Compare real-world outcomes to clinical trial results."""
    return compare_rwe_vs_trial(
        product=req.product, cancer_type=req.cancer_type,
        rwe_n=req.rwe_n, seed=req.seed,
    )


@router.post("/post-market-surveillance")
def surveillance_endpoint(req: SurveillanceRequest):
    """Simulate post-market safety surveillance data."""
    return post_market_surveillance(
        product=req.product, n_patients=req.n_patients,
        monitoring_months=req.monitoring_months, seed=req.seed,
    )


@router.post("/health-technology-assessment")
def hta_endpoint(req: HTARequest):
    """Run health technology assessment (ICER, QALY analysis)."""
    return health_technology_assessment(
        product=req.product, cancer_type=req.cancer_type,
        comparator=req.comparator,
        time_horizon_years=req.time_horizon_years, seed=req.seed,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Presets & Utilities
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/presets")
def get_patient_presets():
    """Return preset patient profiles for demo purposes."""
    return [
        {
            "name": "Pediatric ALL (5yo)",
            "description": "Young child with acute lymphoblastic leukemia, early stage",
            "params": {
                "patient_age": 5, "cancer_stage": "II", "tumor_burden_mm": 25,
                "antigen_expression": 0.9, "prior_car_t": False,
                "cancer_type": "B-cell ALL",
            },
        },
        {
            "name": "Adult DLBCL (45yo)",
            "description": "Middle-aged adult with diffuse large B-cell lymphoma",
            "params": {
                "patient_age": 45, "cancer_stage": "III", "tumor_burden_mm": 60,
                "antigen_expression": 0.75, "prior_car_t": False,
                "cancer_type": "DLBCL",
            },
        },
        {
            "name": "Relapsed Multiple Myeloma (62yo)",
            "description": "Elderly patient with relapsed/refractory multiple myeloma",
            "params": {
                "patient_age": 62, "cancer_stage": "IV", "tumor_burden_mm": 90,
                "antigen_expression": 0.6, "prior_car_t": True,
                "cancer_type": "Multiple Myeloma", "ldh": 450,
            },
        },
        {
            "name": "Mantle Cell Lymphoma (58yo)",
            "description": "Aggressive lymphoma with high tumor burden",
            "params": {
                "patient_age": 58, "cancer_stage": "IV", "tumor_burden_mm": 120,
                "antigen_expression": 0.8, "prior_car_t": False,
                "cancer_type": "Mantle Cell Lymphoma", "ldh": 600,
            },
        },
        {
            "name": "Double-Hit Lymphoma (52yo)",
            "description": "High-risk biology with MYC and BCL2 rearrangements",
            "params": {
                "patient_age": 52, "cancer_stage": "IV", "tumor_burden_mm": 95,
                "antigen_expression": 0.7, "prior_car_t": False,
                "cancer_type": "DLBCL", "ldh": 550,
            },
        },
    ]


@router.get("/engine-status")
def engine_status():
    """Return status and capabilities of all Digital Twin engines."""
    return {
        "engines": [
            {"name": "Immune Simulation", "version": "5.0", "status": "active", "endpoints": 3},
            {"name": "Cancer Profiles", "version": "5.0", "status": "active", "endpoints": 2},
            {"name": "PK/PD Engine", "version": "5.0", "status": "active", "endpoints": 2},
            {"name": "Treatment Protocols", "version": "5.0", "status": "active", "endpoints": 4},
            {"name": "Biomarker Predictor", "version": "5.0", "status": "active", "endpoints": 1},
            {"name": "Treatment Optimizer", "version": "5.0", "status": "active", "endpoints": 2},
            {"name": "Genomic Profiler", "version": "5.0", "status": "active", "endpoints": 3},
            {"name": "Adverse Event Model", "version": "5.0", "status": "active", "endpoints": 3},
            {"name": "Patient Outcomes", "version": "5.0", "status": "active", "endpoints": 4},
            {"name": "Population Simulator", "version": "5.0", "status": "active", "endpoints": 3},
            {"name": "Report Generator", "version": "5.0", "status": "active", "endpoints": 1},
            {"name": "Real-World Evidence", "version": "5.0", "status": "active", "endpoints": 4},
            {"name": "Patient Model", "version": "5.0", "status": "active", "endpoints": 0},
        ],
        "total_endpoints": 35,
        "digital_twin_version": "5.0",
    }
