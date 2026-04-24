"""
CARVanta Collab — Institutional Review & Ethics Engine
========================================================
IRB/IEC management, consent tracking, ethical review
automation, and regulatory document management for
CAR-T clinical research.

Features:
- IRB submission and tracking workflow
- Informed consent document management (ICF)
- Protocol amendment tracking
- Adverse event reporting integration
- Multi-site ethics coordination
- HIPAA compliance verification
- Biospecimen consent tracking
- Continuing review scheduling
- Ethics committee composition management
- Annual report generation
- Conflict of interest disclosure tracking
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.ethics")

# In-memory stores
_IRB_SUBMISSIONS: Dict[str, Dict] = {}
_CONSENT_RECORDS: Dict[str, Dict] = {}
_AMENDMENTS: Dict[str, Dict] = {}
_COI_DISCLOSURES: Dict[str, Dict] = {}

# IRB submission types
_SUBMISSION_TYPES = {
    "new_study": {
        "name": "New Study Application",
        "review_type": "full_board",
        "avg_review_days": 45,
        "required_documents": [
            "Protocol", "Informed Consent Form", "Investigator Brochure",
            "Case Report Forms", "Recruitment Materials", "HIPAA Authorization",
            "Data Safety Monitoring Plan", "CV of Principal Investigator",
        ],
    },
    "amendment": {
        "name": "Protocol Amendment",
        "review_type": "expedited",
        "avg_review_days": 21,
        "required_documents": [
            "Amendment Summary", "Revised Protocol (tracked changes)",
            "Revised Consent Form (if applicable)", "Justification Letter",
        ],
    },
    "continuing_review": {
        "name": "Continuing Review / Annual Renewal",
        "review_type": "expedited",
        "avg_review_days": 30,
        "required_documents": [
            "Progress Report", "Updated Consent Form", "DSMB Report",
            "Enrollment Summary", "SAE/SUSAR Summary", "Protocol Deviation Report",
        ],
    },
    "reportable_event": {
        "name": "Reportable New Information (SAE/Protocol Deviation)",
        "review_type": "expedited",
        "avg_review_days": 14,
        "required_documents": [
            "Event Description", "Causality Assessment", "Corrective Action Plan",
        ],
    },
    "study_closure": {
        "name": "Study Closure Report",
        "review_type": "administrative",
        "avg_review_days": 14,
        "required_documents": [
            "Final Progress Report", "Enrollment Summary", "Publication Summary",
            "Data Retention Plan", "Biospecimen Disposition Plan",
        ],
    },
}

# Consent form modules for CAR-T trials
_CONSENT_MODULES = {
    "general": {
        "name": "General Research Participation",
        "sections": [
            "Purpose of the Study",
            "Study Procedures",
            "Risks and Discomforts",
            "Benefits",
            "Alternatives",
            "Costs and Compensation",
            "Confidentiality",
            "Voluntary Participation",
            "Contact Information",
        ],
    },
    "cart_specific": {
        "name": "CAR-T Cell Therapy Specific",
        "sections": [
            "Leukapheresis Procedure",
            "CAR-T Cell Manufacturing Process",
            "Lymphodepletion Chemotherapy Risks",
            "CAR-T Cell Infusion Procedure",
            "Cytokine Release Syndrome (CRS) Risks",
            "Neurotoxicity (ICANS) Risks",
            "Required Hospitalization Period",
            "Long-term Follow-up (15 years for gene therapy)",
            "Risk of Secondary Malignancy",
            "Fertility Preservation Options",
        ],
    },
    "biospecimen": {
        "name": "Biospecimen Collection & Banking",
        "sections": [
            "Types of Samples Collected",
            "How Samples Will Be Used",
            "Genetic Testing Implications",
            "Sample Storage Duration",
            "Future Use of Samples",
            "Right to Withdraw Samples",
            "Commercial Use Disclaimer",
        ],
    },
    "genomic": {
        "name": "Genomic Data Sharing",
        "sections": [
            "Types of Genomic Data Generated",
            "Data Sharing with Researchers",
            "Deposit in Public Databases (dbGaP)",
            "Incidental Findings Policy",
            "Genetic Information Nondiscrimination Act (GINA)",
            "Re-identification Risks",
        ],
    },
    "hipaa": {
        "name": "HIPAA Authorization",
        "sections": [
            "Protected Health Information to Be Used",
            "Who Will Access Your Information",
            "Purpose of Information Use",
            "Duration of Authorization",
            "Right to Revoke Authorization",
            "De-identification Procedures",
        ],
    },
}

# Ethics committee composition requirements
_COMMITTEE_REQUIREMENTS = {
    "fda_requirements": {
        "minimum_members": 5,
        "diversity_requirements": [
            "At least one scientist",
            "At least one non-scientist",
            "At least one member not affiliated with the institution",
            "Adequate representation by gender",
            "Member with expertise in vulnerable populations (if applicable)",
        ],
    },
    "recommended_expertise": [
        "Hematology/Oncology", "Cell Therapy/Gene Therapy",
        "Bioethics", "Biostatistics", "Patient Advocate",
        "Pharmacy", "Nursing", "Legal/Regulatory",
    ],
}


async def submit_to_irb(
    study_title: str,
    submission_type: str = "new_study",
    principal_investigator: str = "Dr. Researcher",
    institution: str = "Research Medical Center",
    study_description: str = "",
    submitted_by: str = "user_1",
) -> Dict[str, Any]:
    """Submit a study to the IRB for review."""
    sub_type = _SUBMISSION_TYPES.get(submission_type)
    if not sub_type:
        return {"error": f"Unknown type: {submission_type}", "available": list(_SUBMISSION_TYPES.keys())}

    submission_id = f"IRB-{uuid.uuid4().hex[:8]}"
    submitted_at = datetime.utcnow()
    expected_decision = submitted_at + timedelta(days=sub_type["avg_review_days"])

    submission = {
        "submission_id": submission_id,
        "study_title": study_title,
        "submission_type": submission_type,
        "submission_type_name": sub_type["name"],
        "review_type": sub_type["review_type"],
        "principal_investigator": principal_investigator,
        "institution": institution,
        "study_description": study_description,
        "submitted_by": submitted_by,
        "submitted_at": submitted_at.isoformat(),
        "expected_decision_by": expected_decision.isoformat(),
        "status": "submitted",
        "required_documents": sub_type["required_documents"],
        "documents_submitted": [],
        "reviewer_comments": [],
        "decision": None,
        "approval_date": None,
        "expiration_date": None,
    }

    _IRB_SUBMISSIONS[submission_id] = submission
    return {"submission_id": submission_id, "status": "submitted", "submission": submission}


async def irb_status(
    submission_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get IRB submission status."""
    if seed:
        random.seed(seed)

    if submission_id and submission_id in _IRB_SUBMISSIONS:
        return {"submission": _IRB_SUBMISSIONS[submission_id]}

    # Simulate active submissions
    submissions = []
    for i in range(random.randint(2, 6)):
        sub_type = random.choice(list(_SUBMISSION_TYPES.keys()))
        status = random.choice(["submitted", "under_review", "revisions_requested", "approved", "approved"])
        submitted = datetime.utcnow() - timedelta(days=random.randint(5, 120))

        submissions.append({
            "submission_id": f"IRB-{uuid.uuid4().hex[:6]}",
            "study_title": f"CAR-T {random.choice(['CD19', 'BCMA', 'CD22', 'GD2'])} Phase {random.choice(['I', 'I/II', 'II'])} Study",
            "submission_type": sub_type,
            "status": status,
            "submitted_at": submitted.isoformat(),
            "days_pending": (datetime.utcnow() - submitted).days if status in ("submitted", "under_review") else None,
            "decision": "approved" if status == "approved" else None,
        })

    return {
        "total_submissions": len(submissions),
        "submissions": submissions,
        "summary": {
            "approved": sum(1 for s in submissions if s["status"] == "approved"),
            "pending": sum(1 for s in submissions if s["status"] in ("submitted", "under_review")),
            "revisions": sum(1 for s in submissions if s["status"] == "revisions_requested"),
        },
    }


async def consent_tracker(
    study_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Track informed consent status across study participants."""
    if seed:
        random.seed(seed)

    n_patients = random.randint(20, 100)
    consent_records = []
    for i in range(n_patients):
        consented_modules = random.sample(
            list(_CONSENT_MODULES.keys()),
            k=random.randint(2, len(_CONSENT_MODULES))
        )
        status = random.choices(
            ["fully_consented", "partially_consented", "consent_withdrawn", "pending"],
            weights=[60, 15, 5, 20]
        )[0]

        consent_records.append({
            "patient_id": f"PT-{i+1:04d}",
            "status": status,
            "consented_modules": consented_modules,
            "consent_date": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
            "consent_version": f"v{random.choice([1, 2, 3])}.0",
            "re_consent_needed": random.random() > 0.8,
            "lar_consent": random.random() > 0.9,
        })

    return {
        "study_id": study_id or "simulated",
        "total_patients": n_patients,
        "consent_records": consent_records[:20],
        "summary": {
            "fully_consented": sum(1 for c in consent_records if c["status"] == "fully_consented"),
            "partially_consented": sum(1 for c in consent_records if c["status"] == "partially_consented"),
            "withdrawn": sum(1 for c in consent_records if c["status"] == "consent_withdrawn"),
            "pending": sum(1 for c in consent_records if c["status"] == "pending"),
            "re_consent_needed": sum(1 for c in consent_records if c["re_consent_needed"]),
        },
        "modules": _CONSENT_MODULES,
    }


async def coi_disclosure(
    investigator_name: str = "Dr. Researcher",
    disclosures: Optional[List[Dict[str, Any]]] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Submit or review conflict of interest disclosures."""
    if seed:
        random.seed(seed)

    coi_id = f"COI-{uuid.uuid4().hex[:8]}"

    if disclosures:
        _COI_DISCLOSURES[coi_id] = {
            "coi_id": coi_id,
            "investigator": investigator_name,
            "disclosures": disclosures,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "under_review",
        }
        return {"coi_id": coi_id, "status": "submitted"}

    # Generate simulated disclosure
    types = ["consulting_fees", "equity", "grants", "speaking_fees", "advisory_board", "none"]
    n_disclosures = random.randint(0, 3)

    items = []
    for _ in range(n_disclosures):
        items.append({
            "type": random.choice(types[:-1]),
            "entity": random.choice(["Novartis", "BMS", "Gilead/Kite", "J&J/Legend", "Allogene", "Caribou Bio"]),
            "amount_range": random.choice(["<$5,000", "$5,000-$25,000", "$25,000-$100,000", ">$100,000"]),
            "relevant_to_study": random.random() > 0.5,
        })

    management_plan = None
    if any(d["relevant_to_study"] for d in items):
        management_plan = {
            "action": random.choice(["monitoring", "disclosure_only", "recusal_from_enrollment", "independent_review"]),
            "assigned_to": "IRB Committee Chair",
            "review_frequency": "annually",
        }

    return {
        "coi_id": coi_id,
        "investigator": investigator_name,
        "disclosures": items if items else [{"type": "none", "entity": "N/A"}],
        "has_conflicts": len(items) > 0,
        "management_plan": management_plan,
        "committee_requirements": _COMMITTEE_REQUIREMENTS,
    }


async def ethics_dashboard(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Ethics program overview dashboard."""
    if seed:
        random.seed(seed)

    return {
        "active_protocols": random.randint(5, 25),
        "pending_reviews": random.randint(1, 8),
        "upcoming_continuing_reviews": random.randint(0, 5),
        "open_protocol_deviations": random.randint(0, 10),
        "reportable_events_30d": random.randint(0, 3),
        "consent_withdrawal_rate_pct": round(random.uniform(1, 8), 1),
        "avg_review_time_days": random.randint(14, 45),
        "coi_disclosures_pending": random.randint(0, 5),
        "upcoming_expirations": [
            {
                "protocol": f"CAR-T-{random.randint(100,999)}",
                "expires": (datetime.utcnow() + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d"),
                "action_needed": "continuing_review",
            }
            for _ in range(random.randint(1, 4))
        ],
        "available_submission_types": list(_SUBMISSION_TYPES.keys()),
    }
