"""
CARVanta Trials — Regulatory Intelligence Engine
===================================================
Track regulatory landscapes, IND/BLA requirements,
and global regulatory pathway differences for CAR-T trials.

Features:
- FDA/EMA/PMDA/NMPA regulatory comparison
- IND application checklist generator
- BLA submission timeline estimator
- RMAT/Breakthrough/Accelerated designation tracker
- Post-marketing commitment (PMC/PMR) modeling
- Risk Evaluation and Mitigation Strategy (REMS) designer
- Pediatric study plan generator
- CMC (Chemistry, Manufacturing, Controls) module status tracker
"""

import logging
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.regulatory")


# ──────────────────────────────────────────────────────────────────────
# Regulatory Agency Database
# ──────────────────────────────────────────────────────────────────────

_REGULATORY_AGENCIES = {
    "FDA": {
        "name": "U.S. Food and Drug Administration",
        "country": "United States",
        "cell_therapy_division": "OTAT (Office of Tissues and Advanced Therapies)",
        "ind_timeline_months": 1,
        "bla_review_months": 12,
        "priority_review_months": 6,
        "breakthrough_therapy": True,
        "rmat_designation": True,
        "accelerated_approval": True,
        "rems_required": True,
        "pediatric_requirement": "PREA (Pediatric Research Equity Act)",
        "gmp_inspection": "Pre-approval inspection (PAI)",
        "advisory_committee": "ODAC (Oncologic Drugs Advisory Committee)",
        "orphan_drug": True,
        "key_guidance": [
            "Considerations for the Development of Chimeric Antigen Receptor (CAR) T Cell Products (2022)",
            "Long-term Follow-up After Administration of Human Gene Therapy Products (2020)",
            "Chemistry, Manufacturing, and Control (CMC) Information for Human Gene Therapy INDs (2020)",
        ],
    },
    "EMA": {
        "name": "European Medicines Agency",
        "country": "European Union",
        "cell_therapy_division": "CAT (Committee for Advanced Therapies)",
        "ind_timeline_months": 2,
        "bla_review_months": 15,
        "priority_review_months": 9,
        "breakthrough_therapy": False,
        "rmat_designation": False,
        "accelerated_approval": True,
        "rems_required": False,
        "pediatric_requirement": "PIP (Paediatric Investigation Plan)",
        "gmp_inspection": "GMP certification by member state",
        "advisory_committee": "CAT + CHMP joint assessment",
        "orphan_drug": True,
        "key_guidance": [
            "ATMP Regulation (EC) No 1394/2007",
            "Guideline on quality, non-clinical and clinical aspects of medicinal products containing GMOs (2020)",
        ],
    },
    "PMDA": {
        "name": "Pharmaceuticals and Medical Devices Agency",
        "country": "Japan",
        "cell_therapy_division": "Division of Cell and Gene Therapy Products",
        "ind_timeline_months": 1,
        "bla_review_months": 12,
        "priority_review_months": 6,
        "breakthrough_therapy": True,
        "rmat_designation": False,
        "accelerated_approval": True,
        "rems_required": False,
        "pediatric_requirement": "Separate pediatric development plan",
        "gmp_inspection": "PMDA GMP inspection",
        "advisory_committee": "Pharmaceutical Affairs and Food Sanitation Council",
        "orphan_drug": True,
        "key_guidance": [
            "SAKIGAKE designation (pioneer status)",
            "Conditional/Time-limited approval for regenerative medicine products",
        ],
    },
    "NMPA": {
        "name": "National Medical Products Administration",
        "country": "China",
        "cell_therapy_division": "Center for Drug Evaluation (CDE)",
        "ind_timeline_months": 2,
        "bla_review_months": 18,
        "priority_review_months": 8,
        "breakthrough_therapy": True,
        "rmat_designation": False,
        "accelerated_approval": True,
        "rems_required": False,
        "pediatric_requirement": "Guidelines for pediatric drug development",
        "gmp_inspection": "NMPA GMP inspection",
        "advisory_committee": "Expert committee review",
        "orphan_drug": False,
        "key_guidance": [
            "Technical Guidelines for Clinical Trials of CAR-T Products (2022)",
            "Technical Guidelines for Research and Evaluation of Gene Therapy Products (2020)",
        ],
    },
}


_IND_CHECKLIST = {
    "preclinical": [
        {"item": "In vitro cytotoxicity against target-positive cells", "critical": True, "fda_module": "2.4"},
        {"item": "In vitro cytotoxicity against target-negative cells (specificity)", "critical": True, "fda_module": "2.4"},
        {"item": "Cytokine release profiling (IFN-γ, IL-2, TNF-α)", "critical": True, "fda_module": "2.4"},
        {"item": "In vivo efficacy in xenograft model (NSG mice)", "critical": True, "fda_module": "2.4"},
        {"item": "Pharmacology/biodistribution study", "critical": False, "fda_module": "2.4"},
        {"item": "Safety pharmacology (if applicable)", "critical": False, "fda_module": "2.6"},
        {"item": "Tumorigenicity assessment", "critical": True, "fda_module": "2.6"},
        {"item": "Insertional mutagenesis analysis (for viral vectors)", "critical": True, "fda_module": "2.6"},
    ],
    "cmc": [
        {"item": "Vector construction and characterization", "critical": True, "fda_module": "3.2.S"},
        {"item": "Vector production process (GMP)", "critical": True, "fda_module": "3.2.S"},
        {"item": "Vector release testing (identity, potency, purity, sterility)", "critical": True, "fda_module": "3.2.S"},
        {"item": "CAR-T manufacturing process description", "critical": True, "fda_module": "3.2.P"},
        {"item": "Starting material (apheresis) specifications", "critical": True, "fda_module": "3.2.P"},
        {"item": "In-process controls (IPC)", "critical": True, "fda_module": "3.2.P"},
        {"item": "Drug product release specifications", "critical": True, "fda_module": "3.2.P"},
        {"item": "Stability data (storage conditions, shelf life)", "critical": True, "fda_module": "3.2.P"},
        {"item": "Container closure system", "critical": False, "fda_module": "3.2.P"},
        {"item": "Certificate of Analysis (CoA) for clinical lots", "critical": True, "fda_module": "3.2.P"},
    ],
    "clinical": [
        {"item": "Clinical protocol with statistical analysis plan", "critical": True, "fda_module": "5.3"},
        {"item": "Informed consent form (ICF)", "critical": True, "fda_module": "5.3"},
        {"item": "Investigator's Brochure (IB)", "critical": True, "fda_module": "5.3"},
        {"item": "CRS/ICANS management algorithm", "critical": True, "fda_module": "5.3"},
        {"item": "Long-term follow-up plan (15 years per FDA)", "critical": True, "fda_module": "5.3"},
        {"item": "REMS proposal (if required)", "critical": True, "fda_module": "5.3"},
        {"item": "Data Safety Monitoring Board (DSMB) charter", "critical": False, "fda_module": "5.3"},
    ],
}


async def regulatory_comparison(
    agencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compare regulatory pathways across major agencies."""
    if not agencies:
        agencies = list(_REGULATORY_AGENCIES.keys())

    comparison = {}
    for code in agencies:
        if code in _REGULATORY_AGENCIES:
            comparison[code] = _REGULATORY_AGENCIES[code]

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "agencies_compared": len(comparison),
        "comparison": comparison,
        "fastest_to_approval": min(comparison.items(), key=lambda x: x[1]["priority_review_months"])[0],
        "recommendation": "Pursue FDA RMAT + Breakthrough designation for fastest path. File EMA in parallel via centralized procedure.",
    }


async def ind_checklist(
    target: str = "CD19",
    indication: str = "DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate IND application readiness checklist."""
    if seed:
        random.seed(seed)

    sections = {}
    total_items = 0
    completed_items = 0

    for section, items in _IND_CHECKLIST.items():
        section_items = []
        for item in items:
            status = random.choices(["complete", "in_progress", "not_started"], weights=[40, 35, 25])[0]
            if status == "complete":
                completed_items += 1
            total_items += 1

            section_items.append({
                "item": item["item"],
                "critical": item["critical"],
                "fda_module": item["fda_module"],
                "status": status,
                "estimated_completion_weeks": 0 if status == "complete" else random.randint(2, 16),
            })
        sections[section] = section_items

    readiness = completed_items / max(total_items, 1)
    critical_incomplete = sum(
        1 for section in sections.values()
        for item in section
        if item["critical"] and item["status"] != "complete"
    )

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "indication": indication,
        "overall_readiness_pct": round(readiness * 100, 1),
        "total_items": total_items,
        "completed": completed_items,
        "critical_items_incomplete": critical_incomplete,
        "ind_submittable": critical_incomplete == 0,
        "estimated_weeks_to_ind": max(item["estimated_completion_weeks"] for section in sections.values() for item in section),
        "sections": sections,
    }


async def bla_timeline(
    target: str = "CD19",
    phase: str = "Phase 2",
    designation: str = "RMAT",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Estimate BLA submission and approval timeline."""
    if seed:
        random.seed(seed)

    # Base timeline in months
    milestones = [
        {"milestone": "IND Submission", "month": 0, "duration_months": 1, "status": "complete"},
        {"milestone": "IND Clearance (30-day)", "month": 1, "duration_months": 1, "status": "complete"},
        {"milestone": "Phase 1 First Patient In", "month": 2, "duration_months": 0, "status": "complete"},
        {"milestone": "Phase 1 Last Patient In", "month": 8, "duration_months": 6, "status": "in_progress"},
        {"milestone": "Phase 1 Data Analysis", "month": 14, "duration_months": 3, "status": "planned"},
        {"milestone": "End of Phase 1 Meeting (FDA)", "month": 17, "duration_months": 2, "status": "planned"},
        {"milestone": "Phase 2 Protocol Finalization", "month": 19, "duration_months": 2, "status": "planned"},
        {"milestone": "Phase 2 First Patient In", "month": 21, "duration_months": 0, "status": "planned"},
        {"milestone": "Phase 2 Enrollment Complete", "month": 33, "duration_months": 12, "status": "planned"},
        {"milestone": "Primary Endpoint Analysis", "month": 39, "duration_months": 6, "status": "planned"},
        {"milestone": "Pre-BLA Meeting (FDA)", "month": 41, "duration_months": 2, "status": "planned"},
        {"milestone": "BLA Submission", "month": 45, "duration_months": 4, "status": "planned"},
        {"milestone": "BLA Filing Acceptance", "month": 47, "duration_months": 2, "status": "planned"},
        {"milestone": "ODAC Meeting", "month": 53, "duration_months": 0, "status": "planned"},
        {"milestone": "PDUFA Date (Approval)", "month": 57, "duration_months": 0, "status": "planned"},
    ]

    # Adjust for designations
    if "RMAT" in designation or "Breakthrough" in designation:
        for m in milestones:
            if m["month"] > 17:
                m["month"] = int(m["month"] * 0.8)  # 20% faster

    if "Accelerated" in designation:
        # Can use surrogate endpoint, skip Phase 3
        milestones = [m for m in milestones if "Phase 3" not in m.get("milestone", "")]

    total_months = milestones[-1]["month"]

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "regulatory_designation": designation,
        "total_months_to_approval": total_months,
        "total_years": round(total_months / 12, 1),
        "milestones": milestones,
        "critical_path": [m["milestone"] for m in milestones if m.get("duration_months", 0) >= 6],
        "designation_savings_months": round(57 - total_months, 0),
    }


async def rems_design(
    target: str = "CD19",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Design a Risk Evaluation and Mitigation Strategy (REMS)."""
    if seed:
        random.seed(seed)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "rems_name": f"CARVanta {target} CAR-T REMS Program",
        "rems_components": {
            "medication_guide": {
                "required": True,
                "content": "Patient information about CRS, ICANS, and long-term risks",
            },
            "communication_plan": {
                "required": True,
                "elements": ["Dear Healthcare Provider letter", "Training materials", "Website"],
            },
            "etasu": {
                "required": True,
                "name": "Elements to Assure Safe Use",
                "requirements": [
                    "Certified healthcare facility with ICU access",
                    "Tocilizumab available on-site (≥2 doses per patient)",
                    "Prescriber certified through REMS training program",
                    "Patient enrolled in REMS registry before treatment",
                    "Minimum 4-week monitoring period post-infusion",
                    "CRS/ICANS grading and management protocol on file",
                ],
            },
            "implementation_system": {
                "required": True,
                "elements": [
                    "Certified prescriber registry",
                    "Certified treatment center registry",
                    "Patient registry with long-term follow-up (15 years)",
                    "Mandatory adverse event reporting",
                ],
            },
        },
        "certification_requirements": {
            "prescriber": [
                "Board-certified hematologist/oncologist",
                "Completed REMS training module",
                "Experience with CRS/ICANS management",
                "Access to ICU and tocilizumab",
            ],
            "facility": [
                "CAR-T certified treatment center",
                "On-site ICU capability",
                "24/7 laboratory access",
                "Tocilizumab stocked (minimum 2 doses per scheduled patient)",
                "Neurological assessment capability",
            ],
        },
        "monitoring": {
            "acute_period": "Daily assessment for 7 days post-infusion",
            "outpatient": "Remain within 2 hours of treatment center for 4 weeks",
            "long_term": "Annual follow-up for 15 years (secondary malignancy, RCL monitoring)",
        },
    }
