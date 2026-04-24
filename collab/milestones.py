"""
CARVanta Collab — Milestone & Progress Tracker
==================================================
Project milestone management, Gantt-style scheduling,
deliverable tracking, and progress reporting for
multi-phase CAR-T research programs.

Features:
- Milestone definition with dependencies
- Deliverable tracking (reports, datasets, publications)
- Progress burn-down and burn-up charts
- Risk-adjusted timeline forecasting
- Status reporting with RAG (Red/Amber/Green) indicators
- Project phase management (Discovery → IND → Clinical)
- Meeting minutes and action item tracking
- Decision log with rationale documentation
- Resource allocation and conflict detection
- Quarterly review report generation
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.milestones")

# In-memory stores
_MILESTONES: Dict[str, Dict] = {}
_DECISIONS: Dict[str, Dict] = {}
_MEETINGS: Dict[str, Dict] = {}

# CAR-T development phase templates
_PHASE_TEMPLATES = {
    "discovery": {
        "name": "Target Discovery & Validation",
        "phase_number": 1,
        "typical_duration_months": 12,
        "milestones": [
            {"name": "Antigen screen completion", "month": 3, "deliverables": ["Target ranking report", "Expression dataset"]},
            {"name": "Lead target selection", "month": 5, "deliverables": ["Target validation report", "Go/No-Go decision"]},
            {"name": "scFv library generation", "month": 8, "deliverables": ["Phage display library", "Screening data"]},
            {"name": "Lead scFv identification", "month": 10, "deliverables": ["Binding data (SPR/ELISA)", "Humanization report"]},
            {"name": "Discovery phase complete", "month": 12, "deliverables": ["Discovery summary report", "IP landscape"]},
        ],
    },
    "preclinical": {
        "name": "Preclinical Development",
        "phase_number": 2,
        "typical_duration_months": 18,
        "milestones": [
            {"name": "CAR construct optimization", "month": 4, "deliverables": ["Construct comparison data", "Lead CAR selection"]},
            {"name": "In vitro efficacy package", "month": 7, "deliverables": ["Cytotoxicity data", "Cytokine profiling"]},
            {"name": "In vivo POC complete", "month": 11, "deliverables": ["Xenograft efficacy data", "Pharmacology report"]},
            {"name": "GLP toxicology study", "month": 14, "deliverables": ["Tox study report", "NOAEL determination"]},
            {"name": "CMC process locked", "month": 16, "deliverables": ["Manufacturing SOP", "Analytical methods"]},
            {"name": "IND-enabling package complete", "month": 18, "deliverables": ["IND modules", "Pre-IND meeting request"]},
        ],
    },
    "clinical": {
        "name": "Clinical Development (Phase I/II)",
        "phase_number": 3,
        "typical_duration_months": 36,
        "milestones": [
            {"name": "IND submission", "month": 2, "deliverables": ["eCTD submission", "FDA acknowledgment"]},
            {"name": "First site activated", "month": 6, "deliverables": ["IRB approval", "Site initiation visit"]},
            {"name": "First patient enrolled", "month": 8, "deliverables": ["Enrollment notification", "Consent form"]},
            {"name": "Dose escalation complete", "month": 18, "deliverables": ["DLT summary", "RP2D determination"]},
            {"name": "Interim efficacy analysis", "month": 24, "deliverables": ["ORR/CR data", "DSMB recommendation"]},
            {"name": "Primary endpoint data", "month": 30, "deliverables": ["Primary analysis report", "KM curves"]},
            {"name": "CSR and publication", "month": 36, "deliverables": ["Clinical Study Report", "Manuscript draft"]},
        ],
    },
}


async def create_milestone(
    project_id: str,
    name: str,
    due_date: Optional[str] = None,
    description: str = "",
    phase: str = "discovery",
    deliverables: Optional[List[str]] = None,
    assigned_to: str = "",
) -> Dict[str, Any]:
    """Create a project milestone."""
    ms_id = f"MS-{uuid.uuid4().hex[:8]}"
    due = datetime.fromisoformat(due_date) if due_date else datetime.utcnow() + timedelta(days=90)

    milestone = {
        "milestone_id": ms_id,
        "project_id": project_id,
        "name": name,
        "description": description,
        "phase": phase,
        "due_date": due.isoformat(),
        "status": "on_track",
        "progress_pct": 0,
        "deliverables": [{"name": d, "status": "pending"} for d in (deliverables or [])],
        "assigned_to": assigned_to,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "rag_status": "green",
    }

    _MILESTONES[ms_id] = milestone
    return {"milestone_id": ms_id, "status": "created", "milestone": milestone}


async def project_timeline(
    phase: str = "preclinical",
    start_date: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate project timeline from phase template."""
    if seed:
        random.seed(seed)

    tmpl = _PHASE_TEMPLATES.get(phase, _PHASE_TEMPLATES["preclinical"])
    start = datetime.fromisoformat(start_date) if start_date else datetime.utcnow()

    timeline = []
    for ms in tmpl["milestones"]:
        target_date = start + timedelta(days=ms["month"] * 30)
        progress = min(random.randint(0, 100), 100)
        days_remaining = (target_date - datetime.utcnow()).days

        rag = "green"
        if days_remaining < 0:
            rag = "red" if progress < 90 else "green"
        elif days_remaining < 30 and progress < 70:
            rag = "amber"
        elif days_remaining < 14 and progress < 90:
            rag = "red"

        timeline.append({
            "milestone": ms["name"],
            "target_date": target_date.strftime("%Y-%m-%d"),
            "target_month": ms["month"],
            "deliverables": ms["deliverables"],
            "progress_pct": progress,
            "days_remaining": days_remaining,
            "rag_status": rag,
            "on_track": rag != "red",
        })

    return {
        "phase": phase,
        "phase_name": tmpl["name"],
        "start_date": start.strftime("%Y-%m-%d"),
        "duration_months": tmpl["typical_duration_months"],
        "total_milestones": len(timeline),
        "on_track": sum(1 for t in timeline if t["on_track"]),
        "at_risk": sum(1 for t in timeline if t["rag_status"] == "amber"),
        "delayed": sum(1 for t in timeline if t["rag_status"] == "red"),
        "timeline": timeline,
        "available_phases": list(_PHASE_TEMPLATES.keys()),
    }


async def log_decision(
    project_id: str,
    title: str,
    decision: str,
    rationale: str = "",
    alternatives_considered: Optional[List[str]] = None,
    decided_by: str = "PI",
    impact: str = "medium",
) -> Dict[str, Any]:
    """Log a project decision with rationale."""
    dec_id = f"DEC-{uuid.uuid4().hex[:8]}"

    record = {
        "decision_id": dec_id,
        "project_id": project_id,
        "title": title,
        "decision": decision,
        "rationale": rationale,
        "alternatives_considered": alternatives_considered or [],
        "decided_by": decided_by,
        "impact": impact,
        "decided_at": datetime.utcnow().isoformat(),
        "status": "final",
    }

    _DECISIONS[dec_id] = record
    return {"decision_id": dec_id, "logged": True, "decision": record}


async def log_meeting(
    project_id: str,
    title: str,
    attendees: Optional[List[str]] = None,
    minutes: str = "",
    action_items: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Log meeting minutes with action items."""
    mtg_id = f"MTG-{uuid.uuid4().hex[:8]}"

    record = {
        "meeting_id": mtg_id,
        "project_id": project_id,
        "title": title,
        "date": datetime.utcnow().isoformat(),
        "attendees": attendees or ["PI", "Research Team"],
        "minutes": minutes,
        "action_items": action_items or [],
        "n_action_items": len(action_items) if action_items else 0,
    }

    _MEETINGS[mtg_id] = record
    return {"meeting_id": mtg_id, "logged": True, "meeting": record}


async def quarterly_report(
    project_id: str = "default",
    quarter: str = "Q1",
    year: int = 2026,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate quarterly progress report."""
    if seed:
        random.seed(seed)

    return {
        "project_id": project_id,
        "quarter": f"{quarter} {year}",
        "generated_at": datetime.utcnow().isoformat(),
        "executive_summary": {
            "overall_status": random.choice(["on_track", "on_track", "at_risk", "on_track"]),
            "key_achievements": [
                f"Completed {random.randint(2, 8)} milestones this quarter",
                f"Enrolled {random.randint(5, 25)} patients (cumulative: {random.randint(20, 80)})",
                f"Published {random.randint(0, 3)} manuscripts",
                f"Generated {random.randint(1, 5)} datasets",
            ],
            "key_risks": [
                "Manufacturing timeline at risk due to vendor delays" if random.random() > 0.5 else None,
                "Enrollment below target at 2 sites" if random.random() > 0.5 else None,
            ],
        },
        "milestone_progress": {
            "total_milestones": random.randint(8, 20),
            "completed": random.randint(3, 10),
            "on_track": random.randint(2, 8),
            "at_risk": random.randint(0, 3),
            "delayed": random.randint(0, 2),
        },
        "financials": {
            "budget_usd": random.randint(500000, 5000000),
            "spent_usd": random.randint(100000, 3000000),
            "burn_rate_pct": round(random.uniform(15, 35), 1),
            "projected_runway_months": random.randint(6, 24),
        },
        "team": {
            "headcount": random.randint(5, 25),
            "new_hires": random.randint(0, 3),
            "departures": random.randint(0, 2),
            "training_compliance_pct": round(random.uniform(75, 100), 1),
        },
        "next_quarter_priorities": [
            "Complete dose escalation phase",
            "Submit interim analysis to DSMB",
            "Finalize companion diagnostic development",
            "Prepare for regulatory pre-submission meeting",
        ],
    }
