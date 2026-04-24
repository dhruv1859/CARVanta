"""
CARVanta Health Economics — API Router
========================================
Complete REST API for health economics analysis of CAR-T therapies.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.health_econ_router")
router = APIRouter(prefix="/api/v5/health-econ", tags=["Health Economics"])


# ── Request Models ──────────────────────────────────────────────────────────

class CostReq(BaseModel):
    product: str = Field("tisagenlecleucel", max_length=50)
    target: str = Field("cd19", max_length=10)
    country: str = Field("US", max_length=20)
    crs_severity: str = Field("moderate", max_length=10)

class ICERReq(BaseModel):
    product: str = Field("tisagenlecleucel", max_length=50)
    target: str = Field("cd19", max_length=10)
    comparator: str = Field("standard_chemo_dlbcl", max_length=30)
    time_horizon_years: int = Field(5, ge=1, le=20)
    country: str = Field("US", max_length=20)

class BudgetReq(BaseModel):
    product: str = Field("tisagenlecleucel", max_length=50)
    target: str = Field("cd19", max_length=10)
    eligible_patients: int = Field(500, ge=10, le=50000)
    adoption_rate_year1: float = Field(0.15, ge=0, le=1)
    country: str = Field("US", max_length=20)

class MarkovReq(BaseModel):
    treatment: str = Field("cart", max_length=10)
    time_horizon_months: int = Field(60, ge=6, le=240)
    orr: float = Field(0.82, ge=0, le=1)

class ManufacturingReq(BaseModel):
    platform: str = Field("lentiviral", max_length=30)
    facility: str = Field("centralized_large", max_length=30)
    country: str = Field("US", max_length=10)
    include_clinical: bool = Field(True)

class OutcomesContractReq(BaseModel):
    product: str = Field("tisagenlecleucel", max_length=50)
    n_patients: int = Field(100, ge=10, le=10000)
    response_threshold_months: int = Field(1, ge=1, le=12)

class ValuePriceReq(BaseModel):
    qaly_gain: float = Field(3.5, ge=0.1, le=20)
    wtp_low: float = Field(50000, ge=0)
    wtp_high: float = Field(200000, ge=0)
    comparator_cost: float = Field(150000, ge=0)

class BreakEvenReq(BaseModel):
    cart_cost: float = Field(475000, ge=0)
    soc_annual_cost: float = Field(45000, ge=0)
    cart_os_years: float = Field(5.0, ge=0.5, le=30)
    soc_os_years: float = Field(1.5, ge=0.5, le=30)
    discount_rate: float = Field(0.03, ge=0, le=0.2)

class LearningCurveReq(BaseModel):
    initial_cost: float = Field(373000, ge=0)
    learning_rate: float = Field(0.85, ge=0.5, le=1.0)
    target_patients: int = Field(5000, ge=10, le=100000)


# ═══════════════════════════════════════════════════════════════════════════════
# Core Cost Analysis Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/treatment-cost", summary="Calculate treatment cost")
async def treatment_cost(req: CostReq) -> Dict[str, Any]:
    from health_econ.cost_analyzer import calculate_treatment_cost
    return await calculate_treatment_cost(req.product, req.target, req.country, crs_severity=req.crs_severity)

@router.post("/icer", summary="Calculate ICER")
async def icer(req: ICERReq) -> Dict[str, Any]:
    from health_econ.cost_analyzer import calculate_icer
    return await calculate_icer(req.product, req.target, req.comparator, req.time_horizon_years, country=req.country)

@router.post("/sensitivity", summary="Sensitivity analysis")
async def sensitivity(product: str = "tisagenlecleucel", target: str = "cd19") -> Dict[str, Any]:
    from health_econ.cost_analyzer import sensitivity_analysis
    return await sensitivity_analysis(product, target)


# ═══════════════════════════════════════════════════════════════════════════════
# Budget Impact Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/budget-impact", summary="Budget impact analysis")
async def budget_impact(req: BudgetReq) -> Dict[str, Any]:
    from health_econ.budget_impact import budget_impact_analysis
    return await budget_impact_analysis(
        req.product, req.target, req.eligible_patients,
        req.adoption_rate_year1, country=req.country,
    )

@router.post("/outcomes-contract", summary="Outcomes-based contract simulation")
async def outcomes_contract(req: OutcomesContractReq) -> Dict[str, Any]:
    from health_econ.budget_impact import outcomes_based_contract
    return await outcomes_based_contract(
        req.product, n_patients=req.n_patients,
        response_threshold_months=req.response_threshold_months,
    )

@router.post("/value-price-corridor", summary="Value-based price corridor")
async def value_price(req: ValuePriceReq) -> Dict[str, Any]:
    from health_econ.budget_impact import value_based_price_corridor
    return await value_based_price_corridor(
        qaly_gain=req.qaly_gain, wtp_low=req.wtp_low,
        wtp_high=req.wtp_high, comparator_cost=req.comparator_cost,
    )

@router.post("/break-even", summary="Break-even analysis")
async def break_even(req: BreakEvenReq) -> Dict[str, Any]:
    from health_econ.budget_impact import break_even_analysis
    return await break_even_analysis(
        cart_cost=req.cart_cost, soc_annual_cost=req.soc_annual_cost,
        cart_os_years=req.cart_os_years, soc_os_years=req.soc_os_years,
        discount_rate=req.discount_rate,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Manufacturing Cost Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/manufacturing-cost", summary="Manufacturing cost estimate")
async def manufacturing_cost(req: ManufacturingReq) -> Dict[str, Any]:
    from health_econ.manufacturing_cost import estimate_manufacturing_cost
    return await estimate_manufacturing_cost(
        platform=req.platform, facility=req.facility,
        country=req.country, include_clinical=req.include_clinical,
    )

@router.get("/compare-platforms", summary="Compare technology platforms")
async def compare_platforms(country: str = "US") -> Dict[str, Any]:
    from health_econ.manufacturing_cost import compare_platforms
    return await compare_platforms(country=country)

@router.get("/compare-regions", summary="Compare regional costs")
async def compare_regions(platform: str = "lentiviral") -> Dict[str, Any]:
    from health_econ.manufacturing_cost import compare_regions
    return await compare_regions(platform=platform)

@router.post("/learning-curve", summary="Learning curve projection")
async def learning_curve(req: LearningCurveReq) -> Dict[str, Any]:
    from health_econ.manufacturing_cost import learning_curve_projection
    return await learning_curve_projection(
        initial_cost=req.initial_cost,
        learning_rate=req.learning_rate,
        target_patients=req.target_patients,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# QALY / Markov Model Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/markov-model", summary="Run QALY Markov model")
async def markov_model(req: MarkovReq) -> Dict[str, Any]:
    from health_econ.qaly_model import run_markov_model
    return await run_markov_model(req.treatment, time_horizon_months=req.time_horizon_months, orr=req.orr)

@router.post("/compare-treatments", summary="Compare CAR-T vs SOC")
async def compare_treatments() -> Dict[str, Any]:
    from health_econ.qaly_model import compare_treatments
    return await compare_treatments()

@router.get("/utility-values", summary="Health state utilities")
async def utility_values() -> Dict[str, Any]:
    from health_econ.qaly_model import utility_analysis
    return await utility_analysis()


# ═══════════════════════════════════════════════════════════════════════════════
# Market Access Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/hta-landscape", summary="HTA decision landscape")
async def hta_landscape(product: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
    from health_econ.market_access import get_hta_landscape
    return await get_hta_landscape(product=product, country=country)

@router.get("/market-access/{product}", summary="Market access analysis")
async def market_access(product: str) -> Dict[str, Any]:
    from health_econ.market_access import analyze_market_access
    return await analyze_market_access(product)

@router.get("/reimbursement-codes", summary="Reimbursement codes")
async def reimbursement_codes() -> Dict[str, Any]:
    from health_econ.market_access import get_reimbursement_codes
    return await get_reimbursement_codes()
