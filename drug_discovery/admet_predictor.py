"""
CARVanta Drug Discovery — ADMET Prediction Engine
====================================================
Absorption, Distribution, Metabolism, Excretion, Toxicity prediction
for CAR-T cell therapy-related small molecules and biologics.

Features:
- Physicochemical property prediction (Lipinski, Veber, etc.)
- ADME parameter estimation for co-administered drugs
- Toxicity risk profiling (CRS inducers, neurotoxicity, cardiotoxicity)
- Drug-drug interaction prediction with CAR-T supportive therapies
- PK/PD modeling for tocilizumab, corticosteroids, and ICIs
- Therapeutic window optimization

Models: Rule-based predictions using published pharmacokinetic parameters.
"""

import logging
import math
import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.drug_discovery.admet_predictor")


@dataclass
class DrugProfile:
    name: str
    drug_class: str
    molecular_weight: float
    logp: float
    hbd: int  # hydrogen bond donors
    hba: int  # hydrogen bond acceptors
    tpsa: float  # topological polar surface area
    rotatable_bonds: int
    bioavailability: float  # oral, 0-1
    protein_binding: float  # fraction 0-1
    half_life_hours: float
    clearance_ml_min: float
    vd_L: float  # volume of distribution
    metabolism: str  # primary enzyme
    elimination: str  # primary route
    toxicity_flags: List[str] = field(default_factory=list)
    cart_relevance: str = ""


# Drug database for CAR-T relevant molecules
_DRUGS: Dict[str, DrugProfile] = {
    "tocilizumab": DrugProfile(
        "Tocilizumab", "IL-6R mAb", 148000, -4.0, 250, 400, 5000, 0,
        0.0, 0.95, 312, 0.12, 6.4, "Proteolysis", "RES clearance",
        [], "CRS treatment — anti-IL-6R blocks cytokine storm cascade"
    ),
    "dexamethasone": DrugProfile(
        "Dexamethasone", "Corticosteroid", 392.5, 1.83, 3, 6, 94.8, 2,
        0.80, 0.68, 36, 3.7, 0.82, "CYP3A4", "Hepatic/Renal",
        ["immunosuppression", "hyperglycemia", "myopathy"],
        "CRS/ICANS management — broad immune suppression"
    ),
    "siltuximab": DrugProfile(
        "Siltuximab", "Anti-IL-6 mAb", 145500, -3.8, 240, 380, 4800, 0,
        0.0, 0.92, 480, 0.08, 4.7, "Proteolysis", "RES clearance",
        [], "Anti-IL-6 for CRS — binds IL-6 directly (vs receptor)"
    ),
    "levetiracetam": DrugProfile(
        "Levetiracetam", "Antiepileptic", 170.2, -0.64, 2, 3, 63.4, 3,
        0.95, 0.10, 7, 0.96, 0.7, "Hydrolysis", "Renal (66% unchanged)",
        [], "ICANS seizure prophylaxis"
    ),
    "anakinra": DrugProfile(
        "Anakinra", "IL-1Ra", 17258, -6.0, 120, 180, 2200, 0,
        0.0, 0.30, 6, 2.1, 0.14, "Proteolysis", "Renal",
        [], "Alternative CRS treatment — IL-1 receptor antagonist"
    ),
    "fludarabine": DrugProfile(
        "Fludarabine", "Purine analog", 365.2, -1.0, 4, 9, 139.5, 3,
        0.55, 0.19, 20, 8.9, 0.96, "Deaminase", "Renal (40%)",
        ["myelosuppression", "immunosuppression", "neurotoxicity"],
        "Lymphodepletion conditioning — purine analog"
    ),
    "cyclophosphamide": DrugProfile(
        "Cyclophosphamide", "Alkylating agent", 261.1, 0.63, 2, 4, 41.6, 4,
        0.75, 0.13, 6, 4.5, 0.50, "CYP2B6/3A4", "Renal/Hepatic",
        ["myelosuppression", "hemorrhagic_cystitis", "cardiotoxicity_high_dose"],
        "Lymphodepletion conditioning — with fludarabine"
    ),
    "ruxolitinib": DrugProfile(
        "Ruxolitinib", "JAK1/2 inhibitor", 306.4, 1.85, 1, 4, 83.2, 4,
        0.95, 0.97, 3, 11.7, 0.75, "CYP3A4/2C9", "Hepatic (74%)",
        ["cytopenias", "infections"],
        "Steroid-refractory CRS/ICANS — JAK pathway blockade"
    ),
    "ivig": DrugProfile(
        "IVIG", "Polyclonal IgG", 150000, -4.5, 250, 400, 5000, 0,
        0.0, 0.99, 504, 0.05, 3.2, "Proteolysis", "RES clearance",
        ["infusion_reactions", "headache"],
        "Hypogammaglobulinemia treatment post-CAR-T"
    ),
}


# ──────────────────────────────────────────────────────────────────────
# ADMET Prediction Functions
# ──────────────────────────────────────────────────────────────────────

async def predict_admet(drug_name: str) -> Optional[Dict[str, Any]]:
    """Predict ADMET properties for a drug."""
    drug = _DRUGS.get(drug_name.lower())
    if not drug:
        return None

    # Lipinski Rule of 5
    lipinski_violations = sum([
        drug.molecular_weight > 500,
        drug.logp > 5,
        drug.hbd > 5,
        drug.hba > 10,
    ])
    passes_lipinski = lipinski_violations <= 1

    # Veber rules (oral bioavailability)
    passes_veber = drug.rotatable_bonds <= 10 and drug.tpsa <= 140

    # GI absorption prediction
    gi_absorption = "High" if passes_lipinski and passes_veber else "Low" if drug.molecular_weight > 1000 else "Moderate"

    # BBB penetration (relevant for ICANS)
    bbb_penetration = "Yes" if drug.logp > 1 and drug.tpsa < 90 and drug.molecular_weight < 500 else "No"

    # CYP interaction risk
    cyp_risk = "High" if "CYP3A4" in drug.metabolism else "Medium" if "CYP" in drug.metabolism else "Low"

    return {
        "drug": drug.name,
        "class": drug.drug_class,
        "cart_relevance": drug.cart_relevance,
        "physicochemical": {
            "molecular_weight": drug.molecular_weight,
            "logP": drug.logp,
            "HBD": drug.hbd,
            "HBA": drug.hba,
            "TPSA": drug.tpsa,
            "rotatable_bonds": drug.rotatable_bonds,
        },
        "druglikeness": {
            "lipinski_violations": lipinski_violations,
            "passes_lipinski": passes_lipinski,
            "passes_veber": passes_veber,
            "is_biologic": drug.molecular_weight > 5000,
        },
        "absorption": {
            "bioavailability": drug.bioavailability,
            "gi_absorption": gi_absorption,
            "bbb_penetration": bbb_penetration,
        },
        "distribution": {
            "protein_binding": drug.protein_binding,
            "volume_of_distribution_L": drug.vd_L,
        },
        "metabolism": {
            "primary_enzyme": drug.metabolism,
            "cyp_interaction_risk": cyp_risk,
        },
        "excretion": {
            "half_life_hours": drug.half_life_hours,
            "clearance_ml_min": drug.clearance_ml_min,
            "primary_route": drug.elimination,
        },
        "toxicity": {
            "flags": drug.toxicity_flags,
            "risk_level": "High" if len(drug.toxicity_flags) >= 3 else "Medium" if drug.toxicity_flags else "Low",
        },
    }


async def list_drugs(drug_class: Optional[str] = None) -> Dict[str, Any]:
    """List all drugs in the database."""
    results = list(_DRUGS.values())
    if drug_class:
        results = [d for d in results if drug_class.lower() in d.drug_class.lower()]
    return {
        "total": len(results),
        "drugs": [
            {"name": d.name, "class": d.drug_class,
             "mw": d.molecular_weight, "half_life_h": d.half_life_hours,
             "relevance": d.cart_relevance[:60]}
            for d in results
        ],
    }


async def predict_drug_interaction(
    drug1: str, drug2: str,
) -> Dict[str, Any]:
    """Predict interaction between two drugs."""
    d1 = _DRUGS.get(drug1.lower())
    d2 = _DRUGS.get(drug2.lower())
    if not d1 or not d2:
        return {"error": "Drug not found"}

    # CYP-based interaction detection
    cyp_shared = "CYP3A4" in d1.metabolism and "CYP3A4" in d2.metabolism
    immunosuppression = "immunosuppression" in d1.toxicity_flags and "immunosuppression" in d2.toxicity_flags

    interactions = []
    if cyp_shared:
        interactions.append({
            "type": "PK", "mechanism": "CYP3A4 competition",
            "severity": "moderate", "clinical": f"May increase levels of {d1.name} and/or {d2.name}",
        })
    if immunosuppression:
        interactions.append({
            "type": "PD", "mechanism": "Additive immunosuppression",
            "severity": "high", "clinical": "Increased infection risk — monitor closely",
        })

    if d1.drug_class == "Corticosteroid" and "mAb" in d2.drug_class:
        interactions.append({
            "type": "PD", "mechanism": "Corticosteroid may reduce CAR-T efficacy",
            "severity": "high", "clinical": "Dexamethasone can suppress CAR-T expansion — use minimum effective dose",
        })

    return {
        "drug1": d1.name, "drug2": d2.name,
        "interactions": interactions,
        "interaction_count": len(interactions),
        "overall_risk": "High" if any(i["severity"] == "high" for i in interactions) else "Low" if not interactions else "Moderate",
    }


async def pk_simulation(
    drug_name: str, dose_mg: float = 100, interval_hours: float = 24,
    doses: int = 5,
) -> Dict[str, Any]:
    """Simple 1-compartment PK simulation."""
    drug = _DRUGS.get(drug_name.lower())
    if not drug:
        return {"error": "Drug not found"}

    ke = 0.693 / drug.half_life_hours  # elimination rate constant
    ka = ke * 3  # absorption rate (simplified)
    vd = drug.vd_L if drug.vd_L > 0 else 50.0
    f = drug.bioavailability if drug.bioavailability > 0 else 1.0

    timepoints = []
    for dose_num in range(doses):
        dose_time = dose_num * interval_hours
        for t_offset in [0, 0.5, 1, 2, 4, 8, 12, 24]:
            t = dose_time + t_offset
            if t > doses * interval_hours:
                break
            # Sum contributions from all previous doses
            conc = 0.0
            for prev_dose in range(dose_num + 1):
                t_since_dose = t - prev_dose * interval_hours
                if t_since_dose < 0:
                    continue
                if drug.bioavailability > 0:
                    conc += (f * dose_mg * ka / (vd * (ka - ke))) * (
                        math.exp(-ke * t_since_dose) - math.exp(-ka * t_since_dose)
                    )
                else:
                    conc += (dose_mg / vd) * math.exp(-ke * t_since_dose)

            timepoints.append({"time_h": round(t, 1), "concentration_ug_mL": round(max(0, conc), 3)})

    # Steady-state estimates
    css_max = (f * dose_mg) / (vd * (1 - math.exp(-ke * interval_hours))) if ke > 0 else 0
    css_min = css_max * math.exp(-ke * interval_hours) if ke > 0 else 0

    return {
        "drug": drug.name, "dose_mg": dose_mg,
        "interval_hours": interval_hours, "doses": doses,
        "pk_parameters": {
            "ke_per_h": round(ke, 4), "half_life_h": drug.half_life_hours,
            "vd_L": drug.vd_L, "bioavailability": f,
        },
        "steady_state": {
            "cmax_ug_mL": round(css_max, 3),
            "cmin_ug_mL": round(css_min, 3),
            "accumulation_ratio": round(1 / (1 - math.exp(-ke * interval_hours)), 2) if ke > 0 else 1,
        },
        "timepoints": timepoints[:40],  # Limit output
    }
