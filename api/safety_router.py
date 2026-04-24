"""
CARVanta Safety — API Router
================================
REST API for Pharmacovigilance Engine.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.safety_router")

router = APIRouter(prefix="/api/v5/safety-pv", tags=["Pharmacovigilance"])


class ICSRRequest(BaseModel):
    product: str = Field("axi-cel", max_length=30)
    patient_age: int = Field(55, ge=1, le=120)
    ae_type: Optional[str] = Field(None, max_length=30)


class DispropRequest(BaseModel):
    product: str = Field("axi-cel", max_length=30)
    n_reports: int = Field(5000, ge=100, le=100000)


class RiskBenefitRequest(BaseModel):
    product: str = Field("axi-cel", max_length=30)
    cancer_type: str = Field("DLBCL", max_length=50)


@router.post("/icsr", summary="Generate Individual Case Safety Report")
async def gen_icsr(req: ICSRRequest) -> Dict[str, Any]:
    """Generate a simulated ICSR report."""
    from safety.pharmacovigilance import generate_icsr
    return await generate_icsr(product=req.product, patient_age=req.patient_age, ae_type=req.ae_type)


@router.post("/disproportionality", summary="Disproportionality analysis")
async def disprop(req: DispropRequest) -> Dict[str, Any]:
    """Run PRR/ROR/BCPNN signal detection analysis."""
    from safety.pharmacovigilance import disproportionality_analysis
    return await disproportionality_analysis(product=req.product, n_reports=req.n_reports)


@router.post("/risk-benefit", summary="Risk-benefit analysis")
async def risk_benefit(req: RiskBenefitRequest) -> Dict[str, Any]:
    """Compute risk-benefit score for a CAR-T product."""
    from safety.pharmacovigilance import risk_benefit_analysis
    return await risk_benefit_analysis(product=req.product, cancer_type=req.cancer_type)


@router.get("/rems/{product}", summary="REMS monitoring data")
async def rems(product: str, n_patients: int = 200) -> Dict[str, Any]:
    """Get REMS program monitoring data."""
    from safety.pharmacovigilance import rems_monitoring
    return await rems_monitoring(product=product, n_patients=n_patients)


@router.get("/ae-dictionary", summary="Adverse event dictionary")
async def ae_dict() -> Dict[str, Any]:
    """Get MedDRA-coded adverse event dictionary."""
    from safety.pharmacovigilance import get_ae_dictionary
    return await get_ae_dictionary()
