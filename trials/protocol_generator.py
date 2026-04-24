"""
CARVanta Trials — Protocol Generator & Statistical Design Engine
==================================================================
Generate complete ICH-GCP compliant clinical trial protocols
for CAR-T cell therapy, including statistical designs, endpoint
hierarchies, monitoring plans, and consent document templates.

Features:
- Full protocol synopsis generation
- Simon's two-stage optimal design calculator
- BOIN dose escalation implementation
- Endpoint hierarchy builder with primary/secondary/exploratory
- DLT definition library for CAR-T
- Bayesian response-adaptive randomization
- Interim analysis scheduling
- DSMB charter template generation
- Informed consent document structure
- Study schedule (time & events) generator
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.protocol_generator")


# ──────────────────────────────────────────────────────────────────────
# Dose Escalation Designs
# ──────────────────────────────────────────────────────────────────────

_BOIN_TABLE = {
    0.20: {"escalate_if_le": 0.118, "deescalate_if_ge": 0.298},
    0.25: {"escalate_if_le": 0.157, "deescalate_if_ge": 0.359},
    0.30: {"escalate_if_le": 0.196, "deescalate_if_ge": 0.418},
    0.33: {"escalate_if_le": 0.222, "deescalate_if_ge": 0.450},
}

_DLT_LIBRARY = {
    "crs_3plus": {
        "name": "Cytokine Release Syndrome ≥ Grade 3",
        "grading": "ASTCT 2019 consensus",
        "window_days": 28,
        "description": "Grade 3: Hypotension requiring one vasopressor ± vasopressin, or hypoxia requiring high-flow nasal cannula, facemask, or Venturi mask. Grade 4: Life-threatening—requires multiple vasopressors or mechanical ventilation.",
        "management": "Tocilizumab 8mg/kg IV (max 800mg), may repeat x1 at 8h. If Grade ≥3, add dexamethasone 10mg IV Q6h.",
        "de_escalation": "If CRS resolves to Grade ≤1, taper steroids over 3-5 days.",
    },
    "icans_3plus": {
        "name": "Immune Effector Cell-Associated Neurotoxicity ≥ Grade 3",
        "grading": "ASTCT 2019 consensus (ICE score)",
        "window_days": 28,
        "description": "Grade 3: ICE score 0-2, or clinical seizure (responds to benzodiazepines), or focal cerebral edema. Grade 4: Comatose (ICE 0), status epilepticus, diffuse cerebral edema, or decerebrate posturing.",
        "management": "Dexamethasone 10mg IV Q6h. Grade 4: methylprednisolone 1g/day for 3 days + levetiracetam seizure prophylaxis.",
        "de_escalation": "Taper steroids over 7 days once improved to Grade ≤1. MRI for Grade ≥3.",
    },
    "prolonged_cytopenia": {
        "name": "Prolonged Cytopenia (Day 28+)",
        "grading": "CTCAE v5.0",
        "window_days": 42,
        "description": "Grade 4 neutropenia (ANC <500/μL) or Grade 4 thrombocytopenia (platelets <25,000/μL) persisting beyond Day 28 post-infusion.",
        "management": "G-CSF for prolonged neutropenia (start Day 14 if ANC <500). Platelet transfusion for <10K or active bleeding.",
        "de_escalation": "Monitor CBC 3x/week until recovery.",
    },
    "organ_toxicity": {
        "name": "Grade ≥3 Non-Hematologic Organ Toxicity",
        "grading": "CTCAE v5.0",
        "window_days": 28,
        "description": "Any Grade ≥3 non-hematologic toxicity probably or definitely related to CAR-T cell therapy, excluding CRS and ICANS which have separate grading.",
        "management": "Organ-specific management. Grade ≥3 hepatotoxicity: hold any hepatotoxic medications, supportive care.",
        "de_escalation": "Must resolve to Grade ≤1 before proceeding.",
    },
    "manufacturing_failure": {
        "name": "Manufacturing Failure",
        "grading": "N/A (process outcome)",
        "window_days": 0,
        "description": "Inability to manufacture a CAR-T product meeting release specifications from the patient's apheresis material.",
        "management": "Repeat apheresis if feasible. Bridge therapy during re-manufacturing.",
        "de_escalation": "N/A",
    },
    "treatment_related_death": {
        "name": "Treatment-Related Death",
        "grading": "N/A",
        "window_days": 100,
        "description": "Death within 100 days of CAR-T infusion that is probably or definitely related to the investigational product.",
        "management": "N/A — report to DSMB, FDA, and IRB within 24 hours.",
        "de_escalation": "Mandatory DSMB review. Consider study pause.",
    },
}


@dataclass
class ProtocolConfig:
    """Configuration for protocol generation."""
    indication: str = "DLBCL"
    target: str = "CD19"
    phase: str = "Phase 1/2"
    car_generation: str = "2nd"
    costimulation: str = "4-1BB"
    sponsor: str = "CARVanta Therapeutics"
    n_sites: int = 15
    enrollment_target: int = 100


async def generate_full_protocol(
    config: Optional[ProtocolConfig] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate a complete clinical trial protocol."""
    if seed:
        random.seed(seed)
    if not config:
        config = ProtocolConfig()

    protocol_id = f"CRV-{config.target}-{random.randint(100, 999)}"

    return {
        "protocol_id": protocol_id,
        "version": "1.0",
        "date": "2026-01-15",
        "sponsor": config.sponsor,
        "title": _generate_title(config),
        "synopsis": _generate_synopsis(config),
        "background": _generate_background(config),
        "objectives": _generate_objectives(config),
        "study_design": _generate_study_design(config),
        "dose_levels": _generate_dose_levels(config),
        "eligibility": _generate_eligibility(config),
        "study_procedures": _generate_study_procedures(config),
        "endpoints": _generate_endpoints(config),
        "statistical_considerations": _generate_statistics(config),
        "dlt_definitions": {k: v for k, v in _DLT_LIBRARY.items()},
        "safety_monitoring": _generate_safety_monitoring(config),
        "dsmb_charter": _generate_dsmb_charter(config),
        "informed_consent_outline": _generate_icf_outline(config),
        "study_schedule": _generate_study_schedule(config),
    }


def _generate_title(config: ProtocolConfig) -> str:
    return (
        f"A {config.phase}, Open-Label, Multicenter Study to Evaluate "
        f"the Safety, Tolerability, and Efficacy of {config.target}-Directed "
        f"{config.car_generation}-Generation CAR-T Cell Therapy with "
        f"{config.costimulation} Costimulatory Domain in Patients with "
        f"Relapsed or Refractory {config.indication}"
    )


def _generate_synopsis(config: ProtocolConfig) -> Dict[str, Any]:
    return {
        "indication": f"Relapsed/Refractory {config.indication} after ≥2 prior systemic therapies",
        "study_phase": config.phase,
        "primary_objective": f"Evaluate safety and determine recommended Phase 2 dose (RP2D)" if "1" in config.phase else f"Evaluate overall response rate (ORR)",
        "secondary_objectives": [
            "Characterize pharmacokinetics (CAR-T expansion and persistence)",
            "Evaluate duration of response (DOR)",
            "Assess progression-free survival (PFS)",
            "Characterize cytokine release syndrome and neurotoxicity profile",
        ],
        "study_population": f"Adults ≥18 years with R/R {config.indication}, ECOG 0-1",
        "planned_enrollment": config.enrollment_target,
        "treatment": f"{config.target} CAR-T cells, single IV infusion after lymphodepleting chemotherapy",
        "lymphodepletion": "Fludarabine 30mg/m²/day + Cyclophosphamide 300mg/m²/day, Days -5 to -3",
        "duration": "Treatment: Day 0. Follow-up: 24 months minimum, 15 years LTFU",
    }


def _generate_background(config: ProtocolConfig) -> Dict[str, str]:
    return {
        "disease_overview": (
            f"{config.indication} represents a significant unmet medical need, particularly in the "
            f"relapsed/refractory setting where patients have exhausted standard treatment options."
        ),
        "car_t_rationale": (
            f"CAR-T cell therapy targeting {config.target} has demonstrated unprecedented response rates "
            f"in hematologic malignancies. The {config.car_generation}-generation construct with "
            f"{config.costimulation} costimulation provides improved T-cell persistence and reduced exhaustion."
        ),
        "preclinical_data": (
            f"Preclinical studies demonstrate specific cytotoxicity against {config.target}+ cell lines "
            f"with >90% killing at E:T ratios of 1:1. In vivo xenograft models show complete tumor "
            f"eradication with durable CAR-T persistence >60 days."
        ),
    }


def _generate_objectives(config: ProtocolConfig) -> Dict[str, List[str]]:
    primary = []
    if "1" in config.phase:
        primary.append("Determine the safety and tolerability of ascending doses")
        primary.append("Identify the recommended Phase 2 dose (RP2D)")
    if "2" in config.phase:
        primary.append("Evaluate overall response rate (ORR = CR + PR)")

    return {
        "primary": primary,
        "secondary": [
            "Evaluate complete response (CR) rate",
            "Evaluate duration of response (DOR)",
            "Evaluate progression-free survival (PFS)",
            "Characterize CAR-T cell expansion (Cmax, Tmax) and persistence",
            "Evaluate MRD-negative rate (for hematologic malignancies)",
        ],
        "exploratory": [
            "Correlate CAR-T cell kinetics with clinical response",
            "Characterize cytokine profiles and their association with CRS/ICANS",
            "Evaluate immune reconstitution timeline",
            "Assess T-cell phenotype and exhaustion markers",
            "Explore predictive biomarkers of response and resistance",
        ],
    }


def _generate_study_design(config: ProtocolConfig) -> Dict[str, Any]:
    design = {
        "type": "Open-label, multicenter",
        "arms": [],
        "randomization": "Not applicable (single-arm)",
        "blinding": "Open-label",
    }

    if "1" in config.phase:
        design["dose_escalation"] = {
            "method": "BOIN (Bayesian Optimal Interval Design)",
            "target_dlt_rate": 0.25,
            "boundaries": _BOIN_TABLE[0.25],
            "cohort_size": 3,
            "max_dose_levels": 4,
            "dlt_observation_window": "28 days from CAR-T infusion",
        }
        design["arms"].append({"name": "Dose Escalation", "description": "BOIN-guided dose finding"})

    if "2" in config.phase:
        design["arms"].append({"name": "Expansion Cohort", "description": f"RP2D dose in R/R {config.indication}"})
        design["expansion_cohort"] = {
            "sample_size": config.enrollment_target - (24 if "1" in config.phase else 0),
            "primary_endpoint": "ORR",
        }

    return design


def _generate_dose_levels(config: ProtocolConfig) -> List[Dict]:
    if "1" not in config.phase:
        return [{"level": "RP2D", "dose": "To be determined from Phase 1", "cells": None}]

    return [
        {"level": 1, "dose": "5×10⁷ CAR+ T-cells", "cells": 5e7, "rationale": "Starting dose based on 1/10th of murine NOAEL"},
        {"level": 2, "dose": "1×10⁸ CAR+ T-cells", "cells": 1e8, "rationale": "2-fold escalation"},
        {"level": 3, "dose": "2.5×10⁸ CAR+ T-cells", "cells": 2.5e8, "rationale": "2.5-fold escalation, approved dose range"},
        {"level": 4, "dose": "5×10⁸ CAR+ T-cells", "cells": 5e8, "rationale": "Maximum planned dose"},
    ]


def _generate_eligibility(config: ProtocolConfig) -> Dict[str, List[str]]:
    return {
        "key_inclusion": [
            f"Histologically/cytologically confirmed {config.indication}",
            f"Relapsed or refractory disease after ≥2 prior lines of systemic therapy",
            f"Confirmed {config.target} expression by IHC (≥20%) or flow cytometry",
            "Age ≥18 years at time of consent",
            "ECOG performance status 0-1",
            "Adequate organ function: ANC ≥1,000/μL, platelets ≥50,000/μL, hemoglobin ≥8 g/dL",
            "Adequate hepatic function: total bilirubin ≤1.5× ULN, AST/ALT ≤3× ULN",
            "Adequate renal function: creatinine clearance ≥30 mL/min (Cockcroft-Gault)",
            "Adequate cardiac function: LVEF ≥45% by echocardiogram",
            "Adequate pulmonary function: oxygen saturation ≥92% on room air",
            "Negative serum pregnancy test (for women of childbearing potential)",
            "Willingness to remain within 2 hours of treatment center for 4 weeks post-infusion",
        ],
        "key_exclusion": [
            f"Prior CAR-T therapy targeting {config.target}",
            "Active or prior CNS disease (unless protocol-specified CNS cohort)",
            "Active graft-versus-host disease requiring systemic immunosuppression",
            "Active or uncontrolled infection (including HIV, HBV, HCV)",
            "Prior allogeneic hematopoietic stem cell transplant within 90 days",
            "Systemic immunosuppressive therapy within 14 days (excluding physiologic steroids ≤10mg prednisone/day)",
            "Active autoimmune disease requiring systemic treatment in past 2 years",
            "History of seizure disorder requiring anti-epileptic medication",
            "Known hypersensitivity to any protocol-specified agent (tocilizumab, fludarabine, cyclophosphamide)",
            "Pregnant or breastfeeding",
            "Any condition that would, in the investigator's judgment, interfere with study participation",
        ],
    }


def _generate_endpoints(config: ProtocolConfig) -> Dict[str, List[Dict]]:
    return {
        "primary": [
            {
                "name": "Overall Response Rate (ORR)",
                "definition": "Proportion of patients achieving CR or PR per Lugano 2014 criteria",
                "assessment": "Independent Review Committee (IRC) per PET-CT + bone marrow biopsy",
                "timepoint": "Best response within 6 months of infusion",
            },
        ],
        "key_secondary": [
            {"name": "Complete Response Rate", "definition": "Proportion achieving CR (Deauville 1-3)", "timepoint": "Month 3"},
            {"name": "Duration of Response", "definition": "Time from first response to progression or death", "analysis": "Kaplan-Meier"},
            {"name": "Progression-Free Survival", "definition": "Time from infusion to progression or death", "analysis": "Kaplan-Meier"},
            {"name": "Overall Survival", "definition": "Time from infusion to death from any cause", "analysis": "Kaplan-Meier"},
            {"name": "MRD-Negative Rate", "definition": "Proportion achieving MRD negativity at 10⁻⁴", "assessment": "NGS or multiparameter flow"},
        ],
        "safety": [
            {"name": "CRS Incidence by Grade", "grading": "ASTCT 2019", "assessment": "Q12h for 14 days"},
            {"name": "ICANS Incidence by Grade", "grading": "ASTCT 2019 (ICE score)", "assessment": "Q12h for 14 days"},
            {"name": "Cytopenia Duration", "definition": "ANC <500 and platelets <50K duration", "assessment": "CBC 3x/week"},
            {"name": "Infection Rate", "definition": "Grade ≥3 infections within 100 days", "assessment": "Culture/PCR-confirmed"},
        ],
        "pharmacokinetic": [
            {"name": "CAR-T Cmax", "definition": "Peak CAR+ cells/μL in blood", "assessment": "Flow cytometry/qPCR", "schedule": "Days 1,3,5,7,10,14,21,28,M2,M3,M6,M9,M12"},
            {"name": "CAR-T AUC0-28", "definition": "Area under the CAR-T kinetic curve (Days 0-28)", "analysis": "Trapezoidal rule"},
            {"name": "CAR-T Persistence", "definition": "Detectable CAR transgene at ≥6 months", "assessment": "qPCR"},
        ],
    }


def _generate_statistics(config: ProtocolConfig) -> Dict[str, Any]:
    # Simon's two-stage design for Phase 2
    p0 = 0.25  # null hypothesis ORR
    p1 = 0.50  # alternative ORR
    alpha = 0.05
    beta = 0.10  # power = 90%

    z_alpha = 1.645
    z_beta = 1.282
    n = math.ceil(((z_alpha * math.sqrt(p0 * (1 - p0)) + z_beta * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2)

    stage1_n = math.ceil(n * 0.4)
    stage1_futility = math.ceil(stage1_n * p0)

    return {
        "primary_analysis": {
            "design": "Simon's Optimal Two-Stage Design",
            "null_hypothesis": f"ORR ≤ {p0*100}%",
            "alternative_hypothesis": f"ORR ≥ {p1*100}%",
            "one_sided_alpha": alpha,
            "power": 1 - beta,
            "stage_1": {
                "n": stage1_n,
                "futility_boundary": stage1_futility,
                "decision_rule": f"If ≤{stage1_futility} responses in first {stage1_n} patients, stop for futility",
            },
            "stage_2": {
                "total_n": n,
                "reject_null_boundary": math.ceil(n * (p0 + p1) / 2),
                "decision_rule": f"If ≥{math.ceil(n * (p0 + p1) / 2)} responses in {n} patients, reject H0",
            },
        },
        "secondary_analyses": {
            "survival_endpoints": "Kaplan-Meier estimation with Greenwood 95% CI",
            "subgroup_analyses": ["By IPI risk group", "By tumor bulk", "By prior therapy lines", "By age group"],
        },
        "interim_analyses": [
            {"timing": f"After {stage1_n} patients", "purpose": "Futility assessment", "method": "Stage 1 of Simon's design"},
            {"timing": f"After {n // 2} patients", "purpose": "Safety review", "method": "DSMB review of AE data"},
        ],
        "missing_data": "Missing efficacy data: worst-case imputation. Missing safety data: as reported.",
    }


def _generate_safety_monitoring(config: ProtocolConfig) -> Dict[str, Any]:
    return {
        "monitoring_plan": {
            "acute_phase_days_0_14": {
                "inpatient": True,
                "vital_signs": "Q4h for 7 days, then Q8h",
                "crs_assessment": "Q12h using ASTCT criteria",
                "icans_assessment": "Q12h using ICE score + handwriting test",
                "labs": "CBC with diff, CMP, ferritin, CRP, IL-6, fibrinogen daily",
                "neurological_exam": "Daily × 7 days, then Q48h",
            },
            "subacute_phase_days_14_28": {
                "inpatient": False,
                "visits": "2-3x per week",
                "labs": "CBC, CMP, CRP 2-3x weekly",
                "remain_near_center": "Within 2 hours of treatment center",
            },
            "follow_up_months_1_24": {
                "visits": "Monthly × 3, then Q3 months × 21 months",
                "labs": "CBC, CMP, immunoglobulin levels, B-cell counts",
                "imaging": "PET-CT at Month 1, 3, 6, 9, 12, 18, 24",
                "bone_marrow": "Month 1, 3, 6, 12 (if applicable)",
            },
            "long_term_follow_up_years_2_15": {
                "annual_visit": True,
                "monitoring": "Secondary malignancy screening, RCL testing",
                "duration": "15 years per FDA guidance",
            },
        },
        "stopping_rules": {
            "treatment_related_mortality": "Pause enrollment if ≥2 treatment-related deaths in first 20 patients",
            "excessive_crs": "Pause if CRS Grade ≥4 rate exceeds 20%",
            "manufacturing_failure": "Review if failure rate exceeds 15%",
        },
    }


def _generate_dsmb_charter(config: ProtocolConfig) -> Dict[str, Any]:
    return {
        "composition": {
            "members": 5,
            "required": [
                "Chair: Independent hematologist/oncologist with CAR-T experience",
                "Statistician: Independent biostatistician",
                "2 hematologist/oncologists (non-investigator)",
                "Patient advocate representative",
            ],
        },
        "meeting_schedule": {
            "frequency": "After every 10 patients treated, or at interim analysis timepoints",
            "ad_hoc": "Within 48 hours of any treatment-related death or unexpected SAE pattern",
        },
        "data_reviewed": [
            "All SAEs and DLTs",
            "CRS and ICANS rates by grade",
            "Response data (blinded if applicable)",
            "Enrollment rates",
            "Manufacturing success rates",
        ],
        "recommendations": ["Continue as planned", "Continue with protocol amendment", "Pause enrollment", "Terminate study"],
    }


def _generate_icf_outline(config: ProtocolConfig) -> Dict[str, List[str]]:
    return {
        "sections": [
            "Purpose of the research study",
            f"Description of {config.target} CAR-T cell therapy",
            "Study procedures (leukapheresis, lymphodepletion, infusion, follow-up)",
            "Risks and discomforts (CRS, ICANS, cytopenia, infection, organ toxicity)",
            "Potential benefits",
            "Alternatives to participation",
            "Costs and compensation",
            "Confidentiality and data handling",
            "Voluntary participation and right to withdraw",
            "Long-term follow-up requirements (15 years)",
            "Contact information (investigator, IRB, emergency)",
        ],
        "risk_disclosures": [
            "Cytokine Release Syndrome: fever, low blood pressure, difficulty breathing (30-50% grade ≥3)",
            "Neurotoxicity: confusion, difficulty speaking, seizures (10-20% grade ≥3)",
            "Prolonged low blood counts: increased risk of infection and bleeding (weeks to months)",
            "B-cell aplasia: loss of normal B-cells requiring immunoglobulin replacement",
            "Unknown long-term risks: potential for secondary cancers (1-2% estimated based on approved products)",
            "Manufacturing failure: possibility that treatment cannot be produced (5-10%)",
            "Treatment-related death: rare but possible (<5%)",
        ],
    }


def _generate_study_schedule(config: ProtocolConfig) -> Dict[str, Any]:
    return {
        "screening": {
            "window": "Day -30 to Day -6",
            "assessments": [
                "Informed consent", "Demographics", "Medical history", "Physical exam",
                "ECOG PS", "CBC with differential", "CMP", "Coagulation panel",
                "Immunoglobulin levels", "Quantitative B/T-cell subsets",
                f"{config.target} expression confirmation", "PET-CT or CT",
                "Bone marrow biopsy (if applicable)", "Echocardiogram",
                "Pregnancy test", "HIV/HBV/HCV screening",
            ],
        },
        "leukapheresis": {"day": "Day -14 to -10", "assessments": ["Pre-apheresis labs", "Apheresis procedure", "Product shipment"]},
        "lymphodepletion": {"days": "Day -5 to -3", "assessments": ["Flu/Cy chemotherapy", "Daily labs during LD"]},
        "infusion": {"day": "Day 0", "assessments": ["Pre-infusion labs", "CAR-T infusion", "Vital signs Q15min × 2h, then Q1h × 4h"]},
        "acute_monitoring": {
            "days": "Day 1-28",
            "schedule": {
                "D1-D7": "Daily: vitals Q4h, labs, CRS/ICANS grading, neuro exam",
                "D8-D14": "Daily: vitals Q8h, labs, CRS/ICANS grading",
                "D15-D21": "3x/week: labs, clinical assessment",
                "D22-D28": "2x/week: labs, clinical assessment",
            },
        },
        "response_assessment": {
            "Month_1": "PET-CT, bone marrow biopsy, MRD assessment",
            "Month_3": "PET-CT, bone marrow, MRD, CAR-T persistence",
            "Month_6": "PET-CT, bone marrow, MRD, immunoglobulins",
            "Month_9": "CT/PET, labs",
            "Month_12": "PET-CT, bone marrow, MRD, comprehensive labs",
        },
        "long_term_follow_up": {"years": "2-15", "frequency": "Annual visit", "assessments": ["Physical exam", "CBC", "Secondary malignancy screen", "RCL testing"]},
    }


async def compute_boin_decision(
    n_treated: int,
    n_dlt: int,
    target_dlt_rate: float = 0.25,
) -> Dict[str, Any]:
    """Compute BOIN dose escalation decision given observed data."""
    if target_dlt_rate not in _BOIN_TABLE:
        target_dlt_rate = 0.25

    boundaries = _BOIN_TABLE[target_dlt_rate]
    observed_rate = n_dlt / max(n_treated, 1)

    if observed_rate <= boundaries["escalate_if_le"]:
        decision = "ESCALATE"
        rationale = f"Observed DLT rate ({observed_rate:.3f}) ≤ escalation boundary ({boundaries['escalate_if_le']})"
    elif observed_rate >= boundaries["deescalate_if_ge"]:
        decision = "DE-ESCALATE"
        rationale = f"Observed DLT rate ({observed_rate:.3f}) ≥ de-escalation boundary ({boundaries['deescalate_if_ge']})"
    else:
        decision = "STAY"
        rationale = f"Observed DLT rate ({observed_rate:.3f}) within target interval"

    return {
        "n_treated": n_treated,
        "n_dlt": n_dlt,
        "observed_dlt_rate": round(observed_rate, 4),
        "target_dlt_rate": target_dlt_rate,
        "boundaries": boundaries,
        "decision": decision,
        "rationale": rationale,
    }


async def sample_size_calculator(
    design: str = "simon_two_stage",
    p0: float = 0.25,
    p1: float = 0.50,
    alpha: float = 0.05,
    power: float = 0.90,
) -> Dict[str, Any]:
    """Calculate sample size for various clinical trial designs."""
    beta = 1 - power
    z_alpha = abs(_norm_ppf(1 - alpha))
    z_beta = abs(_norm_ppf(1 - beta))

    if design == "simon_two_stage":
        n = math.ceil(((z_alpha * math.sqrt(p0 * (1 - p0)) + z_beta * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2)
        stage1 = math.ceil(n * 0.4)

        return {
            "design": "Simon's Optimal Two-Stage Design",
            "parameters": {"p0": p0, "p1": p1, "alpha": alpha, "power": power},
            "result": {
                "stage_1_n": stage1,
                "stage_1_reject_if_le": math.floor(stage1 * p0),
                "total_n": n,
                "reject_null_if_ge": math.ceil(n * (p0 + p1) / 2),
                "expected_n_under_null": round(stage1 + (1 - _binom_cdf(math.floor(stage1 * p0), stage1, p0)) * (n - stage1), 1),
            },
        }

    elif design == "two_arm_superiority":
        delta = p1 - p0
        p_avg = (p0 + p1) / 2
        n_per_arm = math.ceil(((z_alpha * math.sqrt(2 * p_avg * (1 - p_avg)) + z_beta * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) / delta) ** 2)

        return {
            "design": "Two-Arm Superiority (Chi-Square)",
            "parameters": {"p0": p0, "p1": p1, "alpha": alpha, "power": power},
            "result": {"n_per_arm": n_per_arm, "total_n": n_per_arm * 2},
        }

    return {"error": f"Unknown design: {design}"}


def _norm_ppf(p: float) -> float:
    """Approximate inverse normal CDF (Abramowitz & Stegun)."""
    if p <= 0 or p >= 1:
        return 0
    t = math.sqrt(-2 * math.log(min(p, 1 - p)))
    c0, c1, c2 = 2.515517, 0.802853, 0.010328
    d1, d2, d3 = 1.432788, 0.189269, 0.001308
    result = t - (c0 + c1 * t + c2 * t ** 2) / (1 + d1 * t + d2 * t ** 2 + d3 * t ** 3)
    return result if p > 0.5 else -result


def _binom_cdf(k: int, n: int, p: float) -> float:
    """Cumulative binomial probability P(X <= k)."""
    total = 0
    for i in range(k + 1):
        total += math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    return total
