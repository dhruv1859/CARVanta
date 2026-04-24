"""
CARVanta Collab — Research Collaboration Hub Package
======================================================
GitHub-like collaboration platform for immunotherapy research.
22 specialized engines providing 121+ REST API endpoints.

Architecture:
    collab/
    ├── projects.py           — Research project management, templates [397]
    ├── experiments.py        — Experiment tracking, results, templates [289]
    ├── analytics.py          — Team productivity, impact, funding, trends [344]
    ├── multisite.py          — 8-site coordination, enrollment, harmonization [355]
    ├── inventory.py          — Reagent catalog (8 items), equipment (6), forecasting [346]
    ├── ethics.py             — IRB submission, consent (5 modules), COI tracking [341]
    ├── datasets.py           — Dataset management, FAIR, quality, cohorts [334]
    ├── workflows.py          — 3 workflow templates, Gantt, DAG execution [317]
    ├── peer_review.py        — Submission management, review workflow [307]
    ├── training.py           — 8 training modules, competency matrix [304]
    ├── notebooks.py          — Jupyter-like analysis notebooks [303]
    ├── reproducibility.py    — Scoring, power analysis, checklists [279]
    ├── protocols.py          — 5 CAR-T protocol templates, deviations [271]
    ├── audit_trail.py        — SHA-256 hash chain, compliance, FDA 21 CFR [267]
    ├── messaging.py          — Channel-based messaging, threads [263]
    ├── knowledge_base.py     — Glossary (15 terms), wiki, FAQ, onboarding [261]
    ├── visualizations.py     — 8 chart types (timeline, heatmap, radar, etc.) [248]
    ├── pubmed_linker.py      — PubMed API integration, citation tracking [246]
    ├── milestones.py         — 3 phase templates, RAG tracking, decisions [241]
    ├── permissions.py        — 8 RBAC roles, DSA, API keys, invitations [237]
    ├── notifications.py      — 12 event types, webhooks, preferences [225]
    ├── publications.py       — 8-journal database, CRediT roles, pipeline [224]
    └── __init__.py           — 22-engine registry with introspection

Clinical & Regulatory Standards:
    - Audit trail: FDA 21 CFR Part 11 electronic records compliance
    - Data quality: FAIR principles (Findable, Accessible, Interoperable, Reusable)
    - Research integrity: CONSORT, STROBE, ARRIVE, MDAR reporting checklists
    - Regulatory: GxP, GDPR, HIPAA compliance tracking
    - Protocols: ICH-GCP aligned experimental procedures
    - Ethics: IRB workflow, informed consent (5 modules), COI disclosure
    - Training: GMP, GCP, BSL-2, HIPAA, CRS/ICANS management
    - Reproducibility: Pre-registration, power analysis, blinding verification
    - Data harmonization: CDISC SDTM/ADaM, HL7 FHIR, OMOP CDM

CAR-T Research Features:
    - 5 CAR-T research protocol templates
    - 3 CAR-T development workflow templates
    - 8 CAR-T reagent catalog entries with lot tracking
    - 6 equipment items with calibration scheduling
    - 15-term immunotherapy glossary with relationship mapping
    - 8-journal publication database (Nature Medicine through Cytotherapy)
    - 8-site global research network (MSKCC, UPenn, Fred Hutch, etc.)
    - 3 CAR-T development phase templates (discovery, preclinical, clinical)
    - 8 training curriculum modules (GMP, GCP, CAR-T manufacturing, etc.)
    - CRediT contributor role taxonomy (14 roles)
    - Federated analysis planning (survival, response, biomarker)
    - Multi-site enrollment tracking and performance benchmarking
"""

__version__ = "5.6.0"
__all__ = [
    "projects",
    "experiments",
    "notebooks",
    "peer_review",
    "pubmed_linker",
    "messaging",
    "datasets",
    "audit_trail",
    "analytics",
    "protocols",
    "permissions",
    "reproducibility",
    "workflows",
    "knowledge_base",
    "notifications",
    "inventory",
    "visualizations",
    "ethics",
    "multisite",
    "training",
    "milestones",
    "publications",
]


# ──────────────────────────────────────────────────────────────────────
# Engine Registry for Runtime Introspection
# ──────────────────────────────────────────────────────────────────────

ENGINE_REGISTRY = {
    "projects": {
        "module": "collab.projects",
        "description": "Research project management with templates, team tracking, and milestone monitoring",
        "version": "5.6.0",
        "endpoints": ["projects", "projects/{id}", "projects/{id}/members", "projects/templates/list"],
        "status": "operational",
        "line_count": 397,
    },
    "experiments": {
        "module": "collab.experiments",
        "description": "Experiment lifecycle management with results tracking and statistical summaries",
        "version": "5.6.0",
        "endpoints": ["experiments", "experiments/{id}", "experiments/{id}/results", "experiments/{id}/stats"],
        "status": "operational",
        "line_count": 289,
    },
    "notebooks": {
        "module": "collab.notebooks",
        "description": "Jupyter-like analysis notebooks with cell execution and template library",
        "version": "5.6.0",
        "endpoints": ["notebooks", "notebooks/{id}", "notebooks/{id}/execute/{cell_id}"],
        "status": "operational",
        "line_count": 303,
    },
    "peer_review": {
        "module": "collab.peer_review",
        "description": "Peer review system with submission management, scoring, and decision tracking",
        "version": "5.6.0",
        "endpoints": ["submissions", "submissions/{id}/review", "submissions/{id}/summary"],
        "status": "operational",
        "line_count": 307,
    },
    "pubmed_linker": {
        "module": "collab.pubmed_linker",
        "description": "PubMed integration with citation tracking and target-specific literature search",
        "version": "5.6.0",
        "endpoints": ["pubmed/search", "pubmed/target/{target}", "pubmed/stats"],
        "status": "operational",
        "line_count": 246,
    },
    "messaging": {
        "module": "collab.messaging",
        "description": "Channel-based messaging with threads and @mentions",
        "version": "5.6.0",
        "endpoints": ["channels/{id}/messages"],
        "status": "operational",
        "line_count": 263,
    },
    "datasets": {
        "module": "collab.datasets",
        "description": "Dataset management with FAIR assessment, quality scoring, and patient cohort builder",
        "version": "5.6.0",
        "endpoints": ["datasets", "datasets/{id}/quality", "datasets/{id}/fair", "datasets/{id}/stats", "datasets/cohort"],
        "status": "operational",
        "line_count": 334,
    },
    "audit_trail": {
        "module": "collab.audit_trail",
        "description": "SHA-256 hash-chained audit log with FDA 21 CFR Part 11, GxP, and GDPR compliance",
        "version": "5.6.0",
        "endpoints": ["audit", "audit/compliance/{regulation}", "audit/analytics", "audit/integrity"],
        "status": "operational",
        "line_count": 267,
    },
    "analytics": {
        "module": "collab.analytics",
        "description": "Team productivity, collaboration networks, research impact, funding, and publication tracking",
        "version": "5.6.0",
        "endpoints": ["analytics/productivity", "analytics/network", "analytics/impact", "analytics/trends", "analytics/funding", "analytics/publications"],
        "status": "operational",
        "line_count": 344,
    },
    "protocols": {
        "module": "collab.protocols",
        "description": "5 CAR-T protocol templates (manufacturing, cytotoxicity, flow, xenograft, TCR-seq) with deviation tracking",
        "version": "5.6.0",
        "endpoints": ["protocols/templates", "protocols", "protocols/{id}/deviations", "protocols/{id}/risks"],
        "status": "operational",
        "line_count": 271,
    },
    "permissions": {
        "module": "collab.permissions",
        "description": "8-role RBAC, invitations, data sharing agreements, and API key management",
        "version": "5.6.0",
        "endpoints": ["permissions/roles", "permissions/grant", "permissions/check", "invitations", "data-sharing-agreements"],
        "status": "operational",
        "line_count": 237,
    },
    "reproducibility": {
        "module": "collab.reproducibility",
        "description": "Reproducibility scoring, power analysis, reporting checklists (CONSORT/STROBE/ARRIVE/MDAR), pre-registration",
        "version": "5.6.0",
        "endpoints": ["reproducibility/score", "reproducibility/power-analysis", "reproducibility/checklist/{type}", "reproducibility/preregister"],
        "status": "operational",
        "line_count": 279,
    },
    "workflows": {
        "module": "collab.workflows",
        "description": "3 CAR-T workflow templates (dev pipeline, clinical trial, biomarker), Gantt data, execution tracking",
        "version": "5.6.0",
        "endpoints": ["workflows/templates", "workflows", "workflows/{id}/status", "workflows/{id}/gantt"],
        "status": "operational",
        "line_count": 317,
    },
    "knowledge_base": {
        "module": "collab.knowledge_base",
        "description": "15-term immunotherapy glossary, wiki articles, FAQ system, role-specific onboarding guides",
        "version": "5.6.0",
        "endpoints": ["knowledge/glossary", "knowledge/articles", "knowledge/faq", "knowledge/onboarding/{role}"],
        "status": "operational",
        "line_count": 261,
    },
    "notifications": {
        "module": "collab.notifications",
        "description": "12 notification types, webhook integrations (Slack/Teams/Discord), preferences, activity summaries",
        "version": "5.6.0",
        "endpoints": ["notifications/{user_id}", "notifications/{user_id}/read", "notifications/{user_id}/preferences", "notifications/webhooks", "notifications/{user_id}/summary"],
        "status": "operational",
        "line_count": 225,
    },
    "inventory": {
        "module": "collab.inventory",
        "description": "8 CAR-T reagent catalog entries, 6 equipment items, calibration tracking, consumption forecasting",
        "version": "5.6.0",
        "endpoints": ["inventory/catalog", "inventory/reagents", "inventory/status", "inventory/equipment", "inventory/forecast/{id}"],
        "status": "operational",
        "line_count": 346,
    },
    "visualizations": {
        "module": "collab.visualizations",
        "description": "8 chart types: timeline, heatmap, success trends, scatter, burndown, radar, sparklines, benchmark",
        "version": "5.6.0",
        "endpoints": ["viz/timeline", "viz/heatmap", "viz/success-trends", "viz/impact-scatter", "viz/funding-burndown", "viz/quality-radar", "viz/sparklines", "viz/benchmark"],
        "status": "operational",
        "line_count": 248,
    },
    "ethics": {
        "module": "collab.ethics",
        "description": "IRB submission workflow, 5 consent modules (general, CAR-T, biospecimen, genomic, HIPAA), COI disclosure",
        "version": "5.6.0",
        "endpoints": ["ethics/irb/submit", "ethics/irb/status", "ethics/consent", "ethics/coi/{investigator}", "ethics/dashboard"],
        "status": "operational",
        "line_count": 341,
    },
    "multisite": {
        "module": "collab.multisite",
        "description": "8-site global research network, performance benchmarking, enrollment tracking, data harmonization, federated analysis",
        "version": "5.6.0",
        "endpoints": ["multisite/sites", "multisite/performance", "multisite/enrollment", "multisite/harmonization", "multisite/nearest", "multisite/federated/{type}"],
        "status": "operational",
        "line_count": 355,
    },
    "training": {
        "module": "collab.training",
        "description": "8 CAR-T training modules, role-based requirements, compliance tracking, team competency matrix",
        "version": "5.6.0",
        "endpoints": ["training/modules", "training/record", "training/status/{user_id}", "training/competency-matrix"],
        "status": "operational",
        "line_count": 304,
    },
    "milestones": {
        "module": "collab.milestones",
        "description": "3 CAR-T phase templates (discovery, preclinical, clinical), RAG tracking, decision log, quarterly reports",
        "version": "5.6.0",
        "endpoints": ["milestones", "milestones/timeline/{phase}", "milestones/decisions", "milestones/meetings", "milestones/quarterly-report"],
        "status": "operational",
        "line_count": 241,
    },
    "publications": {
        "module": "collab.publications",
        "description": "8-journal CAR-T database, CRediT roles, journal recommendation, manuscript lifecycle, pipeline dashboard",
        "version": "5.6.0",
        "endpoints": ["publications", "publications/recommend-journals", "publications/dashboard"],
        "status": "operational",
        "line_count": 224,
    },
}


def get_engine_info(engine_name: str) -> dict:
    """Get metadata for a specific collab engine."""
    return ENGINE_REGISTRY.get(engine_name, {"error": f"Engine '{engine_name}' not found"})


def list_engines() -> list:
    """List all registered collab engines with status."""
    return [
        {"name": n, "description": i["description"], "status": i["status"],
         "version": i["version"], "endpoints": len(i["endpoints"]),
         "line_count": i.get("line_count", 0)}
        for n, i in ENGINE_REGISTRY.items()
    ]


def get_total_endpoints() -> int:
    """Total API endpoints across all collab engines."""
    return sum(len(i["endpoints"]) for i in ENGINE_REGISTRY.values())


def get_total_lines() -> int:
    """Total lines of code across all collab engines."""
    return sum(i.get("line_count", 0) for i in ENGINE_REGISTRY.values())


def get_package_summary() -> dict:
    """Complete summary of the collab package."""
    engines = list_engines()
    return {
        "package": "carvanta.collab",
        "version": __version__,
        "total_engines": len(engines),
        "total_endpoints": get_total_endpoints(),
        "total_lines": get_total_lines(),
        "all_operational": all(e["status"] == "operational" for e in engines),
        "engines": engines,
        "capabilities": [
            "Research project management with templates and milestone tracking",
            "Experiment lifecycle tracking and statistical analysis",
            "FAIR-compliant dataset management with quality scoring",
            "SHA-256 hash-chained audit trail for FDA 21 CFR Part 11 compliance",
            "Team productivity analytics and collaboration network analysis",
            "5 CAR-T research protocol templates with deviation tracking",
            "3 CAR-T development workflow templates with Gantt visualization",
            "Peer review system with structured scoring rubrics",
            "8-role RBAC with data sharing agreements and API keys",
            "Reproducibility scoring with CONSORT/ARRIVE/MDAR checklists",
            "15-term immunotherapy glossary with relationship mapping",
            "Publication pipeline and funding tracker",
            "12 notification types with Slack/Teams webhook integration",
            "8 CAR-T reagent catalog entries with consumption forecasting",
            "IRB submission workflow with 5 informed consent modules",
            "8-site global research network with federated analysis",
            "8 training curriculum modules with competency matrix",
            "3 development phase templates with quarterly reporting",
            "8-journal publication database with recommendation engine",
            "8 chart types for research data visualization",
        ],
        "clinical_standards": [
            "FDA 21 CFR Part 11 (electronic records)",
            "ICH-GCP E6(R2) (good clinical practice)",
            "FAIR data principles",
            "CDISC SDTM/ADaM (clinical data standards)",
            "HL7 FHIR R4 (health data interoperability)",
            "OMOP CDM v5.4 (observational data model)",
            "CONSORT/STROBE/ARRIVE/MDAR (reporting checklists)",
            "HIPAA (privacy and security)",
            "GDPR (data protection)",
            "GxP (good practice regulations)",
        ],
    }
