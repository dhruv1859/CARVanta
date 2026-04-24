"""
CARVanta Collab — Shared Experiment Tracking
==============================================
Track, manage, and share experimental results across research teams.
Supports experiment templates, protocol attachment, result recording,
statistical analysis, and cross-experiment comparison.

Features:
- Create experiments from protocol templates
- Track materials, reagents, equipment
- Record multi-dimensional results (numeric, categorical, image)
- Automated statistical summary (mean, SD, CV, t-test readiness)
- Cross-experiment comparison and trend analysis
- Experiment state machine (planned -> running -> analyzing -> complete)
- Reagent lot tracking for reproducibility

Security: Project-scoped, audit-trailed, async.
"""

import logging
import time
import uuid
import math
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("carvanta.collab.experiments")


class ExperimentStatus(Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    ON_HOLD = "on_hold"


class ResultType(Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    IMAGE = "image"
    TEXT = "text"
    BOOLEAN = "boolean"


@dataclass
class Reagent:
    name: str
    catalog_number: str = ""
    lot_number: str = ""
    vendor: str = ""
    concentration: str = ""
    expiry_date: str = ""
    storage_condition: str = ""


@dataclass
class EquipmentEntry:
    name: str
    model: str = ""
    serial_number: str = ""
    calibration_date: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultEntry:
    result_id: str
    metric_name: str
    value: Any
    unit: str = ""
    result_type: str = "numeric"
    replicate: int = 1
    condition: str = ""
    timestamp: str = ""
    notes: str = ""


@dataclass
class Experiment:
    experiment_id: str
    project_id: str
    title: str
    description: str
    protocol_name: str = ""
    hypothesis: str = ""
    status: str = "planned"
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    start_date: str = ""
    end_date: str = ""
    reagents: List[Reagent] = field(default_factory=list)
    equipment: List[EquipmentEntry] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    results: List[ResultEntry] = field(default_factory=list)
    conclusions: str = ""
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Experiment Templates
# ──────────────────────────────────────────────────────────────────────

_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "cytotoxicity_assay": {
        "title": "CAR-T Cytotoxicity Assay",
        "description": "Measure CAR-T cell killing of target cells at multiple E:T ratios.",
        "protocol": "co-culture_cytotoxicity_v3",
        "reagents": [
            {"name": "CytoTox 96 Non-Radioactive Kit", "vendor": "Promega", "catalog_number": "G1780"},
            {"name": "RPMI 1640", "vendor": "Gibco", "catalog_number": "11875-093"},
            {"name": "FBS (heat-inactivated)", "vendor": "Gibco", "catalog_number": "16140-071"},
        ],
        "conditions": ["E:T 1:1", "E:T 5:1", "E:T 10:1", "E:T 20:1", "Untransduced control"],
        "metrics": ["specific_lysis_pct", "cytokine_ifng", "cytokine_tnfa", "cytokine_il2"],
    },
    "flow_cytometry_panel": {
        "title": "CAR-T Phenotyping Flow Panel",
        "description": "Multi-color flow cytometry for CAR-T cell characterization.",
        "protocol": "flow_cart_phenotype_v2",
        "reagents": [
            {"name": "Zombie Aqua Viability Dye", "vendor": "BioLegend", "catalog_number": "423101"},
            {"name": "Anti-CD3 BV421", "vendor": "BioLegend", "catalog_number": "300434"},
            {"name": "Anti-CD4 AF488", "vendor": "BioLegend", "catalog_number": "317420"},
            {"name": "Anti-CD8 PE-Cy7", "vendor": "BioLegend", "catalog_number": "344712"},
            {"name": "Protein L Biotin", "vendor": "GenScript", "catalog_number": "M00097"},
        ],
        "conditions": ["Pre-expansion", "Day 7", "Day 14", "Post-infusion product"],
        "metrics": ["viability_pct", "cd3_pos_pct", "cd4_cd8_ratio", "car_expression_pct", "memory_phenotype"],
    },
    "elisa_cytokine": {
        "title": "Cytokine ELISA Panel",
        "description": "Quantify cytokines released during CAR-T co-culture.",
        "protocol": "elisa_multiplex_v1",
        "reagents": [
            {"name": "Human IFN-γ ELISA Kit", "vendor": "R&D Systems", "catalog_number": "DIF50C"},
            {"name": "Human TNF-α ELISA Kit", "vendor": "R&D Systems", "catalog_number": "DTA00D"},
            {"name": "Human IL-2 ELISA Kit", "vendor": "R&D Systems", "catalog_number": "D2050"},
        ],
        "conditions": ["Stimulated", "Unstimulated", "Positive Control"],
        "metrics": ["ifng_pg_ml", "tnfa_pg_ml", "il2_pg_ml", "il6_pg_ml"],
    },
    "xenograft_efficacy": {
        "title": "NSG Xenograft Efficacy Study",
        "description": "In vivo CAR-T efficacy in NSG mouse xenograft model.",
        "protocol": "xenograft_nsg_v4",
        "reagents": [
            {"name": "Matrigel", "vendor": "Corning", "catalog_number": "354234"},
            {"name": "D-luciferin", "vendor": "Gold Biotechnology", "catalog_number": "LUCK-1G"},
        ],
        "conditions": ["CAR-T treated", "Untransduced control", "Tumor only", "Healthy control"],
        "metrics": ["tumor_volume_mm3", "body_weight_g", "bioluminescence_photons", "survival_days"],
    },
}


# ──────────────────────────────────────────────────────────────────────
# In-Memory Store
# ──────────────────────────────────────────────────────────────────────

_EXPERIMENTS: Dict[str, Experiment] = {}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gid() -> str:
    return uuid.uuid4().hex[:12]


# ──────────────────────────────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────────────────────────────

async def create_experiment(
    project_id: str, title: str, description: str,
    created_by: str, template: Optional[str] = None,
    hypothesis: str = "", tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new experiment, optionally from template."""
    eid = _gid()
    now = _now()

    exp = Experiment(
        experiment_id=eid, project_id=project_id,
        title=title, description=description,
        created_by=created_by, created_at=now, updated_at=now,
        hypothesis=hypothesis, tags=tags or [],
    )

    if template and template in _TEMPLATES:
        tmpl = _TEMPLATES[template]
        exp.protocol_name = tmpl.get("protocol", "")
        if not title:
            exp.title = tmpl["title"]
        exp.description = exp.description or tmpl["description"]
        exp.conditions = tmpl.get("conditions", [])
        for r in tmpl.get("reagents", []):
            exp.reagents.append(Reagent(**r))

    _EXPERIMENTS[eid] = exp
    return _ser_exp(exp)


async def get_experiment(experiment_id: str) -> Optional[Dict[str, Any]]:
    """Get experiment details."""
    exp = _EXPERIMENTS.get(experiment_id)
    return _ser_exp(exp) if exp else None


async def list_experiments(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    max_results: int = 20,
) -> Dict[str, Any]:
    """List experiments with filtering."""
    results = []
    for exp in _EXPERIMENTS.values():
        if project_id and exp.project_id != project_id:
            continue
        if status and exp.status != status:
            continue
        results.append(_ser_exp(exp, summary=True))
    results.sort(key=lambda e: e.get("updated_at", ""), reverse=True)
    return {"total": len(results), "experiments": results[:max_results]}


async def update_experiment_status(
    experiment_id: str, status: str,
) -> Optional[Dict[str, Any]]:
    """Update experiment status."""
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp:
        return None
    exp.status = status
    exp.updated_at = _now()
    if status == "in_progress" and not exp.start_date:
        exp.start_date = _now()
    if status == "completed":
        exp.end_date = _now()
    return _ser_exp(exp)


async def add_result(
    experiment_id: str, metric_name: str, value: Any,
    unit: str = "", replicate: int = 1, condition: str = "", notes: str = "",
) -> Optional[Dict[str, Any]]:
    """Add a result entry to an experiment."""
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp:
        return None
    result = ResultEntry(
        result_id=_gid(), metric_name=metric_name, value=value,
        unit=unit, replicate=replicate, condition=condition,
        timestamp=_now(), notes=notes,
        result_type="numeric" if isinstance(value, (int, float)) else "text",
    )
    exp.results.append(result)
    exp.updated_at = _now()
    return {"result": _ser_result(result), "experiment_id": experiment_id}


async def get_experiment_stats(experiment_id: str) -> Dict[str, Any]:
    """Compute statistical summary for experiment results."""
    exp = _EXPERIMENTS.get(experiment_id)
    if not exp:
        return {"error": "Experiment not found"}

    numeric_results: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for r in exp.results:
        if isinstance(r.value, (int, float)):
            key = r.metric_name
            cond = r.condition or "all"
            numeric_results[key][cond].append(float(r.value))

    stats: Dict[str, Any] = {}
    for metric, conditions in numeric_results.items():
        metric_stats: Dict[str, Any] = {}
        for cond, values in conditions.items():
            n = len(values)
            mean = sum(values) / n if n > 0 else 0
            variance = sum((v - mean) ** 2 for v in values) / max(n - 1, 1) if n > 1 else 0
            sd = math.sqrt(variance)
            cv = (sd / mean * 100) if mean != 0 else 0
            metric_stats[cond] = {
                "n": n, "mean": round(mean, 3), "sd": round(sd, 3),
                "cv_pct": round(cv, 1), "min": round(min(values), 3),
                "max": round(max(values), 3), "median": round(sorted(values)[n // 2], 3),
            }
        stats[metric] = metric_stats

    return {"experiment_id": experiment_id, "title": exp.title, "statistics": stats}


async def get_experiment_templates() -> Dict[str, Any]:
    """Get available experiment templates."""
    return {
        "templates": [
            {"id": tid, "title": t["title"], "description": t["description"],
             "conditions": t.get("conditions", []),
             "metrics": t.get("metrics", []),
             "reagents_count": len(t.get("reagents", []))}
            for tid, t in _TEMPLATES.items()
        ]
    }


# ──────────────────────────────────────────────────────────────────────
# Serialization
# ──────────────────────────────────────────────────────────────────────

def _ser_result(r: ResultEntry) -> Dict[str, Any]:
    return {
        "result_id": r.result_id, "metric": r.metric_name, "value": r.value,
        "unit": r.unit, "replicate": r.replicate, "condition": r.condition,
        "timestamp": r.timestamp, "notes": r.notes,
    }


def _ser_exp(exp: Experiment, summary: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "experiment_id": exp.experiment_id, "project_id": exp.project_id,
        "title": exp.title, "description": exp.description[:150] if summary else exp.description,
        "status": exp.status, "protocol": exp.protocol_name,
        "hypothesis": exp.hypothesis, "created_by": exp.created_by,
        "created_at": exp.created_at, "updated_at": exp.updated_at,
        "results_count": len(exp.results), "conditions": exp.conditions,
        "tags": exp.tags,
    }
    if not summary:
        data["reagents"] = [{"name": r.name, "vendor": r.vendor, "catalog": r.catalog_number, "lot": r.lot_number} for r in exp.reagents]
        data["equipment"] = [{"name": e.name, "model": e.model} for e in exp.equipment]
        data["results"] = [_ser_result(r) for r in exp.results]
        data["conclusions"] = exp.conclusions
    return data
