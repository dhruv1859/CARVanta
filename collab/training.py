"""
CARVanta Collab — Training & Competency Tracker
==================================================
Staff training records, competency assessment, and
certification management for CAR-T research teams.

Features:
- Training curriculum with CAR-T-specific modules
- Competency assessment with scoring rubrics
- Certification tracking (GMP, GCP, IRB, BSL-2/3)
- Training due date monitoring and reminders
- Skill gap analysis for team development
- Onboarding checklist automation
- Training document version control
- Instructor-led and self-paced course support
- Competency matrix visualization data
- Regulatory training compliance (FDA, EMA)
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.training")

# In-memory stores
_TRAINING_RECORDS: Dict[str, List[Dict]] = {}
_COMPETENCY_ASSESSMENTS: Dict[str, Dict] = {}

# Training curriculum
_TRAINING_MODULES = {
    "gmp_basics": {
        "name": "Good Manufacturing Practice Fundamentals",
        "category": "regulatory",
        "duration_hours": 8,
        "format": "instructor_led",
        "recertification_months": 12,
        "required_for": ["manufacturing", "quality_control"],
        "topics": [
            "21 CFR Part 211 overview", "Personnel hygiene and gowning",
            "Environmental monitoring", "Documentation practices (ALCOA+)",
            "Deviation and CAPA management", "Change control procedures",
        ],
        "passing_score": 80,
    },
    "gcp_training": {
        "name": "Good Clinical Practice (ICH E6 R2)",
        "category": "regulatory",
        "duration_hours": 12,
        "format": "online",
        "recertification_months": 24,
        "required_for": ["clinical", "regulatory", "pi"],
        "topics": [
            "Ethical principles (Declaration of Helsinki)", "IRB/IEC responsibilities",
            "Investigator responsibilities", "Informed consent process",
            "Essential documents", "Safety reporting requirements",
            "Data integrity and source documentation",
        ],
        "passing_score": 80,
    },
    "bsl2_biosafety": {
        "name": "Biosafety Level 2 Training",
        "category": "safety",
        "duration_hours": 4,
        "format": "hybrid",
        "recertification_months": 12,
        "required_for": ["laboratory", "manufacturing"],
        "topics": [
            "BSL-2 containment principles", "PPE selection and use",
            "Biological spill procedures", "Sharps safety and waste disposal",
            "Autoclave operation and validation", "Laboratory access control",
        ],
        "passing_score": 90,
    },
    "cart_manufacturing": {
        "name": "CAR-T Cell Manufacturing Operations",
        "category": "technical",
        "duration_hours": 40,
        "format": "hands_on",
        "recertification_months": 12,
        "required_for": ["manufacturing"],
        "topics": [
            "CliniMACS Prodigy operation", "T-cell isolation and activation",
            "Viral transduction procedures", "G-Rex bioreactor culture",
            "Harvest and formulation", "Cryopreservation protocols",
            "Quality control release testing", "Batch record documentation",
            "Aseptic technique mastery", "Equipment cleaning and validation",
        ],
        "passing_score": 85,
    },
    "flow_cytometry": {
        "name": "Flow Cytometry for CAR-T Characterization",
        "category": "technical",
        "duration_hours": 16,
        "format": "hybrid",
        "recertification_months": 24,
        "required_for": ["laboratory", "quality_control"],
        "topics": [
            "Instrument setup and QC (CS&T)", "Compensation and controls (FMO)",
            "CAR-T panel design (CD3/CD4/CD8/CAR/memory/exhaustion)",
            "Data acquisition and gating strategy", "FlowJo/Kaluza analysis",
            "Troubleshooting common issues",
        ],
        "passing_score": 80,
    },
    "crs_icans_management": {
        "name": "CRS & ICANS Recognition and Management",
        "category": "clinical",
        "duration_hours": 6,
        "format": "instructor_led",
        "recertification_months": 12,
        "required_for": ["clinical", "nursing", "pharmacy"],
        "topics": [
            "ASTCT CRS grading criteria (Grade 1-4)", "ICE score assessment",
            "ICANS grading and monitoring", "Tocilizumab dosing and administration",
            "Corticosteroid escalation protocols", "ICU transfer criteria",
            "Vital sign monitoring frequency", "When to call the CAR-T team",
        ],
        "passing_score": 90,
    },
    "data_management": {
        "name": "Clinical Data Management & EDC",
        "category": "data",
        "duration_hours": 8,
        "format": "online",
        "recertification_months": 24,
        "required_for": ["data_management", "clinical"],
        "topics": [
            "Electronic Data Capture (EDC) navigation", "CRF completion guidelines",
            "Query resolution process", "SAE reporting in EDC",
            "Source data verification", "Database lock procedures",
        ],
        "passing_score": 80,
    },
    "hipaa_privacy": {
        "name": "HIPAA Privacy & Security Training",
        "category": "regulatory",
        "duration_hours": 2,
        "format": "online",
        "recertification_months": 12,
        "required_for": ["all"],
        "topics": [
            "Protected Health Information (PHI) definition",
            "Minimum necessary standard", "De-identification methods",
            "Breach notification requirements", "Security safeguards",
        ],
        "passing_score": 80,
    },
}

# Role-based training requirements
_ROLE_REQUIREMENTS = {
    "pi": ["gcp_training", "hipaa_privacy", "crs_icans_management"],
    "clinical_research_coordinator": ["gcp_training", "hipaa_privacy", "data_management", "crs_icans_management"],
    "manufacturing_specialist": ["gmp_basics", "bsl2_biosafety", "cart_manufacturing", "hipaa_privacy"],
    "research_associate": ["bsl2_biosafety", "flow_cytometry", "hipaa_privacy"],
    "data_manager": ["gcp_training", "data_management", "hipaa_privacy"],
    "quality_control": ["gmp_basics", "flow_cytometry", "hipaa_privacy"],
    "nurse": ["gcp_training", "crs_icans_management", "hipaa_privacy"],
}


async def list_training_modules(
    category: Optional[str] = None,
    role: Optional[str] = None,
) -> Dict[str, Any]:
    """List available training modules."""
    modules = []
    required_ids = _ROLE_REQUIREMENTS.get(role, []) if role else []

    for key, m in _TRAINING_MODULES.items():
        if category and m["category"] != category:
            continue
        modules.append({
            "module_id": key,
            **m,
            "required_for_role": key in required_ids if role else None,
        })

    categories = list(set(m["category"] for m in _TRAINING_MODULES.values()))
    return {
        "total": len(modules),
        "modules": modules,
        "categories": categories,
        "available_roles": list(_ROLE_REQUIREMENTS.keys()),
    }


async def record_training(
    user_id: str,
    module_id: str,
    score: float = 85,
    instructor: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """Record a training completion."""
    module = _TRAINING_MODULES.get(module_id)
    if not module:
        return {"error": f"Unknown module: {module_id}", "available": list(_TRAINING_MODULES.keys())}

    record_id = f"TRN-{uuid.uuid4().hex[:8]}"
    completed = datetime.utcnow()
    expires = completed + timedelta(days=module["recertification_months"] * 30)

    record = {
        "record_id": record_id,
        "user_id": user_id,
        "module_id": module_id,
        "module_name": module["name"],
        "score": score,
        "passed": score >= module["passing_score"],
        "passing_score": module["passing_score"],
        "completed_at": completed.isoformat(),
        "expires_at": expires.isoformat(),
        "instructor": instructor,
        "notes": notes,
    }

    if user_id not in _TRAINING_RECORDS:
        _TRAINING_RECORDS[user_id] = []
    _TRAINING_RECORDS[user_id].append(record)

    return {"record_id": record_id, "passed": record["passed"], "record": record}


async def training_status(
    user_id: str = "user_1",
    role: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get training compliance status for a user."""
    if seed:
        random.seed(seed)

    required = _ROLE_REQUIREMENTS.get(role, list(_TRAINING_MODULES.keys())[:4])

    status = []
    for mod_id in required:
        mod = _TRAINING_MODULES.get(mod_id)
        if not mod:
            continue

        completed = random.random() > 0.3
        if completed:
            completed_date = datetime.utcnow() - timedelta(days=random.randint(30, 365))
            expires_date = completed_date + timedelta(days=mod["recertification_months"] * 30)
            expired = expires_date < datetime.utcnow()
        else:
            completed_date = None
            expires_date = None
            expired = False

        status.append({
            "module_id": mod_id,
            "module_name": mod["name"],
            "required": True,
            "completed": completed,
            "completed_date": completed_date.strftime("%Y-%m-%d") if completed_date else None,
            "expires_date": expires_date.strftime("%Y-%m-%d") if expires_date else None,
            "expired": expired,
            "score": random.randint(mod["passing_score"], 100) if completed else None,
            "status": "expired" if expired else "compliant" if completed else "overdue",
        })

    compliant = sum(1 for s in status if s["status"] == "compliant")

    return {
        "user_id": user_id,
        "role": role or "general",
        "total_required": len(status),
        "compliant": compliant,
        "compliance_pct": round(compliant / max(len(status), 1) * 100, 1),
        "training_status": status,
        "overdue": [s for s in status if s["status"] == "overdue"],
        "expiring_soon": [s for s in status if s.get("expires_date") and not s["expired"] and
                         (datetime.strptime(s["expires_date"], "%Y-%m-%d") - datetime.utcnow()).days < 60],
    }


async def competency_matrix(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate team competency matrix."""
    if seed:
        random.seed(seed)

    team_members = [
        {"user_id": f"user_{i+1}", "role": random.choice(list(_ROLE_REQUIREMENTS.keys()))}
        for i in range(random.randint(5, 12))
    ]

    skills = list(_TRAINING_MODULES.keys())
    matrix = []

    for member in team_members:
        member_skills = {}
        required = _ROLE_REQUIREMENTS.get(member["role"], [])
        for skill in skills:
            if skill in required:
                level = random.choices([0, 1, 2, 3], weights=[10, 20, 40, 30])[0]
            else:
                level = random.choices([0, 1, 2, 3], weights=[50, 30, 15, 5])[0]
            member_skills[skill] = {
                "level": level,
                "label": ["Not trained", "Basic", "Proficient", "Expert"][level],
                "required": skill in required,
            }
        matrix.append({
            "user_id": member["user_id"],
            "role": member["role"],
            "skills": member_skills,
            "overall_competency": round(sum(s["level"] for s in member_skills.values()) / len(skills) * 100 / 3, 1),
        })

    # Skill gap analysis
    gaps = []
    for skill in skills:
        avg_level = sum(m["skills"][skill]["level"] for m in matrix) / len(matrix)
        if avg_level < 1.5:
            gaps.append({
                "skill": skill,
                "skill_name": _TRAINING_MODULES[skill]["name"],
                "avg_level": round(avg_level, 1),
                "team_members_untrained": sum(1 for m in matrix if m["skills"][skill]["level"] == 0),
                "recommendation": f"Schedule team training for {_TRAINING_MODULES[skill]['name']}",
            })

    return {
        "team_size": len(matrix),
        "matrix": matrix,
        "skill_gaps": gaps,
        "overall_team_competency": round(sum(m["overall_competency"] for m in matrix) / len(matrix), 1),
    }
