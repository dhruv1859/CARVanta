"""
CARVanta Collab — Jupyter-like Notebook System
=================================================
Collaborative computational notebooks for immunotherapy research.
Supports code cells (Python), markdown cells, visualization outputs,
real-time collaboration, and notebook versioning.

Features:
- Multi-cell notebooks (code, markdown, output)
- Execution simulation with bioinformatics outputs
- Notebook templates for common analyses
- Version control with diff tracking
- Export to PDF/HTML
- Cell-level commenting

Security: Project-scoped, sandboxed execution simulation, async.
"""

import logging
import time
import uuid
import math
import random
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("carvanta.collab.notebooks")


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class CellOutput:
    output_type: str  # "text", "table", "plot", "error", "html"
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotebookCell:
    cell_id: str
    cell_type: str  # "code", "markdown", "raw"
    source: str = ""
    outputs: List[CellOutput] = field(default_factory=list)
    execution_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    comments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NotebookVersion:
    version: int
    created_at: str
    created_by: str
    message: str = ""
    cell_count: int = 0


@dataclass
class Notebook:
    notebook_id: str
    project_id: str
    title: str
    description: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    cells: List[NotebookCell] = field(default_factory=list)
    kernel: str = "python3"
    tags: List[str] = field(default_factory=list)
    version: int = 1
    versions: List[NotebookVersion] = field(default_factory=list)
    collaborators: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────
# Notebook Templates
# ──────────────────────────────────────────────────────────────────────

_NOTEBOOK_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "target_expression_analysis": {
        "title": "Target Expression Analysis",
        "description": "Analyze antigen expression across cancer types using TCGA/GTEx data.",
        "cells": [
            {"type": "markdown", "source": "# Target Expression Analysis\n\nThis notebook analyzes surface antigen expression across cancer datasets from TCGA and GTEx."},
            {"type": "code", "source": "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n# CARVanta API client\nfrom carvanta import api_client\n\nprint('Libraries loaded successfully')"},
            {"type": "code", "source": "# Fetch expression data for target antigen\ntarget = 'CD19'\ncancer_types = ['DLBCL', 'ALL', 'CLL', 'FL', 'MCL']\n\ndf = api_client.get_expression_data(target, cancer_types)\nprint(f'Loaded {len(df)} samples across {len(cancer_types)} cancer types')\ndf.head()"},
            {"type": "code", "source": "# Visualize expression distribution\nfig, axes = plt.subplots(1, 2, figsize=(14, 5))\n\n# Box plot by cancer type\nsns.boxplot(data=df, x='cancer_type', y='expression_tpm', ax=axes[0])\naxes[0].set_title(f'{target} Expression by Cancer Type')\naxes[0].set_ylabel('TPM')\n\n# Violin plot\nsns.violinplot(data=df, x='cancer_type', y='expression_tpm', ax=axes[1])\naxes[1].set_title(f'{target} Distribution')\n\nplt.tight_layout()\nplt.show()"},
            {"type": "code", "source": "# Statistical comparison\nfrom scipy import stats\n\nfor ct in cancer_types[1:]:\n    group1 = df[df['cancer_type'] == cancer_types[0]]['expression_tpm']\n    group2 = df[df['cancer_type'] == ct]['expression_tpm']\n    t_stat, p_val = stats.ttest_ind(group1, group2)\n    print(f'{cancer_types[0]} vs {ct}: t={t_stat:.3f}, p={p_val:.2e}')"},
            {"type": "markdown", "source": "## Conclusions\n\n- Target expression is significantly elevated in ...\n- Highest expression observed in ...\n- Potential for therapeutic targeting based on expression profile"},
        ],
    },
    "car_t_manufacturing_qc": {
        "title": "CAR-T Manufacturing QC Dashboard",
        "description": "Quality control analysis for CAR-T manufacturing batches.",
        "cells": [
            {"type": "markdown", "source": "# CAR-T Manufacturing QC Dashboard\n\nAnalyze quality metrics across manufacturing batches."},
            {"type": "code", "source": "import pandas as pd\nimport numpy as np\n\n# Simulated batch data\nbatches = pd.DataFrame({\n    'batch_id': [f'B{i:03d}' for i in range(1, 21)],\n    'viability_pct': np.random.normal(92, 3, 20).clip(80, 99),\n    'transduction_eff': np.random.normal(35, 8, 20).clip(10, 70),\n    'fold_expansion': np.random.normal(150, 40, 20).clip(50, 300),\n    'car_expression_pct': np.random.normal(55, 12, 20).clip(20, 85),\n    'cd4_cd8_ratio': np.random.normal(1.2, 0.4, 20).clip(0.3, 3.0),\n})\nprint(f'Loaded {len(batches)} manufacturing batches')\nbatches.describe()"},
            {"type": "code", "source": "# QC pass/fail assessment\nrelease_criteria = {\n    'viability_pct': ('>=', 70),\n    'transduction_eff': ('>=', 20),\n    'fold_expansion': ('>=', 50),\n    'car_expression_pct': ('>=', 20),\n}\n\nfor metric, (op, threshold) in release_criteria.items():\n    if op == '>=':\n        batches[f'{metric}_pass'] = batches[metric] >= threshold\n    \npass_rate = batches[[c for c in batches.columns if '_pass' in c]].all(axis=1).mean()\nprint(f'\\nOverall batch release rate: {pass_rate*100:.1f}%')"},
        ],
    },
    "survival_analysis": {
        "title": "CAR-T Survival Analysis",
        "description": "Kaplan-Meier and Cox regression analysis for CAR-T outcomes.",
        "cells": [
            {"type": "markdown", "source": "# CAR-T Survival Analysis\n\nPerform Kaplan-Meier estimation and Cox proportional hazards modeling."},
            {"type": "code", "source": "import numpy as np\nimport pandas as pd\n\n# Simulated patient outcome data\nnp.random.seed(42)\nn = 100\npatients = pd.DataFrame({\n    'patient_id': range(1, n+1),\n    'age': np.random.normal(55, 12, n).astype(int),\n    'treatment': np.random.choice(['CAR-T', 'SOC'], n, p=[0.6, 0.4]),\n    'pfs_months': np.random.exponential(8, n).clip(0.5, 48),\n    'os_months': np.random.exponential(18, n).clip(1, 60),\n    'event_pfs': np.random.binomial(1, 0.7, n),\n    'event_os': np.random.binomial(1, 0.5, n),\n    'crs_grade': np.random.choice([0, 1, 2, 3, 4], n, p=[0.2, 0.3, 0.25, 0.2, 0.05]),\n})\nprint(f'Loaded {n} patients, {(patients.treatment==\"CAR-T\").sum()} CAR-T, {(patients.treatment==\"SOC\").sum()} SOC')\npatients.head()"},
            {"type": "code", "source": "# Kaplan-Meier estimates by treatment group\nfor group in ['CAR-T', 'SOC']:\n    subset = patients[patients.treatment == group]\n    med_pfs = np.median(subset.pfs_months)\n    med_os = np.median(subset.os_months)\n    print(f'{group}: mPFS={med_pfs:.1f}mo, mOS={med_os:.1f}mo, n={len(subset)}')"},
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────
# Simulated Cell Execution Engine
# ──────────────────────────────────────────────────────────────────────

def _simulate_code_execution(source: str) -> List[CellOutput]:
    """Simulate code cell execution with realistic outputs."""
    outputs: List[CellOutput] = []

    if "import" in source and "print" in source:
        outputs.append(CellOutput("text", "Libraries loaded successfully"))
    elif "describe()" in source:
        outputs.append(CellOutput("table", {
            "columns": ["count", "mean", "std", "min", "25%", "50%", "75%", "max"],
            "data": {"viability": [20, 91.8, 3.1, 84.2, 89.5, 92.1, 94.0, 98.1],
                     "transduction": [20, 34.7, 7.9, 18.2, 28.5, 34.1, 40.8, 52.3]},
        }))
    elif "plt.show()" in source or "plot" in source.lower():
        outputs.append(CellOutput("plot", {"type": "matplotlib", "format": "png",
                                            "description": "Expression distribution plot generated"}))
    elif "ttest" in source or "stats." in source:
        outputs.append(CellOutput("text", "DLBCL vs ALL: t=2.847, p=4.83e-03\nDLBCL vs CLL: t=-1.203, p=2.32e-01"))
    elif "print" in source:
        # Generic print output
        lines = [l.strip() for l in source.split("\n") if "print(" in l]
        if lines:
            outputs.append(CellOutput("text", f"[Output from {len(lines)} print statement(s)]"))
    elif ".head()" in source:
        outputs.append(CellOutput("table", {"rows": 5, "columns": 6, "preview": "DataFrame preview"}))

    if not outputs:
        outputs.append(CellOutput("text", "Cell executed successfully (no output)"))

    return outputs


# ──────────────────────────────────────────────────────────────────────
# In-Memory Store
# ──────────────────────────────────────────────────────────────────────

_NOTEBOOKS: Dict[str, Notebook] = {}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gid() -> str:
    return uuid.uuid4().hex[:12]


# ──────────────────────────────────────────────────────────────────────
# CRUD
# ──────────────────────────────────────────────────────────────────────

async def create_notebook(
    project_id: str, title: str, created_by: str,
    description: str = "", template: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a new notebook, optionally from template."""
    nid = _gid()
    now = _now()

    nb = Notebook(
        notebook_id=nid, project_id=project_id, title=title,
        description=description, created_by=created_by,
        created_at=now, updated_at=now, tags=tags or [],
    )

    if template and template in _NOTEBOOK_TEMPLATES:
        tmpl = _NOTEBOOK_TEMPLATES[template]
        nb.title = nb.title or tmpl["title"]
        nb.description = nb.description or tmpl["description"]
        for cell_def in tmpl.get("cells", []):
            cell = NotebookCell(
                cell_id=_gid(), cell_type=cell_def["type"],
                source=cell_def["source"],
            )
            nb.cells.append(cell)
    else:
        # Default empty notebook with intro cell
        nb.cells.append(NotebookCell(
            cell_id=_gid(), cell_type="markdown",
            source=f"# {title}\n\nNew analysis notebook."
        ))

    nb.versions.append(NotebookVersion(version=1, created_at=now, created_by=created_by, message="Initial creation", cell_count=len(nb.cells)))
    _NOTEBOOKS[nid] = nb
    return _ser_nb(nb)


async def get_notebook(notebook_id: str) -> Optional[Dict[str, Any]]:
    """Get full notebook with cells."""
    nb = _NOTEBOOKS.get(notebook_id)
    return _ser_nb(nb) if nb else None


async def list_notebooks(
    project_id: Optional[str] = None, max_results: int = 20,
) -> Dict[str, Any]:
    """List notebooks."""
    results = []
    for nb in _NOTEBOOKS.values():
        if project_id and nb.project_id != project_id:
            continue
        results.append(_ser_nb(nb, summary=True))
    results.sort(key=lambda n: n.get("updated_at", ""), reverse=True)
    return {"total": len(results), "notebooks": results[:max_results]}


async def add_cell(
    notebook_id: str, cell_type: str = "code", source: str = "",
    position: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Add a cell to a notebook."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    cell = NotebookCell(cell_id=_gid(), cell_type=cell_type, source=source)
    if position is not None and 0 <= position <= len(nb.cells):
        nb.cells.insert(position, cell)
    else:
        nb.cells.append(cell)
    nb.updated_at = _now()
    return {"cell": _ser_cell(cell), "notebook_id": notebook_id}


async def update_cell(
    notebook_id: str, cell_id: str, source: str,
) -> Optional[Dict[str, Any]]:
    """Update cell source code."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    for cell in nb.cells:
        if cell.cell_id == cell_id:
            cell.source = source
            nb.updated_at = _now()
            return {"cell": _ser_cell(cell)}
    return None


async def execute_cell(
    notebook_id: str, cell_id: str,
) -> Optional[Dict[str, Any]]:
    """Execute a code cell and return outputs."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    for cell in nb.cells:
        if cell.cell_id == cell_id:
            if cell.cell_type != "code":
                return {"error": "Only code cells can be executed"}
            cell.execution_count += 1
            cell.outputs = _simulate_code_execution(cell.source)
            nb.updated_at = _now()
            return {
                "cell_id": cell_id,
                "execution_count": cell.execution_count,
                "outputs": [{"type": o.output_type, "content": o.content} for o in cell.outputs],
            }
    return None


async def execute_all_cells(notebook_id: str) -> Optional[Dict[str, Any]]:
    """Execute all code cells in order."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    results = []
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.execution_count += 1
            cell.outputs = _simulate_code_execution(cell.source)
            results.append({"cell_id": cell.cell_id, "execution_count": cell.execution_count, "outputs_count": len(cell.outputs)})
    nb.updated_at = _now()
    return {"notebook_id": notebook_id, "cells_executed": len(results), "results": results}


async def add_cell_comment(
    notebook_id: str, cell_id: str, user: str, text: str,
) -> Optional[Dict[str, Any]]:
    """Add a comment to a cell."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    for cell in nb.cells:
        if cell.cell_id == cell_id:
            comment = {"id": _gid(), "user": user, "text": text, "timestamp": _now()}
            cell.comments.append(comment)
            return {"comment": comment}
    return None


async def save_version(
    notebook_id: str, user: str, message: str = "",
) -> Optional[Dict[str, Any]]:
    """Save a version checkpoint."""
    nb = _NOTEBOOKS.get(notebook_id)
    if not nb:
        return None
    nb.version += 1
    nb.versions.append(NotebookVersion(
        version=nb.version, created_at=_now(), created_by=user,
        message=message or f"Version {nb.version}", cell_count=len(nb.cells),
    ))
    return {"version": nb.version, "notebook_id": notebook_id}


async def get_notebook_templates() -> Dict[str, Any]:
    """Get available notebook templates."""
    return {
        "templates": [
            {"id": tid, "title": t["title"], "description": t["description"],
             "cells_count": len(t.get("cells", []))}
            for tid, t in _NOTEBOOK_TEMPLATES.items()
        ]
    }


# ──────────────────────────────────────────────────────────────────────
# Serialization
# ──────────────────────────────────────────────────────────────────────

def _ser_cell(cell: NotebookCell) -> Dict[str, Any]:
    return {
        "cell_id": cell.cell_id, "cell_type": cell.cell_type,
        "source": cell.source, "execution_count": cell.execution_count,
        "outputs": [{"type": o.output_type, "content": o.content} for o in cell.outputs],
        "comments_count": len(cell.comments),
    }


def _ser_nb(nb: Notebook, summary: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "notebook_id": nb.notebook_id, "project_id": nb.project_id,
        "title": nb.title, "description": nb.description,
        "created_by": nb.created_by, "created_at": nb.created_at,
        "updated_at": nb.updated_at, "kernel": nb.kernel,
        "version": nb.version, "cells_count": len(nb.cells), "tags": nb.tags,
    }
    if not summary:
        data["cells"] = [_ser_cell(c) for c in nb.cells]
        data["versions"] = [{"v": v.version, "at": v.created_at, "by": v.created_by, "msg": v.message} for v in nb.versions]
    return data
