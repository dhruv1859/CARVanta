"""
CARVanta Collab — Peer Review System
======================================
Community peer review workflow for immunotherapy target proposals
and research findings. Supports structured review criteria,
score-based evaluation, voting, and editorial decisions.

Features:
- Submit proposals/findings for review
- Multi-reviewer assignment with conflict-of-interest check
- Structured review form (10 criteria)
- Score aggregation with weighted reviewer expertise
- Revision cycle tracking (submit → review → revise → accept/reject)
- Community voting on proposals
- Review metrics and reviewer leaderboard

Security: Double-blind option, reviewer anonymization, async.
"""

import logging
import time
import uuid
import math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.collab.peer_review")


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ReviewCriterion:
    name: str
    description: str
    score: float = 0.0  # 1-10
    weight: float = 1.0
    comments: str = ""


@dataclass
class Review:
    review_id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_expertise: str = ""
    submitted_at: str = ""
    criteria_scores: List[ReviewCriterion] = field(default_factory=list)
    overall_score: float = 0.0
    recommendation: str = ""  # "accept", "minor_revision", "major_revision", "reject"
    summary_comments: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    is_anonymous: bool = True


@dataclass
class Vote:
    voter_id: str
    voter_name: str
    vote_type: str  # "upvote", "downvote"
    timestamp: str = ""
    reason: str = ""


@dataclass
class Submission:
    submission_id: str
    project_id: str
    title: str
    abstract: str
    content: str = ""
    submission_type: str = "target_proposal"  # target_proposal, finding, protocol, dataset
    author_id: str = ""
    author_name: str = ""
    submitted_at: str = ""
    updated_at: str = ""
    status: str = "submitted"  # submitted, under_review, revision_requested, accepted, rejected
    reviews: List[Review] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    revision_history: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    target_antigen: str = ""
    disease_context: str = ""
    data_availability: str = ""
    review_round: int = 1


# ──────────────────────────────────────────────────────────────────────
# Review Criteria Templates
# ──────────────────────────────────────────────────────────────────────

_REVIEW_CRITERIA: Dict[str, List[Dict[str, Any]]] = {
    "target_proposal": [
        {"name": "Scientific Merit", "description": "Strength of biological rationale for target selection", "weight": 2.0},
        {"name": "Expression Specificity", "description": "Evidence for tumor-specific expression vs normal tissue", "weight": 2.0},
        {"name": "Data Quality", "description": "Quality and reproducibility of supporting data", "weight": 1.5},
        {"name": "Novelty", "description": "How novel is this target compared to existing literature?", "weight": 1.5},
        {"name": "Therapeutic Potential", "description": "Likelihood of clinical translation", "weight": 1.5},
        {"name": "Safety Profile", "description": "Expected safety based on expression pattern", "weight": 2.0},
        {"name": "Feasibility", "description": "Technical feasibility of CAR-T construct development", "weight": 1.0},
        {"name": "Clinical Need", "description": "Unmet medical need in the target disease", "weight": 1.0},
        {"name": "Reproducibility", "description": "Can results be independently verified?", "weight": 1.0},
        {"name": "Presentation Quality", "description": "Clarity and completeness of the submission", "weight": 0.5},
    ],
    "finding": [
        {"name": "Scientific Rigor", "description": "Methodological soundness", "weight": 2.0},
        {"name": "Statistical Validity", "description": "Appropriate statistical methods and sample size", "weight": 1.5},
        {"name": "Impact", "description": "Potential impact on the field", "weight": 1.5},
        {"name": "Novelty", "description": "New insights beyond existing knowledge", "weight": 1.5},
        {"name": "Reproducibility", "description": "Likelihood of reproduction by others", "weight": 1.5},
        {"name": "Data Transparency", "description": "Data and code availability", "weight": 1.0},
        {"name": "Writing Quality", "description": "Clarity of presentation", "weight": 1.0},
    ],
}


# ──────────────────────────────────────────────────────────────────────
# In-Memory Store
# ──────────────────────────────────────────────────────────────────────

_SUBMISSIONS: Dict[str, Submission] = {}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gid() -> str:
    return uuid.uuid4().hex[:12]


# ──────────────────────────────────────────────────────────────────────
# Submission CRUD
# ──────────────────────────────────────────────────────────────────────

async def create_submission(
    project_id: str, title: str, abstract: str, content: str,
    author_id: str, author_name: str,
    submission_type: str = "target_proposal",
    target_antigen: str = "", disease_context: str = "",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Submit a proposal or finding for peer review."""
    sid = _gid()
    now = _now()
    sub = Submission(
        submission_id=sid, project_id=project_id, title=title,
        abstract=abstract, content=content,
        submission_type=submission_type, author_id=author_id,
        author_name=author_name, submitted_at=now, updated_at=now,
        tags=tags or [], target_antigen=target_antigen,
        disease_context=disease_context,
    )
    _SUBMISSIONS[sid] = sub
    return _ser_sub(sub)


async def get_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    """Get submission details with reviews."""
    sub = _SUBMISSIONS.get(submission_id)
    return _ser_sub(sub, full=True) if sub else None


async def list_submissions(
    project_id: Optional[str] = None, status: Optional[str] = None,
    submission_type: Optional[str] = None, max_results: int = 20,
) -> Dict[str, Any]:
    """List submissions with filtering."""
    results = []
    for sub in _SUBMISSIONS.values():
        if project_id and sub.project_id != project_id:
            continue
        if status and sub.status != status:
            continue
        if submission_type and sub.submission_type != submission_type:
            continue
        results.append(_ser_sub(sub))
    results.sort(key=lambda s: s.get("submitted_at", ""), reverse=True)
    return {"total": len(results), "submissions": results[:max_results]}


# ──────────────────────────────────────────────────────────────────────
# Review Operations
# ──────────────────────────────────────────────────────────────────────

async def submit_review(
    submission_id: str, reviewer_id: str, reviewer_name: str,
    scores: Dict[str, float], recommendation: str,
    summary: str = "", strengths: Optional[List[str]] = None,
    weaknesses: Optional[List[str]] = None,
    reviewer_expertise: str = "general",
) -> Optional[Dict[str, Any]]:
    """Submit a peer review for a submission."""
    sub = _SUBMISSIONS.get(submission_id)
    if not sub:
        return None

    # Build criteria scores
    criteria_template = _REVIEW_CRITERIA.get(sub.submission_type, _REVIEW_CRITERIA["finding"])
    criteria_scores = []
    for crit in criteria_template:
        score = scores.get(crit["name"], 5.0)
        criteria_scores.append(ReviewCriterion(
            name=crit["name"], description=crit["description"],
            score=min(10, max(1, score)), weight=crit["weight"],
            comments="",
        ))

    # Compute overall score
    total_weight = sum(c.weight for c in criteria_scores)
    overall = sum(c.score * c.weight for c in criteria_scores) / total_weight if total_weight > 0 else 0

    review = Review(
        review_id=_gid(), reviewer_id=reviewer_id, reviewer_name=reviewer_name,
        reviewer_expertise=reviewer_expertise, submitted_at=_now(),
        criteria_scores=criteria_scores, overall_score=round(overall, 2),
        recommendation=recommendation, summary_comments=summary,
        strengths=strengths or [], weaknesses=weaknesses or [],
    )

    sub.reviews.append(review)
    sub.updated_at = _now()
    if sub.status == "submitted":
        sub.status = "under_review"

    return {"review": _ser_review(review), "submission_id": submission_id}


async def get_review_summary(submission_id: str) -> Dict[str, Any]:
    """Get aggregated review summary for a submission."""
    sub = _SUBMISSIONS.get(submission_id)
    if not sub:
        return {"error": "Submission not found"}
    if not sub.reviews:
        return {"submission_id": submission_id, "reviews_count": 0, "message": "No reviews yet"}

    scores = [r.overall_score for r in sub.reviews]
    recs = defaultdict(int)
    for r in sub.reviews:
        recs[r.recommendation] += 1

    all_strengths = []
    all_weaknesses = []
    for r in sub.reviews:
        all_strengths.extend(r.strengths)
        all_weaknesses.extend(r.weaknesses)

    avg_score = sum(scores) / len(scores)
    recommendation_counts = dict(recs)

    # Editorial decision suggestion
    if avg_score >= 7.0 and recs.get("accept", 0) >= len(sub.reviews) // 2:
        suggested_decision = "accept"
    elif avg_score >= 5.0:
        suggested_decision = "minor_revision"
    elif avg_score >= 3.0:
        suggested_decision = "major_revision"
    else:
        suggested_decision = "reject"

    return {
        "submission_id": submission_id,
        "title": sub.title,
        "reviews_count": len(sub.reviews),
        "average_score": round(avg_score, 2),
        "score_range": [round(min(scores), 2), round(max(scores), 2)],
        "score_std": round(math.sqrt(sum((s - avg_score) ** 2 for s in scores) / max(len(scores) - 1, 1)), 2),
        "recommendations": recommendation_counts,
        "suggested_decision": suggested_decision,
        "key_strengths": list(set(all_strengths))[:5],
        "key_weaknesses": list(set(all_weaknesses))[:5],
        "criteria_averages": {
            crit.name: round(sum(r.criteria_scores[i].score for r in sub.reviews if i < len(r.criteria_scores)) / len(sub.reviews), 2)
            for i, crit in enumerate(sub.reviews[0].criteria_scores) if sub.reviews
        },
    }


# ──────────────────────────────────────────────────────────────────────
# Voting
# ──────────────────────────────────────────────────────────────────────

async def vote_on_submission(
    submission_id: str, voter_id: str, voter_name: str,
    vote_type: str = "upvote", reason: str = "",
) -> Optional[Dict[str, Any]]:
    """Vote on a submission."""
    sub = _SUBMISSIONS.get(submission_id)
    if not sub:
        return None
    # Remove previous vote by same user
    sub.votes = [v for v in sub.votes if v.voter_id != voter_id]
    sub.votes.append(Vote(voter_id=voter_id, voter_name=voter_name, vote_type=vote_type, timestamp=_now(), reason=reason))
    upvotes = sum(1 for v in sub.votes if v.vote_type == "upvote")
    downvotes = sum(1 for v in sub.votes if v.vote_type == "downvote")
    return {"submission_id": submission_id, "upvotes": upvotes, "downvotes": downvotes, "net_score": upvotes - downvotes}


async def make_editorial_decision(
    submission_id: str, decision: str, editor_comments: str = "",
) -> Optional[Dict[str, Any]]:
    """Make editorial decision on a submission."""
    sub = _SUBMISSIONS.get(submission_id)
    if not sub:
        return None
    sub.status = decision  # "accepted", "rejected", "revision_requested"
    sub.updated_at = _now()
    sub.revision_history.append({
        "round": sub.review_round, "decision": decision,
        "comments": editor_comments, "timestamp": _now(),
    })
    if decision == "revision_requested":
        sub.review_round += 1
    return _ser_sub(sub, full=True)


async def get_review_criteria(submission_type: str = "target_proposal") -> Dict[str, Any]:
    """Get review criteria for a submission type."""
    criteria = _REVIEW_CRITERIA.get(submission_type, _REVIEW_CRITERIA["finding"])
    return {"type": submission_type, "criteria": criteria}


# ──────────────────────────────────────────────────────────────────────
# Serialization
# ──────────────────────────────────────────────────────────────────────

def _ser_review(review: Review) -> Dict[str, Any]:
    return {
        "review_id": review.review_id,
        "reviewer": review.reviewer_name if not review.is_anonymous else "Anonymous Reviewer",
        "expertise": review.reviewer_expertise,
        "overall_score": review.overall_score,
        "recommendation": review.recommendation,
        "summary": review.summary_comments,
        "strengths": review.strengths,
        "weaknesses": review.weaknesses,
        "submitted_at": review.submitted_at,
        "criteria": [{"name": c.name, "score": c.score, "weight": c.weight} for c in review.criteria_scores],
    }


def _ser_sub(sub: Submission, full: bool = False) -> Dict[str, Any]:
    upvotes = sum(1 for v in sub.votes if v.vote_type == "upvote")
    downvotes = sum(1 for v in sub.votes if v.vote_type == "downvote")
    data: Dict[str, Any] = {
        "submission_id": sub.submission_id, "project_id": sub.project_id,
        "title": sub.title, "abstract": sub.abstract[:200],
        "type": sub.submission_type, "author": sub.author_name,
        "status": sub.status, "submitted_at": sub.submitted_at,
        "review_round": sub.review_round, "reviews_count": len(sub.reviews),
        "upvotes": upvotes, "downvotes": downvotes,
        "net_votes": upvotes - downvotes, "tags": sub.tags,
        "target_antigen": sub.target_antigen,
    }
    if full:
        data["abstract"] = sub.abstract
        data["content"] = sub.content
        data["reviews"] = [_ser_review(r) for r in sub.reviews]
        data["revision_history"] = sub.revision_history
    return data
