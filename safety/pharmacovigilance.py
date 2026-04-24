"""
CARVanta Safety — Pharmacovigilance Engine
=============================================
Post-market safety surveillance, adverse event signal
detection, and risk-benefit analysis for CAR-T therapies.

Features:
- Individual Case Safety Report (ICSR) generation
- MedDRA-coded adverse event classification
- Disproportionality analysis (PRR, ROR, BCPNN)
- Signal detection algorithms
- Risk-benefit scoring framework
- REMS program monitoring
- FDA FAERS integration modeling
- Periodic Safety Update Report (PSUR) data
"""

import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger("carvanta.safety.pharmacovigilance")


# ──────────────────────────────────────────────────────────────────────
# MedDRA Adverse Event Dictionary
# ──────────────────────────────────────────────────────────────────────

@dataclass
class AdverseEvent:
    """MedDRA-coded adverse event."""
    pt_code: str       # Preferred Term code
    pt_name: str       # Preferred Term name
    soc: str           # System Organ Class
    hlt: str           # High Level Term
    severity_distribution: Dict[str, float] = field(default_factory=dict)
    car_t_specific: bool = False
    median_onset_days: float = 7
    management: str = ""


_AE_DICTIONARY: Dict[str, AdverseEvent] = {
    "CRS": AdverseEvent("10068752", "Cytokine release syndrome", "Immune system disorders",
        "Cytokine-related disorders", {"Grade 1": 0.35, "Grade 2": 0.30, "Grade 3": 0.20, "Grade 4": 0.10, "Grade 5": 0.02},
        True, 3, "Tocilizumab ± corticosteroids per ASTCT grading"),
    "ICANS": AdverseEvent("10082484", "Immune effector cell-associated neurotoxicity",
        "Nervous system disorders", "Neurotoxicity",
        {"Grade 1": 0.30, "Grade 2": 0.25, "Grade 3": 0.18, "Grade 4": 0.08, "Grade 5": 0.01},
        True, 5, "Dexamethasone; seizure prophylaxis with levetiracetam"),
    "CYTOPENIAS": AdverseEvent("10011968", "Cytopenias", "Blood and lymphatic system disorders",
        "Bone marrow failure", {"Grade 1": 0.10, "Grade 2": 0.20, "Grade 3": 0.40, "Grade 4": 0.25},
        True, 7, "Growth factors; transfusion support"),
    "NEUTROPENIA": AdverseEvent("10029354", "Neutropenia", "Blood and lymphatic system disorders",
        "Neutropenias", {"Grade 3": 0.45, "Grade 4": 0.35},
        True, 7, "G-CSF if prolonged; antimicrobial prophylaxis"),
    "THROMBOCYTOPENIA": AdverseEvent("10043554", "Thrombocytopenia",
        "Blood and lymphatic system disorders", "Thrombocytopenias",
        {"Grade 3": 0.30, "Grade 4": 0.15}, True, 10, "Platelet transfusion if <10K or bleeding"),
    "INFECTION": AdverseEvent("10021789", "Infection", "Infections and infestations",
        "Infections NEC",
        {"Grade 1": 0.15, "Grade 2": 0.20, "Grade 3": 0.30, "Grade 4": 0.10, "Grade 5": 0.03},
        False, 14, "Broad-spectrum antibiotics; IVIG for hypogammaglobulinemia"),
    "HYPOGAMMA": AdverseEvent("10020607", "Hypogammaglobulinemia",
        "Immune system disorders", "Immunodeficiency disorders",
        {"Grade 1": 0.30, "Grade 2": 0.40, "Grade 3": 0.15},
        True, 30, "IVIG replacement if IgG <400 mg/dL"),
    "TUMOR_LYSIS": AdverseEvent("10045170", "Tumour lysis syndrome",
        "Metabolism and nutrition disorders", "Purine/pyrimidine metabolism disorders",
        {"Grade 1": 0.10, "Grade 3": 0.08, "Grade 4": 0.03, "Grade 5": 0.01},
        False, 2, "Rasburicase; aggressive hydration; allopurinol"),
    "HLH_MAS": AdverseEvent("10019678", "Haemophagocytic lymphohistiocytosis",
        "Blood and lymphatic system disorders", "Histiocytic disorders",
        {"Grade 3": 0.04, "Grade 4": 0.02, "Grade 5": 0.01},
        True, 7, "High-dose corticosteroids; etoposide; anakinra"),
    "CEREBRAL_EDEMA": AdverseEvent("10007760", "Cerebral oedema",
        "Nervous system disorders", "Brain oedema",
        {"Grade 3": 0.01, "Grade 4": 0.005, "Grade 5": 0.003},
        True, 6, "Emergency: mannitol, hypertonic saline, neurosurgery consult"),
    "CARDIAC": AdverseEvent("10007515", "Cardiac disorder",
        "Cardiac disorders", "Cardiac disorders NEC",
        {"Grade 1": 0.08, "Grade 2": 0.05, "Grade 3": 0.03, "Grade 4": 0.01},
        False, 5, "Troponin monitoring; cardiology consult; inotropic support"),
    "B_CELL_APLASIA": AdverseEvent("10004530", "B-cell aplasia",
        "Blood and lymphatic system disorders", "Bone marrow failure",
        {"Grade 1": 0.50, "Grade 2": 0.35},
        True, 14, "Expected on-target effect; IVIG replacement"),
    "COAGULOPATHY": AdverseEvent("10009797", "Coagulopathy",
        "Blood and lymphatic system disorders", "Coagulopathies",
        {"Grade 1": 0.10, "Grade 2": 0.08, "Grade 3": 0.05, "Grade 4": 0.02},
        False, 5, "FFP, cryoprecipitate; fibrinogen replacement"),
    "GVHD": AdverseEvent("10018135", "Graft versus host disease",
        "Immune system disorders", "Transplant-related disorders",
        {"Grade 1": 0.02, "Grade 2": 0.01, "Grade 3": 0.005},
        True, 21, "Corticosteroids; ruxolitinib; ibrutinib"),
    "SECONDARY_MALIG": AdverseEvent("10039722", "Secondary malignancy",
        "Neoplasms benign, malignant, unspecified", "Malignant neoplasms",
        {"Grade 3": 0.005, "Grade 4": 0.002},
        True, 365, "Per FDA REMS; 15-year monitoring"),
}


# ──────────────────────────────────────────────────────────────────────
# Pharmacovigilance Functions
# ──────────────────────────────────────────────────────────────────────

async def generate_icsr(
    product: str = "axi-cel",
    patient_age: int = 55,
    ae_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an Individual Case Safety Report (ICSR)."""
    random.seed(42)
    case_id = f"ICSR-{uuid.uuid4().hex[:10].upper()}"

    ae_code = ae_type or random.choice(list(_AE_DICTIONARY.keys()))
    ae = _AE_DICTIONARY.get(ae_code)
    if not ae:
        return {"error": f"Unknown AE type: {ae_code}"}

    # Random severity from distribution
    grades = list(ae.severity_distribution.keys())
    weights = list(ae.severity_distribution.values())
    severity = random.choices(grades, weights=weights, k=1)[0]

    # Outcome
    if "Grade 5" in severity:
        outcome = "fatal"
    elif "Grade 4" in severity:
        outcome = random.choice(["recovering", "not_recovered", "recovered_with_sequelae"])
    else:
        outcome = random.choice(["recovered", "recovering", "recovered"])

    onset = datetime.now() - timedelta(days=random.randint(1, 180))
    onset_from_infusion = max(1, int(ae.median_onset_days + random.gauss(0, ae.median_onset_days * 0.3)))

    return {
        "case_id": case_id,
        "report_type": "spontaneous",
        "seriousness": "serious" if "Grade 3" in severity or "Grade 4" in severity or "Grade 5" in severity else "non-serious",
        "product": {
            "name": product,
            "indication": "relapsed/refractory DLBCL",
            "dose": "1-2×10⁸ CAR+ T cells",
        },
        "patient": {
            "age": patient_age,
            "sex": random.choice(["M", "F"]),
            "weight_kg": random.randint(50, 100),
        },
        "adverse_event": {
            "meddra_pt": ae.pt_name,
            "meddra_code": ae.pt_code,
            "soc": ae.soc,
            "hlt": ae.hlt,
            "severity": severity,
            "seriousness_criteria": ["hospitalization", "life-threatening"] if "Grade 4" in severity else ["hospitalization"],
            "onset_date": onset.isoformat()[:10],
            "onset_days_from_infusion": onset_from_infusion,
            "car_t_specific": ae.car_t_specific,
        },
        "management": ae.management,
        "outcome": outcome,
        "causality": random.choice(["certain", "probable", "possible"]),
        "reporter": {"type": "physician", "country": random.choice(["US", "EU", "UK", "JP"])},
    }


async def disproportionality_analysis(
    product: str = "axi-cel",
    n_reports: int = 5000,
) -> Dict[str, Any]:
    """Run disproportionality analysis across all AE types (PRR, ROR, BCPNN)."""
    random.seed(42)

    signals = []
    for code, ae in _AE_DICTIONARY.items():
        # Simulated counts
        a = random.randint(10, 500)  # product + AE
        b = random.randint(50, 2000)  # product + no AE
        c = random.randint(20, 1000)  # no product + AE
        d = n_reports - a - b - c

        # PRR
        prr = (a / max(a + b, 1)) / (c / max(c + d, 1))
        prr_chi2 = ((a * d - b * c) ** 2 * (a + b + c + d)) / max((a + b) * (c + d) * (a + c) * (b + d), 1)

        # ROR
        ror = (a * d) / max(b * c, 1)

        # BCPNN IC
        expected = (a + b) * (a + c) / max(a + b + c + d, 1)
        ic = math.log2(a / max(expected, 0.001)) if expected > 0 else 0

        is_signal = prr > 2.0 and prr_chi2 > 4.0 and a >= 3
        signals.append({
            "ae_code": code,
            "ae_name": ae.pt_name,
            "soc": ae.soc,
            "car_t_specific": ae.car_t_specific,
            "counts": {"a": a, "b": b, "c": c, "d": max(0, d)},
            "prr": round(prr, 2),
            "chi_squared": round(prr_chi2, 2),
            "ror": round(ror, 2),
            "ic": round(ic, 3),
            "is_signal": is_signal,
            "signal_strength": "strong" if prr > 5 and is_signal else "moderate" if is_signal else "none",
        })

    signals.sort(key=lambda x: x["prr"], reverse=True)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "product": product,
        "total_reports": n_reports,
        "total_aes_analyzed": len(signals),
        "signals_detected": sum(1 for s in signals if s["is_signal"]),
        "strong_signals": sum(1 for s in signals if s["signal_strength"] == "strong"),
        "methods": ["PRR (Proportional Reporting Ratio)", "ROR (Reporting Odds Ratio)", "BCPNN (IC)"],
        "results": signals,
    }


async def risk_benefit_analysis(
    product: str = "axi-cel",
    cancer_type: str = "DLBCL",
) -> Dict[str, Any]:
    """Risk-benefit scoring for a CAR-T product."""
    random.seed(42)

    # Efficacy data
    efficacy = {
        "ORR": random.uniform(0.70, 0.85),
        "CR_rate": random.uniform(0.45, 0.65),
        "median_PFS_months": random.uniform(8, 18),
        "median_OS_months": random.uniform(18, 36),
        "durable_CR_rate": random.uniform(0.30, 0.50),
    }

    # Safety data
    safety = {
        "any_grade_CRS": random.uniform(0.80, 0.95),
        "grade_3plus_CRS": random.uniform(0.08, 0.20),
        "any_grade_ICANS": random.uniform(0.50, 0.70),
        "grade_3plus_ICANS": random.uniform(0.10, 0.25),
        "grade_3plus_cytopenias": random.uniform(0.60, 0.80),
        "grade_3plus_infections": random.uniform(0.15, 0.30),
        "treatment_related_mortality": random.uniform(0.01, 0.04),
    }

    # Compute composite scores
    efficacy_score = (efficacy["ORR"] * 0.3 + efficacy["CR_rate"] * 0.3 +
                      min(efficacy["median_PFS_months"] / 24, 1) * 0.2 +
                      efficacy["durable_CR_rate"] * 0.2)

    safety_score = 1 - (safety["grade_3plus_CRS"] * 0.25 +
                        safety["grade_3plus_ICANS"] * 0.20 +
                        safety["treatment_related_mortality"] * 0.30 +
                        safety["grade_3plus_infections"] * 0.25)

    rba_score = efficacy_score * 0.6 + safety_score * 0.4

    return {
        "product": product,
        "cancer_type": cancer_type,
        "efficacy": {k: round(v, 3) for k, v in efficacy.items()},
        "safety": {k: round(v, 3) for k, v in safety.items()},
        "composite_scores": {
            "efficacy_score": round(efficacy_score, 3),
            "safety_score": round(safety_score, 3),
            "risk_benefit_score": round(rba_score, 3),
            "classification": "favorable" if rba_score > 0.65 else "moderate" if rba_score > 0.45 else "unfavorable",
        },
        "comparator": {
            "salvage_chemotherapy_ORR": 0.26,
            "salvage_chemotherapy_CR": 0.07,
            "NNT_vs_chemo": round(1 / max(efficacy["CR_rate"] - 0.07, 0.01), 1),
        },
    }


async def rems_monitoring(
    product: str = "axi-cel",
    n_patients: int = 200,
) -> Dict[str, Any]:
    """Simulate REMS program monitoring data."""
    random.seed(42)

    patients = []
    for i in range(n_patients):
        enrolled_days_ago = random.randint(30, 730)
        crs_occurred = random.random() < 0.85
        icans_occurred = random.random() < 0.55
        secondary_malig = random.random() < 0.01

        patients.append({
            "patient_id": f"REMS-{i+1:04d}",
            "enrollment_date": (datetime.now() - timedelta(days=enrolled_days_ago)).isoformat()[:10],
            "follow_up_months": round(enrolled_days_ago / 30, 1),
            "crs_reported": crs_occurred,
            "crs_grade": random.choice([1, 2, 3, 4]) if crs_occurred else 0,
            "icans_reported": icans_occurred,
            "icans_grade": random.choice([1, 2, 3, 4]) if icans_occurred else 0,
            "tocilizumab_used": crs_occurred and random.random() < 0.6,
            "icu_admission": random.random() < 0.25,
            "secondary_malignancy": secondary_malig,
            "alive": random.random() < 0.85,
            "lost_to_followup": random.random() < 0.08,
        })

    return {
        "program": f"{product.upper()} REMS",
        "total_enrolled": n_patients,
        "monitoring_period": "15 years (FDA requirement)",
        "summary": {
            "crs_incidence": round(sum(1 for p in patients if p["crs_reported"]) / n_patients * 100, 1),
            "icans_incidence": round(sum(1 for p in patients if p["icans_reported"]) / n_patients * 100, 1),
            "icu_rate": round(sum(1 for p in patients if p["icu_admission"]) / n_patients * 100, 1),
            "secondary_malignancy": sum(1 for p in patients if p["secondary_malignancy"]),
            "mortality": round(sum(1 for p in patients if not p["alive"]) / n_patients * 100, 1),
            "lost_to_followup": round(sum(1 for p in patients if p["lost_to_followup"]) / n_patients * 100, 1),
        },
        "patients_sample": patients[:20],
    }


async def get_ae_dictionary() -> Dict[str, Any]:
    """Get the complete adverse event dictionary."""
    return {
        "total_events": len(_AE_DICTIONARY),
        "events": [
            {
                "code": code,
                "name": ae.pt_name,
                "meddra_code": ae.pt_code,
                "soc": ae.soc,
                "car_t_specific": ae.car_t_specific,
                "median_onset_days": ae.median_onset_days,
                "management": ae.management,
                "severity_distribution": ae.severity_distribution,
            }
            for code, ae in _AE_DICTIONARY.items()
        ],
    }
