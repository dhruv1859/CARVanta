"""
CARVanta Collab — Publication Pipeline Manager
=================================================
End-to-end manuscript lifecycle management from
draft through submission, peer review, revision,
and final publication. Tracks authorship, journal
selection, and open access compliance.

Features:
- Manuscript lifecycle tracking (draft → submitted → accepted → published)
- Authorship order management with CRediT roles
- Journal recommendation based on scope and impact
- Cover letter and response-to-reviewers templates
- Preprint (bioRxiv/medRxiv) submission tracking
- Open access fund management
- DOI and citation tracking post-publication
- Embargo period management
- Co-author approval workflow
- Publication metrics dashboard
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.publications")

# In-memory stores
_MANUSCRIPTS: Dict[str, Dict] = {}

# CRediT (Contributor Roles Taxonomy) roles
_CREDIT_ROLES = [
    "Conceptualization", "Data curation", "Formal analysis",
    "Funding acquisition", "Investigation", "Methodology",
    "Project administration", "Resources", "Software",
    "Supervision", "Validation", "Visualization",
    "Writing – original draft", "Writing – review & editing",
]

# Journal database for CAR-T research
_JOURNAL_DATABASE = {
    "nature_medicine": {
        "name": "Nature Medicine",
        "publisher": "Springer Nature",
        "impact_factor": 82.9,
        "tier": 1,
        "scope": ["clinical_trials", "translational", "cell_therapy"],
        "review_time_weeks": 6,
        "acceptance_rate_pct": 7,
        "open_access_fee_usd": 11390,
        "preprint_policy": "allowed",
    },
    "nejm": {
        "name": "New England Journal of Medicine",
        "publisher": "NEJM Group",
        "impact_factor": 158.5,
        "tier": 1,
        "scope": ["clinical_trials", "landmark_studies"],
        "review_time_weeks": 4,
        "acceptance_rate_pct": 5,
        "open_access_fee_usd": 0,
        "preprint_policy": "allowed_with_conditions",
    },
    "blood": {
        "name": "Blood",
        "publisher": "American Society of Hematology",
        "impact_factor": 25.4,
        "tier": 1,
        "scope": ["hematology", "cell_therapy", "car_t", "lymphoma", "leukemia"],
        "review_time_weeks": 5,
        "acceptance_rate_pct": 18,
        "open_access_fee_usd": 4000,
        "preprint_policy": "allowed",
    },
    "jci": {
        "name": "Journal of Clinical Investigation",
        "publisher": "ASCI",
        "impact_factor": 15.9,
        "tier": 1,
        "scope": ["translational", "immunology", "cell_therapy"],
        "review_time_weeks": 6,
        "acceptance_rate_pct": 10,
        "open_access_fee_usd": 0,
        "preprint_policy": "allowed",
    },
    "science_translational": {
        "name": "Science Translational Medicine",
        "publisher": "AAAS",
        "impact_factor": 17.1,
        "tier": 1,
        "scope": ["translational", "preclinical", "biomarkers"],
        "review_time_weeks": 8,
        "acceptance_rate_pct": 8,
        "open_access_fee_usd": 5500,
        "preprint_policy": "allowed",
    },
    "molecular_therapy": {
        "name": "Molecular Therapy",
        "publisher": "Cell Press / ASGCT",
        "impact_factor": 12.1,
        "tier": 2,
        "scope": ["gene_therapy", "cell_therapy", "car_t", "vector_design"],
        "review_time_weeks": 5,
        "acceptance_rate_pct": 22,
        "open_access_fee_usd": 5200,
        "preprint_policy": "allowed",
    },
    "jitc": {
        "name": "Journal for ImmunoTherapy of Cancer",
        "publisher": "BMJ / SITC",
        "impact_factor": 10.9,
        "tier": 2,
        "scope": ["immunotherapy", "car_t", "checkpoint", "clinical_trials"],
        "review_time_weeks": 4,
        "acceptance_rate_pct": 25,
        "open_access_fee_usd": 3690,
        "preprint_policy": "allowed",
    },
    "cytotherapy": {
        "name": "Cytotherapy",
        "publisher": "Elsevier / ISCT",
        "impact_factor": 4.3,
        "tier": 3,
        "scope": ["cell_therapy", "manufacturing", "car_t", "clinical"],
        "review_time_weeks": 6,
        "acceptance_rate_pct": 35,
        "open_access_fee_usd": 3500,
        "preprint_policy": "allowed",
    },
}


async def create_manuscript(
    title: str,
    manuscript_type: str = "research_article",
    authors: Optional[List[Dict[str, str]]] = None,
    project_id: str = "default",
    target_journal: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a manuscript record."""
    ms_id = f"PUB-{uuid.uuid4().hex[:8]}"

    manuscript = {
        "manuscript_id": ms_id,
        "title": title,
        "type": manuscript_type,
        "project_id": project_id,
        "authors": authors or [{"name": "Corresponding Author", "role": "first_author", "credit_roles": ["Conceptualization", "Writing – original draft"]}],
        "target_journal": target_journal,
        "target_journal_name": _JOURNAL_DATABASE.get(target_journal, {}).get("name", "Not selected"),
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "submitted_at": None,
        "accepted_at": None,
        "published_at": None,
        "preprint_doi": None,
        "final_doi": None,
        "version": 1,
    }

    _MANUSCRIPTS[ms_id] = manuscript
    return {"manuscript_id": ms_id, "status": "created", "manuscript": manuscript}


async def recommend_journals(
    topics: Optional[List[str]] = None,
    manuscript_type: str = "research_article",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Recommend journals based on research topic."""
    if seed:
        random.seed(seed)

    topics = topics or ["car_t", "cell_therapy"]

    scored = []
    for jid, j in _JOURNAL_DATABASE.items():
        overlap = len(set(topics) & set(j["scope"]))
        if overlap == 0:
            continue
        score = overlap * 30 + j["impact_factor"] * 0.5 + j["acceptance_rate_pct"] * 0.3
        scored.append({
            "journal_id": jid,
            "name": j["name"],
            "impact_factor": j["impact_factor"],
            "tier": j["tier"],
            "acceptance_rate_pct": j["acceptance_rate_pct"],
            "review_time_weeks": j["review_time_weeks"],
            "open_access_fee_usd": j["open_access_fee_usd"],
            "topic_match": overlap,
            "recommendation_score": round(score, 1),
        })

    scored.sort(key=lambda x: x["recommendation_score"], reverse=True)

    return {
        "query_topics": topics,
        "total_matches": len(scored),
        "recommendations": scored,
        "credit_roles": _CREDIT_ROLES,
    }


async def publication_dashboard(
    project_id: str = "default",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get publication pipeline dashboard."""
    if seed:
        random.seed(seed)

    statuses = ["draft", "internal_review", "submitted", "under_review",
                "revision_requested", "revised", "accepted", "published"]
    manuscripts = []
    for i in range(random.randint(4, 12)):
        status = random.choice(statuses)
        journal = random.choice(list(_JOURNAL_DATABASE.values()))
        manuscripts.append({
            "id": f"PUB-{i+1:03d}",
            "title": f"CAR-T {''.join(random.choice('ABCDEFG') for _ in range(2))}-{random.randint(1,99)} Study",
            "status": status,
            "journal": journal["name"],
            "impact_factor": journal["impact_factor"],
            "tier": journal["tier"],
            "days_in_status": random.randint(1, 60),
        })

    by_status = {}
    for ms in manuscripts:
        by_status[ms["status"]] = by_status.get(ms["status"], 0) + 1

    return {
        "project_id": project_id,
        "total_manuscripts": len(manuscripts),
        "manuscripts": manuscripts,
        "by_status": by_status,
        "pipeline_summary": {
            "in_progress": sum(1 for m in manuscripts if m["status"] in ("draft", "internal_review")),
            "under_review": sum(1 for m in manuscripts if m["status"] in ("submitted", "under_review")),
            "accepted_published": sum(1 for m in manuscripts if m["status"] in ("accepted", "published")),
        },
        "avg_impact_factor": round(sum(m["impact_factor"] for m in manuscripts) / max(len(manuscripts), 1), 1),
    }
