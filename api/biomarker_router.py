"""
CARVanta Biomarker — API Router
===================================
REST API endpoints for Biomarker Analytics Engine.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.biomarker_router")

router = APIRouter(prefix="/api/v5/biomarker", tags=["Biomarker Analytics"])


class PanelRequest(BaseModel):
    panel_type: str = Field("pre_treatment", max_length=30)
    patient_risk: str = Field("moderate", max_length=20)


class MonitoringRequest(BaseModel):
    days: int = Field(30, ge=1, le=180)
    panel_type: str = Field("crs_panel", max_length=30)


@router.post("/panel", summary="Generate biomarker panel")
async def gen_panel(req: PanelRequest) -> Dict[str, Any]:
    """Generate comprehensive biomarker panel with clinical alerts."""
    from biomarker.analytics import generate_biomarker_panel
    return await generate_biomarker_panel(panel_type=req.panel_type, patient_risk=req.patient_risk)


@router.post("/monitoring", summary="Serial biomarker monitoring")
async def monitoring(req: MonitoringRequest) -> Dict[str, Any]:
    """Generate serial biomarker monitoring data (CRS kinetics)."""
    from biomarker.analytics import serial_monitoring
    return await serial_monitoring(days=req.days, panel_type=req.panel_type)


@router.get("/correlations", summary="Biomarker-outcome correlations")
async def correlations() -> Dict[str, Any]:
    """Analyze biomarker-outcome correlations."""
    from biomarker.analytics import biomarker_correlation
    return await biomarker_correlation()


@router.get("/definitions", summary="Biomarker reference ranges")
async def definitions() -> Dict[str, Any]:
    """List all biomarker definitions with reference ranges."""
    from biomarker.analytics import list_biomarker_definitions
    return await list_biomarker_definitions()
