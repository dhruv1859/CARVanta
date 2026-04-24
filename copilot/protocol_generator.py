"""
CARVanta Copilot — Protocol Generator
========================================
AI-powered clinical protocol generation for CAR-T cell therapy.
Generates treatment protocols, SOPs, and clinical guidelines
based on patient parameters and institutional requirements.

Features:
- Treatment protocol templates (conditioning, infusion, monitoring)
- Patient-specific protocol customization
- CRS/ICANS management algorithms
- Post-infusion monitoring schedules
- Dose modification guidelines
- Bridging therapy selection
- Lymphodepletion regimen selection
- Response assessment timelines (Lugano, IMWG, etc.)

Compliance: Protocols reference NCCN, ASTCT, EHA/EBMT guidelines.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.copilot.protocol_generator")


@dataclass
class ProtocolSection:
    title: str
    content: str
    subsections: List[Dict[str, str]] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Lymphodepletion Regimens
# ──────────────────────────────────────────────────────────────────────

_LYMPHODEPLETION_REGIMENS: Dict[str, Dict[str, Any]] = {
    "flu_cy_standard": {
        "name": "Fludarabine/Cyclophosphamide (Standard)",
        "regimen": "Fludarabine 30 mg/m² IV daily × 3 days + Cyclophosphamide 500 mg/m² IV daily × 3 days",
        "schedule": "Day -5 to Day -3 (infusion on Day 0)",
        "indications": ["CD19 CAR-T (DLBCL, ALL)", "BCMA CAR-T (MM)"],
        "monitoring": {
            "pre_conditioning": ["CBC with differential", "CMP", "LDH", "Ferritin", "CRP", "IL-6"],
            "during": ["Daily CBC", "Renal function Q48h", "Tumor lysis labs Q12h if high burden"],
            "post": ["CBC daily until CAR-T infusion", "ALC on Day 0 (target <500/µL)"],
        },
        "contraindications": ["CrCl <30 mL/min", "Active uncontrolled infection", "ECOG ≥3"],
        "dose_modifications": {
            "renal_impairment": "CrCl 30-50: Reduce fludarabine to 20 mg/m²",
            "elderly": "Age >70: Consider reducing cyclophosphamide to 300 mg/m²",
            "cytopenias": "Plt <50K: Hold until recovery",
        },
    },
    "flu_cy_reduced": {
        "name": "Fludarabine/Cyclophosphamide (Reduced Intensity)",
        "regimen": "Fludarabine 25 mg/m² IV daily × 3 days + Cyclophosphamide 250 mg/m² IV daily × 3 days",
        "schedule": "Day -5 to Day -3",
        "indications": ["Elderly patients (>70)", "Renal impairment", "Prior heavy chemotherapy"],
        "monitoring": {"pre_conditioning": ["Same as standard"], "during": ["Same as standard"], "post": ["Same as standard"]},
        "contraindications": ["Same as standard"],
        "dose_modifications": {},
    },
    "bendamustine": {
        "name": "Bendamustine",
        "regimen": "Bendamustine 90 mg/m² IV daily × 2 days",
        "schedule": "Day -5 to Day -4",
        "indications": ["Patients intolerant to Flu/Cy", "Prior fludarabine exposure"],
        "monitoring": {"pre_conditioning": ["CBC", "CMP"], "during": ["Daily CBC"], "post": ["ALC monitoring"]},
        "contraindications": ["Prior bendamustine hypersensitivity"],
        "dose_modifications": {},
    },
}


# ──────────────────────────────────────────────────────────────────────
# CRS/ICANS Management Algorithms
# ──────────────────────────────────────────────────────────────────────

_CRS_MANAGEMENT: Dict[int, Dict[str, Any]] = {
    1: {
        "grade": 1,
        "criteria": "Fever ≥38°C, no hypotension, no hypoxia",
        "management": [
            "Supportive care: antipyretics (acetaminophen 650mg Q6h PRN)",
            "IV fluids: NS at 75-100 mL/hr",
            "Monitoring: vitals Q4h, I/Os Q12h",
            "Labs: CRP, ferritin, IL-6, CBC Q12h",
        ],
        "tocilizumab": "Not indicated for Grade 1",
        "dexamethasone": "Not indicated",
        "escalation_criteria": "Escalate if fever >39.5°C for >24h or new symptoms develop",
    },
    2: {
        "grade": 2,
        "criteria": "Fever ≥38°C with hypotension not requiring vasopressors, OR hypoxia requiring low-flow O2 (≤6L NC)",
        "management": [
            "Tocilizumab 8 mg/kg IV (max 800 mg) — may repeat ×1 in 8h if no improvement",
            "IV fluids: bolus 500 mL NS, then 125 mL/hr",
            "O2 supplementation as needed",
            "Monitoring: vitals Q2h, continuous SpO2, I/Os Q8h",
            "Labs: CRP, ferritin, IL-6, CBC Q8h, troponin if cardiac symptoms",
        ],
        "tocilizumab": "Indicated — administer promptly",
        "dexamethasone": "Consider if no improvement 12h after tocilizumab (10 mg IV Q12h)",
        "escalation_criteria": "Escalate if requiring vasopressors or high-flow O2",
    },
    3: {
        "grade": 3,
        "criteria": "Fever ≥38°C with hypotension requiring 1 vasopressor ± vasopressin, OR hypoxia requiring high-flow O2 (>6L NC, CPAP, BiPAP)",
        "management": [
            "Tocilizumab 8 mg/kg IV + Dexamethasone 10 mg IV Q6h",
            "Vasopressor support (norepinephrine preferred)",
            "ICU transfer if not already in ICU",
            "High-flow O2 or non-invasive ventilation",
            "Monitoring: continuous telemetry, arterial line, central line",
            "Labs: Q6h CRS panel, troponin, pro-BNP, fibrinogen",
            "Consider: Siltuximab 11 mg/kg if refractory to tocilizumab",
        ],
        "tocilizumab": "Administer immediately, may repeat ×1",
        "dexamethasone": "Dexamethasone 10 mg IV Q6h, taper over 3-5 days after resolution",
        "escalation_criteria": "Escalate if requiring ≥2 vasopressors or intubation",
    },
    4: {
        "grade": 4,
        "criteria": "Fever ≥38°C with hypotension requiring multiple vasopressors, OR hypoxia requiring positive-pressure ventilation (intubation/ECMO)",
        "management": [
            "Tocilizumab 8 mg/kg IV + Methylprednisolone 1-2 mg/kg IV Q12h",
            "Multiple vasopressors, hemodynamic optimization",
            "Mechanical ventilation / ECMO if needed",
            "Consider: Anakinra 200 mg SC Q12h for refractory cases",
            "Consider: Ruxolitinib 10 mg PO BID if steroid-refractory",
            "Monitoring: ICU-level, invasive monitoring",
            "Labs: Q4h CRS panel, organ function panel",
            "Ethics/palliative care consultation if clinical trajectory concerning",
        ],
        "tocilizumab": "Administer if not given in prior 8h",
        "dexamethasone": "Methylprednisolone 1-2 mg/kg IV Q12h, prolonged taper",
        "escalation_criteria": "Multi-organ failure — consider ECMO, renal replacement therapy",
    },
}

_ICANS_MANAGEMENT: Dict[int, Dict[str, Any]] = {
    1: {
        "grade": 1, "ice_score": "7-9/10",
        "management": ["Supportive care", "Neurology consult", "q4h neuro checks", "Seizure prophylaxis (levetiracetam 500mg BID)"],
        "dexamethasone": "Consider Dex 10mg IV Q12h",
    },
    2: {
        "grade": 2, "ice_score": "3-6/10",
        "management": ["Dexamethasone 10mg IV Q6h", "Continuous EEG monitoring", "q2h neuro checks", "MRI brain if symptoms persist >24h"],
        "dexamethasone": "Dex 10mg IV Q6h until Grade ≤1, then taper",
    },
    3: {
        "grade": 3, "ice_score": "0-2/10",
        "management": ["Methylprednisolone 1mg/kg IV Q12h", "ICU transfer", "Continuous EEG", "Brain MRI", "LP if concern for infection",
                        "Intubation supplies at bedside"],
        "dexamethasone": "Methylpred 1mg/kg IV Q12h, taper over 7 days",
    },
    4: {
        "grade": 4, "ice_score": "Unarousable / Status epilepticus / Cerebral edema",
        "management": ["Methylprednisolone 1g IV daily × 3 days", "Seizure management (lorazepam, levetiracetam)", "Neurosurgery consult",
                        "Consider mannitol/hypertonic saline for cerebral edema", "Intubation for airway protection"],
        "dexamethasone": "High-dose methylpred 1g IV × 3, then rapid taper",
    },
}


# ──────────────────────────────────────────────────────────────────────
# Protocol Generation
# ──────────────────────────────────────────────────────────────────────

async def generate_treatment_protocol(
    cancer_type: str = "DLBCL",
    product: str = "axi-cel",
    patient_age: int = 55,
    ecog: int = 1,
    tumor_burden: str = "moderate",
    prior_lines: int = 3,
    institution: str = "Academic Medical Center",
) -> Dict[str, Any]:
    """Generate a comprehensive treatment protocol."""
    protocol_id = f"PROT-{uuid.uuid4().hex[:8].upper()}"

    # Select lymphodepletion
    if patient_age > 70 or ecog >= 2:
        ld_key = "flu_cy_reduced"
    else:
        ld_key = "flu_cy_standard"
    ld = _LYMPHODEPLETION_REGIMENS[ld_key]

    # Build monitoring schedule
    monitoring = _build_monitoring_schedule(cancer_type)

    # Response assessment
    response_criteria = _get_response_criteria(cancer_type)

    return {
        "protocol_id": protocol_id,
        "title": f"CAR-T Cell Therapy Protocol — {product.upper()} for {cancer_type}",
        "version": "1.0",
        "institution": institution,
        "patient_criteria": {
            "cancer_type": cancer_type,
            "product": product,
            "age": patient_age,
            "ecog": ecog,
            "tumor_burden": tumor_burden,
            "prior_lines": prior_lines,
        },
        "sections": {
            "pre_treatment": {
                "title": "Pre-Treatment Workup",
                "items": [
                    "Confirm diagnosis and eligibility",
                    "Baseline imaging (PET/CT within 4 weeks)",
                    "Bone marrow biopsy (if hematologic malignancy)",
                    "Cardiac evaluation (ECHO, EKG)",
                    "Baseline labs: CBC, CMP, LDH, ferritin, CRP, IL-6, coagulation panel",
                    "Infectious disease screening (HIV, HBV, HCV, CMV, HSV)",
                    "Leukapheresis scheduling",
                    "Bridging therapy assessment (if needed)",
                    "Tocilizumab availability confirmed (bedside stock)",
                    "ICU bed reserved",
                ],
            },
            "lymphodepletion": ld,
            "infusion": {
                "title": "CAR-T Cell Infusion",
                "day": "Day 0",
                "pre_medications": [
                    "Acetaminophen 650 mg PO",
                    "Diphenhydramine 25-50 mg IV/PO",
                    "Do NOT give systemic corticosteroids pre-infusion",
                ],
                "procedure": [
                    "Verify product identity (TWO independent verifiers)",
                    "Thaw product at bedside per manufacturer instructions",
                    "Infuse within 30 minutes of thaw",
                    f"Target dose: As per {product} label",
                    "Monitor vitals Q15min × 1h, then Q30min × 2h, then Q1h × 4h",
                ],
                "post_infusion": [
                    "Observation minimum 1 hour post-infusion",
                    "Baseline CRS assessment",
                    "Document time of infusion (T₀)",
                ],
            },
            "crs_management": _CRS_MANAGEMENT,
            "icans_management": _ICANS_MANAGEMENT,
            "monitoring_schedule": monitoring,
            "response_assessment": response_criteria,
        },
        "references": [
            "NCCN Guidelines: B-Cell Lymphomas, Version 6.2024",
            "ASTCT CRS Consensus Grading (Lee et al., 2019)",
            "EHA/EBMT CAR-T Recommendations (2024)",
            f"{product.upper()} Prescribing Information",
        ],
    }


def _build_monitoring_schedule(cancer_type: str) -> Dict[str, Any]:
    return {
        "inpatient_phase": {
            "duration": "Day 0 to Day +14 (minimum)",
            "vitals": "Q4h (Q2h if CRS ≥ Grade 2)",
            "labs": {
                "daily": ["CBC with differential"],
                "q48h": ["CMP", "LDH", "Ferritin", "CRP"],
                "if_crs": ["IL-6", "Troponin", "Fibrinogen Q8h"],
            },
            "neuro_assessment": "ICE assessment Q8h",
        },
        "outpatient_weeks_2_4": {
            "visits": "2-3× per week",
            "labs": ["CBC", "CMP", "LDH", "CRP"],
            "assessment": ["CRS resolution check", "ICANS screening", "Infection surveillance"],
        },
        "month_1_3": {
            "visits": "Weekly → Biweekly",
            "labs": ["CBC", "CMP", "Quantitative immunoglobulins"],
            "imaging": "PET/CT at Day +30 and Day +90",
        },
        "month_3_12": {
            "visits": "Monthly",
            "labs": ["CBC", "IgG levels (replace if <400 mg/dL)"],
            "imaging": "PET/CT Q3 months",
            "b_cell_aplasia": "Monitor CD19+ B-cells and immunoglobulins",
        },
        "long_term": {
            "visits": "Q3-6 months for 5 years, then annually for 15 years",
            "monitoring": [
                "Secondary malignancy screening (per FDA REMS)",
                "IVIG replacement if hypogammaglobulinemia",
                "Vaccination schedule (no live vaccines while B-cell aplastic)",
            ],
        },
    }


def _get_response_criteria(cancer_type: str) -> Dict[str, Any]:
    if "lymphoma" in cancer_type.lower() or "dlbcl" in cancer_type.lower():
        return {
            "system": "Lugano Classification",
            "timepoints": ["Day +30", "Day +90", "Day +180", "Month 12"],
            "cr": "Complete metabolic response: Deauville ≤3",
            "pr": "Partial response: ≥50% decrease in SPD",
            "sd": "Stable disease: <50% decrease and <50% increase",
            "pd": "Progressive disease: ≥50% increase or new lesions",
        }
    elif "myeloma" in cancer_type.lower():
        return {
            "system": "IMWG Criteria",
            "timepoints": ["Day +28", "Day +60", "Day +100", "Month 6", "Month 12"],
            "scr": "Stringent CR: CR + normal FLC ratio + no clonal cells",
            "cr": "Complete Response: Negative IF on serum/urine",
            "vgpr": "Very Good PR: ≥90% reduction in M-protein",
            "pr": "Partial Response: ≥50% reduction in M-protein",
        }
    else:
        return {
            "system": "Standard response criteria",
            "timepoints": ["Day +30", "Day +90", "Month 6"],
        }


async def get_crs_algorithm(grade: int = 0) -> Dict[str, Any]:
    """Get CRS management algorithm for a specific grade."""
    if grade == 0:
        return {"all_grades": _CRS_MANAGEMENT}
    return _CRS_MANAGEMENT.get(grade, {"error": "Invalid CRS grade"})


async def get_icans_algorithm(grade: int = 0) -> Dict[str, Any]:
    """Get ICANS management algorithm."""
    if grade == 0:
        return {"all_grades": _ICANS_MANAGEMENT}
    return _ICANS_MANAGEMENT.get(grade, {"error": "Invalid ICANS grade"})


async def get_lymphodepletion_options() -> Dict[str, Any]:
    """Get available lymphodepletion regimens."""
    return {"regimens": _LYMPHODEPLETION_REGIMENS}
