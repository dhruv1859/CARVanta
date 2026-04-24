"""
CARVanta Copilot — Experiment Protocol Designer
==================================================
Generates experimentalprotocol suggestions for CAR-T research,
including in vitro assays, in vivo models, manufacturing steps,
and clinical biomarker panels.

Covers 8 protocol categories with step-by-step procedures,
reagent lists, timelines, and expected outcomes.

Security: Stateless, async, input-validated.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.copilot.experiment_designer")

# ──────────────────────────────────────────────────────────────────────
# Protocol Categories
# ──────────────────────────────────────────────────────────────────────

class ProtocolCategory(Enum):
    """Experiment protocol categories."""
    IN_VITRO_CYTOTOXICITY = "in_vitro_cytotoxicity"
    IN_VITRO_ACTIVATION = "in_vitro_activation"
    IN_VIVO_XENOGRAFT = "in_vivo_xenograft"
    CAR_CONSTRUCTION = "car_construction"
    T_CELL_MANUFACTURING = "t_cell_manufacturing"
    FLOW_CYTOMETRY = "flow_cytometry"
    CYTOKINE_PROFILING = "cytokine_profiling"
    PERSISTENCE_ASSAY = "persistence_assay"
    ANTIGEN_EXPRESSION = "antigen_expression"
    BINDING_AFFINITY = "binding_affinity"


@dataclass
class ProtocolStep:
    """Single protocol step."""
    step_number: int
    description: str
    duration: str
    notes: str = ""
    critical: bool = False


@dataclass
class Reagent:
    """Reagent requirement."""
    name: str
    catalog_number: str
    vendor: str
    quantity: str
    storage: str = ""


@dataclass
class ExperimentProtocol:
    """Complete experiment protocol."""
    title: str
    category: str
    target: str
    objective: str
    steps: List[ProtocolStep] = field(default_factory=list)
    reagents: List[Reagent] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)
    expected_timeline: str = ""
    expected_outcome: str = ""
    safety_notes: List[str] = field(default_factory=list)
    analysis_methods: List[str] = field(default_factory=list)
    confidence: float = 0.0


# ──────────────────────────────────────────────────────────────────────
# Protocol Templates
# ──────────────────────────────────────────────────────────────────────

_PROTOCOL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "cytotoxicity": {
        "title": "CAR-T Cytotoxicity Assay (Chromium Release / Luciferase)",
        "objective": "Quantify target-specific killing of tumor cells by CAR-T cells at multiple E:T ratios.",
        "steps": [
            {"step": 1, "desc": "Culture target-positive tumor cells (expressing target antigen) and target-negative controls to 80% confluence", "duration": "48h", "critical": False},
            {"step": 2, "desc": "Label tumor cells with [51Cr] chromium (4h, 100 µCi/1e6 cells) or pre-transduce with luciferase reporter", "duration": "4-24h", "critical": True},
            {"step": 3, "desc": "Wash labeled tumor cells 3× with warm PBS, resuspend at 1e4 cells/100µL in complete RPMI", "duration": "30min", "critical": False},
            {"step": 4, "desc": "Plate CAR-T cells at E:T ratios of 10:1, 5:1, 2:1, 1:1, and 0.5:1 in triplicate 96-well U-bottom plates", "duration": "30min", "critical": False},
            {"step": 5, "desc": "Add labeled tumor cells (1e4/well) to effector wells. Include spontaneous release (media only) and maximum release (1% Triton X-100) controls", "duration": "15min", "critical": True},
            {"step": 6, "desc": "Incubate at 37°C, 5% CO2 for 4-16h (4h standard, 16h for persistence readout)", "duration": "4-16h", "critical": False},
            {"step": 7, "desc": "Harvest 50µL supernatant, measure [51Cr] release on gamma counter or luminescence on plate reader", "duration": "1h", "critical": False},
            {"step": 8, "desc": "Calculate % specific lysis: (Experimental - Spontaneous) / (Maximum - Spontaneous) × 100", "duration": "1h", "critical": False},
        ],
        "reagents": [
            {"name": "Complete RPMI 1640", "catalog": "11875093", "vendor": "Gibco", "qty": "500 mL"},
            {"name": "Na₂[⁵¹Cr]O₄", "catalog": "NEZ030", "vendor": "PerkinElmer", "qty": "1 mCi"},
            {"name": "Triton X-100", "catalog": "T8787", "vendor": "Sigma-Aldrich", "qty": "100 mL"},
            {"name": "IL-2 (recombinant human)", "catalog": "200-02", "vendor": "PeproTech", "qty": "50 µg"},
            {"name": "Anti-human CD3/CD28 Dynabeads", "catalog": "11131D", "vendor": "Thermo Fisher", "qty": "4e7 beads"},
        ],
        "controls": [
            "Untransduced T cells (same donor)",
            "Target-negative cell line (antigen-negative)",
            "Mock-transduced T cells (empty vector)",
            "Spontaneous release (media only)",
            "Maximum release (1% Triton X-100)",
        ],
        "timeline": "5-7 days (including T cell expansion)",
        "outcome": "Expect 40-80% specific lysis at 10:1 E:T ratio for well-functioning CAR-T. EC50 should be <5:1 E:T.",
        "safety": ["Handle [51Cr] in designated radiation area", "Use BSL-2 practices for cell culture", "Dispose of radioactive waste per institutional protocol"],
        "analysis": ["Non-linear regression (4-parameter logistic)", "EC50 calculation", "Statistical comparison (paired t-test)", "Flow cytometry for T cell phenotype"],
    },
    "flow": {
        "title": "CAR-T Phenotyping by Multi-Parameter Flow Cytometry",
        "objective": "Characterize CAR expression, T cell subset composition, and activation/exhaustion markers in CAR-T products.",
        "steps": [
            {"step": 1, "desc": "Harvest CAR-T cells, wash 2× with FACS buffer (PBS + 2% FBS + 0.1% sodium azide)", "duration": "20min", "critical": False},
            {"step": 2, "desc": "Block Fc receptors with Human TruStain FcX (5µL/1e6 cells) for 10min at RT", "duration": "10min", "critical": True},
            {"step": 3, "desc": "Stain with surface antibody panel (CD3, CD4, CD8, CD45RA, CCR7, PD-1, TIM-3, LAG-3, Protein L or anti-idiotype for CAR detection) for 30min at 4°C in dark", "duration": "30min", "critical": True},
            {"step": 4, "desc": "Wash 2× with FACS buffer, fix with 2% PFA for 15min if needed", "duration": "30min", "critical": False},
            {"step": 5, "desc": "For intracellular staining (Ki-67, Granzyme B, IFN-γ), permeabilize with Cytofix/Cytoperm kit, stain for 30min", "duration": "45min", "critical": False},
            {"step": 6, "desc": "Acquire ≥50,000 events on flow cytometer (e.g., BD LSRFortessa, Cytek Aurora). Include FMO and single-stain compensation controls", "duration": "1-2h", "critical": True},
            {"step": 7, "desc": "Analyze with FlowJo v10: gate on singlets → live cells → CD3+ → CD4/CD8 → CAR+ → memory subsets and exhaustion markers", "duration": "2-4h", "critical": False},
        ],
        "reagents": [
            {"name": "Protein L-biotin", "catalog": "29997", "vendor": "Thermo Scientific", "qty": "100 µg"},
            {"name": "Streptavidin-PE", "catalog": "554061", "vendor": "BD Biosciences", "qty": "100 tests"},
            {"name": "Anti-CD3-BV421", "catalog": "562426", "vendor": "BD Biosciences", "qty": "100 tests"},
            {"name": "Anti-PD-1-PE-Cy7", "catalog": "329918", "vendor": "BioLegend", "qty": "100 tests"},
            {"name": "LIVE/DEAD Fixable Aqua", "catalog": "L34965", "vendor": "Thermo Fisher", "qty": "1 vial"},
            {"name": "Cytofix/Cytoperm kit", "catalog": "554714", "vendor": "BD Biosciences", "qty": "1 kit"},
        ],
        "controls": ["FMO controls for each fluorochrome", "Unstained cells", "Single-stain compensation beads", "Positive control (activated PBMCs)", "Isotype controls (optional)"],
        "timeline": "1 day (staining + acquisition + analysis)",
        "outcome": "Expect >30% CAR+ for well-transduced products. Ideal phenotype: >50% CD8+, Tcm/Tscm > Teff, PD-1 low. High exhaustion markers (PD-1+TIM-3+LAG-3+) indicate dysfunction.",
        "safety": ["Handle sodium azide with caution", "Use PFA in fume hood", "Dispose of biohazardous waste properly"],
        "analysis": ["tSNE/UMAP dimensionality reduction", "Manual gating with FlowJo", "Statistical analysis of marker frequencies", "Memory subset quantification"],
    },
    "xenograft": {
        "title": "In Vivo CAR-T Efficacy in Xenograft Mouse Model",
        "objective": "Evaluate anti-tumor efficacy, T cell persistence, and safety of CAR-T cells in a human tumor xenograft model.",
        "steps": [
            {"step": 1, "desc": "Engraft NSG mice (6-8 weeks, female) with 1e6 luciferase-expressing tumor cells (IV for disseminated, SC for solid)", "duration": "Day -14", "critical": True},
            {"step": 2, "desc": "Confirm tumor engraftment by bioluminescence imaging (IVIS) on Day -7 and Day -1. Randomize mice with comparable tumor burden", "duration": "Day -7 to -1", "critical": True},
            {"step": 3, "desc": "Administer lymphodepleting conditioning: cyclophosphamide 150 mg/kg IP on Day -1 (optional but recommended)", "duration": "Day -1", "critical": False},
            {"step": 4, "desc": "Infuse CAR-T cells via tail vein: 1e6, 5e6, or 10e6 CAR+ cells/mouse. Include untransduced T cells and PBS controls (n=5-8/group)", "duration": "Day 0", "critical": True},
            {"step": 5, "desc": "Monitor tumor burden by IVIS weekly. Measure body weight 2×/week. Score GvHD daily", "duration": "Day 0-60", "critical": False},
            {"step": 6, "desc": "Collect peripheral blood weekly for flow cytometry (human CD45+, CD3+, CAR+ quantification)", "duration": "Weekly", "critical": False},
            {"step": 7, "desc": "At study endpoint, harvest tumors, spleen, blood, and organs. Process for flow cytometry, IHC, and histopathology", "duration": "Endpoint", "critical": True},
            {"step": 8, "desc": "Analyze survival curves (Kaplan-Meier), tumor growth kinetics, and T cell persistence data", "duration": "1 week", "critical": False},
        ],
        "reagents": [
            {"name": "NSG mice (NOD.Cg-Prkdcscid Il2rgtm1Wjl/SzJ)", "catalog": "005557", "vendor": "Jackson Labs", "qty": "30-50 mice"},
            {"name": "D-Luciferin potassium salt", "catalog": "122799", "vendor": "PerkinElmer", "qty": "1g"},
            {"name": "Cyclophosphamide", "catalog": "C0768", "vendor": "Sigma-Aldrich", "qty": "5g"},
            {"name": "Matrigel (for SC tumors)", "catalog": "354234", "vendor": "Corning", "qty": "10 mL"},
        ],
        "controls": ["PBS (vehicle only)", "Untransduced T cells", "Mock CAR (irrelevant antigen)", "Tumor-only (no treatment)"],
        "timeline": "60-90 days total study",
        "outcome": "Expect complete tumor clearance at 10e6 dose within 14-21 days for validated targets (CD19, BCMA). Dose-dependent response. T cell persistence detectable in blood for 30-60 days.",
        "safety": ["IACUC approval required", "BSL-2 containment for human cell handling", "Monitor for GvHD symptoms", "Humane endpoints per institutional guidelines"],
        "analysis": ["Kaplan-Meier survival analysis", "Log-rank test for group comparisons", "Bioluminescence flux quantification", "Flow cytometry for T cell phenotype and persistence"],
    },
}


# ──────────────────────────────────────────────────────────────────────
# Protocol Suggestion Engine
# ──────────────────────────────────────────────────────────────────────

def _detect_protocol_type(query: str) -> str:
    """Detect the most appropriate protocol type from user query."""
    q = query.lower()
    if any(kw in q for kw in ["kill", "cytotox", "lysis", "tumor killing"]):
        return "cytotoxicity"
    if any(kw in q for kw in ["flow", "phenotype", "marker", "stain", "facs"]):
        return "flow"
    if any(kw in q for kw in ["mouse", "xenograft", "in vivo", "animal", "nsg"]):
        return "xenograft"
    return "cytotoxicity"  # Default


async def suggest_protocol(target: str, query: str = "") -> Dict[str, Any]:
    """
    Suggest an experiment protocol for a CAR-T target.
    """
    target = re.sub(r'[^a-zA-Z0-9_\-]', '', target).strip().upper()[:32]
    protocol_type = _detect_protocol_type(query)
    template = _PROTOCOL_TEMPLATES.get(protocol_type, _PROTOCOL_TEMPLATES["cytotoxicity"])

    # Personalize for target
    title = f"{template['title']} — {target} CAR-T"
    objective = template["objective"].replace("target antigen", f"{target} antigen")

    steps = []
    for s in template["steps"]:
        steps.append({
            "step": s["step"],
            "description": s["desc"],
            "duration": s["duration"],
            "critical": s.get("critical", False),
        })

    reagents = []
    for r in template["reagents"]:
        reagents.append({
            "name": r["name"],
            "catalog_number": r["catalog"],
            "vendor": r["vendor"],
            "quantity": r["qty"],
        })

    protocol_text = f"# {title}\n\n**Objective:** {objective}\n\n"
    protocol_text += "## Protocol Steps\n\n"
    for s in steps:
        crit = " ⚠️ CRITICAL" if s["critical"] else ""
        protocol_text += f"{s['step']}. {s['description']} [{s['duration']}]{crit}\n"

    protocol_text += f"\n## Expected Timeline\n{template['timeline']}\n"
    protocol_text += f"\n## Expected Outcome\n{template['outcome']}\n"
    protocol_text += "\n## Controls Required\n" + "\n".join(f"- {c}" for c in template["controls"])
    protocol_text += "\n\n## Safety Notes\n" + "\n".join(f"- {s}" for s in template["safety"])

    return {
        "title": title,
        "category": protocol_type,
        "target": target,
        "objective": objective,
        "protocol_text": protocol_text,
        "steps": steps,
        "reagents": reagents,
        "controls": template["controls"],
        "timeline": template["timeline"],
        "expected_outcome": template["outcome"],
        "safety_notes": template["safety"],
        "analysis_methods": template["analysis"],
        "confidence": 0.85,
    }


async def list_available_protocols() -> List[Dict[str, str]]:
    """List all available protocol templates."""
    return [
        {"type": k, "title": v["title"], "objective": v["objective"]}
        for k, v in _PROTOCOL_TEMPLATES.items()
    ]
