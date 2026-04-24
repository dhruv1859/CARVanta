"""
CARVanta Collab — API Router (Expanded)
==========================================
REST API endpoints for Module 6: Research Collaboration Hub.
Covers 12 engines with 65+ endpoints.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger("carvanta.api.collab_router")
router = APIRouter(prefix="/api/v5/collab", tags=["Collaboration Hub"])


# ── Request Models ────────────────────────────────────────────────────

class CreateProjectReq(BaseModel):
    title: str = Field(..., max_length=200)
    description: str = Field("", max_length=2000)
    owner_id: str = Field("user_1", max_length=32)
    owner_name: str = Field("researcher", max_length=50)
    template: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    research_area: str = ""
    target_antigen: str = ""
    disease_focus: str = ""

class AddMemberReq(BaseModel):
    user_id: str = Field(..., max_length=32)
    username: str = Field(..., max_length=50)
    role: str = Field("researcher", max_length=20)

class CreateExperimentReq(BaseModel):
    project_id: str = Field(..., max_length=32)
    title: str = Field(..., max_length=200)
    description: str = Field("", max_length=2000)
    created_by: str = Field("user_1", max_length=32)
    template: Optional[str] = None
    hypothesis: str = ""
    tags: List[str] = Field(default_factory=list)

class AddResultReq(BaseModel):
    metric_name: str = Field(..., max_length=100)
    value: Any
    unit: str = ""
    replicate: int = 1
    condition: str = ""

class CreateNotebookReq(BaseModel):
    project_id: str = Field(..., max_length=32)
    title: str = Field(..., max_length=200)
    created_by: str = Field("user_1", max_length=32)
    template: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class SubmitReviewReq(BaseModel):
    reviewer_id: str = Field("reviewer_1", max_length=32)
    reviewer_name: str = Field("Dr. Reviewer", max_length=100)
    scores: Dict[str, float] = Field(default_factory=dict)
    recommendation: str = Field("minor_revision", max_length=20)
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

class CreateSubmissionReq(BaseModel):
    project_id: str = Field(..., max_length=32)
    title: str = Field(..., max_length=200)
    abstract: str = Field(..., max_length=2000)
    content: str = Field("", max_length=10000)
    author_id: str = Field("user_1", max_length=32)
    author_name: str = Field("researcher", max_length=100)
    submission_type: str = Field("target_proposal", max_length=30)
    target_antigen: str = ""
    tags: List[str] = Field(default_factory=list)

class SendMessageReq(BaseModel):
    sender_id: str = Field("user_1", max_length=32)
    sender_name: str = Field("researcher", max_length=50)
    content: str = Field(..., max_length=5000)
    reply_to: Optional[str] = None

class CreateDatasetReq(BaseModel):
    project_id: str = Field("default", max_length=32)
    title: str = Field(..., max_length=200)
    description: str = Field("", max_length=2000)
    created_by: str = Field("user_1", max_length=32)
    data_type: str = Field("csv", max_length=20)
    tags: List[str] = Field(default_factory=list)
    access_level: str = Field("team", max_length=20)
    organism: str = "Homo sapiens"
    disease: str = ""

class GrantPermissionReq(BaseModel):
    resource_type: str = Field(..., max_length=32)
    resource_id: str = Field(..., max_length=64)
    user_id: str = Field(..., max_length=32)
    role: str = Field("researcher", max_length=32)

class CreateInviteReq(BaseModel):
    project_id: str = Field(..., max_length=32)
    email: str = Field(..., max_length=100)
    role: str = Field("researcher", max_length=32)
    message: str = ""

class CreateProtocolReq(BaseModel):
    template_id: str = Field(..., max_length=64)
    project_id: str = Field("default", max_length=32)
    created_by: str = Field("user_1", max_length=32)

class LogDeviationReq(BaseModel):
    step_number: int = 1
    severity: str = Field("minor", max_length=20)
    description: str = ""
    root_cause: str = ""
    corrective_action: str = ""

class PreregisterReq(BaseModel):
    title: str = Field(..., max_length=200)
    hypothesis: str = Field(..., max_length=2000)
    primary_outcome: str = Field(..., max_length=500)
    sample_size: int = Field(100, ge=1)
    analysis_plan: str = ""

class DSAReq(BaseModel):
    project_id: str = Field(..., max_length=32)
    partner_institution: str = Field(..., max_length=200)
    data_types: List[str] = Field(default_factory=lambda: ["clinical", "genomic"])
    purpose: str = ""
    duration_months: int = 12


# ── Project Endpoints ─────────────────────────────────────────────────

@router.post("/projects", summary="Create research project")
async def create_project(req: CreateProjectReq) -> Dict[str, Any]:
    from collab.projects import create_project
    return await create_project(req.title, req.description, req.owner_id, req.owner_name, req.template, req.tags, req.research_area, req.target_antigen, req.disease_focus)

@router.get("/projects", summary="List projects")
async def list_projects(status: Optional[str] = None, tag: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    from collab.projects import list_projects
    return await list_projects(status=status, tag=tag, search=search)

@router.get("/projects/{project_id}", summary="Get project details")
async def get_project(project_id: str) -> Dict[str, Any]:
    from collab.projects import get_project
    result = await get_project(project_id)
    if not result: raise HTTPException(404, "Project not found")
    return result

@router.post("/projects/{project_id}/members", summary="Add team member")
async def add_member(project_id: str, req: AddMemberReq) -> Dict[str, Any]:
    from collab.projects import add_member
    result = await add_member(project_id, req.user_id, req.username, req.role)
    if not result: raise HTTPException(404, "Project not found")
    return result

@router.get("/projects/templates/list", summary="Get project templates")
async def project_templates() -> Dict[str, Any]:
    from collab.projects import get_project_templates
    return await get_project_templates()


# ── Experiment Endpoints ──────────────────────────────────────────────

@router.post("/experiments", summary="Create experiment")
async def create_experiment(req: CreateExperimentReq) -> Dict[str, Any]:
    from collab.experiments import create_experiment
    return await create_experiment(req.project_id, req.title, req.description, req.created_by, req.template, req.hypothesis, req.tags)

@router.get("/experiments", summary="List experiments")
async def list_experiments(project_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    from collab.experiments import list_experiments
    return await list_experiments(project_id=project_id, status=status)

@router.get("/experiments/{experiment_id}", summary="Get experiment")
async def get_experiment(experiment_id: str) -> Dict[str, Any]:
    from collab.experiments import get_experiment
    result = await get_experiment(experiment_id)
    if not result: raise HTTPException(404, "Experiment not found")
    return result

@router.post("/experiments/{experiment_id}/results", summary="Add result")
async def add_result(experiment_id: str, req: AddResultReq) -> Dict[str, Any]:
    from collab.experiments import add_result
    result = await add_result(experiment_id, req.metric_name, req.value, req.unit, req.replicate, req.condition)
    if not result: raise HTTPException(404, "Experiment not found")
    return result

@router.get("/experiments/{experiment_id}/stats", summary="Experiment stats")
async def experiment_stats(experiment_id: str) -> Dict[str, Any]:
    from collab.experiments import get_experiment_stats
    return await get_experiment_stats(experiment_id)

@router.get("/experiments/templates/list", summary="Experiment templates")
async def experiment_templates() -> Dict[str, Any]:
    from collab.experiments import get_experiment_templates
    return await get_experiment_templates()


# ── Notebook Endpoints ────────────────────────────────────────────────

@router.post("/notebooks", summary="Create notebook")
async def create_notebook(req: CreateNotebookReq) -> Dict[str, Any]:
    from collab.notebooks import create_notebook
    return await create_notebook(req.project_id, req.title, req.created_by, template=req.template, tags=req.tags)

@router.get("/notebooks", summary="List notebooks")
async def list_notebooks(project_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.notebooks import list_notebooks
    return await list_notebooks(project_id=project_id)

@router.get("/notebooks/{notebook_id}", summary="Get notebook")
async def get_notebook(notebook_id: str) -> Dict[str, Any]:
    from collab.notebooks import get_notebook
    result = await get_notebook(notebook_id)
    if not result: raise HTTPException(404, "Notebook not found")
    return result

@router.post("/notebooks/{notebook_id}/execute/{cell_id}", summary="Execute cell")
async def execute_cell(notebook_id: str, cell_id: str) -> Dict[str, Any]:
    from collab.notebooks import execute_cell
    result = await execute_cell(notebook_id, cell_id)
    if not result: raise HTTPException(404, "Not found")
    return result

@router.get("/notebooks/templates/list", summary="Notebook templates")
async def notebook_templates() -> Dict[str, Any]:
    from collab.notebooks import get_notebook_templates
    return await get_notebook_templates()


# ── Peer Review Endpoints ────────────────────────────────────────────

@router.post("/submissions", summary="Create submission")
async def create_submission(req: CreateSubmissionReq) -> Dict[str, Any]:
    from collab.peer_review import create_submission
    return await create_submission(req.project_id, req.title, req.abstract, req.content, req.author_id, req.author_name, req.submission_type, req.target_antigen, tags=req.tags)

@router.get("/submissions", summary="List submissions")
async def list_submissions(project_id: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
    from collab.peer_review import list_submissions
    return await list_submissions(project_id=project_id, status=status)

@router.post("/submissions/{submission_id}/review", summary="Submit review")
async def submit_review(submission_id: str, req: SubmitReviewReq) -> Dict[str, Any]:
    from collab.peer_review import submit_review
    result = await submit_review(submission_id, req.reviewer_id, req.reviewer_name, req.scores, req.recommendation, req.summary, req.strengths, req.weaknesses)
    if not result: raise HTTPException(404, "Submission not found")
    return result

@router.get("/submissions/{submission_id}/summary", summary="Review summary")
async def review_summary(submission_id: str) -> Dict[str, Any]:
    from collab.peer_review import get_review_summary
    return await get_review_summary(submission_id)


# ── PubMed Endpoints ─────────────────────────────────────────────────

@router.get("/pubmed/search", summary="Search PubMed")
async def search_pubmed(query: str = "", max_results: int = 15) -> Dict[str, Any]:
    from collab.pubmed_linker import search_pubmed
    return await search_pubmed(query, max_results=max_results)

@router.get("/pubmed/target/{target}", summary="Citations for target")
async def citations_for_target(target: str) -> Dict[str, Any]:
    from collab.pubmed_linker import get_citations_for_target
    return await get_citations_for_target(target)

@router.get("/pubmed/stats", summary="PubMed index stats")
async def pubmed_stats() -> Dict[str, Any]:
    from collab.pubmed_linker import get_pubmed_stats
    return await get_pubmed_stats()


# ── Messaging Endpoints ──────────────────────────────────────────────

@router.post("/channels/{channel_id}/messages", summary="Send message")
async def send_message(channel_id: str, req: SendMessageReq) -> Dict[str, Any]:
    from collab.messaging import send_message
    result = await send_message(channel_id, req.sender_id, req.sender_name, req.content, req.reply_to)
    if not result: raise HTTPException(404, "Channel not found")
    return result

@router.get("/channels/{channel_id}/messages", summary="Get messages")
async def get_messages(channel_id: str, limit: int = 50) -> Dict[str, Any]:
    from collab.messaging import get_messages
    return await get_messages(channel_id, limit=limit)


# ── Dataset Endpoints ────────────────────────────────────────────────

@router.post("/datasets", summary="Create dataset")
async def create_dataset(req: CreateDatasetReq) -> Dict[str, Any]:
    from collab.datasets import create_dataset
    return await create_dataset(req.project_id, req.title, req.description, req.created_by, req.data_type, req.tags, req.access_level, req.organism, req.disease)

@router.get("/datasets", summary="List datasets")
async def list_datasets(project_id: Optional[str] = None, data_type: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    from collab.datasets import list_datasets
    return await list_datasets(project_id=project_id, data_type=data_type, search=search)

@router.get("/datasets/{dataset_id}/quality", summary="Dataset quality assessment")
async def dataset_quality(dataset_id: str) -> Dict[str, Any]:
    from collab.datasets import assess_data_quality
    return await assess_data_quality(dataset_id)

@router.get("/datasets/{dataset_id}/fair", summary="FAIR assessment")
async def dataset_fair(dataset_id: str) -> Dict[str, Any]:
    from collab.datasets import fair_assessment
    return await fair_assessment(dataset_id)

@router.get("/datasets/{dataset_id}/stats", summary="Dataset statistics")
async def dataset_stats(dataset_id: str) -> Dict[str, Any]:
    from collab.datasets import dataset_statistics
    return await dataset_statistics(dataset_id)

@router.post("/datasets/cohort", summary="Build patient cohort")
async def build_cohort(template: Optional[str] = None) -> Dict[str, Any]:
    from collab.datasets import build_cohort
    return await build_cohort(template=template)


# ── Audit Trail Endpoints ────────────────────────────────────────────

@router.get("/audit", summary="Get audit trail")
async def get_audit(entity_id: Optional[str] = None, user_id: Optional[str] = None, category: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    from collab.audit_trail import get_audit_trail
    return await get_audit_trail(entity_id=entity_id, user_id=user_id, category=category, limit=limit)

@router.get("/audit/compliance/{regulation}", summary="Compliance report")
async def compliance_report(regulation: str = "FDA_21CFR11") -> Dict[str, Any]:
    from collab.audit_trail import compliance_report
    return await compliance_report(regulation=regulation)

@router.get("/audit/analytics", summary="Activity analytics")
async def activity_analytics(days: int = Query(30, ge=1, le=365)) -> Dict[str, Any]:
    from collab.audit_trail import activity_analytics
    return await activity_analytics(days=days)

@router.get("/audit/integrity", summary="Verify hash chain integrity")
async def verify_integrity() -> Dict[str, Any]:
    from collab.audit_trail import verify_chain_integrity
    return verify_chain_integrity()


# ── Analytics Endpoints ───────────────────────────────────────────────

@router.get("/analytics/productivity", summary="Team productivity")
async def team_productivity(project_id: Optional[str] = None, period_days: int = 90) -> Dict[str, Any]:
    from collab.analytics import team_productivity
    return await team_productivity(project_id=project_id, period_days=period_days)

@router.get("/analytics/network", summary="Collaboration network")
async def collaboration_network() -> Dict[str, Any]:
    from collab.analytics import collaboration_network
    return await collaboration_network()

@router.get("/analytics/impact", summary="Research impact metrics")
async def impact_metrics(project_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.analytics import impact_metrics
    return await impact_metrics(project_id=project_id)

@router.get("/analytics/trends", summary="Research trends")
async def research_trends() -> Dict[str, Any]:
    from collab.analytics import research_trends
    return await research_trends()

@router.get("/analytics/funding", summary="Funding tracker")
async def funding_tracker(project_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.analytics import funding_tracker
    return await funding_tracker(project_id=project_id)

@router.get("/analytics/publications", summary="Publication pipeline")
async def publication_pipeline() -> Dict[str, Any]:
    from collab.analytics import publication_pipeline
    return await publication_pipeline()


# ── Protocol Endpoints ────────────────────────────────────────────────

@router.get("/protocols/templates", summary="List protocol templates")
async def protocol_templates(category: Optional[str] = None) -> Dict[str, Any]:
    from collab.protocols import list_protocol_templates
    return await list_protocol_templates(category=category)

@router.post("/protocols", summary="Create protocol from template")
async def create_protocol(req: CreateProtocolReq) -> Dict[str, Any]:
    from collab.protocols import create_protocol
    return await create_protocol(req.template_id, req.project_id, req.created_by)

@router.post("/protocols/{protocol_id}/deviations", summary="Log protocol deviation")
async def log_deviation(protocol_id: str, req: LogDeviationReq) -> Dict[str, Any]:
    from collab.protocols import log_deviation
    return await log_deviation(protocol_id, req.step_number, req.severity, req.description, req.root_cause, req.corrective_action)

@router.get("/protocols/{protocol_id}/risks", summary="Protocol risk assessment")
async def protocol_risks(protocol_id: str, template_id: str = "car_t_manufacturing") -> Dict[str, Any]:
    from collab.protocols import risk_assessment
    return await risk_assessment(protocol_id=protocol_id, template_id=template_id)


# ── Permissions Endpoints ─────────────────────────────────────────────

@router.get("/permissions/roles", summary="List all roles")
async def list_roles() -> Dict[str, Any]:
    from collab.permissions import list_roles
    return await list_roles()

@router.post("/permissions/grant", summary="Grant permission")
async def grant_permission(req: GrantPermissionReq) -> Dict[str, Any]:
    from collab.permissions import grant_permission
    return await grant_permission(req.resource_type, req.resource_id, req.user_id, req.role)

@router.get("/permissions/check", summary="Check access")
async def check_access(resource_type: str, resource_id: str, user_id: str, action: str = "read") -> Dict[str, Any]:
    from collab.permissions import check_access
    return await check_access(resource_type, resource_id, user_id, action)

@router.post("/invitations", summary="Create invitation")
async def create_invitation(req: CreateInviteReq) -> Dict[str, Any]:
    from collab.permissions import create_invitation
    return await create_invitation(req.project_id, req.email, req.role, message=req.message)

@router.post("/data-sharing-agreements", summary="Create DSA")
async def create_dsa(req: DSAReq) -> Dict[str, Any]:
    from collab.permissions import create_data_sharing_agreement
    return await create_data_sharing_agreement(req.project_id, req.partner_institution, req.data_types, req.purpose, req.duration_months)


# ── Reproducibility Endpoints ─────────────────────────────────────────

@router.get("/reproducibility/score", summary="Reproducibility score")
async def repro_score(experiment_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.reproducibility import reproducibility_score
    return await reproducibility_score(experiment_id=experiment_id)

@router.get("/reproducibility/power-analysis", summary="Statistical power analysis")
async def power_analysis_endpoint(
    effect_size: float = Query(0.5, ge=0.01, le=3.0),
    alpha: float = Query(0.05, ge=0.001, le=0.1),
    power: float = Query(0.8, ge=0.5, le=0.99),
    test_type: str = "two_sample_t",
    groups: int = Query(2, ge=2, le=10),
) -> Dict[str, Any]:
    from collab.reproducibility import power_analysis
    return await power_analysis(effect_size=effect_size, alpha=alpha, power=power, test_type=test_type, groups=groups)

@router.get("/reproducibility/checklist/{checklist_type}", summary="Reporting checklist")
async def reporting_checklist(checklist_type: str = "CONSORT") -> Dict[str, Any]:
    from collab.reproducibility import generate_checklist
    return await generate_checklist(checklist_type=checklist_type)

@router.post("/reproducibility/preregister", summary="Pre-register experiment")
async def preregister(req: PreregisterReq) -> Dict[str, Any]:
    from collab.reproducibility import preregister_experiment
    return await preregister_experiment(req.title, req.hypothesis, req.primary_outcome, req.sample_size, req.analysis_plan)


# ── Workflow Endpoints ─────────────────────────────────────────────────

@router.get("/workflows/templates", summary="List workflow templates")
async def workflow_templates(category: Optional[str] = None) -> Dict[str, Any]:
    from collab.workflows import list_workflow_templates
    return await list_workflow_templates(category=category)

@router.post("/workflows", summary="Create workflow instance")
async def create_workflow(
    template_id: str = "cart_development",
    project_id: str = "default",
) -> Dict[str, Any]:
    from collab.workflows import create_workflow
    return await create_workflow(template_id=template_id, project_id=project_id)

@router.get("/workflows/{workflow_id}/status", summary="Workflow execution status")
async def workflow_status(workflow_id: str) -> Dict[str, Any]:
    from collab.workflows import workflow_status
    return await workflow_status(workflow_id=workflow_id)

@router.get("/workflows/{workflow_id}/gantt", summary="Gantt chart data")
async def workflow_gantt(workflow_id: str) -> Dict[str, Any]:
    from collab.workflows import gantt_data
    return await gantt_data(workflow_id=workflow_id)


# ── Knowledge Base Endpoints ──────────────────────────────────────────

@router.get("/knowledge/glossary", summary="Search immunotherapy glossary")
async def search_glossary(query: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
    from collab.knowledge_base import search_glossary
    return await search_glossary(query=query, category=category)

@router.post("/knowledge/articles", summary="Create KB article")
async def create_kb_article(
    title: str = "New Article",
    content: str = "",
    category: str = "getting_started",
) -> Dict[str, Any]:
    from collab.knowledge_base import create_article
    return await create_article(title=title, content=content, category=category)

@router.get("/knowledge/articles", summary="List KB articles")
async def list_kb_articles(category: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    from collab.knowledge_base import list_articles
    return await list_articles(category=category, search=search)

@router.post("/knowledge/faq", summary="Create FAQ entry")
async def create_faq_entry(
    question: str = "",
    answer: str = "",
    category: str = "general",
) -> Dict[str, Any]:
    from collab.knowledge_base import create_faq
    return await create_faq(question=question, answer=answer, category=category)

@router.get("/knowledge/onboarding/{role}", summary="Onboarding guide")
async def onboarding_guide(role: str = "researcher") -> Dict[str, Any]:
    from collab.knowledge_base import get_onboarding_guide
    return await get_onboarding_guide(role=role)


# ── Notification Endpoints ────────────────────────────────────────────

@router.get("/notifications/{user_id}", summary="Get user notifications")
async def get_notifications(user_id: str, unread_only: bool = False, category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    from collab.notifications import get_notifications
    return await get_notifications(user_id, unread_only=unread_only, category=category, limit=limit)

@router.post("/notifications/{user_id}/read", summary="Mark notifications read")
async def mark_notifications_read(user_id: str, notification_id: Optional[str] = None, mark_all: bool = False) -> Dict[str, Any]:
    from collab.notifications import mark_read
    return await mark_read(user_id, notification_id=notification_id, mark_all=mark_all)

@router.post("/notifications/{user_id}/preferences", summary="Set notification preferences")
async def set_notification_prefs(user_id: str, email_digest: str = "daily") -> Dict[str, Any]:
    from collab.notifications import set_preferences
    return await set_preferences(user_id, email_digest=email_digest)

@router.post("/notifications/webhooks", summary="Register webhook")
async def register_webhook(project_id: str = "default", url: str = "", platform: str = "slack") -> Dict[str, Any]:
    from collab.notifications import register_webhook
    return await register_webhook(project_id, url, platform)

@router.get("/notifications/{user_id}/summary", summary="Notification summary")
async def notification_summary(user_id: str, days: int = 7) -> Dict[str, Any]:
    from collab.notifications import notification_summary
    return await notification_summary(user_id=user_id, days=days)


# ── Inventory Endpoints ───────────────────────────────────────────────

@router.get("/inventory/catalog", summary="Reagent catalog")
async def reagent_catalog() -> Dict[str, Any]:
    from collab.inventory import list_reagent_catalog
    return await list_reagent_catalog()

@router.post("/inventory/reagents", summary="Add reagent to inventory")
async def add_reagent(reagent_id: str, lot_number: str = "", quantity: float = 1) -> Dict[str, Any]:
    from collab.inventory import add_reagent_to_inventory
    return await add_reagent_to_inventory(reagent_id, lot_number, quantity)

@router.get("/inventory/status", summary="Inventory status with alerts")
async def inv_status(category: Optional[str] = None, critical_only: bool = False) -> Dict[str, Any]:
    from collab.inventory import inventory_status
    return await inventory_status(category=category, critical_only=critical_only)

@router.get("/inventory/equipment", summary="Equipment status & calibration")
async def equip_status() -> Dict[str, Any]:
    from collab.inventory import equipment_status
    return await equipment_status()

@router.get("/inventory/forecast/{reagent_id}", summary="Consumption forecast")
async def consumption_forecast(reagent_id: str, months: int = 6) -> Dict[str, Any]:
    from collab.inventory import consumption_forecast
    return await consumption_forecast(reagent_id=reagent_id, forecast_months=months)


# ── Visualization Endpoints ───────────────────────────────────────────

@router.get("/viz/timeline", summary="Research output timeline chart")
async def viz_timeline(months: int = 12) -> Dict[str, Any]:
    from collab.visualizations import research_timeline
    return await research_timeline(months=months)

@router.get("/viz/heatmap", summary="Collaboration heatmap")
async def viz_heatmap(n_researchers: int = 10) -> Dict[str, Any]:
    from collab.visualizations import collaboration_heatmap
    return await collaboration_heatmap(n_researchers=n_researchers)

@router.get("/viz/success-trends", summary="Experiment success trends")
async def viz_success_trends(months: int = 12) -> Dict[str, Any]:
    from collab.visualizations import experiment_success_trends
    return await experiment_success_trends(months=months)

@router.get("/viz/impact-scatter", summary="Publication impact scatter")
async def viz_impact_scatter() -> Dict[str, Any]:
    from collab.visualizations import impact_scatter
    return await impact_scatter()

@router.get("/viz/funding-burndown", summary="Funding burn-down chart")
async def viz_burndown(months: int = 24, budget: int = 5000000) -> Dict[str, Any]:
    from collab.visualizations import funding_burndown
    return await funding_burndown(months=months, total_budget=budget)

@router.get("/viz/quality-radar", summary="Research quality radar chart")
async def viz_quality_radar() -> Dict[str, Any]:
    from collab.visualizations import quality_radar
    return await quality_radar()

@router.get("/viz/sparklines", summary="Team activity sparklines")
async def viz_sparklines(days: int = 30) -> Dict[str, Any]:
    from collab.visualizations import team_sparklines
    return await team_sparklines(days=days)

@router.get("/viz/benchmark", summary="Institutional benchmarking")
async def viz_benchmark() -> Dict[str, Any]:
    from collab.visualizations import benchmark_comparison
    return await benchmark_comparison()


# ── Ethics & IRB Endpoints ────────────────────────────────────────────

@router.post("/ethics/irb/submit", summary="Submit to IRB")
async def submit_irb(
    study_title: str = "CAR-T Study",
    submission_type: str = "new_study",
    principal_investigator: str = "Dr. Researcher",
) -> Dict[str, Any]:
    from collab.ethics import submit_to_irb
    return await submit_to_irb(study_title, submission_type, principal_investigator)

@router.get("/ethics/irb/status", summary="IRB submission status")
async def irb_status_endpoint(submission_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.ethics import irb_status
    return await irb_status(submission_id=submission_id)

@router.get("/ethics/consent", summary="Consent tracker")
async def consent_tracker(study_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.ethics import consent_tracker
    return await consent_tracker(study_id=study_id)

@router.get("/ethics/coi/{investigator}", summary="COI disclosure")
async def coi_disclosure(investigator: str = "Dr. Researcher") -> Dict[str, Any]:
    from collab.ethics import coi_disclosure
    return await coi_disclosure(investigator_name=investigator)

@router.get("/ethics/dashboard", summary="Ethics program dashboard")
async def ethics_dashboard() -> Dict[str, Any]:
    from collab.ethics import ethics_dashboard
    return await ethics_dashboard()


# ── Multi-Site Coordination Endpoints ─────────────────────────────────

@router.get("/multisite/sites", summary="List research sites")
async def list_sites(country: Optional[str] = None, capability: Optional[str] = None) -> Dict[str, Any]:
    from collab.multisite import list_sites
    return await list_sites(country=country, capability=capability)

@router.get("/multisite/performance", summary="Site performance metrics")
async def site_performance(site_id: Optional[str] = None) -> Dict[str, Any]:
    from collab.multisite import site_performance
    return await site_performance(site_id=site_id)

@router.get("/multisite/enrollment", summary="Cross-site enrollment")
async def cross_site_enrollment() -> Dict[str, Any]:
    from collab.multisite import cross_site_enrollment
    return await cross_site_enrollment()

@router.get("/multisite/harmonization", summary="Data harmonization status")
async def data_harmonization() -> Dict[str, Any]:
    from collab.multisite import data_harmonization
    return await data_harmonization()

@router.get("/multisite/nearest", summary="Find nearest sites")
async def nearest_sites(lat: float = 40.7128, lon: float = -74.006, max_km: float = 5000) -> Dict[str, Any]:
    from collab.multisite import find_nearest_sites
    return await find_nearest_sites(latitude=lat, longitude=lon, max_distance_km=max_km)

@router.get("/multisite/federated/{analysis_type}", summary="Federated analysis plan")
async def federated_analysis(analysis_type: str = "survival") -> Dict[str, Any]:
    from collab.multisite import federated_analysis_plan
    return await federated_analysis_plan(analysis_type=analysis_type)


# ── Training & Competency Endpoints ──────────────────────────────────

@router.get("/training/modules", summary="List training modules")
async def training_modules(category: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
    from collab.training import list_training_modules
    return await list_training_modules(category=category, role=role)

@router.post("/training/record", summary="Record training completion")
async def record_training(user_id: str = "user_1", module_id: str = "gcp_training", score: float = 85) -> Dict[str, Any]:
    from collab.training import record_training
    return await record_training(user_id, module_id, score)

@router.get("/training/status/{user_id}", summary="Training compliance status")
async def training_status(user_id: str, role: Optional[str] = None) -> Dict[str, Any]:
    from collab.training import training_status
    return await training_status(user_id=user_id, role=role)

@router.get("/training/competency-matrix", summary="Team competency matrix")
async def competency_matrix() -> Dict[str, Any]:
    from collab.training import competency_matrix
    return await competency_matrix()


# ── Milestone & Progress Endpoints ───────────────────────────────────

@router.post("/milestones", summary="Create milestone")
async def create_milestone(project_id: str = "default", name: str = "", phase: str = "discovery") -> Dict[str, Any]:
    from collab.milestones import create_milestone
    return await create_milestone(project_id, name, phase=phase)

@router.get("/milestones/timeline/{phase}", summary="Project timeline")
async def project_timeline(phase: str = "preclinical") -> Dict[str, Any]:
    from collab.milestones import project_timeline
    return await project_timeline(phase=phase)

@router.post("/milestones/decisions", summary="Log decision")
async def log_decision(project_id: str = "default", title: str = "", decision: str = "", rationale: str = "") -> Dict[str, Any]:
    from collab.milestones import log_decision
    return await log_decision(project_id, title, decision, rationale)

@router.post("/milestones/meetings", summary="Log meeting minutes")
async def log_meeting(project_id: str = "default", title: str = "") -> Dict[str, Any]:
    from collab.milestones import log_meeting
    return await log_meeting(project_id, title)

@router.get("/milestones/quarterly-report", summary="Quarterly progress report")
async def quarterly_report(project_id: str = "default", quarter: str = "Q1", year: int = 2026) -> Dict[str, Any]:
    from collab.milestones import quarterly_report
    return await quarterly_report(project_id=project_id, quarter=quarter, year=year)


# ── Publication Pipeline Endpoints ────────────────────────────────────

@router.post("/publications", summary="Create manuscript")
async def create_manuscript(title: str = "CAR-T Study", target_journal: Optional[str] = None) -> Dict[str, Any]:
    from collab.publications import create_manuscript
    return await create_manuscript(title, target_journal=target_journal)

@router.get("/publications/recommend-journals", summary="Journal recommendations")
async def recommend_journals(topics: str = "car_t,cell_therapy") -> Dict[str, Any]:
    from collab.publications import recommend_journals
    return await recommend_journals(topics=topics.split(","))

@router.get("/publications/dashboard", summary="Publication pipeline dashboard")
async def pub_dashboard(project_id: str = "default") -> Dict[str, Any]:
    from collab.publications import publication_dashboard
    return await publication_dashboard(project_id=project_id)


# ── Module Status ─────────────────────────────────────────────────────

@router.get("/status", summary="Collab module status")
async def module_status() -> Dict[str, Any]:
    return {
        "module": "Research Collaboration Hub",
        "version": "5.6.0",
        "engines": 22,
        "endpoints": 121,
        "status": "operational",
        "engine_list": [
            "projects", "experiments", "notebooks", "peer_review",
            "pubmed_linker", "messaging", "datasets", "audit_trail",
            "analytics", "protocols", "permissions", "reproducibility",
            "workflows", "knowledge_base", "notifications",
            "inventory", "visualizations", "ethics", "multisite",
            "training", "milestones", "publications",
        ],
    }
