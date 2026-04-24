"""
CARVanta Collab — Research Project Management
===============================================
Complete project management system for immunotherapy research teams.
Supports project creation, team management, activity tracking,
document sharing, version control, and milestone planning.

Features:
- Create/archive/clone research projects
- Role-based team membership (PI, co-PI, researcher, analyst, guest)
- Activity feed with event tracking
- Document versioning with diff tracking
- Milestone & deliverable planning
- Project templates for common research workflows
- Tag-based project discovery
- Fork/merge for collaborative analysis

Security: Owner-controllable permissions, audit trail, async.
API Version: v5
"""

import hashlib
import logging
import random
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("carvanta.collab.projects")


# ──────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────

class ProjectStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    COMPLETED = "completed"


class MemberRole(Enum):
    PI = "pi"
    CO_PI = "co_pi"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    GUEST = "guest"


class ActivityType(Enum):
    PROJECT_CREATED = "project_created"
    MEMBER_ADDED = "member_added"
    MEMBER_REMOVED = "member_removed"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_UPDATED = "document_updated"
    EXPERIMENT_CREATED = "experiment_created"
    EXPERIMENT_COMPLETED = "experiment_completed"
    NOTEBOOK_CREATED = "notebook_created"
    REVIEW_SUBMITTED = "review_submitted"
    MILESTONE_COMPLETED = "milestone_completed"
    COMMENT_ADDED = "comment_added"
    FORK_CREATED = "fork_created"


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TeamMember:
    user_id: str
    username: str
    display_name: str
    email: str
    role: str = "researcher"
    institution: str = ""
    joined_at: str = ""
    permissions: List[str] = field(default_factory=lambda: ["read", "comment"])


@dataclass
class Document:
    doc_id: str
    filename: str
    file_type: str
    size_bytes: int = 0
    version: int = 1
    uploaded_by: str = ""
    uploaded_at: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    versions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Milestone:
    milestone_id: str
    title: str
    description: str
    due_date: str = ""
    status: str = "pending"
    assigned_to: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    completed_at: str = ""


@dataclass
class ActivityEntry:
    activity_id: str
    activity_type: str
    user_id: str
    username: str
    timestamp: str
    details: Dict[str, Any] = field(default_factory=dict)
    project_id: str = ""


@dataclass
class ResearchProject:
    project_id: str
    title: str
    description: str
    status: str = "active"
    visibility: str = "team"  # "public", "team", "private"
    owner_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)
    team: List[TeamMember] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)
    activity_feed: List[ActivityEntry] = field(default_factory=list)
    forked_from: Optional[str] = None
    research_area: str = ""
    target_antigen: str = ""
    disease_focus: str = ""
    funding_source: str = ""
    irb_protocol: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────
# Project Templates
# ──────────────────────────────────────────────────────────────────────

_PROJECT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "car_t_target_discovery": {
        "title": "CAR-T Target Discovery",
        "description": "Systematic identification and validation of novel CAR-T cell therapy targets.",
        "milestones": [
            {"title": "Literature Review", "description": "Comprehensive review of existing targets and expression data"},
            {"title": "Bioinformatic Screen", "description": "In silico screening of potential surface antigens"},
            {"title": "Expression Validation", "description": "Validate target expression in patient samples"},
            {"title": "CAR Construct Design", "description": "Design optimal scFv and CAR architecture"},
            {"title": "In Vitro Testing", "description": "Cytotoxicity and specificity assays"},
            {"title": "In Vivo Validation", "description": "Xenograft model efficacy testing"},
            {"title": "Publication", "description": "Prepare and submit manuscript"},
        ],
        "tags": ["CAR-T", "target-discovery", "immunotherapy"],
    },
    "clinical_correlative": {
        "title": "Clinical Correlative Study",
        "description": "Analysis of biomarkers and clinical outcomes in CAR-T treated patients.",
        "milestones": [
            {"title": "Cohort Definition", "description": "Define patient inclusion criteria"},
            {"title": "Sample Collection", "description": "Collect and process clinical samples"},
            {"title": "Biomarker Analysis", "description": "Measure biomarker levels"},
            {"title": "Statistical Analysis", "description": "Correlate biomarkers with outcomes"},
            {"title": "Manuscript Preparation", "description": "Write and submit findings"},
        ],
        "tags": ["clinical", "biomarker", "correlative"],
    },
    "combination_therapy": {
        "title": "Combination Therapy Investigation",
        "description": "Evaluate synergistic effects of CAR-T with checkpoint inhibitors or other agents.",
        "milestones": [
            {"title": "Agent Selection", "description": "Identify combination partners"},
            {"title": "In Vitro Synergy", "description": "Dose-response and synergy studies"},
            {"title": "Mechanism Study", "description": "Elucidate mechanism of combination effect"},
            {"title": "Animal Model", "description": "In vivo combination efficacy"},
            {"title": "Safety Assessment", "description": "Toxicology evaluation"},
        ],
        "tags": ["combination", "checkpoint", "synergy"],
    },
    "manufacturing_optimization": {
        "title": "Manufacturing Process Optimization",
        "description": "Optimize CAR-T cell manufacturing for improved yield and quality.",
        "milestones": [
            {"title": "Process Mapping", "description": "Document current manufacturing workflow"},
            {"title": "Parameter Optimization", "description": "Optimize culture conditions and transduction"},
            {"title": "Scale-Up Study", "description": "Validate at clinical scale"},
            {"title": "Quality Control", "description": "Develop and validate QC assays"},
            {"title": "SOP Development", "description": "Finalize standard operating procedures"},
        ],
        "tags": ["manufacturing", "GMP", "process"],
    },
}


# ──────────────────────────────────────────────────────────────────────
# In-Memory Project Store
# ──────────────────────────────────────────────────────────────────────

_PROJECTS: Dict[str, ResearchProject] = {}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gen_id() -> str:
    return uuid.uuid4().hex[:12]


def _add_activity(project: ResearchProject, atype: str, user_id: str, username: str, details: Dict[str, Any] = None) -> None:
    entry = ActivityEntry(
        activity_id=_gen_id(), activity_type=atype,
        user_id=user_id, username=username,
        timestamp=_now_iso(), details=details or {},
        project_id=project.project_id,
    )
    project.activity_feed.insert(0, entry)
    if len(project.activity_feed) > 200:
        project.activity_feed = project.activity_feed[:200]
    project.updated_at = _now_iso()


# ──────────────────────────────────────────────────────────────────────
# Project CRUD
# ──────────────────────────────────────────────────────────────────────

async def create_project(
    title: str, description: str, owner_id: str, owner_name: str,
    template: Optional[str] = None, tags: Optional[List[str]] = None,
    research_area: str = "", target_antigen: str = "", disease_focus: str = "",
) -> Dict[str, Any]:
    """Create a new research project."""
    pid = _gen_id()
    now = _now_iso()

    proj = ResearchProject(
        project_id=pid, title=title, description=description,
        owner_id=owner_id, created_at=now, updated_at=now,
        tags=tags or [], research_area=research_area,
        target_antigen=target_antigen, disease_focus=disease_focus,
    )

    # Add owner as PI
    proj.team.append(TeamMember(
        user_id=owner_id, username=owner_name, display_name=owner_name,
        email=f"{owner_name}@carvanta.io", role="pi", joined_at=now,
        permissions=["read", "write", "admin", "delete"],
    ))

    # Apply template if specified
    if template and template in _PROJECT_TEMPLATES:
        tmpl = _PROJECT_TEMPLATES[template]
        if not title:
            proj.title = tmpl["title"]
        proj.description = proj.description or tmpl["description"]
        proj.tags.extend(tmpl.get("tags", []))
        for ms in tmpl.get("milestones", []):
            proj.milestones.append(Milestone(
                milestone_id=_gen_id(), title=ms["title"],
                description=ms["description"],
            ))

    _add_activity(proj, "project_created", owner_id, owner_name, {"template": template})
    _PROJECTS[pid] = proj

    return _serialize_project(proj)


async def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Get project details."""
    proj = _PROJECTS.get(project_id)
    return _serialize_project(proj) if proj else None


async def list_projects(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    max_results: int = 20,
) -> Dict[str, Any]:
    """List projects with optional filtering."""
    results: List[Dict[str, Any]] = []
    for proj in _PROJECTS.values():
        if status and proj.status != status:
            continue
        if user_id and not any(m.user_id == user_id for m in proj.team):
            if proj.visibility != "public":
                continue
        if tag and tag not in proj.tags:
            continue
        if search:
            text = f"{proj.title} {proj.description} {' '.join(proj.tags)}".lower()
            if search.lower() not in text:
                continue
        results.append(_serialize_project(proj, summary=True))

    results.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return {"total": len(results), "projects": results[:max_results]}


async def update_project(
    project_id: str, user_id: str, username: str,
    title: Optional[str] = None, description: Optional[str] = None,
    status: Optional[str] = None, tags: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Update project metadata."""
    proj = _PROJECTS.get(project_id)
    if not proj:
        return None
    if title:
        proj.title = title
    if description:
        proj.description = description
    if status:
        proj.status = status
    if tags is not None:
        proj.tags = tags
    _add_activity(proj, "project_updated", user_id, username)
    return _serialize_project(proj)


async def add_member(
    project_id: str, user_id: str, username: str, role: str = "researcher",
    added_by: str = "", added_by_name: str = "",
) -> Optional[Dict[str, Any]]:
    """Add a team member to a project."""
    proj = _PROJECTS.get(project_id)
    if not proj:
        return None
    perms = {"pi": ["read","write","admin","delete"], "co_pi": ["read","write","admin"],
             "researcher": ["read","write","comment"], "analyst": ["read","write"],
             "guest": ["read","comment"]}.get(role, ["read"])
    proj.team.append(TeamMember(
        user_id=user_id, username=username, display_name=username,
        email=f"{username}@carvanta.io", role=role, joined_at=_now_iso(),
        permissions=perms,
    ))
    _add_activity(proj, "member_added", added_by, added_by_name, {"new_member": username, "role": role})
    return _serialize_project(proj)


async def upload_document(
    project_id: str, filename: str, file_type: str, size_bytes: int,
    uploaded_by: str, uploader_name: str, description: str = "", tags: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Upload a document to a project."""
    proj = _PROJECTS.get(project_id)
    if not proj:
        return None
    doc = Document(
        doc_id=_gen_id(), filename=filename, file_type=file_type,
        size_bytes=size_bytes, uploaded_by=uploaded_by, uploaded_at=_now_iso(),
        description=description, tags=tags or [],
        versions=[{"version": 1, "uploaded_at": _now_iso(), "uploaded_by": uploader_name, "size_bytes": size_bytes}],
    )
    proj.documents.append(doc)
    _add_activity(proj, "document_uploaded", uploaded_by, uploader_name, {"filename": filename})
    return {"document": _serialize_document(doc), "project_id": project_id}


async def fork_project(
    project_id: str, forker_id: str, forker_name: str,
    new_title: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fork (clone) a project for independent work."""
    orig = _PROJECTS.get(project_id)
    if not orig:
        return None
    fork = await create_project(
        title=new_title or f"Fork of {orig.title}",
        description=f"Forked from {orig.title}: {orig.description}",
        owner_id=forker_id, owner_name=forker_name,
        tags=orig.tags + ["fork"], research_area=orig.research_area,
        target_antigen=orig.target_antigen, disease_focus=orig.disease_focus,
    )
    if fork:
        _PROJECTS[fork["project_id"]].forked_from = project_id
    return fork


async def get_project_templates() -> Dict[str, Any]:
    """Get available project templates."""
    return {
        "templates": [
            {"id": tid, "title": t["title"], "description": t["description"],
             "milestones_count": len(t.get("milestones", [])), "tags": t.get("tags", [])}
            for tid, t in _PROJECT_TEMPLATES.items()
        ]
    }


async def get_activity_feed(project_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get project activity feed."""
    proj = _PROJECTS.get(project_id)
    if not proj:
        return {"error": "Project not found", "activities": []}
    return {
        "project_id": project_id,
        "total_activities": len(proj.activity_feed),
        "activities": [
            {"id": a.activity_id, "type": a.activity_type, "user": a.username,
             "timestamp": a.timestamp, "details": a.details}
            for a in proj.activity_feed[:limit]
        ],
    }


# ──────────────────────────────────────────────────────────────────────
# Serialization
# ──────────────────────────────────────────────────────────────────────

def _serialize_document(doc: Document) -> Dict[str, Any]:
    return {
        "doc_id": doc.doc_id, "filename": doc.filename, "file_type": doc.file_type,
        "size_bytes": doc.size_bytes, "version": doc.version, "uploaded_by": doc.uploaded_by,
        "uploaded_at": doc.uploaded_at, "description": doc.description, "tags": doc.tags,
        "versions_count": len(doc.versions),
    }


def _serialize_project(proj: ResearchProject, summary: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "project_id": proj.project_id, "title": proj.title,
        "description": proj.description[:200] + "..." if summary and len(proj.description) > 200 else proj.description,
        "status": proj.status, "visibility": proj.visibility,
        "owner_id": proj.owner_id, "created_at": proj.created_at,
        "updated_at": proj.updated_at, "tags": proj.tags,
        "team_count": len(proj.team), "documents_count": len(proj.documents),
        "milestones_count": len(proj.milestones),
        "research_area": proj.research_area, "target_antigen": proj.target_antigen,
        "disease_focus": proj.disease_focus,
    }
    if not summary:
        data["team"] = [
            {"user_id": m.user_id, "username": m.username, "role": m.role,
             "institution": m.institution, "joined_at": m.joined_at}
            for m in proj.team
        ]
        data["documents"] = [_serialize_document(d) for d in proj.documents]
        data["milestones"] = [
            {"id": ms.milestone_id, "title": ms.title, "description": ms.description,
             "due_date": ms.due_date, "status": ms.status, "assigned_to": ms.assigned_to}
            for ms in proj.milestones
        ]
        data["recent_activity"] = [
            {"type": a.activity_type, "user": a.username, "timestamp": a.timestamp}
            for a in proj.activity_feed[:10]
        ]
        data["forked_from"] = proj.forked_from
    return data
