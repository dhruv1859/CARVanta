"""
CARVanta Trials — Patient Journey & Screening Tracker
========================================================
Model the complete patient journey from referral through
screening, enrollment, treatment, and long-term follow-up.

Features:
- Patient journey stage modeling (referral → screening → enrolled → treated → FU)
- Screen failure analysis and root cause tracking
- Pre-screening checklist automation
- Patient timeline visualization data
- Journey milestone tracking
- Screening-to-treatment conversion metrics
- Patient-reported outcome (PRO) integration
- Quality of life trajectory modeling (FACT-Lym, EQ-5D)
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.patient_journey")


# ──────────────────────────────────────────────────────────────────────
# Journey Stage Definitions
# ──────────────────────────────────────────────────────────────────────

_JOURNEY_STAGES = {
    "referral": {
        "name": "Referral Received",
        "description": "Patient referred by treating physician",
        "avg_duration_days": 3,
        "documents": ["Referral form", "Medical records summary"],
    },
    "pre_screening": {
        "name": "Pre-Screening",
        "description": "Initial eligibility review from medical records",
        "avg_duration_days": 5,
        "documents": ["Prior treatment history", "Lab results", "Pathology reports"],
        "common_failures": [
            {"reason": "ECOG too high", "frequency_pct": 15},
            {"reason": "Insufficient prior therapies", "frequency_pct": 12},
            {"reason": "Active CNS disease", "frequency_pct": 8},
        ],
    },
    "informed_consent": {
        "name": "Informed Consent",
        "description": "Patient education and consent signing",
        "avg_duration_days": 7,
        "documents": ["ICF", "HIPAA authorization", "Long-term FU consent"],
    },
    "screening": {
        "name": "Screening Assessments",
        "description": "Comprehensive eligibility workup",
        "avg_duration_days": 14,
        "assessments": [
            "Physical examination", "ECOG assessment", "CBC with differential",
            "CMP (comprehensive metabolic panel)", "Coagulation studies",
            "Immunoglobulin levels", "B/T-cell subsets", "PET-CT scan",
            "Bone marrow biopsy", "Target antigen confirmation",
            "Echocardiogram", "Pulmonary function", "Pregnancy test",
            "Viral screening (HIV, HBV, HCV)",
        ],
        "common_failures": [
            {"reason": "Target antigen negative", "frequency_pct": 10},
            {"reason": "Inadequate organ function", "frequency_pct": 8},
            {"reason": "Disease progression during screening", "frequency_pct": 7},
            {"reason": "Cardiac function (LVEF <45%)", "frequency_pct": 5},
            {"reason": "Active infection", "frequency_pct": 4},
        ],
    },
    "enrollment": {
        "name": "Enrollment Confirmed",
        "description": "All eligibility criteria met, assigned to cohort",
        "avg_duration_days": 2,
        "documents": ["Enrollment form", "Randomization (if applicable)"],
    },
    "leukapheresis": {
        "name": "Leukapheresis",
        "description": "T-cell collection via apheresis",
        "avg_duration_days": 1,
        "assessments": ["Pre-apheresis labs", "Apheresis procedure (4-6 hours)", "Product shipment to manufacturing"],
    },
    "bridging_therapy": {
        "name": "Bridging Therapy (if needed)",
        "description": "Disease stabilization during manufacturing",
        "avg_duration_days": 21,
        "common_regimens": ["R-ICE", "R-DHAP", "Polatuzumab-BR", "Ibrutinib (MCL)"],
    },
    "manufacturing": {
        "name": "CAR-T Manufacturing",
        "description": "Ex vivo T-cell engineering and expansion",
        "avg_duration_days": 28,
        "milestones": ["T-cell activation", "Viral transduction", "Expansion", "Harvest", "Release testing", "Cryopreservation", "Shipment"],
    },
    "lymphodepletion": {
        "name": "Lymphodepleting Chemotherapy",
        "description": "Flu/Cy conditioning regimen",
        "avg_duration_days": 3,
        "regimen": "Fludarabine 30mg/m²/day + Cyclophosphamide 300mg/m²/day × 3 days",
    },
    "infusion": {
        "name": "CAR-T Infusion",
        "description": "Day 0: Single IV infusion",
        "avg_duration_days": 1,
        "milestones": ["Pre-infusion labs", "Product thaw and preparation", "IV infusion (30-60 min)", "Post-infusion monitoring"],
    },
    "acute_monitoring": {
        "name": "Acute Monitoring",
        "description": "Inpatient/close outpatient monitoring for CRS/ICANS",
        "avg_duration_days": 28,
        "assessments": ["Vital signs Q4h", "CRS grading Q12h", "ICE score Q12h", "Daily labs"],
    },
    "response_assessment": {
        "name": "Response Assessment",
        "description": "PET-CT and bone marrow at Day 28-30",
        "avg_duration_days": 7,
        "assessments": ["PET-CT", "Bone marrow biopsy", "MRD assessment", "CAR-T kinetics"],
    },
    "follow_up": {
        "name": "Active Follow-Up",
        "description": "Monthly → quarterly monitoring for 24 months",
        "avg_duration_days": 730,
        "schedule": "Monthly × 3, then Q3months × 21 months",
    },
    "long_term_fu": {
        "name": "Long-Term Follow-Up",
        "description": "Annual monitoring for secondary malignancy and RCL",
        "avg_duration_days": 4745,
        "schedule": "Annual × 13 years (Year 2-15)",
    },
}


async def get_journey_stages() -> Dict[str, Any]:
    """Get all patient journey stages with detailed descriptions."""
    total_days = sum(s["avg_duration_days"] for s in _JOURNEY_STAGES.values())
    return {
        "total_stages": len(_JOURNEY_STAGES),
        "estimated_total_journey_days": total_days,
        "stages": _JOURNEY_STAGES,
    }


async def simulate_patient_journey(
    cancer_type: str = "DLBCL",
    target: str = "CD19",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Simulate a single patient's complete journey through a CAR-T trial."""
    if seed:
        random.seed(seed)

    journey = []
    current_day = 0
    screen_pass = True

    for stage_key, stage in _JOURNEY_STAGES.items():
        # Add variability to duration
        duration = max(1, int(stage["avg_duration_days"] * random.uniform(0.7, 1.5)))

        # Check for screen failure
        status = "completed"
        failure_reason = None
        if stage_key in ("pre_screening", "screening") and random.random() < 0.15:
            failures = stage.get("common_failures", [])
            if failures:
                fail = random.choice(failures)
                failure_reason = fail["reason"]
                status = "screen_failure"
                screen_pass = False

        entry = {
            "stage": stage_key,
            "name": stage["name"],
            "start_day": current_day,
            "end_day": current_day + duration,
            "duration_days": duration,
            "status": status,
        }
        if failure_reason:
            entry["failure_reason"] = failure_reason

        journey.append(entry)
        current_day += duration

        if not screen_pass:
            break

    # Quality of life trajectory (if patient made it to treatment)
    qol_trajectory = []
    if screen_pass:
        for month in range(0, 25):
            # Baseline → dip at treatment → recovery
            if month == 0:
                score = round(random.gauss(55, 8), 1)
            elif month <= 1:
                score = round(random.gauss(35, 10), 1)  # Nadir
            elif month <= 3:
                score = round(random.gauss(50, 8), 1)
            elif month <= 6:
                score = round(random.gauss(65, 8), 1)
            else:
                score = round(random.gauss(72, 7), 1)
            qol_trajectory.append({"month": month, "FACT_Lym_score": max(0, min(100, score))})

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "cancer_type": cancer_type,
        "target": target,
        "screen_passed": screen_pass,
        "total_days": current_day,
        "journey": journey,
        "quality_of_life": qol_trajectory,
    }


async def screen_failure_analysis(
    n_patients: int = 200,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze screen failure rates and root causes."""
    if seed:
        random.seed(seed)

    failures = {
        "ECOG_too_high": {"count": 0, "stage": "pre_screening"},
        "insufficient_prior_therapies": {"count": 0, "stage": "pre_screening"},
        "active_CNS_disease": {"count": 0, "stage": "pre_screening"},
        "target_antigen_negative": {"count": 0, "stage": "screening"},
        "inadequate_organ_function": {"count": 0, "stage": "screening"},
        "disease_progression": {"count": 0, "stage": "screening"},
        "cardiac_function_low": {"count": 0, "stage": "screening"},
        "active_infection": {"count": 0, "stage": "screening"},
        "patient_withdrawal": {"count": 0, "stage": "informed_consent"},
        "insurance_denial": {"count": 0, "stage": "enrollment"},
    }

    screened = 0
    enrolled = 0
    for _ in range(n_patients):
        screened += 1
        failed = False
        for reason, info in failures.items():
            prob = random.uniform(0.02, 0.12)
            if random.random() < prob:
                info["count"] += 1
                failed = True
                break
        if not failed:
            enrolled += 1

    total_failures = sum(f["count"] for f in failures.values())
    screen_failure_rate = total_failures / max(screened, 1)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "patients_screened": screened,
        "patients_enrolled": enrolled,
        "screen_failure_rate_pct": round(screen_failure_rate * 100, 1),
        "screening_to_enrollment_ratio": round(screened / max(enrolled, 1), 2),
        "failure_reasons": {
            reason: {
                "count": info["count"],
                "pct_of_failures": round(info["count"] / max(total_failures, 1) * 100, 1),
                "stage": info["stage"],
            }
            for reason, info in failures.items() if info["count"] > 0
        },
        "recommendations": [
            "Consider broader ECOG criteria (0-2) to increase enrollment",
            "Add pre-screening call to assess basic eligibility before site visit",
            "Implement central target antigen testing to reduce screen failure",
        ],
    }


async def pre_screening_checklist(
    cancer_type: str = "DLBCL",
    target: str = "CD19",
) -> Dict[str, Any]:
    """Generate a pre-screening checklist for rapid eligibility assessment."""
    return {
        "checklist_name": f"CAR-T {target} Pre-Screening for {cancer_type}",
        "estimated_time_minutes": 15,
        "sections": {
            "disease_confirmation": [
                {"item": f"Histologically confirmed {cancer_type}", "critical": True},
                {"item": f"Relapsed or refractory after ≥2 prior systemic therapies", "critical": True},
                {"item": f"{target} expression confirmed or tissue available for testing", "critical": True},
            ],
            "performance_status": [
                {"item": "ECOG Performance Status 0-1", "critical": True},
                {"item": "Ambulatory and capable of self-care", "critical": False},
                {"item": "Life expectancy ≥12 weeks", "critical": True},
            ],
            "organ_function": [
                {"item": "Adequate renal function (CrCl ≥30 mL/min)", "critical": True},
                {"item": "Adequate hepatic function (bilirubin ≤1.5× ULN)", "critical": True},
                {"item": "Adequate cardiac function (LVEF ≥45%)", "critical": True},
                {"item": "Oxygen saturation ≥92% on room air", "critical": True},
            ],
            "exclusions": [
                {"item": "No prior CAR-T therapy targeting same antigen", "critical": True},
                {"item": "No active CNS involvement", "critical": True},
                {"item": "No active GVHD requiring systemic treatment", "critical": True},
                {"item": "No uncontrolled active infection", "critical": True},
                {"item": "No active autoimmune disease", "critical": True},
            ],
            "logistics": [
                {"item": "Able to remain within 2 hours of center for 4 weeks", "critical": True},
                {"item": "Caregiver available for post-infusion period", "critical": False},
                {"item": "Insurance authorization (or financial assistance)", "critical": True},
            ],
        },
    }
