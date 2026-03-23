"""
CARVanta – Clinical Guidelines Engine
========================================
Evidence-based clinical decision support for CAR-T therapy.
Implements:
  - NCCN / ASTCT consensus guidelines
  - Patient eligibility screening
  - Pre-treatment workup checklists
  - Toxicity management algorithms (CRS, ICANS, cytopenias)
  - Response assessment criteria (Lugano, IMWG)
  - Follow-up protocols by cancer type
  - Bridging therapy selection
  - Drug interaction checking
  - Consent documentation requirements
  - Regulatory compliance (REMS)
  - Evidence summaries for treatment decisions
"""

import math
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════════════════════
# Eligibility Criteria
# ═══════════════════════════════════════════════════════════════════════════════

ELIGIBILITY_CRITERIA = {
    "axi-cel": {
        "name": "Axicabtagene ciloleucel (Yescarta)",
        "indications": [
            {
                "cancer": "DLBCL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Relapsed or refractory DLBCL not otherwise specified, including DLBCL arising from FL",
                "exclusions": ["Primary CNS lymphoma"],
            },
            {
                "cancer": "PMBCL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Primary mediastinal large B-cell lymphoma",
                "exclusions": [],
            },
            {
                "cancer": "HGBCL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "High grade B-cell lymphoma",
                "exclusions": [],
            },
            {
                "cancer": "FL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Follicular lymphoma (grade 1-3a) after ≥2 prior lines",
                "exclusions": [],
            },
            {
                "cancer": "LBCL (2L)",
                "line": "After first-line chemoimmunotherapy (ZUMA-7)",
                "age": "≥18 years",
                "specific": "LBCL refractory to or relapsed within 12 months of first-line therapy",
                "exclusions": [],
            },
        ],
        "general_requirements": [
            "ECOG performance status 0-1",
            "Adequate organ function",
            "ALC ≥100/µL",
            "No active infections (including HIV, HBV, HCV)",
            "No prior allogeneic stem cell transplant within 6 months",
            "No active GVHD",
        ],
        "organ_function": {
            "cardiac": "LVEF ≥40%",
            "hepatic": "AST/ALT ≤3x ULN, total bilirubin ≤2.0 mg/dL",
            "renal": "Creatinine clearance ≥40 mL/min",
            "pulmonary": "SpO2 ≥92% on room air",
        },
    },
    "tisa-cel": {
        "name": "Tisagenlecleucel (Kymriah)",
        "indications": [
            {
                "cancer": "ALL",
                "line": "≥2 relapses or refractory",
                "age": "Up to 25 years",
                "specific": "B-cell precursor ALL that is refractory or in 2nd or later relapse",
                "exclusions": ["Philadelphia chromosome-positive ALL (unless failed 2 TKIs)"],
            },
            {
                "cancer": "DLBCL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Relapsed or refractory DLBCL after ≥2 lines of systemic therapy",
                "exclusions": ["Primary CNS lymphoma"],
            },
            {
                "cancer": "FL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Relapsed or refractory FL after ≥2 prior lines",
                "exclusions": [],
            },
        ],
        "general_requirements": [
            "ECOG performance status 0-1 (adults); Lansky/Karnofsky ≥50 (pediatric)",
            "Adequate organ function",
            "No active or latent hepatitis B or C",
            "No HIV infection",
            "No active uncontrolled infection",
        ],
        "organ_function": {
            "cardiac": "LVEF ≥45%",
            "hepatic": "AST/ALT ≤5x ULN, total bilirubin ≤2.0 mg/dL",
            "renal": "Creatinine clearance ≥30 mL/min",
            "pulmonary": "SpO2 ≥92% on room air",
        },
    },
    "liso-cel": {
        "name": "Lisocabtagene maraleucel (Breyanzi)",
        "indications": [
            {
                "cancer": "LBCL",
                "line": "≥2 prior systemic therapies",
                "age": "≥18 years",
                "specific": "Relapsed or refractory LBCL after ≥2 prior lines, including DLBCL-NOS, HGBCL, FL3B, PMBCL",
                "exclusions": ["Primary CNS lymphoma"],
            },
            {
                "cancer": "CLL/SLL",
                "line": "≥2 prior therapies (including BTK inhibitor)",
                "age": "≥18 years",
                "specific": "Relapsed or refractory CLL/SLL",
                "exclusions": [],
            },
            {
                "cancer": "MCL",
                "line": "≥2 prior therapies (including BTK inhibitor)",
                "age": "≥18 years",
                "specific": "Relapsed or refractory MCL",
                "exclusions": [],
            },
        ],
        "general_requirements": [
            "ECOG performance status 0-1",
            "Adequate organ function",
            "No active CNS involvement",
            "No prior CAR-T therapy (relative)",
        ],
        "organ_function": {
            "cardiac": "LVEF ≥40%",
            "hepatic": "AST/ALT ≤3x ULN, total bilirubin ≤1.5x ULN",
            "renal": "eGFR ≥30 mL/min",
            "pulmonary": "SpO2 ≥92% on room air",
        },
    },
    "ide-cel": {
        "name": "Idecabtagene vicleucel (Abecma)",
        "indications": [
            {
                "cancer": "Multiple Myeloma",
                "line": "≥4 prior lines (including IMiD, PI, anti-CD38)",
                "age": "≥18 years",
                "specific": "Relapsed or refractory multiple myeloma after ≥4 prior therapies",
                "exclusions": ["Prior BCMA-directed therapy (relative)"],
            },
        ],
        "general_requirements": [
            "ECOG performance status 0-1",
            "Measurable disease per IMWG criteria",
            "Documented progression on last line of therapy",
            "No active plasma cell leukemia",
        ],
        "organ_function": {
            "cardiac": "LVEF ≥45%",
            "hepatic": "AST/ALT ≤2.5x ULN, total bilirubin ≤1.5x ULN",
            "renal": "Creatinine clearance ≥45 mL/min",
            "pulmonary": "SpO2 ≥92% on room air",
        },
    },
    "cilta-cel": {
        "name": "Ciltacabtagene autoleucel (Carvykti)",
        "indications": [
            {
                "cancer": "Multiple Myeloma",
                "line": "≥4 prior lines or double-refractory to PI and IMiD",
                "age": "≥18 years",
                "specific": "Relapsed or refractory MM after ≥4 prior therapies (including PI, IMiD, anti-CD38)",
                "exclusions": [],
            },
        ],
        "general_requirements": [
            "ECOG performance status 0-1",
            "Measurable disease",
            "Adequate bone marrow function",
            "No active hepatitis B/C or HIV",
        ],
        "organ_function": {
            "cardiac": "LVEF ≥45%, no Class III/IV heart failure",
            "hepatic": "AST/ALT ≤2.5x ULN",
            "renal": "Creatinine clearance ≥40 mL/min",
            "pulmonary": "SpO2 ≥92% on room air, no supplemental O2",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Pre-Treatment Workup
# ═══════════════════════════════════════════════════════════════════════════════

PRE_TREATMENT_WORKUP = {
    "baseline_labs": {
        "hematology": ["CBC with differential", "Reticulocyte count", "Blood type and screen"],
        "chemistry": ["CMP (Comprehensive Metabolic Panel)", "LDH", "Uric acid", "Phosphorus", "Magnesium"],
        "inflammatory": ["CRP", "Ferritin", "IL-6 (if available)", "D-dimer", "Fibrinogen"],
        "coagulation": ["PT/INR", "aPTT"],
        "immunology": ["Quantitative immunoglobulins (IgG, IgA, IgM)", "CD4/CD8 T-cell count",
                       "B-cell count (CD19+)", "NK cell count"],
        "infectious": ["HIV 1/2 Ab/Ag", "Hepatitis B surface Ag, core Ab", "Hepatitis C Ab",
                       "CMV IgG/IgM", "EBV VCA IgG/IgM", "Quantiferon/TB Gold"],
        "tumor_markers": ["LDH", "Beta-2 microglobulin", "Disease-specific markers"],
    },
    "imaging": [
        "PET/CT (baseline for response assessment)",
        "CT chest/abdomen/pelvis (within 30 days of infusion)",
        "Brain MRI (if CNS involvement suspected)",
        "Echocardiogram (LVEF assessment)",
    ],
    "functional": [
        "ECOG Performance Status assessment",
        "Pulmonary function tests (if history of lung disease)",
        "Neurocognitive baseline assessment (ICE score)",
    ],
    "procedures": [
        "Bone marrow biopsy (disease assessment)",
        "Leukapheresis (for CAR-T manufacturing)",
        "Central venous access placement",
    ],
    "consultations": [
        "Hematology/Oncology",
        "Infectious Disease (if active infections)",
        "Cardiology (if cardiac concerns)",
        "Neurology (if neurologic history)",
        "Social work/Psychology (consent and support)",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Toxicity Management Algorithms
# ═══════════════════════════════════════════════════════════════════════════════

CRS_MANAGEMENT_ALGORITHM = {
    1: {
        "grade": 1,
        "definition": "Temperature ≥38°C",
        "management": [
            "Supportive care: IV fluids, antipyretics (acetaminophen 650mg q6h PRN)",
            "Monitor: vitals q4h, daily labs (CBC, CMP, CRP, ferritin)",
            "Maintain IV access",
            "Rule out infection: blood cultures if febrile",
        ],
        "escalation_criteria": [
            "Hypotension (SBP <90 or requiring IV fluids)",
            "Hypoxia (SpO2 <94% on room air)",
            "Organ dysfunction",
        ],
        "tocilizumab": False,
        "corticosteroids": False,
    },
    2: {
        "grade": 2,
        "definition": "Temperature ≥38°C WITH hypotension responsive to fluids/low-dose vasopressor OR hypoxia requiring low-flow O2 (<40%)",
        "management": [
            "Tocilizumab 8 mg/kg IV (max 800 mg), may repeat in 8h (max 3 doses in 24h)",
            "IV fluid bolus (NS 500-1000 mL)",
            "Low-flow oxygen via nasal cannula",
            "Dexamethasone 10mg IV q12h if no improvement in 12-24h after tocilizumab",
            "Monitor: vitals q2h, labs q12h (CBC, CMP, CRP, ferritin, fibrinogen)",
            "Consider ICU transfer",
        ],
        "escalation_criteria": [
            "Requiring vasopressors (not low-dose)",
            "Requiring high-flow oxygen (>40%)",
            "No improvement after 2 doses of tocilizumab",
        ],
        "tocilizumab": True,
        "corticosteroids": "if_refractory",
    },
    3: {
        "grade": 3,
        "definition": "Temperature ≥38°C WITH hypotension requiring vasopressor(s) ± vasopressin AND/OR hypoxia requiring high-flow O2/CPAP/BiPAP",
        "management": [
            "Tocilizumab 8 mg/kg IV (if not already given or can repeat)",
            "Dexamethasone 10mg IV q6h",
            "ICU transfer (mandatory)",
            "Vasopressor support: Norepinephrine first-line",
            "High-flow nasal cannula or NIV",
            "Monitor: vitals continuous, labs q8h, troponin, BNP",
            "Consider methylprednisolone 1 mg/kg q12h if progressive",
            "Fibrinogen replacement if <150 mg/dL (cryoprecipitate)",
            "Consider siltuximab if refractory to tocilizumab",
        ],
        "escalation_criteria": [
            "Mechanical ventilation required",
            "Multiple vasopressors required",
            "Evidence of MAS/HLH (ferritin >10,000, rising LFTs)",
        ],
        "tocilizumab": True,
        "corticosteroids": True,
    },
    4: {
        "grade": 4,
        "definition": "Life-threatening: mechanical ventilation required AND/OR multiple vasopressors (excluding vasopressin)",
        "management": [
            "Methylprednisolone 1-2 mg/kg IV q12h",
            "Tocilizumab 8 mg/kg IV (if <3 prior doses in 24h)",
            "Aggressive ICU management",
            "Mechanical ventilation with lung-protective strategy",
            "Multi-vasopressor support",
            "Consider anakinra 200mg IV q6h (IL-1 receptor antagonist) for refractory CRS",
            "Consider ruxolitinib 10mg PO BID if available",
            "Continuous renal replacement therapy if AKI",
            "Assess for MAS/HLH — if ferritin >10,000: treat per HLH protocol",
            "Daily troponin, BNP — cardiology consult if elevated",
        ],
        "escalation_criteria": [
            "Multi-organ failure",
            "Refractory shock",
        ],
        "tocilizumab": True,
        "corticosteroids": True,
    },
}

ICANS_MANAGEMENT_ALGORITHM = {
    1: {
        "grade": 1,
        "definition": "ICE score 7-9 or mild depressed consciousness",
        "management": [
            "ICE assessment q8h",
            "Neurovital signs q4h (pupil reactivity, motor strength)",
            "Supportive care",
            "Levetiracetam seizure prophylaxis: 750mg PO BID",
            "Avoid sedatives and CNS depressants",
        ],
        "corticosteroids": False,
    },
    2: {
        "grade": 2,
        "definition": "ICE score 3-6 or moderate depressed consciousness",
        "management": [
            "Dexamethasone 10mg IV q6h",
            "ICE assessment q4h",
            "Neurovital signs q2h",
            "Consider neurology consult",
            "Brain MRI if worsening",
            "EEG if concern for subclinical seizures",
            "Consider ICU transfer",
        ],
        "corticosteroids": True,
    },
    3: {
        "grade": 3,
        "definition": "ICE score 0-2 or any clinical seizure, or focal/local edema on imaging",
        "management": [
            "Methylprednisolone 1 mg/kg IV q12h (or dexamethasone 10mg IV q6h)",
            "ICU transfer (mandatory)",
            "Neurovital signs q1h",
            "Urgent neurology consult",
            "Brain MRI",
            "Continuous EEG monitoring",
            "Seizure management: lorazepam 0.5mg IV PRN, levetiracetam dose escalation",
            "If cerebral edema suspected: mannitol 20% 1g/kg IV, hyperventilation",
        ],
        "corticosteroids": True,
    },
    4: {
        "grade": 4,
        "definition": "ICE score 0, prolonged seizures, diffuse cerebral edema, coma",
        "management": [
            "Methylprednisolone 1-2 g IV daily × 3 days (pulse dose)",
            "ICU with intubation for airway protection if needed",
            "Aggressive seizure management: continuous infusion anti-epileptics",
            "Mannitol 20% 1g/kg IV q6h PRN + hypertonic saline 3% 250mL bolus",
            "Hyperventilation to pCO2 30-35 mmHg",
            "Consider anakinra if concurrent CRS",
            "Neurosurgery consult if mass lesion or VP shunt consideration",
            "Continuous EEG monitoring",
        ],
        "corticosteroids": True,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Response Assessment Criteria
# ═══════════════════════════════════════════════════════════════════════════════

LUGANO_CRITERIA = {
    "CR": {
        "name": "Complete Response",
        "pet_ct": "Deauville 1-3 (no metabolically active disease)",
        "ct": "Target lesions ≤1.5cm in longest diameter",
        "bone_marrow": "Normal morphology; if indeterminate, IHC negative",
        "new_lesions": "None",
    },
    "PR": {
        "name": "Partial Response",
        "pet_ct": "Deauville 4-5 with decreased uptake from baseline, and residual mass of any size",
        "ct": "≥50% decrease in SPD of up to 6 target lesions",
        "bone_marrow": "Assessment not required if PET-positive",
        "new_lesions": "None",
    },
    "SD": {
        "name": "Stable Disease",
        "pet_ct": "Deauville 4-5 with no significant change from baseline",
        "ct": "<50% decrease in SPD from baseline (and not sufficient for PD)",
        "bone_marrow": "Not applicable",
        "new_lesions": "None",
    },
    "PD": {
        "name": "Progressive Disease",
        "pet_ct": "Deauville 4-5 with increase in intensity of uptake OR new FDG-avid foci",
        "ct": "Individual node/lesion ≥1.5cm AND ≥50% increase in PLD or SPD nadir",
        "bone_marrow": "New or recurrent involvement",
        "new_lesions": "Present",
    },
}

IMWG_CRITERIA = {
    "sCR": {
        "name": "Stringent Complete Response",
        "requirements": [
            "Normal FLC ratio",
            "Absence of clonal cells in bone marrow by IHC or flow cytometry",
            "Plus CR criteria",
        ],
    },
    "CR": {
        "name": "Complete Response",
        "requirements": [
            "Negative serum and urine immunofixation",
            "Disappearance of soft tissue plasmacytomas",
            "<5% plasma cells in bone marrow",
        ],
    },
    "VGPR": {
        "name": "Very Good Partial Response",
        "requirements": [
            "Serum and urine M-protein detectable by immunofixation but not on electrophoresis",
            "OR ≥90% reduction in serum M-protein + urine M-protein <100mg/24h",
        ],
    },
    "PR": {
        "name": "Partial Response",
        "requirements": [
            "≥50% reduction of serum M-protein",
            "≥90% reduction in 24h urinary M-protein to <200mg/24h",
            "If measurable, ≥50% reduction in size of soft tissue plasmacytomas",
        ],
    },
    "MR": {
        "name": "Minimal Response",
        "requirements": ["25-49% reduction of serum M-protein"],
    },
    "SD": {
        "name": "Stable Disease",
        "requirements": ["Not meeting criteria for CR, VGPR, PR, or PD"],
    },
    "PD": {
        "name": "Progressive Disease",
        "requirements": [
            "≥25% increase from lowest response in serum M-protein (absolute ≥0.5 g/dL)",
            "OR ≥25% increase in 24h urine M-protein (absolute ≥200 mg/24h)",
            "OR new bone lesions or soft tissue plasmacytomas",
            "OR definite increase in existing bone lesions",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Bridging Therapy Options
# ═══════════════════════════════════════════════════════════════════════════════

BRIDGING_THERAPY_OPTIONS = {
    "DLBCL": [
        {
            "regimen": "Polatuzumab vedotin + Bendamustine + Rituximab (PBR)",
            "response_rate": "45%",
            "cycle_duration": "21 days",
            "typical_cycles": "1-2",
            "pros": ["High response rate in R/R DLBCL", "Good tumor debulking"],
            "cons": ["Cytopenias may delay CAR-T", "Peripheral neuropathy"],
        },
        {
            "regimen": "R-GemOx (Rituximab + Gemcitabine + Oxaliplatin)",
            "response_rate": "40%",
            "cycle_duration": "14 days",
            "typical_cycles": "1-2",
            "pros": ["Well tolerated", "Minimal T-cell toxicity"],
            "cons": ["Peripheral neuropathy from oxaliplatin"],
        },
        {
            "regimen": "Radiation therapy (involved-field)",
            "response_rate": "60-80% (local)",
            "cycle_duration": "1-2 weeks",
            "typical_cycles": "1",
            "pros": ["Local control", "No systemic toxicity", "Preserves T-cell function"],
            "cons": ["Only local effect", "Not for widespread disease"],
        },
        {
            "regimen": "Corticosteroids (Dexamethasone 40mg PO × 4d)",
            "response_rate": "20-30%",
            "cycle_duration": "4 days",
            "typical_cycles": "1-2",
            "pros": ["Rapid cytoreduction", "Well tolerated"],
            "cons": ["May impair T-cell function; stop ≥5 days before leukapheresis"],
        },
    ],
    "ALL": [
        {
            "regimen": "Blinatumomab",
            "response_rate": "40-45%",
            "cycle_duration": "28 days (continuous infusion)",
            "typical_cycles": "1",
            "pros": ["Good bridge for ALL", "Can assess CD19 expression"],
            "cons": ["CRS risk", "Neurotoxicity", "Continuous infusion logistics"],
        },
        {
            "regimen": "Inotuzumab ozogamicin",
            "response_rate": "70-80%",
            "cycle_duration": "21-28 days",
            "typical_cycles": "1",
            "pros": ["High response rate", "Well tolerated"],
            "cons": ["Hepatotoxicity (VOD risk)", "Thrombocytopenia"],
        },
    ],
    "MCL": [
        {
            "regimen": "Ibrutinib (or other BTK inhibitor)",
            "response_rate": "65-70%",
            "cycle_duration": "Continuous",
            "typical_cycles": "Until CAR-T",
            "pros": ["Oral therapy", "May enhance CAR-T expansion"],
            "cons": ["Bleeding risk", "Atrial fibrillation"],
        },
    ],
    "Multiple Myeloma": [
        {
            "regimen": "DPd (Daratumumab + Pomalidomide + Dexamethasone)",
            "response_rate": "55%",
            "cycle_duration": "28 days",
            "typical_cycles": "1-2",
            "pros": ["Standard R/R MM regimen", "Disease control"],
            "cons": ["Cytopenias", "Infection risk"],
        },
        {
            "regimen": "Selinexor + Dexamethasone",
            "response_rate": "25%",
            "cycle_duration": "Weekly",
            "typical_cycles": "Until CAR-T",
            "pros": ["Novel mechanism", "Oral"],
            "cons": ["GI toxicity", "Cytopenias"],
        },
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Functions
# ═══════════════════════════════════════════════════════════════════════════════

def check_eligibility(
    product: str,
    cancer_type: str,
    patient_age: int,
    prior_lines: int,
    ecog: int,
    lvef: Optional[float] = None,
    creatinine_cl: Optional[float] = None,
    spo2: Optional[float] = None,
    alt: Optional[float] = None,
    bilirubin: Optional[float] = None,
    active_infection: bool = False,
    prior_allo_sct: bool = False,
    cns_involvement: bool = False,
) -> Dict[str, Any]:
    """
    Check patient eligibility for a specific CAR-T product.
    Returns detailed eligibility assessment with pass/fail for each criterion.
    """
    criteria = ELIGIBILITY_CRITERIA.get(product)
    if not criteria:
        return {"error": f"Unknown product: {product}", "eligible": False}

    checks = []
    overall_eligible = True

    # Indication check
    ct = cancer_type.upper()
    indication_match = False
    matched_indication = None
    for ind in criteria["indications"]:
        if ct in ind["cancer"].upper() or ind["cancer"].upper() in ct:
            indication_match = True
            matched_indication = ind
            break

    checks.append({
        "criterion": "Approved indication",
        "required": f"Must match approved indication for {criteria['name']}",
        "actual": cancer_type,
        "passed": indication_match,
        "note": f"Matched: {matched_indication['specific']}" if indication_match else "No matching indication found",
    })
    if not indication_match:
        overall_eligible = False

    # Prior lines
    if matched_indication:
        min_lines = 2  # default
        if "first-line" in (matched_indication.get("line") or "").lower():
            min_lines = 1
        elif "4" in (matched_indication.get("line") or ""):
            min_lines = 4

        lines_ok = prior_lines >= min_lines
        checks.append({
            "criterion": "Prior lines of therapy",
            "required": matched_indication.get("line", "≥2 prior lines"),
            "actual": f"{prior_lines} prior lines",
            "passed": lines_ok,
        })
        if not lines_ok:
            overall_eligible = False

    # Age
    age_ok = True
    if matched_indication:
        age_spec = matched_indication.get("age", "≥18 years")
        if "25" in age_spec and patient_age > 25:
            age_ok = False
        elif "18" in age_spec and patient_age < 18:
            age_ok = False

    checks.append({
        "criterion": "Age requirement",
        "required": matched_indication.get("age", "≥18 years") if matched_indication else "≥18 years",
        "actual": f"{patient_age} years",
        "passed": age_ok,
    })
    if not age_ok:
        overall_eligible = False

    # ECOG
    ecog_ok = ecog <= 1
    checks.append({
        "criterion": "ECOG Performance Status",
        "required": "0-1",
        "actual": f"ECOG {ecog}",
        "passed": ecog_ok,
    })
    if not ecog_ok:
        overall_eligible = False

    # Organ function
    organ_reqs = criteria.get("organ_function", {})

    if lvef is not None:
        lvef_threshold = 40
        if "45" in organ_reqs.get("cardiac", ""):
            lvef_threshold = 45
        lvef_ok = lvef >= lvef_threshold
        checks.append({
            "criterion": "Cardiac (LVEF)",
            "required": organ_reqs.get("cardiac", f"≥{lvef_threshold}%"),
            "actual": f"LVEF {lvef}%",
            "passed": lvef_ok,
        })
        if not lvef_ok:
            overall_eligible = False

    if creatinine_cl is not None:
        crcl_threshold = 40
        if "30" in organ_reqs.get("renal", ""):
            crcl_threshold = 30
        elif "45" in organ_reqs.get("renal", ""):
            crcl_threshold = 45
        crcl_ok = creatinine_cl >= crcl_threshold
        checks.append({
            "criterion": "Renal (CrCl)",
            "required": organ_reqs.get("renal", f"≥{crcl_threshold} mL/min"),
            "actual": f"CrCl {creatinine_cl} mL/min",
            "passed": crcl_ok,
        })
        if not crcl_ok:
            overall_eligible = False

    if spo2 is not None:
        spo2_ok = spo2 >= 92
        checks.append({
            "criterion": "Pulmonary (SpO2)",
            "required": "≥92% on room air",
            "actual": f"SpO2 {spo2}%",
            "passed": spo2_ok,
        })
        if not spo2_ok:
            overall_eligible = False

    # Exclusions
    if active_infection:
        checks.append({
            "criterion": "Active infection",
            "required": "No active infections",
            "actual": "Active infection present",
            "passed": False,
        })
        overall_eligible = False

    if cns_involvement and product in ("axi-cel", "liso-cel"):
        checks.append({
            "criterion": "CNS involvement",
            "required": "No primary CNS lymphoma",
            "actual": "CNS involvement present",
            "passed": False,
        })
        overall_eligible = False

    passed_count = sum(1 for c in checks if c["passed"])

    return {
        "product": criteria["name"],
        "eligible": overall_eligible,
        "checks": checks,
        "passed_count": passed_count,
        "total_checks": len(checks),
        "pass_rate": round(passed_count / max(1, len(checks)) * 100, 1),
        "recommendation": (
            "Patient meets eligibility criteria — proceed with CAR-T evaluation"
            if overall_eligible else
            "Patient does NOT meet eligibility criteria — review failed criteria"
        ),
    }


def get_crs_management(grade: int) -> Dict[str, Any]:
    """Get CRS management algorithm for a specific grade."""
    if grade not in CRS_MANAGEMENT_ALGORITHM:
        return {"error": f"Invalid CRS grade: {grade}. Must be 1-4."}
    algo = CRS_MANAGEMENT_ALGORITHM[grade]
    return {
        "grade": algo["grade"],
        "definition": algo["definition"],
        "management_steps": algo["management"],
        "escalation_criteria": algo["escalation_criteria"],
        "tocilizumab_indicated": algo["tocilizumab"],
        "steroids_indicated": algo["corticosteroids"],
    }


def get_icans_management(grade: int) -> Dict[str, Any]:
    """Get ICANS management algorithm for a specific grade."""
    if grade not in ICANS_MANAGEMENT_ALGORITHM:
        return {"error": f"Invalid ICANS grade: {grade}. Must be 1-4."}
    algo = ICANS_MANAGEMENT_ALGORITHM[grade]
    return {
        "grade": algo["grade"],
        "definition": algo["definition"],
        "management_steps": algo["management"],
        "steroids_indicated": algo["corticosteroids"],
    }


def get_response_criteria(cancer_type: str) -> Dict[str, Any]:
    """Get appropriate response criteria for a cancer type."""
    ct = cancer_type.upper()
    if "MYELOMA" in ct or "MM" in ct:
        return {"criteria": "IMWG", "categories": IMWG_CRITERIA}
    return {"criteria": "Lugano", "categories": LUGANO_CRITERIA}


def get_bridging_options(cancer_type: str) -> Dict[str, Any]:
    """Get bridging therapy options for a cancer type."""
    ct = cancer_type.upper()
    for key, options in BRIDGING_THERAPY_OPTIONS.items():
        if key.upper() in ct or ct in key.upper():
            return {"cancer_type": cancer_type, "options": options}
    return {"cancer_type": cancer_type, "options": BRIDGING_THERAPY_OPTIONS.get("DLBCL", [])}


def get_pre_treatment_workup() -> Dict[str, Any]:
    """Get complete pre-treatment workup checklist."""
    return PRE_TREATMENT_WORKUP


def get_all_eligibility_criteria() -> Dict[str, Any]:
    """Get eligibility criteria for all approved products."""
    return {
        key: {
            "name": val["name"],
            "indications": [{"cancer": i["cancer"], "line": i["line"]} for i in val["indications"]],
            "organ_function": val["organ_function"],
        }
        for key, val in ELIGIBILITY_CRITERIA.items()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Post-Infusion Monitoring Schedule
# ═══════════════════════════════════════════════════════════════════════════════

POST_INFUSION_MONITORING = {
    "acute_phase": {
        "duration": "Days 0-14 post-infusion",
        "location": "Inpatient or certified outpatient facility within 2h travel",
        "vitals": "Every 4 hours (every 2 hours if febrile or symptomatic)",
        "labs": {
            "frequency": "Daily",
            "panel": [
                "CBC with differential",
                "CMP (comprehensive metabolic panel)",
                "CRP (C-reactive protein)",
                "Ferritin",
                "Fibrinogen",
                "LDH",
            ],
            "additional_prn": [
                "IL-6 (if CRS suspected)",
                "Troponin (if cardiac symptoms)",
                "BNP (if heart failure suspected)",
                "Blood cultures (if febrile)",
                "Coagulation studies (PT/INR, aPTT, D-dimer)",
            ],
        },
        "assessments": [
            "ICE score every 12 hours (or more frequently if ICANS suspected)",
            "CRS grading per ASTCT consensus (Lee criteria)",
            "Neurovital signs every 4 hours",
            "Pulse oximetry continuous or q4h",
            "Input/output monitoring",
            "Daily weight",
        ],
        "medications": {
            "required": [
                "Levetiracetam 750mg PO BID (seizure prophylaxis) — start Day 0, continue 30 days",
                "Rasburicase or allopurinol (tumor lysis prophylaxis) if bulky disease",
                "IV fluids maintenance",
            ],
            "avoid": [
                "Systemic corticosteroids (unless treating CRS/ICANS ≥ Grade 2)",
                "Myeloid growth factors (G-CSF) — may exacerbate CRS; delay until Day +21",
                "Live vaccines — avoid for ≥6 months",
                "Intrathecal chemotherapy",
            ],
            "keep_bedside": [
                "Tocilizumab 8mg/kg IV (≥2 doses available at all times)",
                "Dexamethasone 10mg IV",
                "Lorazepam 0.5mg IV (for seizures)",
                "Epinephrine (for anaphylaxis)",
            ],
        },
    },
    "early_recovery": {
        "duration": "Days 14-28",
        "location": "Outpatient with ≤1h travel to certified center",
        "vitals": "Every clinic visit (2-3x per week)",
        "labs": {
            "frequency": "2-3 times per week",
            "panel": ["CBC with differential", "CMP", "CRP", "Ferritin", "Quantitative immunoglobulins"],
        },
        "assessments": [
            "ICE score at each visit",
            "CRS/ICANS reassessment",
            "Disease restaging (PET/CT at Day 28 ±3)",
        ],
    },
    "month_1_to_3": {
        "duration": "Month 1-3",
        "frequency": "Every 2 weeks",
        "labs": ["CBC with differential", "CMP", "Quantitative immunoglobulins", "CD4/CD8 T-cell count"],
        "assessments": [
            "Disease response assessment (Day 90 PET/CT)",
            "Bone marrow biopsy (if applicable, especially for ALL/MM)",
            "MRD assessment (if available)",
            "Infection screening",
            "Vaccination readiness assessment",
        ],
    },
    "month_3_to_12": {
        "duration": "Month 3-12",
        "frequency": "Monthly",
        "labs": ["CBC with differential", "CMP", "IgG level", "CD19 B-cell count"],
        "assessments": [
            "PET/CT every 3 months (or as clinically indicated)",
            "Neurocognitive assessment if prior ICANS",
            "IVIG replacement if IgG <400 mg/dL",
            "Vaccination: begin at 3-6 months with inactivated vaccines",
        ],
    },
    "year_1_plus": {
        "duration": "Year 1+",
        "frequency": "Every 3 months × 2 years, then every 6 months",
        "labs": ["CBC", "IgG", "CD19 B-cell count", "Disease-specific markers"],
        "assessments": [
            "Annual PET/CT (or as clinically indicated)",
            "B-cell aplasia monitoring (may persist >5 years)",
            "Secondary malignancy screening (per REMS requirement)",
            "Long-term neurocognitive follow-up if history of severe ICANS",
            "Complete vaccination schedule by 12 months",
        ],
        "late_effects": [
            "Prolonged cytopenias (monitor CBC monthly until recovered)",
            "B-cell aplasia and hypogammaglobulinemia (IVIG support)",
            "Infection susceptibility (pneumococcal, influenza prophylaxis)",
            "Secondary T-cell lymphoma (extremely rare — REMS reporting required)",
            "Myelodysplastic syndrome/AML (monitor for 15 years post-treatment)",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# REMS (Risk Evaluation and Mitigation Strategy)
# ═══════════════════════════════════════════════════════════════════════════════

REMS_REQUIREMENTS = {
    "general": {
        "description": "All FDA-approved CAR-T products have mandatory REMS programs",
        "objectives": [
            "Ensure proper training for healthcare providers",
            "Mitigate risk of CRS and neurological toxicities",
            "Ensure availability of tocilizumab at treatment site",
            "Long-term safety monitoring (15-year follow-up)",
        ],
    },
    "facility_certification": {
        "requirements": [
            "FACT-accredited cell therapy program",
            "On-site ICU or rapid ICU access",
            "Trained pharmacy for tocilizumab dispensing",
            "Nurse certification in CAR-T care",
            "Enrollment in product-specific REMS program",
        ],
        "training": [
            "CRS identification and grading (ASTCT consensus)",
            "ICANS identification and ICE scoring",
            "Tocilizumab administration protocols",
            "Steroid management algorithms",
            "Emergency escalation procedures",
        ],
    },
    "tocilizumab_requirements": {
        "minimum_supply": "≥2 doses per patient (8mg/kg, max 800mg each)",
        "availability": "Must be available bedside within 2 hours of infusion",
        "administration": "Only for CRS ≥ Grade 2 (or per institutional protocol)",
        "reorder": "Replace within 24 hours of use",
    },
    "patient_monitoring": {
        "location_restriction": "Patient must remain within 2 hours travel of certified center for 4 weeks",
        "caregiver": "24/7 caregiver required for first 30 days post-infusion",
        "driving": "No driving or operating heavy machinery for 8 weeks post-infusion",
        "reporting": "Serious adverse events must be reported within 15 days",
    },
    "long_term_follow_up": {
        "duration": "15 years from infusion",
        "annual_assessments": [
            "Secondary malignancy screening",
            "Hematologic malignancy surveillance",
            "Quality of life assessment",
            "Ongoing adverse event monitoring",
        ],
        "reporting_to_fda": "Annual safety summary required",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Infection Prophylaxis
# ═══════════════════════════════════════════════════════════════════════════════

INFECTION_PROPHYLAXIS = {
    "antiviral": {
        "drug": "Acyclovir 400mg PO BID (or valacyclovir 500mg PO daily)",
        "indication": "HSV/VZV prophylaxis",
        "start": "Day -5 (with lymphodepletion)",
        "duration": "≥6 months or until CD4 >200/µL",
    },
    "antifungal": {
        "drug": "Fluconazole 200mg PO daily (or micafungin 50mg IV daily)",
        "indication": "Candida prophylaxis",
        "start": "Day -5",
        "duration": "Until neutrophil recovery (ANC >500/µL)",
    },
    "pneumocystis": {
        "drug": "TMP-SMX 1 DS tablet PO 3×/week (or pentamidine 300mg inhaled monthly)",
        "indication": "PJP prophylaxis",
        "start": "After neutrophil recovery",
        "duration": "≥6 months or until CD4 >200/µL",
    },
    "ivig_replacement": {
        "drug": "IVIG 0.4g/kg IV every 3-4 weeks",
        "indication": "Hypogammaglobulinemia (IgG <400 mg/dL)",
        "start": "When IgG documented <400 mg/dL on 2 separate occasions",
        "duration": "Until B-cell recovery and IgG normalization",
    },
    "vaccination_schedule": {
        "timing": "Begin at 3-6 months post-infusion (inactivated vaccines only)",
        "priority_vaccines": [
            {"vaccine": "Pneumococcal (PCV20)", "schedule": "3 doses at 0, 2, 8 months"},
            {"vaccine": "Influenza (inactivated)", "schedule": "Annual, begin at 3 months"},
            {"vaccine": "Haemophilus influenzae type b", "schedule": "3 doses starting at 6 months"},
            {"vaccine": "Meningococcal (MCV4 + MenB)", "schedule": "Per CDC schedule at 6 months"},
            {"vaccine": "Hepatitis B", "schedule": "3-dose series at 6 months if non-immune"},
            {"vaccine": "Tdap", "schedule": "Single dose at 6 months"},
            {"vaccine": "COVID-19 (mRNA)", "schedule": "Primary series at 3 months"},
        ],
        "avoid_until_immune_recovery": [
            "MMR (live)",
            "Varicella (live)",
            "Yellow fever (live)",
            "Oral polio (live)",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Consent Documentation Checklist
# ═══════════════════════════════════════════════════════════════════════════════

CONSENT_CHECKLIST = {
    "required_discussions": [
        "Purpose and nature of CAR-T cell therapy",
        "Expected benefits and response rates (product-specific)",
        "Risk of cytokine release syndrome (CRS) — grades, management, ICU possibility",
        "Risk of ICANS/neurotoxicity — grades, management, potential for seizures",
        "Risk of prolonged cytopenias and infection",
        "Risk of B-cell aplasia and need for IVIG replacement",
        "Extremely rare risk of T-cell lymphoma (REMS-mandated disclosure)",
        "Fertility considerations (lymphodepletion may affect fertility)",
        "Financial implications and insurance coverage",
        "Need for caregiver support (24/7 for 30 days)",
        "Driving and activity restrictions (8 weeks)",
        "Long-term follow-up requirements (15 years — REMS)",
        "Alternative treatment options",
    ],
    "documents_required": [
        "Informed consent form (product-specific)",
        "REMS Patient Guide (product-specific)",
        "Financial counseling documentation",
        "Emergency contact information",
        "Advance directive review",
        "HIPAA authorization",
    ],
    "special_populations": {
        "pediatric": [
            "Parental/guardian consent + patient assent (if age-appropriate)",
            "Pediatric-specific risk discussion",
            "Growth and development monitoring plan",
            "Fertility preservation discussion",
        ],
        "geriatric": [
            "Geriatric assessment discussion",
            "Fall risk assessment",
            "Polypharmacy review",
            "Goals of care discussion",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Additional Analysis Functions
# ═══════════════════════════════════════════════════════════════════════════════

def get_monitoring_schedule(phase: str = "all") -> Dict[str, Any]:
    """Get post-infusion monitoring schedule for a specific phase or all."""
    if phase == "all":
        return POST_INFUSION_MONITORING
    return POST_INFUSION_MONITORING.get(phase, {"error": f"Unknown phase: {phase}"})


def get_infection_prophylaxis() -> Dict[str, Any]:
    """Get complete infection prophylaxis protocol."""
    return INFECTION_PROPHYLAXIS


def get_rems_requirements() -> Dict[str, Any]:
    """Get REMS requirements for CAR-T treatment centers."""
    return REMS_REQUIREMENTS


def get_consent_checklist() -> Dict[str, Any]:
    """Get consent documentation checklist."""
    return CONSENT_CHECKLIST


def generate_treatment_summary(
    product: str,
    cancer_type: str,
    response: str = "CR",
    crs_grade: int = 0,
    icans_grade: int = 0,
) -> Dict[str, Any]:
    """
    Generate a comprehensive treatment summary document structure.
    """
    criteria = ELIGIBILITY_CRITERIA.get(product, {})
    product_name = criteria.get("name", product)

    # Get response criteria
    if "myeloma" in cancer_type.lower() or "mm" in cancer_type.lower():
        response_criteria = "IMWG"
        response_detail = IMWG_CRITERIA.get(response, {})
    else:
        response_criteria = "Lugano"
        response_detail = LUGANO_CRITERIA.get(response, {})

    # Get toxicity management details
    crs_mgmt = get_crs_management(crs_grade) if crs_grade > 0 else None
    icans_mgmt = get_icans_management(icans_grade) if icans_grade > 0 else None

    # Get bridging options used
    bridging = get_bridging_options(cancer_type)

    return {
        "summary_type": "CAR-T Treatment Summary",
        "product": product_name,
        "cancer_type": cancer_type,
        "response": {
            "category": response,
            "criteria_used": response_criteria,
            "detail": response_detail,
        },
        "toxicities": {
            "crs": {
                "max_grade": crs_grade,
                "management": crs_mgmt,
            },
            "icans": {
                "max_grade": icans_grade,
                "management": icans_mgmt,
            },
        },
        "follow_up_plan": POST_INFUSION_MONITORING,
        "prophylaxis": INFECTION_PROPHYLAXIS,
        "rems_obligations": {
            "long_term_follow_up": "15 years",
            "annual_screening": "Secondary malignancy, hematologic surveillance",
            "reporting": "Annual safety summary to FDA",
        },
        "bridging_options": bridging,
    }
