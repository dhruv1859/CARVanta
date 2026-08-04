"""
CARVanta Copilot — API Router
================================
REST API endpoints for the AI Research Copilot (Module 9).
Provides chat, paper search, literature review, experiment
protocol, and voice interaction endpoints.

Security: Rate-limited, input-sanitized, API v5.
"""

import re
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.copilot_router")

router = APIRouter(prefix="/api/v5/copilot", tags=["AI Research Copilot"])


# ──────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: Optional[str] = Field(None, max_length=20)


class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    max_results: int = Field(10, ge=1, le=50)
    year_min: Optional[int] = Field(None, ge=1990, le=2030)
    year_max: Optional[int] = Field(None, ge=1990, le=2030)
    categories: Optional[List[str]] = None
    targets: Optional[List[str]] = None


class ReviewRequest(BaseModel):
    target: str = Field(..., max_length=32)
    include_preclinical: bool = True
    include_economics: bool = False


class ProtocolRequest(BaseModel):
    target: str = Field(..., max_length=32)
    description: str = Field("", max_length=500)


class VoiceSessionRequest(BaseModel):
    language: str = Field("en-US", max_length=10)
    speech_rate: float = Field(1.0, ge=0.5, le=2.0)
    noise_filter: bool = True


class SynthesisRequest(BaseModel):
    text: str = Field(..., max_length=5000)
    language: str = Field("en-US", max_length=10)
    speech_rate: float = Field(1.0, ge=0.5, le=2.0)
    session_id: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────
# Chat Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/chat", summary="Send a message to the AI Research Copilot")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """
    Send a research question and get an AI-generated answer with sources.
    Maintains multi-turn conversation context per session.
    """
    from copilot.chat_handler import handle_message
    return await handle_message(request.session_id, request.message)


@router.get("/chat/history/{session_id}", summary="Get chat history for a session")
async def chat_history(session_id: str) -> Dict[str, Any]:
    """Retrieve chat history for a session."""
    from copilot.chat_handler import get_chat_history
    messages = await get_chat_history(session_id)
    return {"session_id": session_id, "messages": messages, "total": len(messages)}


@router.get("/chat/stats", summary="Get chat session statistics")
async def chat_stats() -> Dict[str, Any]:
    """Get aggregate chat session statistics."""
    from copilot.chat_handler import get_session_stats
    return await get_session_stats()


# ──────────────────────────────────────────────────────────────────────
# Paper Search Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/search", summary="Search immunotherapy research papers")
async def search_papers(request: SearchRequest) -> Dict[str, Any]:
    """
    Search 500+ indexed immunotherapy papers using TF-IDF relevance scoring.
    Filter by year, category, and target antigen.
    """
    from copilot.paper_index import search_papers as do_search
    results = await do_search(
        query=request.query,
        max_results=request.max_results,
        year_min=request.year_min,
        year_max=request.year_max,
        categories=request.categories,
        targets=request.targets,
    )
    return {
        "query": request.query,
        "total_results": len(results),
        "papers": [
            {
                "rank": r.rank,
                "pmid": r.paper.pmid,
                "title": r.paper.title,
                "authors": r.paper.authors[:3],
                "journal": r.paper.journal,
                "year": r.paper.year,
                "citations": r.paper.citations,
                "impact_factor": r.paper.impact_factor,
                "categories": r.paper.categories,
                "targets": r.paper.targets,
                "relevance": r.match_score,
                "matched_terms": r.matched_terms,
            }
            for r in results
        ],
    }


@router.get("/search/stats", summary="Get paper index statistics")
async def paper_stats() -> Dict[str, Any]:
    """Get statistics about the indexed paper database."""
    from copilot.paper_index import get_index_stats
    return await get_index_stats()


# ──────────────────────────────────────────────────────────────────────
# Literature Review Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/review", summary="Generate an automated literature review")
async def generate_review(request: ReviewRequest) -> Dict[str, Any]:
    """
    Generate a structured literature review for a CAR-T target.
    Includes executive summary, clinical evidence, safety, manufacturing, and gaps.
    """
    from copilot.lit_reviewer import generate_full_review
    return await generate_full_review(
        target=request.target,
        include_preclinical=request.include_preclinical,
        include_economics=request.include_economics,
    )


@router.get("/review/compare", summary="Generate comparative review across targets")
async def compare_review(
    targets: List[str] = Query(..., max_length=10),
) -> Dict[str, Any]:
    """Compare literature reviews across multiple CAR-T targets."""
    from copilot.lit_reviewer import compare_targets_review
    return await compare_targets_review(targets)


# ──────────────────────────────────────────────────────────────────────
# Experiment Protocol Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/protocol", summary="Suggest experiment protocol")
async def suggest_protocol(request: ProtocolRequest) -> Dict[str, Any]:
    """
    Suggest an experiment protocol for CAR-T research.
    Includes step-by-step procedures, reagents, controls, and timelines.
    """
    from copilot.experiment_designer import suggest_protocol as do_suggest
    return await do_suggest(request.target, request.description)


@router.get("/protocol/templates", summary="List available protocol templates")
async def list_protocols() -> Dict[str, Any]:
    """List all available experiment protocol templates."""
    from copilot.experiment_designer import list_available_protocols
    return {"templates": await list_available_protocols()}


# ──────────────────────────────────────────────────────────────────────
# Voice Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.post("/voice/session", summary="Create a voice interaction session")
async def create_voice_session(request: VoiceSessionRequest) -> Dict[str, Any]:
    """Create a new voice interaction session with language and speed settings."""
    from copilot.voice_handler import create_voice_session as do_create
    session = await do_create(request.language, request.speech_rate, request.noise_filter)
    return {
        "session_id": session.session_id,
        "language": session.language,
        "speech_rate": session.speech_rate,
        "noise_filter": session.noise_filter,
    }


@router.post("/voice/synthesize", summary="Convert text to speech")
async def synthesize_speech(request: SynthesisRequest) -> Dict[str, Any]:
    """Convert text to speech audio (returns metadata; production returns audio stream)."""
    from copilot.voice_handler import synthesize_speech as do_synth
    result = await do_synth(request.text, request.language, request.speech_rate, session_id=request.session_id)
    return {
        "synthesis_id": result.synthesis_id,
        "text_preview": result.text,
        "duration_seconds": result.duration_seconds,
        "format": result.audio_format,
        "sample_rate": result.sample_rate,
        "voice_id": result.voice_id,
        "language": result.language,
    }


@router.get("/voice/voices", summary="List available voice profiles")
async def list_voices() -> Dict[str, Any]:
    """List all available TTS voice profiles."""
    from copilot.voice_handler import get_available_voices
    return {"voices": await get_available_voices()}


@router.get("/voice/languages", summary="List supported voice languages")
async def list_languages() -> Dict[str, Any]:
    """List supported voice languages."""
    from copilot.voice_handler import get_supported_languages
    return {"languages": await get_supported_languages()}


# ──────────────────────────────────────────────────────────────────────
# Treatment Protocol Endpoints
# ──────────────────────────────────────────────────────────────────────

class TreatmentProtocolRequest(BaseModel):
    cancer_type: str = Field("DLBCL", max_length=50)
    product: str = Field("axi-cel", max_length=30)
    patient_age: int = Field(55, ge=1, le=120)
    ecog: int = Field(1, ge=0, le=4)
    tumor_burden: str = Field("moderate", max_length=20)
    prior_lines: int = Field(3, ge=0, le=20)


@router.post("/treatment-protocol", summary="Generate treatment protocol")
async def gen_treatment_protocol(req: TreatmentProtocolRequest) -> Dict[str, Any]:
    """Generate comprehensive CAR-T treatment protocol with CRS/ICANS management."""
    from copilot.protocol_generator import generate_treatment_protocol
    return await generate_treatment_protocol(
        cancer_type=req.cancer_type, product=req.product,
        patient_age=req.patient_age, ecog=req.ecog,
        tumor_burden=req.tumor_burden, prior_lines=req.prior_lines,
    )


@router.get("/crs-algorithm", summary="CRS management algorithm")
async def crs_algo(grade: int = 0) -> Dict[str, Any]:
    """Get CRS management algorithm (grade 0 = all grades)."""
    from copilot.protocol_generator import get_crs_algorithm
    return await get_crs_algorithm(grade)


@router.get("/icans-algorithm", summary="ICANS management algorithm")
async def icans_algo(grade: int = 0) -> Dict[str, Any]:
    """Get ICANS management algorithm."""
    from copilot.protocol_generator import get_icans_algorithm
    return await get_icans_algorithm(grade)


@router.get("/lymphodepletion-regimens", summary="Lymphodepletion options")
async def ld_regimens() -> Dict[str, Any]:
    """Get available lymphodepletion regimens."""
    from copilot.protocol_generator import get_lymphodepletion_options
    return await get_lymphodepletion_options()


# ──────────────────────────────────────────────────────────────────────
# Data Visualization Endpoints
# ──────────────────────────────────────────────────────────────────────

@router.get("/chart/survival", summary="Survival curve data")
async def survival_chart(product: str = "axi-cel", n: int = 50) -> Dict[str, Any]:
    """Generate Kaplan-Meier survival curve data."""
    from copilot.data_visualizer import generate_survival_curve
    return await generate_survival_curve(n_patients=n, product=product)


@router.get("/chart/waterfall", summary="Waterfall response data")
async def waterfall_chart(product: str = "axi-cel", n: int = 30) -> Dict[str, Any]:
    """Generate waterfall plot data for treatment response."""
    from copilot.data_visualizer import generate_waterfall_plot
    return await generate_waterfall_plot(n_patients=n, product=product)


@router.get("/chart/spider", summary="Spider plot tumor dynamics")
async def spider_chart(n: int = 10) -> Dict[str, Any]:
    """Generate spider plot data."""
    from copilot.data_visualizer import generate_spider_plot
    return await generate_spider_plot(n_patients=n)


@router.get("/chart/forest", summary="Forest plot subgroup analysis")
async def forest_chart(product: str = "axi-cel") -> Dict[str, Any]:
    """Generate forest plot for subgroup analysis."""
    from copilot.data_visualizer import generate_forest_plot
    return await generate_forest_plot(product=product)


@router.get("/chart/heatmap", summary="Biomarker correlation heatmap")
async def heatmap_chart() -> Dict[str, Any]:
    """Generate biomarker correlation heatmap."""
    from copilot.data_visualizer import generate_heatmap
    return await generate_heatmap()


@router.get("/chart/volcano", summary="Volcano plot differential expression")
async def volcano_chart(n: int = 200) -> Dict[str, Any]:
    """Generate volcano plot for differential gene expression."""
    from copilot.data_visualizer import generate_volcano_plot
    return await generate_volcano_plot(n_genes=n)


class VoiceQueryRequest(BaseModel):
    transcript: str = Field(..., max_length=1000)

@router.post("/voice-query", summary="Voice Clinical Copilot for ICU emergencies")
async def voice_query(request: VoiceQueryRequest) -> Dict[str, Any]:
    """Process voice transcription from ICU doctors and return clinical protocols."""
    transcript = request.transcript.lower()
    
    # Hackathon MVP: Pattern match keywords for CRS shock
    if any(word in transcript for word in ["fever", "temperature", "blood pressure", "dropping", "shock"]):
        return {
            "status": "emergency",
            "clinical_insight": "Grade 3 CRS detected based on fever and hypotensive shock indicators. Immediate intervention required.",
            "protocol": "Administer 8mg/kg of Tocilizumab immediately. Monitor via Digital Twin.",
            "action_trigger": "run_digital_twin_crs_sim",
            "suggested_dose": "8mg/kg"
        }
    
    return {
         "status": "standard",
         "clinical_insight": "Patient vitals received. Monitoring CAR-T expansion.",
         "protocol": "Continue standard 4-hour vitals check.",
         "action_trigger": "none",
         "suggested_dose": "N/A"
    }
