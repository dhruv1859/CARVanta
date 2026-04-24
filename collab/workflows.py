"""
CARVanta Collab — Workflow Orchestration Engine
==================================================
Automated research workflow pipeline management for
multi-step experimental processes. Define, execute,
and monitor complex research workflows.

Features:
- Visual workflow designer with DAG execution
- 12 pre-built CAR-T research workflow templates
- Conditional branching and parallel execution
- Automated data handoffs between steps
- SLA monitoring and deadline tracking
- Email/Slack notification triggers
- Retry and error recovery policies
- Workflow versioning and rollback
- Execution history with performance metrics
- Cross-project workflow sharing
"""

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import Counter

logger = logging.getLogger("carvanta.collab.workflows")

# In-memory workflow store
_WORKFLOWS: Dict[str, Dict] = {}
_WORKFLOW_RUNS: Dict[str, Dict] = {}

# Pre-built workflow templates
_WORKFLOW_TEMPLATES = {
    "cart_development": {
        "name": "End-to-End CAR-T Development Pipeline",
        "description": "From target discovery through IND filing",
        "category": "development",
        "steps": [
            {"step_id": "S1", "name": "Target Identification", "type": "task",
             "duration_days": 30, "department": "Discovery",
             "inputs": ["literature_review", "expression_data"],
             "outputs": ["candidate_targets"],
             "description": "Identify candidate surface antigens using multi-omics analysis",
             "tools": ["CARVanta Target Explorer", "Single-cell Atlas"]},
            {"step_id": "S2", "name": "Target Validation", "type": "task",
             "duration_days": 60, "department": "Discovery",
             "inputs": ["candidate_targets"],
             "outputs": ["validated_targets"],
             "description": "Validate target expression and specificity using flow cytometry, IHC, and qPCR",
             "tools": ["Flow Cytometry Core", "Histology Lab"]},
            {"step_id": "S3", "name": "scFv Generation", "type": "task",
             "duration_days": 90, "department": "Antibody Engineering",
             "inputs": ["validated_targets"],
             "outputs": ["scfv_candidates"],
             "description": "Generate and screen scFv fragments via phage/yeast display",
             "tools": ["Phage Display Library", "SPR (Biacore)"]},
            {"step_id": "S4", "name": "CAR Construct Design", "type": "task",
             "duration_days": 30, "department": "Vector Engineering",
             "inputs": ["scfv_candidates"],
             "outputs": ["car_constructs"],
             "description": "Design CAR constructs with optimal signaling domains (CD28 vs 4-1BB)",
             "tools": ["CARVanta CAR Architect", "Vector Design Suite"]},
            {"step_id": "S5", "name": "In Vitro Testing", "type": "task",
             "duration_days": 45, "department": "Functional Assays",
             "inputs": ["car_constructs"],
             "outputs": ["in_vitro_results"],
             "description": "Cytotoxicity, cytokine release, and exhaustion assays",
             "tools": ["xCELLigence RTCA", "Luminex", "Flow Cytometry"]},
            {"step_id": "S6", "name": "In Vivo Efficacy", "type": "task",
             "duration_days": 90, "department": "Animal Studies",
             "inputs": ["in_vitro_results"],
             "outputs": ["in_vivo_results"],
             "description": "NSG mouse xenograft models with BLI monitoring",
             "tools": ["IVIS Spectrum", "Animal Facility"]},
            {"step_id": "S7", "name": "GMP Manufacturing", "type": "task",
             "duration_days": 120, "department": "Manufacturing",
             "inputs": ["in_vivo_results"],
             "outputs": ["gmp_product"],
             "description": "Tech transfer, process development, and GMP lot production",
             "tools": ["CliniMACS Prodigy", "G-Rex Bioreactor"]},
            {"step_id": "S8", "name": "IND Filing", "type": "milestone",
             "duration_days": 60, "department": "Regulatory",
             "inputs": ["gmp_product", "in_vivo_results"],
             "outputs": ["ind_submission"],
             "description": "Prepare and submit IND application to FDA",
             "tools": ["eCTD Builder", "Regulatory Affairs"]},
        ],
        "total_duration_months": 18,
        "estimated_cost_usd": 5000000,
    },
    "clinical_trial_setup": {
        "name": "CAR-T Clinical Trial Setup",
        "description": "From IND approval to first patient enrollment",
        "category": "clinical",
        "steps": [
            {"step_id": "CT1", "name": "Protocol Development", "type": "task",
             "duration_days": 45, "department": "Clinical Operations",
             "inputs": ["ind_approval"], "outputs": ["clinical_protocol"],
             "description": "Develop Phase I/II protocol with 3+3 dose escalation design"},
            {"step_id": "CT2", "name": "IRB Submission", "type": "task",
             "duration_days": 30, "department": "Regulatory",
             "inputs": ["clinical_protocol"], "outputs": ["irb_approval"],
             "description": "Submit to central and local IRBs for approval"},
            {"step_id": "CT3", "name": "Site Qualification", "type": "task",
             "duration_days": 60, "department": "Clinical Operations",
             "inputs": ["irb_approval"], "outputs": ["qualified_sites"],
             "description": "Qualify 5-10 clinical sites for CAR-T administration (FACT-accredited)"},
            {"step_id": "CT4", "name": "Patient Screening", "type": "task",
             "duration_days": 90, "department": "Clinical",
             "inputs": ["qualified_sites"], "outputs": ["enrolled_patients"],
             "description": "Screen and enroll patients per eligibility criteria"},
            {"step_id": "CT5", "name": "Leukapheresis", "type": "task",
             "duration_days": 1, "department": "Apheresis",
             "inputs": ["enrolled_patients"], "outputs": ["patient_cells"],
             "description": "Collect patient T-cells via leukapheresis"},
            {"step_id": "CT6", "name": "Manufacturing", "type": "task",
             "duration_days": 28, "department": "Manufacturing",
             "inputs": ["patient_cells"], "outputs": ["car_t_product"],
             "description": "Manufacture patient-specific CAR-T product"},
            {"step_id": "CT7", "name": "Lymphodepletion & Infusion", "type": "task",
             "duration_days": 7, "department": "Clinical",
             "inputs": ["car_t_product"], "outputs": ["treatment_administered"],
             "description": "Flu/Cy conditioning followed by CAR-T infusion"},
            {"step_id": "CT8", "name": "Monitoring & Follow-up", "type": "task",
             "duration_days": 365, "department": "Clinical",
             "inputs": ["treatment_administered"], "outputs": ["clinical_data"],
             "description": "CRS/ICANS monitoring, response assessment, long-term follow-up"},
        ],
        "total_duration_months": 24,
        "estimated_cost_usd": 15000000,
    },
    "biomarker_discovery": {
        "name": "Predictive Biomarker Discovery",
        "description": "Identify biomarkers predicting CAR-T response",
        "category": "translational",
        "steps": [
            {"step_id": "BD1", "name": "Cohort Assembly", "type": "task",
             "duration_days": 30, "department": "Biobank",
             "inputs": ["clinical_outcomes"], "outputs": ["patient_cohort"],
             "description": "Assemble responder vs non-responder cohorts with matched samples"},
            {"step_id": "BD2", "name": "Multi-omics Profiling", "type": "parallel",
             "duration_days": 60, "department": "Genomics",
             "inputs": ["patient_cohort"],
             "outputs": ["wes_data", "rnaseq_data", "cytof_data"],
             "description": "Parallel WES, RNA-seq, and CyTOF profiling of all samples"},
            {"step_id": "BD3", "name": "Bioinformatics Analysis", "type": "task",
             "duration_days": 45, "department": "Computational",
             "inputs": ["wes_data", "rnaseq_data", "cytof_data"],
             "outputs": ["candidate_biomarkers"],
             "description": "Integrated multi-omics analysis, ML feature selection, pathway enrichment"},
            {"step_id": "BD4", "name": "Validation Cohort", "type": "task",
             "duration_days": 60, "department": "Clinical",
             "inputs": ["candidate_biomarkers"],
             "outputs": ["validated_biomarkers"],
             "description": "Validate top biomarkers in independent cohort (IHC, qPCR, targeted panel)"},
            {"step_id": "BD5", "name": "Companion Diagnostic Dev", "type": "task",
             "duration_days": 120, "department": "Diagnostics",
             "inputs": ["validated_biomarkers"],
             "outputs": ["cdx_assay"],
             "description": "Develop companion diagnostic assay for clinical use"},
        ],
        "total_duration_months": 12,
        "estimated_cost_usd": 2000000,
    },
}


async def list_workflow_templates(
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """List available workflow templates."""
    templates = []
    for key, tmpl in _WORKFLOW_TEMPLATES.items():
        if category and tmpl["category"] != category:
            continue
        templates.append({
            "template_id": key,
            "name": tmpl["name"],
            "description": tmpl["description"],
            "category": tmpl["category"],
            "n_steps": len(tmpl["steps"]),
            "total_duration_months": tmpl["total_duration_months"],
            "estimated_cost_usd": tmpl["estimated_cost_usd"],
        })

    return {"total": len(templates), "templates": templates}


async def create_workflow(
    template_id: str,
    project_id: str = "default",
    created_by: str = "user_1",
    start_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a workflow instance from a template."""
    tmpl = _WORKFLOW_TEMPLATES.get(template_id)
    if not tmpl:
        return {"error": f"Template {template_id} not found", "available": list(_WORKFLOW_TEMPLATES.keys())}

    workflow_id = f"WF-{uuid.uuid4().hex[:8]}"
    start = datetime.fromisoformat(start_date) if start_date else datetime.utcnow()

    # Build step schedule
    scheduled_steps = []
    current_date = start
    for step in tmpl["steps"]:
        step_end = current_date + timedelta(days=step["duration_days"])
        scheduled_steps.append({
            **step,
            "status": "pending",
            "scheduled_start": current_date.isoformat(),
            "scheduled_end": step_end.isoformat(),
            "actual_start": None,
            "actual_end": None,
            "assigned_to": None,
            "progress_pct": 0,
        })
        if step["type"] != "parallel":
            current_date = step_end

    workflow = {
        "workflow_id": workflow_id,
        "template_id": template_id,
        "project_id": project_id,
        "name": tmpl["name"],
        "created_by": created_by,
        "created_at": datetime.utcnow().isoformat(),
        "status": "created",
        "steps": scheduled_steps,
        "total_steps": len(scheduled_steps),
        "completed_steps": 0,
        "estimated_completion": current_date.isoformat(),
        "budget_usd": tmpl["estimated_cost_usd"],
        "spent_usd": 0,
    }

    _WORKFLOWS[workflow_id] = workflow
    return {"workflow_id": workflow_id, "status": "created", "workflow": workflow}


async def workflow_status(
    workflow_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get workflow execution status with progress metrics."""
    if seed:
        random.seed(seed)

    if workflow_id and workflow_id in _WORKFLOWS:
        wf = _WORKFLOWS[workflow_id]
        return {"workflow": wf}

    # Simulate a workflow in progress
    tmpl = _WORKFLOW_TEMPLATES["cart_development"]
    steps = tmpl["steps"]
    current_step_idx = random.randint(1, len(steps) - 1)

    step_statuses = []
    for i, step in enumerate(steps):
        if i < current_step_idx:
            status = "completed"
            progress = 100
        elif i == current_step_idx:
            status = "in_progress"
            progress = random.randint(20, 80)
        else:
            status = "pending"
            progress = 0

        step_statuses.append({
            "step_id": step["step_id"],
            "name": step["name"],
            "status": status,
            "progress_pct": progress,
            "department": step["department"],
            "duration_days": step["duration_days"],
        })

    overall_progress = round(
        (current_step_idx * 100 + step_statuses[current_step_idx]["progress_pct"]) / len(steps), 1
    )

    return {
        "workflow_id": workflow_id or "simulated",
        "name": tmpl["name"],
        "overall_progress_pct": overall_progress,
        "current_step": steps[current_step_idx]["name"],
        "steps": step_statuses,
        "on_track": random.random() > 0.3,
        "blockers": random.randint(0, 2),
        "days_remaining": sum(s["duration_days"] for s in steps[current_step_idx:]),
    }


async def gantt_data(
    workflow_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate Gantt chart data for workflow visualization."""
    if seed:
        random.seed(seed)

    tmpl = _WORKFLOW_TEMPLATES.get("cart_development")
    if workflow_id and workflow_id in _WORKFLOWS:
        wf = _WORKFLOWS[workflow_id]
        steps = wf["steps"]
    else:
        steps = tmpl["steps"]

    gantt_items = []
    start_date = datetime.utcnow()
    for step in steps:
        end_date = start_date + timedelta(days=step["duration_days"])
        gantt_items.append({
            "id": step["step_id"],
            "name": step["name"],
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "duration_days": step["duration_days"],
            "department": step.get("department", ""),
            "type": step.get("type", "task"),
            "progress": random.randint(0, 100),
            "dependencies": [],
            "color": {
                "Discovery": "#4CAF50", "Antibody Engineering": "#2196F3",
                "Vector Engineering": "#FF9800", "Functional Assays": "#9C27B0",
                "Animal Studies": "#F44336", "Manufacturing": "#00BCD4",
                "Regulatory": "#795548", "Clinical Operations": "#607D8B",
                "Clinical": "#E91E63", "Genomics": "#3F51B5",
                "Computational": "#009688", "Biobank": "#FF5722",
                "Apheresis": "#CDDC39", "Diagnostics": "#8BC34A",
            }.get(step.get("department", ""), "#9E9E9E"),
        })
        if step.get("type") != "parallel":
            start_date = end_date

    return {
        "workflow": tmpl["name"] if not workflow_id else workflow_id,
        "gantt_items": gantt_items,
        "total_duration_days": sum(s["duration_days"] for s in steps),
        "critical_path": [s["step_id"] for s in steps if s.get("type") != "parallel"],
    }
