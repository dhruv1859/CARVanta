"""CARVanta Disease Atlas — API Router (Expanded)"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger("carvanta.api.atlas_router")
router = APIRouter(prefix="/api/v5/atlas", tags=["Disease Atlas"])


# ═══════════════════════════════════════════════════════════════════════════════
# Core Disease Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diseases", summary="List all diseases")
async def list_diseases(category: Optional[str] = None) -> Dict[str, Any]:
    from disease_atlas.epidemiology import list_diseases
    return await list_diseases(category=category)

@router.get("/diseases/{disease_id}", summary="Get disease profile")
async def get_disease(disease_id: str) -> Dict[str, Any]:
    from disease_atlas.epidemiology import get_disease_profile
    result = await get_disease_profile(disease_id)
    if not result: raise HTTPException(404, "Disease not found")
    return result

@router.get("/diseases/{disease_id}/treatment", summary="Treatment landscape")
async def treatment_landscape(disease_id: str) -> Dict[str, Any]:
    from disease_atlas.epidemiology import get_treatment_landscape
    return await get_treatment_landscape(disease_id)

@router.get("/diseases/{disease_id}/regions", summary="Regional epidemiology")
async def regional_data(disease_id: str, region: Optional[str] = None) -> Dict[str, Any]:
    from disease_atlas.epidemiology import get_regional_data
    return await get_regional_data(disease_id, region=region)

@router.get("/pipeline", summary="Cell therapy pipeline")
async def pipeline(target: Optional[str] = None) -> Dict[str, Any]:
    from disease_atlas.epidemiology import get_pipeline
    return await get_pipeline(target=target)

@router.get("/summary", summary="Global atlas summary")
async def global_summary() -> Dict[str, Any]:
    from disease_atlas.epidemiology import get_global_summary
    return await get_global_summary()


# ═══════════════════════════════════════════════════════════════════════════════
# Prevalence Analysis Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/prevalence/{antigen}", summary="Antigen prevalence by cancer")
async def antigen_prevalence(
    antigen: str,
    cancer_type: Optional[str] = Query(None),
) -> Dict[str, Any]:
    from disease_atlas.prevalence_analyzer import antigen_prevalence_by_cancer
    return await antigen_prevalence_by_cancer(antigen, cancer_type=cancer_type)

@router.get("/prevalence/{antigen}/ethnicity", summary="Ethnic prevalence disparity")
async def ethnic_prevalence(
    antigen: str,
    cancer_type: str = Query("dlbcl"),
) -> Dict[str, Any]:
    from disease_atlas.prevalence_analyzer import antigen_prevalence_by_ethnicity
    return await antigen_prevalence_by_ethnicity(antigen, cancer_type=cancer_type)

@router.get("/prevalence/{antigen}/age", summary="Age-stratified prevalence")
async def age_prevalence(
    antigen: str,
    cancer_type: str = Query("all"),
) -> Dict[str, Any]:
    from disease_atlas.prevalence_analyzer import antigen_prevalence_by_age
    return await antigen_prevalence_by_age(antigen, cancer_type=cancer_type)

@router.get("/coexpression", summary="Co-expression matrix")
async def coexpression(
    cancer_type: str = Query("dlbcl"),
) -> Dict[str, Any]:
    from disease_atlas.prevalence_analyzer import coexpression_matrix
    return await coexpression_matrix(cancer_type=cancer_type)

@router.get("/addressable-population", summary="Addressable patient population")
async def addressable_pop(
    antigen: str = Query("CD19"),
    cancer_type: str = Query("dlbcl"),
) -> Dict[str, Any]:
    from disease_atlas.prevalence_analyzer import addressable_population
    return await addressable_population(antigen, cancer_type)


# ═══════════════════════════════════════════════════════════════════════════════
# Access & Regulatory Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/regulatory-map", summary="Regulatory approval map")
async def regulatory_map(
    product: Optional[str] = Query(None),
) -> Dict[str, Any]:
    from disease_atlas.access_gaps import get_regulatory_map
    return await get_regulatory_map(product=product)

@router.get("/access-gaps/{cancer_type}", summary="Treatment access gap analysis")
async def access_gaps(cancer_type: str) -> Dict[str, Any]:
    from disease_atlas.access_gaps import access_gap_analysis
    return await access_gap_analysis(cancer_type=cancer_type)

@router.get("/infrastructure", summary="Healthcare infrastructure readiness")
async def infrastructure(
    country: Optional[str] = Query(None),
) -> Dict[str, Any]:
    from disease_atlas.access_gaps import infrastructure_readiness
    return await infrastructure_readiness(country=country)

@router.get("/patient-journey", summary="Patient journey mapping")
async def patient_journey_endpoint(
    country: str = Query("US"),
    cancer_type: str = Query("dlbcl"),
) -> Dict[str, Any]:
    from disease_atlas.access_gaps import patient_journey
    return await patient_journey(country=country, cancer_type=cancer_type)


# ═══════════════════════════════════════════════════════════════════════════════
# Epidemiological Trend Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/trends/incidence/{cancer_type}", summary="Incidence trends")
async def incidence_trends(
    cancer_type: str,
    projection_years: int = Query(10, ge=1, le=20),
) -> Dict[str, Any]:
    from disease_atlas.trends import incidence_trend
    return await incidence_trend(cancer_type, projection_years=projection_years)

@router.get("/trends/survival/{cancer_type}", summary="Survival trends")
async def survival_trends(cancer_type: str) -> Dict[str, Any]:
    from disease_atlas.trends import survival_trend
    return await survival_trend(cancer_type)

@router.get("/trends/burden/{cancer_type}", summary="Disease burden (DALYs)")
async def disease_burden_endpoint(
    cancer_type: str,
    country: str = Query("US"),
) -> Dict[str, Any]:
    from disease_atlas.trends import disease_burden
    return await disease_burden(cancer_type, country=country)

@router.get("/trends/treatment-adoption/{cancer_type}", summary="Treatment adoption trends")
async def treatment_adoption(cancer_type: str) -> Dict[str, Any]:
    from disease_atlas.trends import treatment_adoption_trends
    return await treatment_adoption_trends(cancer_type)
