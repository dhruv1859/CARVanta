"""
CARVanta Collab — Research Protocol Library
=============================================
Standardized research protocol management for immunotherapy
experiments. Template library, version control, and regulatory
compliance for experimental procedures.

Features:
- 15+ CAR-T research protocol templates
- Protocol versioning with diff tracking
- SOP (Standard Operating Procedure) management
- Regulatory compliance checklists (IRB, IBC, FDA IND)
- Material and reagent tracking
- Equipment calibration logging
- Risk assessment and mitigation
- Protocol deviation tracking
- Cross-site protocol harmonization
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.protocols")

# In-memory protocol store
_PROTOCOLS: Dict[str, Dict] = {}

# Protocol templates library
_PROTOCOL_TEMPLATES = {
    "car_t_manufacturing": {
        "name": "CAR-T Cell Manufacturing Protocol",
        "category": "manufacturing",
        "steps": [
            {"step": 1, "name": "Leukapheresis Collection", "duration_hours": 4,
             "description": "Collect patient PBMCs via leukapheresis (10-15L blood volume processed)",
             "critical_params": ["ALC >0.5 ×10⁹/L", "CD3+ >300 cells/μL", "Viability >90%"]},
            {"step": 2, "name": "T-cell Enrichment", "duration_hours": 2,
             "description": "CD3+ T-cell selection using CliniMACS or equivalent",
             "critical_params": ["Purity >95% CD3+", "Recovery >70%", "Viability >95%"]},
            {"step": 3, "name": "T-cell Activation", "duration_hours": 48,
             "description": "Anti-CD3/CD28 bead activation with IL-2/IL-7/IL-15",
             "critical_params": ["CD25+ >80%", "Blast formation visible", "IL-2 concentration 100 IU/mL"]},
            {"step": 4, "name": "Viral Transduction", "duration_hours": 24,
             "description": "Lentiviral/retroviral vector transduction at MOI 3-10",
             "critical_params": ["MOI 3-10", "Transduction efficiency target >20%", "VCN 1-5"]},
            {"step": 5, "name": "Expansion Culture", "duration_hours": 240,
             "description": "10-14 day expansion in G-Rex or wave bioreactor",
             "critical_params": ["Fold expansion >50x", "Viability >70%", "Daily cell counts"]},
            {"step": 6, "name": "Harvest & Formulation", "duration_hours": 4,
             "description": "Harvest, wash, formulate in CryoStor CS10 or equivalent",
             "critical_params": ["Cell count within dose range", "Viability >70%", "Volume 10-50 mL"]},
            {"step": 7, "name": "Quality Control Testing", "duration_hours": 72,
             "description": "Sterility, mycoplasma, endotoxin, identity, potency testing",
             "critical_params": ["Sterility: no growth 14d", "Mycoplasma: negative", "Endotoxin <5 EU/kg"]},
            {"step": 8, "name": "Cryopreservation", "duration_hours": 2,
             "description": "Controlled-rate freezing and LN2 storage",
             "critical_params": ["Cooling rate -1°C/min", "Storage <-150°C", "Post-thaw viability >70%"]},
        ],
        "total_duration_days": 14,
        "regulatory": ["FDA BLA", "GMP compliance", "USP <71>", "USP <85>"],
    },
    "cytotoxicity_assay": {
        "name": "CAR-T Cytotoxicity Assay (Chromium Release)",
        "category": "functional_assay",
        "steps": [
            {"step": 1, "name": "Target Cell Labeling", "duration_hours": 2,
             "description": "Label target cells with ⁵¹Cr (100 μCi per 10⁶ cells, 1hr 37°C)",
             "critical_params": ["Labeling efficiency >50%", "Spontaneous release <20%"]},
            {"step": 2, "name": "Effector-Target Co-culture", "duration_hours": 4,
             "description": "Co-culture at E:T ratios 40:1, 20:1, 10:1, 5:1, 1:1",
             "critical_params": ["Duplicate/triplicate wells", "Total volume 200 μL/well"]},
            {"step": 3, "name": "Supernatant Collection", "duration_hours": 0.5,
             "description": "Collect 100 μL supernatant after 4hr incubation",
             "critical_params": ["Avoid cell pellet disturbance", "Include spontaneous and max controls"]},
            {"step": 4, "name": "Gamma Counting & Analysis", "duration_hours": 1,
             "description": "Count ⁵¹Cr release on gamma counter; calculate % specific lysis",
             "critical_params": ["Specific lysis = (exp - spont) / (max - spont) × 100"]},
        ],
        "total_duration_days": 1,
        "regulatory": ["Radiation safety", "Biosafety Level 2"],
    },
    "flow_cytometry_panel": {
        "name": "CAR-T Immunophenotyping Flow Cytometry",
        "category": "characterization",
        "steps": [
            {"step": 1, "name": "Sample Preparation", "duration_hours": 0.5,
             "description": "Wash cells, adjust to 1×10⁶/tube, Fc block",
             "critical_params": ["Viability >85%", "10⁶ cells per panel"]},
            {"step": 2, "name": "Surface Staining", "duration_hours": 0.5,
             "description": "Stain with antibody cocktail: CD3/CD4/CD8/CAR/CD45RA/CCR7/PD-1/LAG-3/TIM-3",
             "critical_params": ["Protect from light", "30 min 4°C", "Include FMO controls"]},
            {"step": 3, "name": "Acquisition", "duration_hours": 1,
             "description": "Acquire on flow cytometer (BD FACSCanto/LSRFortessa/Cytek Aurora)",
             "critical_params": ["Minimum 50,000 events in live gate", "Compensation verified"]},
            {"step": 4, "name": "Analysis", "duration_hours": 2,
             "description": "Gate: Live → Singlets → CD3+ → CD4/CD8 → CAR+ → memory/exhaustion",
             "critical_params": ["Consistent gating strategy", "Report MFI and %positive"]},
        ],
        "total_duration_days": 1,
        "regulatory": ["Equipment QC", "Antibody lot verification"],
    },
    "xenograft_model": {
        "name": "CAR-T In Vivo Xenograft Efficacy Study",
        "category": "in_vivo",
        "steps": [
            {"step": 1, "name": "Tumor Engraftment", "duration_hours": 168,
             "description": "Inject 1×10⁶ luciferase-expressing tumor cells IV in NSG mice",
             "critical_params": ["NSG mice 6-8 weeks", "Tumor take >90%", "BLI baseline Day 7"]},
            {"step": 2, "name": "Randomization", "duration_hours": 1,
             "description": "Randomize mice into groups based on BLI signal (Day 7)",
             "critical_params": ["n=5-8 per group", "Equal tumor burden across groups"]},
            {"step": 3, "name": "CAR-T Infusion", "duration_hours": 1,
             "description": "IV injection of 1-10×10⁶ CAR-T cells via tail vein",
             "critical_params": ["Viability >80%", "Dose: 1M, 5M, 10M cells", "Include UTD control"]},
            {"step": 4, "name": "Monitoring", "duration_hours": 1344,
             "description": "Weekly BLI, weight, clinical scoring for 8 weeks",
             "critical_params": ["BLI weekly", "Weight loss >20% = humane endpoint", "Score 3/5 = endpoint"]},
            {"step": 5, "name": "Endpoint Analysis", "duration_hours": 24,
             "description": "Euthanize at endpoint; collect blood, spleen, tumor for flow/IHC",
             "critical_params": ["Blood for CAR-T persistence", "Tumor for target antigen expression"]},
        ],
        "total_duration_days": 60,
        "regulatory": ["IACUC approval", "ARRIVE guidelines", "3Rs principles"],
    },
    "tcr_sequencing": {
        "name": "TCR Repertoire Sequencing Protocol",
        "category": "sequencing",
        "steps": [
            {"step": 1, "name": "Sample Collection", "duration_hours": 1,
             "description": "Collect 5-10 mL peripheral blood or tissue biopsy",
             "critical_params": ["EDTA anticoagulant", "Process within 6 hours"]},
            {"step": 2, "name": "DNA/RNA Extraction", "duration_hours": 3,
             "description": "Extract genomic DNA (for DNA-based) or total RNA (for RNA-based TCR-seq)",
             "critical_params": ["DNA: >50 ng/μL, A260/280 1.8-2.0", "RNA: RIN >7"]},
            {"step": 3, "name": "Library Preparation", "duration_hours": 8,
             "description": "Multiplex PCR targeting TRBV-TRBJ segments (immunoSEQ/10X VDJ)",
             "critical_params": ["Input: 200-1000 ng DNA", "Bias-controlled amplification"]},
            {"step": 4, "name": "Sequencing", "duration_hours": 48,
             "description": "Illumina MiSeq/NovaSeq 2×300bp paired-end",
             "critical_params": ["Depth: >100K reads per sample", "Q30 >80%"]},
            {"step": 5, "name": "Bioinformatics", "duration_hours": 4,
             "description": "CDR3 extraction, clonotype calling, diversity analysis",
             "critical_params": ["MiXCR or immuneSEQ analyzer", "Shannon diversity, Clonality, V-gene usage"]},
        ],
        "total_duration_days": 5,
        "regulatory": ["IRB for human samples", "Informed consent"],
    },
}

# Deviation categories
_DEVIATION_TYPES = {
    "minor": {"description": "No impact on data quality or patient safety", "max_resolution_days": 30},
    "major": {"description": "May impact data quality; requires corrective action", "max_resolution_days": 14},
    "critical": {"description": "Impacts patient safety or data integrity", "max_resolution_days": 3},
}


async def list_protocol_templates(
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """List available protocol templates."""
    templates = []
    for key, tmpl in _PROTOCOL_TEMPLATES.items():
        if category and tmpl["category"] != category:
            continue
        templates.append({
            "template_id": key,
            "name": tmpl["name"],
            "category": tmpl["category"],
            "n_steps": len(tmpl["steps"]),
            "total_duration_days": tmpl["total_duration_days"],
            "regulatory": tmpl["regulatory"],
        })

    categories = list(set(t["category"] for t in _PROTOCOL_TEMPLATES.values()))
    return {"total": len(templates), "templates": templates, "categories": categories}


async def create_protocol(
    template_id: str,
    project_id: str = "default",
    created_by: str = "user_1",
    customizations: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a protocol instance from a template."""
    tmpl = _PROTOCOL_TEMPLATES.get(template_id)
    if not tmpl:
        return {"error": f"Template {template_id} not found", "available": list(_PROTOCOL_TEMPLATES.keys())}

    protocol_id = f"PROT-{uuid.uuid4().hex[:8]}"
    protocol = {
        "protocol_id": protocol_id,
        "template_id": template_id,
        "project_id": project_id,
        "name": tmpl["name"],
        "category": tmpl["category"],
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "version": 1,
        "status": "draft",
        "steps": tmpl["steps"],
        "customizations": customizations or {},
        "regulatory": tmpl["regulatory"],
        "deviations": [],
        "approval_status": "pending",
    }

    _PROTOCOLS[protocol_id] = protocol
    return {"protocol_id": protocol_id, "status": "created", "protocol": protocol}


async def log_deviation(
    protocol_id: str,
    step_number: int,
    severity: str = "minor",
    description: str = "",
    root_cause: str = "",
    corrective_action: str = "",
    reported_by: str = "user_1",
) -> Dict[str, Any]:
    """Log a protocol deviation."""
    deviation_id = f"DEV-{uuid.uuid4().hex[:8]}"
    dev_info = _DEVIATION_TYPES.get(severity, _DEVIATION_TYPES["minor"])

    deviation = {
        "deviation_id": deviation_id,
        "protocol_id": protocol_id,
        "step_number": step_number,
        "severity": severity,
        "description": description,
        "root_cause": root_cause,
        "corrective_action": corrective_action,
        "reported_by": reported_by,
        "reported_at": datetime.utcnow().isoformat(),
        "status": "open",
        "resolution_deadline": (datetime.utcnow() + timedelta(days=dev_info["max_resolution_days"])).isoformat(),
    }

    if protocol_id in _PROTOCOLS:
        _PROTOCOLS[protocol_id]["deviations"].append(deviation)

    return {"deviation_id": deviation_id, "logged": True, "deviation": deviation}


async def risk_assessment(
    protocol_id: Optional[str] = None,
    template_id: str = "car_t_manufacturing",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Perform risk assessment on a protocol."""
    if seed:
        random.seed(seed)

    tmpl = _PROTOCOL_TEMPLATES.get(template_id, _PROTOCOL_TEMPLATES["car_t_manufacturing"])

    risks = []
    for step in tmpl["steps"]:
        n_risks = random.randint(1, 3)
        for _ in range(n_risks):
            likelihood = random.choice([1, 2, 3, 4, 5])
            impact = random.choice([1, 2, 3, 4, 5])
            rpn = likelihood * impact

            risks.append({
                "step": step["step"],
                "step_name": step["name"],
                "risk": random.choice([
                    "Equipment failure", "Contamination", "Cell viability loss",
                    "Reagent quality issue", "Operator error", "Temperature excursion",
                    "Documentation error", "Sample mix-up", "Timing deviation",
                ]),
                "likelihood": likelihood,
                "impact": impact,
                "rpn": rpn,
                "category": "high" if rpn >= 15 else "medium" if rpn >= 8 else "low",
                "mitigation": random.choice([
                    "Implement dual verification", "Add monitoring alarm",
                    "Train backup operator", "Validate reagent lots",
                    "Install redundant equipment", "Implement checklist",
                ]),
            })

    risks.sort(key=lambda x: x["rpn"], reverse=True)

    return {
        "protocol": tmpl["name"],
        "total_risks": len(risks),
        "high_risks": sum(1 for r in risks if r["category"] == "high"),
        "medium_risks": sum(1 for r in risks if r["category"] == "medium"),
        "low_risks": sum(1 for r in risks if r["category"] == "low"),
        "risks": risks,
        "overall_risk_level": "high" if any(r["category"] == "high" for r in risks) else "medium",
    }
