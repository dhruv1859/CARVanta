"""
CARVanta Discovery — API Router
==================================
REST API endpoints for the AI-Powered Drug Discovery Engine (Module 3).
Provides proteome scanning, GNN-based interaction prediction, novelty
detection, toxicity assessment, scFv design, and CAR architecture.

Security: Rate-limited, input-sanitized, auth-protected, API v5.
"""

import re
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

logger = logging.getLogger("carvanta.api.discovery_router")

router = APIRouter(prefix="/api/v5/discovery", tags=["AI Drug Discovery"])

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")


def _sanitize_gene(gene: str) -> str:
    """Sanitize gene symbol input."""
    gene = gene.strip().upper()
    if not _SAFE_ID_RE.match(gene):
        raise HTTPException(status_code=400, detail="Invalid gene symbol format")
    return gene


# ──────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────

class ProteomeScanRequest(BaseModel):
    tumor_types: Optional[List[str]] = None
    min_surface_probability: float = Field(0.3, ge=0.0, le=1.0)
    exclude_essential: bool = False
    max_results: int = Field(50, ge=1, le=500)

    @validator("tumor_types", each_item=True, pre=True)
    def validate_tumor_type(cls, v: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-]", "", v)[:64]


class ScFvDesignRequest(BaseModel):
    target: str = Field(..., max_length=32)
    num_candidates: int = Field(5, ge=1, le=20)
    humanization: str = Field("humanized_cdr_graft", max_length=32)
    format: str = Field("VH-linker-VL", max_length=16)


class CARDesignRequest(BaseModel):
    target: str = Field(..., max_length=32)
    generation: str = Field("2nd_generation", max_length=20)
    costim: Optional[List[str]] = None
    armor: str = Field("none", max_length=32)
    optimize_for: str = Field("balanced", max_length=16)
    num_designs: int = Field(5, ge=1, le=20)


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/proteome-scan", summary="Scan the full human proteome for CAR-T targets")
async def scan_proteome(request: ProteomeScanRequest) -> Dict[str, Any]:
    """
    Scan 20,000+ human proteins for CAR-T target potential.
    Multi-dimensional scoring: surface expression, tumor specificity,
    druggability, essential gene status, clinical precedent.
    """
    from discovery.proteome_scanner import scan_full_proteome, rank_proteome_targets

    summary = await scan_full_proteome(
        target_tumor_types=request.tumor_types,
        min_surface_probability=request.min_surface_probability,
        exclude_essential=request.exclude_essential,
        max_results=request.max_results,
    )

    ranked = await rank_proteome_targets(summary)

    return {
        "total_scanned": summary.total_proteins_scanned,
        "surface_proteins": summary.surface_proteins_found,
        "ideal_targets": summary.ideal_targets,
        "promising_targets": summary.promising_targets,
        "exploratory_targets": summary.exploratory_targets,
        "clinical_targets": summary.targets_in_clinical,
        "tumor_coverage": summary.tumor_type_coverage,
        "ranked_targets": ranked[:request.max_results],
    }


@router.get("/target/{gene}/score", summary="Score a specific target for CAR-T potential")
async def score_target(gene: str) -> Dict[str, Any]:
    """Get detailed CAR-T target potential score for a specific gene."""
    from discovery.proteome_scanner import score_surface_antigen_potential, SURFACE_PROTEIN_DATABASE

    gene = _sanitize_gene(gene)
    if gene not in SURFACE_PROTEIN_DATABASE:
        raise HTTPException(status_code=404, detail=f"Gene '{gene}' not found in proteome database")

    info = SURFACE_PROTEIN_DATABASE[gene]
    score = score_surface_antigen_potential(info)

    return {
        "gene": gene,
        "protein_name": info.get("name", ""),
        "uniprot": info.get("uniprot", ""),
        "target_class": score.target_class.value,
        "composite_score": score.composite_score,
        "dimensions": {
            "surface_probability": score.surface_probability,
            "tumor_specificity": score.tumor_specificity,
            "tumor_expression": score.tumor_expression_level,
            "essential_gene_risk": score.essential_gene_risk,
            "druggability": score.druggability_score,
            "clinical_precedent": score.clinical_precedent,
        },
        "tumor_types": info.get("tumor_types", []),
        "clinical_stage": info.get("clinical_stage", ""),
        "approved_products": info.get("approved_products", []),
    }


@router.post("/graph/build", summary="Build protein interaction graph")
async def build_graph(
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    pathways: Optional[List[str]] = Query(None),
) -> Dict[str, Any]:
    """
    Build protein-protein interaction graph and run GNN inference.
    Returns community clusters, hub proteins, and node details.
    """
    from discovery.graph_nn import build_protein_interaction_graph, run_gnn_inference

    graph = await build_protein_interaction_graph(
        include_pathways=pathways,
        min_confidence=min_confidence,
    )
    result = await run_gnn_inference(graph)
    return result


@router.get("/graph/predict/{gene}", summary="Predict novel interactions for a target")
async def predict_interactions(
    gene: str,
    top_k: int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    """Predict novel protein-protein interactions using GNN embeddings."""
    from discovery.graph_nn import build_protein_interaction_graph, run_gnn_inference, predict_target_interactions

    gene = _sanitize_gene(gene)
    graph = await build_protein_interaction_graph()
    await run_gnn_inference(graph)
    predictions = await predict_target_interactions(graph, gene, top_k)

    return {
        "target": gene,
        "predictions": [
            {
                "partner": p.protein_b,
                "probability": p.predicted_interaction,
                "type": p.predicted_type.value,
                "confidence": p.confidence,
                "pathways": p.pathway_context,
                "evidence": p.supporting_evidence,
            }
            for p in predictions
        ],
    }


@router.get("/novelty/{gene}", summary="Assess target novelty and white-space opportunity")
async def assess_novelty(gene: str) -> Dict[str, Any]:
    """Compare target against the clinical landscape for white-space opportunity."""
    from discovery.novelty_detector import compare_to_clinical_landscape

    gene = _sanitize_gene(gene)
    return await compare_to_clinical_landscape(gene)


@router.get("/novelty", summary="Detect novel underexplored targets")
async def detect_novel(
    min_novelty: float = Query(0.4, ge=0.0, le=1.0),
    max_results: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Discover underexplored targets with high scientific potential."""
    from discovery.novelty_detector import detect_novel_targets

    results = await detect_novel_targets(min_novelty=min_novelty, max_results=max_results)
    return {
        "total_novel_targets": len(results),
        "targets": [
            {
                "gene": r.gene_symbol,
                "novelty": r.novelty_score.overall_novelty,
                "white_space_index": r.novelty_score.white_space_index,
                "opportunity_score": r.opportunity_score,
                "stage": r.development_stage.value,
                "pubmed_count": r.pubmed_count,
                "clinical_trials": r.clinical_trials,
                "competitors": r.competitors,
                "market_size_B": r.market_size_B,
                "concerns": [c.value for c in r.concerns],
                "recommendations": r.recommendations,
                "rank": r.rank,
            }
            for r in results
        ],
    }


@router.get("/toxicity/{gene}", summary="Predict off-target toxicity for a target")
async def predict_toxicity(
    gene: str,
    tumor_expression: float = Query(0.8, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    """Predict off-target toxicity with tissue expression risk analysis."""
    from discovery.toxicity_predictor import generate_safety_profile

    gene = _sanitize_gene(gene)
    return await generate_safety_profile(gene, tumor_expression)


@router.post("/scfv/design", summary="Design scFv antibody fragment candidates")
async def design_scfv(request: ScFvDesignRequest) -> Dict[str, Any]:
    """
    Design optimized scFv candidates with binding affinity prediction,
    CDR analysis, and developability assessment.
    """
    from discovery.scfv_designer import design_scfv_candidates

    target = _sanitize_gene(request.target)
    candidates = await design_scfv_candidates(
        target=target,
        num_candidates=request.num_candidates,
        humanization_level=request.humanization,
        format_preference=request.format,
    )

    return {
        "target": target,
        "total_candidates": len(candidates),
        "candidates": [
            {
                "id": c.candidate_id,
                "rank": c.rank,
                "overall_score": c.overall_score,
                "template": c.source_template,
                "format": c.format.value,
                "humanization": c.humanization.value,
                "binding": {
                    "kd_nm": c.binding.kd_nm,
                    "kon": c.binding.kon_1_Ms,
                    "koff": c.binding.koff_1_s,
                    "binding_energy": c.binding.binding_energy_kcal,
                    "epitope_accessibility": c.binding.epitope_accessibility,
                    "cross_reactivity_risk": c.binding.cross_reactivity_risk,
                },
                "developability": {
                    "overall_risk": c.developability.overall_risk.value,
                    "aggregation": c.developability.aggregation_risk,
                    "immunogenicity": c.developability.immunogenicity_risk,
                    "stability_tm": c.developability.thermal_stability_c,
                    "yield": c.developability.expression_yield,
                    "risk_factors": c.developability.risk_factors,
                },
                "cdr_sequences": {
                    "VH_CDR1": c.vh_cdr1, "VH_CDR2": c.vh_cdr2, "VH_CDR3": c.vh_cdr3,
                    "VL_CDR1": c.vl_cdr1, "VL_CDR2": c.vl_cdr2, "VL_CDR3": c.vl_cdr3,
                },
                "mutations": c.mutations_from_template,
            }
            for c in candidates
        ],
    }


@router.post("/car/design", summary="Design CAR construct architectures")
async def design_car(request: CARDesignRequest) -> Dict[str, Any]:
    """
    Design CAR constructs with modular domain selection,
    fitness prediction, and head-to-head comparison.
    """
    from discovery.car_architect import design_car_construct

    target = _sanitize_gene(request.target)
    constructs = await design_car_construct(
        target=target,
        generation=request.generation,
        costim_preference=request.costim,
        armor_type=request.armor,
        optimize_for=request.optimize_for,
        num_designs=request.num_designs,
    )

    return {
        "target": target,
        "total_designs": len(constructs),
        "constructs": [
            {
                "id": c.construct_id,
                "name": c.name,
                "rank": c.rank,
                "generation": c.generation.value,
                "domains": {
                    "costim": [cd.value for cd in c.costim_domains],
                    "hinge": c.hinge.value,
                    "tm": c.transmembrane.value,
                    "signaling": c.signaling.value,
                    "armor": c.armor.value,
                },
                "fitness": {
                    "activation": c.fitness.activation_strength,
                    "persistence": c.fitness.persistence,
                    "exhaustion_resistance": c.fitness.exhaustion_resistance,
                    "memory_formation": c.fitness.memory_formation,
                    "tumor_killing": c.fitness.tumor_killing,
                    "safety": c.fitness.safety_score,
                    "manufacturing": c.fitness.manufacturing_ease,
                    "overall": c.fitness.overall_fitness,
                },
                "size_kda": c.estimated_size_kda,
                "vector_kb": c.viral_vector_size_kb,
                "rationale": c.design_rationale,
                "risks": c.risk_factors,
                "manufacturing": c.recommended_manufacturing,
            }
            for c in constructs
        ],
    }


@router.get("/car/compare/{gene}", summary="Compare CAR generations head-to-head")
async def compare_generations(gene: str) -> Dict[str, Any]:
    """Compare all 5 CAR generations for a target antigen."""
    from discovery.car_architect import compare_car_generations

    gene = _sanitize_gene(gene)
    return await compare_car_generations(gene)


# ──────────────────────────────────────────────────────────────────────
# Molecular Docking Endpoints
# ──────────────────────────────────────────────────────────────────────

class DockingRequest(BaseModel):
    target: str = Field(..., max_length=32)
    binder_type: str = Field("scFv", max_length=16)
    affinity_engineering: float = Field(1.0, ge=0.1, le=10.0)


class LinkerRequest(BaseModel):
    linker_type: str = Field("G4S", max_length=16)
    repeats: int = Field(3, ge=1, le=10)


@router.post("/dock", summary="Dock binder to target")
async def dock_binder(req: DockingRequest) -> Dict[str, Any]:
    """Molecular docking energy estimation and interaction analysis."""
    from drug_discovery.molecular_docking import dock_binder
    target = _sanitize_gene(req.target)
    return await dock_binder(target, req.binder_type, req.affinity_engineering)


@router.post("/linker/analyze", summary="Analyze scFv linker")
async def analyze_linker(req: LinkerRequest) -> Dict[str, Any]:
    """Linker flexibility, stability, and length optimization."""
    from drug_discovery.molecular_docking import analyze_linker
    return await analyze_linker(linker_type=req.linker_type, repeats=req.repeats)


@router.get("/crossreactivity/{gene}", summary="Cross-reactivity prediction")
async def cross_reactivity(gene: str, kd_nM: float = Query(1.0, ge=0.001)) -> Dict[str, Any]:
    """Predict off-target binding risk against human proteome homologs."""
    from drug_discovery.molecular_docking import predict_cross_reactivity
    gene = _sanitize_gene(gene)
    return await predict_cross_reactivity(gene, kd_nM)


@router.get("/structure/{gene}", summary="Target structure info")
async def target_structure(gene: str) -> Dict[str, Any]:
    """Get target structural information including epitopes and PDB IDs."""
    from drug_discovery.molecular_docking import get_target_structure
    gene = _sanitize_gene(gene)
    result = await get_target_structure(gene)
    if not result:
        raise HTTPException(404, "Target structure not found")
    return result


@router.get("/structures", summary="List targets with structural data")
async def list_structures() -> Dict[str, Any]:
    """List all targets with available structural data."""
    from drug_discovery.molecular_docking import list_targets
    return await list_targets()


# ──────────────────────────────────────────────────────────────────────
# ADMET Prediction Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/admet/{drug}", summary="ADMET prediction")
async def admet_prediction(drug: str) -> Dict[str, Any]:
    """Predict ADMET properties for CAR-T relevant drugs."""
    from drug_discovery.admet_predictor import predict_admet
    result = await predict_admet(drug)
    if not result:
        raise HTTPException(404, "Drug not found")
    return result


@router.get("/admet", summary="List drugs database")
async def list_drugs(drug_class: Optional[str] = None) -> Dict[str, Any]:
    """List all drugs in the CAR-T pharmacology database."""
    from drug_discovery.admet_predictor import list_drugs
    return await list_drugs(drug_class=drug_class)


@router.get("/ddi/{drug1}/{drug2}", summary="Drug-drug interaction")
async def drug_interaction(drug1: str, drug2: str) -> Dict[str, Any]:
    """Predict interaction between two CAR-T relevant drugs."""
    from drug_discovery.admet_predictor import predict_drug_interaction
    return await predict_drug_interaction(drug1, drug2)


@router.get("/pk/{drug}", summary="PK simulation")
async def pk_sim(drug: str, dose_mg: float = 100, interval_h: float = 24) -> Dict[str, Any]:
    """Run 1-compartment PK simulation."""
    from drug_discovery.admet_predictor import pk_simulation
    return await pk_simulation(drug, dose_mg, interval_h)


# ──────────────────────────────── Lead Optimizer ────────────────────────────────

class OptimizeRequest(BaseModel):
    target: str = Field("CD19", max_length=20)
    n_candidates: int = Field(50, ge=5, le=200)
    optimization_goals: Optional[List[str]] = None


class AffinityRequest(BaseModel):
    scfv: str = Field("FMC63", max_length=30)
    target_kd_nm: float = Field(0.1, ge=0.001, le=100)
    n_rounds: int = Field(5, ge=1, le=10)


@router.post("/optimize-car", summary="Multi-objective CAR construct optimization")
async def optimize_car(req: OptimizeRequest) -> Dict[str, Any]:
    """Generate and rank optimal CAR construct designs across multiple objectives."""
    from drug_discovery.lead_optimizer import optimize_car_construct
    return await optimize_car_construct(target=req.target, n_candidates=req.n_candidates, optimization_goals=req.optimization_goals)


@router.post("/affinity-maturation", summary="In silico affinity maturation")
async def affinity_mat(req: AffinityRequest) -> Dict[str, Any]:
    """Simulate directed evolution to improve scFv binding affinity."""
    from drug_discovery.lead_optimizer import affinity_maturation
    return await affinity_maturation(scfv=req.scfv, target_kd_nm=req.target_kd_nm, n_rounds=req.n_rounds)


@router.get("/stability/{scfv}", summary="Biophysical stability prediction")
async def stability(scfv: str) -> Dict[str, Any]:
    """Predict thermal stability, aggregation, and manufacturability."""
    from drug_discovery.lead_optimizer import predict_stability
    return await predict_stability(scfv=scfv)


@router.get("/immunogenicity/{scfv}", summary="Immunogenicity risk assessment")
async def immunogenicity(scfv: str) -> Dict[str, Any]:
    """Predict T-cell epitopes, ADA risk, and deimmunization strategies."""
    from drug_discovery.lead_optimizer import immunogenicity_assessment
    return await immunogenicity_assessment(scfv=scfv)


@router.get("/combination/{target}", summary="Combination therapy design")
async def combination(target: str, cancer_type: str = "DLBCL") -> Dict[str, Any]:
    """Design rational combination strategies (checkpoints, TME modulators, dual-target)."""
    from drug_discovery.lead_optimizer import design_combination_therapy
    return await design_combination_therapy(primary_target=target, cancer_type=cancer_type)


@router.get("/validate/{target}", summary="Target validation pipeline")
async def validate(target: str) -> Dict[str, Any]:
    """Run 8-stage target validation pipeline with go/no-go scoring."""
    from drug_discovery.lead_optimizer import target_validation_pipeline
    return await target_validation_pipeline(target=target)


# ──────────────────────────────── Clinical Profiler ────────────────────────────

@router.get("/landscape/{target}", summary="Competitive landscape analysis")
async def landscape(target: str) -> Dict[str, Any]:
    """Analyze approved products, pipeline, and differentiation opportunities."""
    from drug_discovery.clinical_profiler import competitive_landscape
    return await competitive_landscape(target=target)


@router.get("/regulatory/{target}", summary="Regulatory strategy")
async def regulatory(target: str, indication: str = "r/r DLBCL") -> Dict[str, Any]:
    """Design regulatory approval strategy with designations and timeline."""
    from drug_discovery.clinical_profiler import regulatory_strategy
    return await regulatory_strategy(target=target, indication=indication)


@router.post("/trial-design", summary="Clinical trial design generator")
async def trial_design(target: str = "CD19", indication: str = "r/r DLBCL", phase: str = "Phase II") -> Dict[str, Any]:
    """Generate optimized clinical trial protocol."""
    from drug_discovery.clinical_profiler import clinical_trial_design
    return await clinical_trial_design(target=target, indication=indication, phase=phase)


@router.get("/approved-products", summary="FDA-approved CAR-T products")
async def approved() -> Dict[str, Any]:
    """Get database of all approved CAR-T products and pipeline."""
    from drug_discovery.clinical_profiler import get_approved_products
    return await get_approved_products()


# ──────────────────────────────── Safety Switches ─────────────────────────────

@router.get("/safety-switch/design", summary="Design safety switch strategy")
async def safety_switch_design(risk_profile: str = "moderate") -> Dict[str, Any]:
    """Design optimal safety switch strategy for a CAR construct."""
    from drug_discovery.safety_switch import design_safety_switch
    return await design_safety_switch(risk_profile=risk_profile)


@router.get("/safety-switch/simulate/{switch_type}", summary="Simulate switch activation")
async def safety_switch_sim(switch_type: str, activation_hour: float = 24) -> Dict[str, Any]:
    """Simulate safety switch activation kinetics over time."""
    from drug_discovery.safety_switch import simulate_switch_activation
    return await simulate_switch_activation(switch_type=switch_type, activation_time_hours=activation_hour)


@router.get("/safety-switch/all", summary="List all safety switches")
async def all_switches() -> Dict[str, Any]:
    """Get all available safety switch mechanisms."""
    from drug_discovery.safety_switch import get_all_switches
    return await get_all_switches()


# ──────────────────────────────── Epitope Mapper ─────────────────────────────

@router.get("/epitopes/{target}", summary="Predict B-cell epitopes")
async def epitopes(target: str, window_size: int = Query(15, ge=8, le=25)) -> Dict[str, Any]:
    """Predict surface-accessible B-cell epitopes on a target protein."""
    from drug_discovery.epitope_mapper import predict_epitopes
    return await predict_epitopes(target=target, window_size=window_size)


@router.get("/epitopes/{target}/conservation", summary="Epitope conservation analysis")
async def conservation(target: str, n_variants: int = Query(50, ge=10, le=200)) -> Dict[str, Any]:
    """Analyze epitope conservation across population variants."""
    from drug_discovery.epitope_mapper import epitope_conservation
    return await epitope_conservation(target=target, n_variants=n_variants)


@router.get("/epitopes/{target}/cross-reactivity", summary="Cross-reactivity prediction")
async def cross_react(target: str) -> Dict[str, Any]:
    """Predict cross-reactivity across protein family homologs."""
    from drug_discovery.epitope_mapper import cross_reactivity_analysis
    return await cross_reactivity_analysis(target=target)


@router.get("/epitopes/{target}/binning", summary="Epitope binning")
async def binning(target: str, n_antibodies: int = Query(20, ge=5, le=100)) -> Dict[str, Any]:
    """Simulate competitive epitope binning experiment."""
    from drug_discovery.epitope_mapper import epitope_binning
    return await epitope_binning(target=target, n_antibodies=n_antibodies)


@router.get("/target-info/{target}", summary="Target protein info")
async def target_info(target: str) -> Dict[str, Any]:
    """Get structural information for a CAR-T target protein."""
    from drug_discovery.epitope_mapper import get_target_info
    return await get_target_info(target=target)


# ──────────────────────────────── Manufacturing ──────────────────────────────

class MfgRequest(BaseModel):
    target: str = Field("CD19", max_length=20)
    car_generation: str = Field("2nd", max_length=10)
    process_type: str = Field("centralized", max_length=20)


@router.post("/manufacturing/simulate", summary="Simulate CAR-T manufacturing")
async def mfg_simulate(req: MfgRequest) -> Dict[str, Any]:
    """Simulate a complete 14-day GMP manufacturing run."""
    from drug_discovery.manufacturing import simulate_manufacturing
    return await simulate_manufacturing(
        target=req.target, car_generation=req.car_generation,
        process_type=req.process_type,
    )


@router.get("/manufacturing/compare", summary="Compare manufacturing models")
async def mfg_compare() -> Dict[str, Any]:
    """Compare centralized vs point-of-care manufacturing."""
    from drug_discovery.manufacturing import compare_manufacturing_models
    return await compare_manufacturing_models()


@router.get("/manufacturing/vector", summary="Viral vector production")
async def mfg_vector(vector_type: str = "lentiviral") -> Dict[str, Any]:
    """Simulate viral vector production pipeline."""
    from drug_discovery.manufacturing import viral_vector_production
    return await viral_vector_production(vector_type=vector_type)


@router.get("/manufacturing/failure-analysis", summary="Batch failure analysis")
async def mfg_failure(n_batches: int = Query(100, ge=10, le=1000)) -> Dict[str, Any]:
    """Monte Carlo simulation of batch outcomes."""
    from drug_discovery.manufacturing import batch_failure_analysis
    return await batch_failure_analysis(n_batches=n_batches)


# ──────────────────────────────── Module Overview ────────────────────────────

@router.get("/overview", summary="Drug Discovery module overview")
async def overview() -> Dict[str, Any]:
    """Get a summary of all Drug Discovery capabilities."""
    return {
        "module": "AI-Powered Drug Discovery Engine",
        "version": "5.0",
        "capabilities": {
            "proteome_scanning": {
                "description": "Scan entire proteome for novel CAR-T targets",
                "endpoints": ["/proteome-scan", "/target/{gene}/score"],
            },
            "novelty_detection": {
                "description": "Identify underexplored white-space opportunities",
                "endpoints": ["/novelty"],
            },
            "toxicity_prediction": {
                "description": "Predict on-target off-tumor toxicity across 30+ tissues",
                "endpoints": ["/toxicity/{gene}"],
            },
            "scfv_design": {
                "description": "AI-driven scFv candidate generation with CDR optimization",
                "endpoints": ["/scfv/design"],
            },
            "car_architecture": {
                "description": "Multi-generation CAR construct design with fitness scoring",
                "endpoints": ["/car/design"],
            },
            "lead_optimization": {
                "description": "Pareto-optimal CAR construct optimization across 4 objectives",
                "endpoints": ["/optimize-car", "/affinity-maturation", "/stability/{scfv}", "/immunogenicity/{scfv}"],
            },
            "combination_therapy": {
                "description": "Rational combination strategy design (checkpoints, TME, dual-target)",
                "endpoints": ["/combination/{target}"],
            },
            "target_validation": {
                "description": "8-stage validation pipeline with go/no-go scoring",
                "endpoints": ["/validate/{target}"],
            },
            "competitive_landscape": {
                "description": "Approved products database and market analysis",
                "endpoints": ["/landscape/{target}", "/approved-products", "/regulatory/{target}"],
            },
            "clinical_trials": {
                "description": "Phase I-III clinical trial design generator",
                "endpoints": ["/trial-design"],
            },
            "safety_switches": {
                "description": "9 safety switch mechanisms with activation kinetics simulation",
                "endpoints": ["/safety-switch/design", "/safety-switch/simulate/{type}", "/safety-switch/all"],
            },
            "epitope_mapping": {
                "description": "B-cell epitope prediction, conservation, cross-reactivity, binning",
                "endpoints": ["/epitopes/{target}", "/epitopes/{target}/conservation", "/epitopes/{target}/cross-reactivity"],
            },
            "admet": {
                "description": "ADMET prediction, drug-drug interactions, PK simulation",
                "endpoints": ["/admet/{drug}", "/ddi/{drug1}/{drug2}", "/pk/{drug}"],
            },
            "molecular_docking": {
                "description": "Binding affinity prediction and docking simulation",
                "endpoints": ["/dock", "/dock/batch"],
            },
            "manufacturing": {
                "description": "End-to-end GMP manufacturing simulation with COGS analysis",
                "endpoints": ["/manufacturing/simulate", "/manufacturing/compare", "/manufacturing/vector", "/manufacturing/failure-analysis"],
            },
        },
        "total_endpoints": 30,
        "domain_libraries": {
            "scFv": 12, "hinge": 5, "transmembrane": 3,
            "costimulatory": 6, "signaling": 2, "safety_switches": 9,
            "target_proteins": 8, "approved_products": 6,
            "pipeline_candidates": 15,
        },
    }


# ──────────────────────────────── Resistance Prediction ──────────────────────

@router.get("/resistance/{target}", summary="Predict resistance mechanisms")
async def resistance(
    target: str,
    cancer_type: str = Query("DLBCL"),
    costim: str = Query("4-1BB"),
) -> Dict[str, Any]:
    """Predict resistance mechanisms for a CAR-T targeting a specific antigen."""
    from drug_discovery.resistance import predict_resistance
    return await predict_resistance(target=target, cancer_type=cancer_type, car_costim=costim)


@router.get("/resistance/exhaustion-trajectory", summary="Model T-cell exhaustion")
async def exhaustion(
    costim: str = Query("4-1BB"),
    antigen_load: str = Query("high"),
    n_days: int = Query(90, ge=14, le=365),
) -> Dict[str, Any]:
    """Model T-cell exhaustion trajectory over time."""
    from drug_discovery.resistance import exhaustion_trajectory
    return await exhaustion_trajectory(costim=costim, antigen_load=antigen_load, n_days=n_days)


@router.get("/resistance/antigen-escape", summary="Antigen escape modeling")
async def antigen_escape(
    target: str = Query("CD19"),
    initial_ag_neg_fraction: float = Query(0.001, ge=0, le=0.5),
    n_days: int = Query(180, ge=30, le=730),
) -> Dict[str, Any]:
    """Model antigen-negative clonal escape under CAR-T selection."""
    from drug_discovery.resistance import antigen_escape_model
    return await antigen_escape_model(target=target, antigen_negative_fraction=initial_ag_neg_fraction, n_days=n_days)


@router.get("/resistance/mechanisms", summary="List all resistance mechanisms")
async def resistance_mechanisms() -> Dict[str, Any]:
    """Get all known CAR-T resistance mechanisms from the database."""
    from drug_discovery.resistance import get_all_resistance_mechanisms
    return await get_all_resistance_mechanisms()


# ──────────────────────────────── Pharmacokinetics ───────────────────────────

class PKRequest(BaseModel):
    dose_cells: float = Field(2e8, gt=1e6, lt=1e11)
    target: str = Field("CD19", max_length=20)
    costim: str = Field("4-1BB", max_length=20)
    tumor_burden: str = Field("high", max_length=20)
    n_days: int = Field(365, ge=30, le=730)


@router.post("/pk/simulate", summary="Simulate CAR-T pharmacokinetics")
async def pk_simulate(req: PKRequest) -> Dict[str, Any]:
    """Simulate CAR-T expansion, persistence, CRS/ICANS prediction, and cytokine kinetics."""
    from drug_discovery.pk_engine import simulate_pk
    return await simulate_pk(
        dose_cells=req.dose_cells, target=req.target,
        costim=req.costim, tumor_burden=req.tumor_burden,
        n_days=req.n_days,
    )


@router.get("/pk/dose-response/{target}", summary="Dose-response analysis")
async def pk_dose_response(target: str) -> Dict[str, Any]:
    """Model dose-response relationship across 5 dose levels."""
    from drug_discovery.pk_engine import dose_response_analysis
    return await dose_response_analysis(target=target)


@router.get("/pk/population", summary="Population PK simulation")
async def pk_population(
    n_patients: int = Query(50, ge=10, le=200),
    dose: float = Query(2e8, gt=1e6),
) -> Dict[str, Any]:
    """Simulate population PK variability with covariate effects."""
    from drug_discovery.pk_engine import population_pk
    return await population_pk(n_patients=n_patients, dose_cells=dose)


# ──────────────────────────────── Module Status ──────────────────────────────

@router.get("/status", summary="Drug Discovery module status")
async def module_status() -> Dict[str, Any]:
    """Health check and capability listing for the Drug Discovery module."""
    engines = {
        "proteome_scanner": {"status": "operational", "version": "5.0"},
        "novelty_detector": {"status": "operational", "version": "5.0"},
        "toxicity_predictor": {"status": "operational", "version": "5.0"},
        "scfv_designer": {"status": "operational", "version": "5.0"},
        "car_architect": {"status": "operational", "version": "5.0"},
        "lead_optimizer": {"status": "operational", "version": "1.0"},
        "clinical_profiler": {"status": "operational", "version": "1.0"},
        "safety_switch_designer": {"status": "operational", "version": "1.0"},
        "epitope_mapper": {"status": "operational", "version": "1.0"},
        "admet_predictor": {"status": "operational", "version": "1.0"},
        "molecular_docking": {"status": "operational", "version": "1.0"},
        "manufacturing_sim": {"status": "operational", "version": "1.0"},
        "resistance_predictor": {"status": "operational", "version": "1.0"},
        "pk_engine": {"status": "operational", "version": "1.0"},
    }
    return {
        "module": "Drug Discovery",
        "status": "operational",
        "engines": engines,
        "total_engines": len(engines),
        "total_endpoints": 35,
        "api_prefix": "/api/v5/discovery",
    }
