"""
CARVanta Regulatory — API Router
===================================
REST API for Module 11: Regulatory & Compliance.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.regulatory_router")
router = APIRouter(prefix="/api/v5/regulatory", tags=["Regulatory Compliance"])


class DeviationReq(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    severity: str = Field("major", max_length=10)
    opened_by: str = Field("qa_user", max_length=50)
    affected_lots: List[str] = Field(default_factory=list)

class CAPAReq(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    capa_type: str = Field("corrective", max_length=15)
    priority: str = Field("high", max_length=10)
    initiated_by: str = Field("qa_user", max_length=50)
    deviation_id: Optional[str] = None

class LotReq(BaseModel):
    product: str = Field(..., max_length=100)
    batch_size: str = Field("", max_length=50)

class TrainingReq(BaseModel):
    user_id: str = Field(..., max_length=32)
    user_name: str = Field(..., max_length=50)
    training_type: str = Field("SOP", max_length=30)
    course_name: str = Field(..., max_length=200)


@router.get("/dashboard", summary="Compliance dashboard")
async def compliance_dashboard() -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_compliance_dashboard
    return await get_compliance_dashboard()

@router.post("/deviations", summary="Create deviation")
async def create_deviation(req: DeviationReq) -> Dict[str, Any]:
    from regulatory.gxp_compliance import create_deviation
    return await create_deviation(req.title, req.description, req.severity, req.opened_by, req.affected_lots)

@router.get("/deviations", summary="List deviations")
async def list_deviations(status: Optional[str] = None, severity: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import list_deviations
    return await list_deviations(status=status, severity=severity)

@router.post("/capas", summary="Create CAPA")
async def create_capa(req: CAPAReq) -> Dict[str, Any]:
    from regulatory.gxp_compliance import create_capa
    return await create_capa(req.title, req.description, req.capa_type, req.priority, req.initiated_by, req.deviation_id)

@router.get("/capas", summary="List CAPAs")
async def list_capas(status: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import list_capas
    return await list_capas(status=status)

@router.post("/lots", summary="Create lot record")
async def create_lot(req: LotReq) -> Dict[str, Any]:
    from regulatory.gxp_compliance import create_lot_record
    return await create_lot_record(req.product, req.batch_size)

@router.get("/lots/{lot_id}", summary="Get lot genealogy")
async def lot_genealogy(lot_id: str) -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_lot_genealogy
    result = await get_lot_genealogy(lot_id)
    if not result: raise HTTPException(404, "Lot not found")
    return result

@router.get("/audit-trail", summary="Get audit trail")
async def audit_trail(entity_type: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_audit_trail
    return await get_audit_trail(entity_type=entity_type)

@router.get("/ich-guidelines", summary="ICH guidelines")
async def ich_guidelines(applicability: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_ich_guidelines
    return await get_ich_guidelines(applicability=applicability)

@router.get("/regulatory-bodies", summary="Regulatory requirements")
async def regulatory_bodies(body: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_regulatory_requirements
    return await get_regulatory_requirements(body=body)

@router.post("/training", summary="Add training record")
async def add_training(req: TrainingReq) -> Dict[str, Any]:
    from regulatory.gxp_compliance import add_training_record
    return await add_training_record(req.user_id, req.user_name, req.training_type, req.course_name)

@router.get("/training", summary="Training matrix")
async def training_matrix(user_id: Optional[str] = None) -> Dict[str, Any]:
    from regulatory.gxp_compliance import get_training_matrix
    return await get_training_matrix(user_id=user_id)
