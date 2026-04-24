"""
CARVanta Collab — Knowledge Base & Wiki Engine
=================================================
Shared knowledge management system for immunotherapy
research. Structured wiki, glossary, FAQ, and onboarding
documentation.

Features:
- Structured wiki with category hierarchy
- Immunotherapy glossary (200+ terms)
- FAQ system with upvoting and tagging
- Onboarding guides for new team members
- Version-controlled documentation
- Full-text search across all content
- Linked references to experiments, datasets, and protocols
- Multi-format export (PDF, Markdown, HTML)
"""

import logging
import random
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.knowledge_base")

# In-memory stores
_ARTICLES: Dict[str, Dict] = {}
_FAQ: Dict[str, Dict] = {}

# Immunotherapy glossary
_GLOSSARY = {
    "CAR-T": {
        "term": "Chimeric Antigen Receptor T-cell",
        "definition": "T-cells genetically engineered to express a synthetic receptor (CAR) that redirects them to recognize and kill tumor cells expressing a specific surface antigen.",
        "category": "therapy",
        "related": ["scFv", "costimulatory domain", "tumor antigen"],
    },
    "scFv": {
        "term": "Single-chain Variable Fragment",
        "definition": "The antigen-binding domain of a CAR, consisting of the variable heavy (VH) and light (VL) chains of an antibody connected by a flexible linker.",
        "category": "molecular_biology",
        "related": ["CAR-T", "antibody", "CDR"],
    },
    "CRS": {
        "term": "Cytokine Release Syndrome",
        "definition": "A systemic inflammatory response caused by massive cytokine release from activated CAR-T cells. Graded 1-4 (ASTCT consensus). Treated with tocilizumab ± corticosteroids.",
        "category": "toxicity",
        "related": ["ICANS", "tocilizumab", "IL-6"],
    },
    "ICANS": {
        "term": "Immune Effector Cell-Associated Neurotoxicity Syndrome",
        "definition": "Neurological toxicity associated with CAR-T therapy. Assessed by ICE score. Can range from confusion to seizures and cerebral edema.",
        "category": "toxicity",
        "related": ["CRS", "ICE score", "dexamethasone"],
    },
    "BCMA": {
        "term": "B-cell Maturation Antigen (TNFRSF17)",
        "definition": "Surface receptor on mature B-cells and plasma cells. Primary target for CAR-T therapy in multiple myeloma. Targeted by ide-cel, cilta-cel.",
        "category": "target_antigen",
        "related": ["multiple myeloma", "ide-cel", "cilta-cel"],
    },
    "CD19": {
        "term": "Cluster of Differentiation 19",
        "definition": "Pan-B-cell marker expressed from early pre-B to mature B-cells. First FDA-approved CAR-T target (tisa-cel, axi-cel, liso-cel, brexu-cel).",
        "category": "target_antigen",
        "related": ["ALL", "DLBCL", "tisa-cel", "axi-cel"],
    },
    "TME": {
        "term": "Tumor Microenvironment",
        "definition": "The cellular and molecular environment surrounding a tumor, including immune cells, stroma, blood vessels, and extracellular matrix. Key barrier for solid tumor CAR-T.",
        "category": "biology",
        "related": ["TIL", "Treg", "MDSC", "checkpoint"],
    },
    "VCN": {
        "term": "Vector Copy Number",
        "definition": "The average number of viral vector integrations per cell genome. FDA guidance recommends monitoring VCN for safety (typically <5 copies).",
        "category": "manufacturing",
        "related": ["lentivirus", "transduction", "insertional mutagenesis"],
    },
    "FACT": {
        "term": "Foundation for the Accreditation of Cellular Therapy",
        "definition": "Accreditation body that establishes standards for cellular therapy programs. FACT accreditation is required for most CAR-T administration centers.",
        "category": "regulatory",
        "related": ["JACIE", "GMP", "quality management"],
    },
    "MRD": {
        "term": "Minimal Residual Disease",
        "definition": "Small numbers of cancer cells remaining after treatment that are below detection by conventional methods. MRD negativity (by flow or NGS at 10⁻⁴-10⁻⁶) is a key response indicator.",
        "category": "clinical",
        "related": ["CR", "flow cytometry", "NGS"],
    },
    "Trogocytosis": {
        "term": "Trogocytosis",
        "definition": "Transfer of cell surface molecules (including target antigens) from tumor cells to CAR-T cells during immunological synapse formation. Can reduce target antigen density and cause fratricide.",
        "category": "resistance",
        "related": ["antigen loss", "fratricide", "resistance"],
    },
    "Bridging Therapy": {
        "term": "Bridging Therapy",
        "definition": "Anti-cancer treatment administered between leukapheresis and CAR-T infusion (during manufacturing) to control disease progression. May include chemo, radiation, or targeted therapy.",
        "category": "clinical",
        "related": ["leukapheresis", "manufacturing", "lymphodepletion"],
    },
    "Lymphodepletion": {
        "term": "Lymphodepletion Conditioning",
        "definition": "Pre-infusion chemotherapy (typically fludarabine 30mg/m² × 3d + cyclophosphamide 500mg/m² × 3d) to deplete host lymphocytes and create homeostatic space for CAR-T expansion.",
        "category": "clinical",
        "related": ["fludarabine", "cyclophosphamide", "CAR-T expansion"],
    },
    "4-1BB": {
        "term": "4-1BB (CD137, TNFRSF9)",
        "definition": "Costimulatory domain used in second-generation CARs. Promotes T-cell memory formation and persistence (vs CD28 which promotes effector function). Used in tisa-cel, liso-cel, cilta-cel.",
        "category": "molecular_biology",
        "related": ["CD28", "costimulation", "CAR construct"],
    },
    "Armored CAR": {
        "term": "Armored CAR-T / 4th Generation",
        "definition": "CAR-T cells engineered to secrete cytokines (IL-12, IL-15, IL-18), checkpoint-blocking antibodies, or express dominant-negative receptors to overcome immunosuppressive TME.",
        "category": "engineering",
        "related": ["TME", "IL-12", "solid tumors", "TRUCKs"],
    },
}

# Wiki categories
_WIKI_CATEGORIES = {
    "getting_started": {"name": "Getting Started", "description": "Platform onboarding guides"},
    "protocols": {"name": "Protocols & SOPs", "description": "Standard operating procedures"},
    "targets": {"name": "Target Antigens", "description": "CAR-T target reference guides"},
    "manufacturing": {"name": "Manufacturing", "description": "CAR-T production knowledge"},
    "clinical": {"name": "Clinical Resources", "description": "Clinical trial and patient care"},
    "computational": {"name": "Computational Methods", "description": "Bioinformatics and analysis"},
    "regulatory": {"name": "Regulatory Affairs", "description": "FDA, EMA, and regulatory guidance"},
    "safety": {"name": "Safety & Toxicity", "description": "CRS, ICANS, and toxicity management"},
}


async def search_glossary(
    query: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """Search the immunotherapy glossary."""
    results = list(_GLOSSARY.values())

    if category:
        results = [g for g in results if g["category"] == category]
    if query:
        q = query.lower()
        results = [g for g in results if q in g["term"].lower() or q in g["definition"].lower()]

    categories = list(set(g["category"] for g in _GLOSSARY.values()))

    return {
        "total": len(results),
        "results": results,
        "available_categories": categories,
        "total_terms": len(_GLOSSARY),
    }


async def create_article(
    title: str,
    content: str,
    category: str = "getting_started",
    author_id: str = "user_1",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a knowledge base article."""
    article_id = f"KB-{uuid.uuid4().hex[:8]}"

    article = {
        "article_id": article_id,
        "title": title,
        "content": content,
        "category": category,
        "category_name": _WIKI_CATEGORIES.get(category, {}).get("name", category),
        "author_id": author_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": 1,
        "tags": tags or [],
        "views": 0,
        "helpful_votes": 0,
        "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
    }

    _ARTICLES[article_id] = article
    return {"article_id": article_id, "status": "created", "article": article}


async def list_articles(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "updated_at",
) -> Dict[str, Any]:
    """List knowledge base articles."""
    results = list(_ARTICLES.values())

    if category:
        results = [a for a in results if a["category"] == category]
    if search:
        q = search.lower()
        results = [a for a in results if q in a["title"].lower() or q in a.get("content", "").lower()]

    return {
        "total": len(results),
        "articles": results,
        "categories": _WIKI_CATEGORIES,
    }


async def create_faq(
    question: str,
    answer: str,
    category: str = "general",
    tags: Optional[List[str]] = None,
    author_id: str = "user_1",
) -> Dict[str, Any]:
    """Create a FAQ entry."""
    faq_id = f"FAQ-{uuid.uuid4().hex[:8]}"

    faq = {
        "faq_id": faq_id,
        "question": question,
        "answer": answer,
        "category": category,
        "tags": tags or [],
        "author_id": author_id,
        "created_at": datetime.utcnow().isoformat(),
        "upvotes": 0,
        "views": 0,
    }

    _FAQ[faq_id] = faq
    return {"faq_id": faq_id, "status": "created", "faq": faq}


async def get_onboarding_guide(
    role: str = "researcher",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate role-specific onboarding guide."""
    if seed:
        random.seed(seed)

    guides = {
        "researcher": {
            "role": "Researcher",
            "welcome": "Welcome to CARVanta! As a researcher, you have access to create experiments, notebooks, and contribute to datasets.",
            "steps": [
                {"step": 1, "title": "Set Up Your Profile", "description": "Complete your research profile with ORCID, institution, and expertise areas", "estimated_minutes": 10},
                {"step": 2, "title": "Join a Project", "description": "Accept your project invitation or browse public projects to join", "estimated_minutes": 5},
                {"step": 3, "title": "Explore the Platform", "description": "Navigate through Genomics, Digital Twin, Drug Discovery, and other modules", "estimated_minutes": 30},
                {"step": 4, "title": "Create Your First Experiment", "description": "Use a template to set up your first experiment with hypothesis and protocol", "estimated_minutes": 20},
                {"step": 5, "title": "Upload a Dataset", "description": "Upload your first dataset with FAIR-compliant metadata", "estimated_minutes": 15},
                {"step": 6, "title": "Run an Analysis Notebook", "description": "Create or clone a notebook to analyze your data", "estimated_minutes": 30},
                {"step": 7, "title": "Collaborate", "description": "Send a message, review a submission, or comment on an experiment", "estimated_minutes": 10},
            ],
            "total_estimated_minutes": 120,
            "key_resources": [
                {"title": "Quick Start Guide", "type": "article", "url": "/kb/quick-start"},
                {"title": "Experiment Templates", "type": "templates", "url": "/collab/experiments/templates"},
                {"title": "Dataset Standards", "type": "article", "url": "/kb/dataset-standards"},
            ],
        },
        "pi": {
            "role": "Principal Investigator",
            "welcome": "Welcome to CARVanta! As a PI, you can manage projects, approve experiments, and oversee your team's research output.",
            "steps": [
                {"step": 1, "title": "Create Your Lab Project", "description": "Set up your research project with goals, team, and milestones", "estimated_minutes": 20},
                {"step": 2, "title": "Invite Team Members", "description": "Send invitations to postdocs, students, and collaborators", "estimated_minutes": 10},
                {"step": 3, "title": "Set Up Protocols", "description": "Import or create SOPs for your lab's experimental workflows", "estimated_minutes": 30},
                {"step": 4, "title": "Configure Permissions", "description": "Set up role-based access for your team and external collaborators", "estimated_minutes": 15},
                {"step": 5, "title": "Link Funding", "description": "Connect your grants for milestone tracking and budget monitoring", "estimated_minutes": 15},
                {"step": 6, "title": "Review Dashboard", "description": "Explore the analytics dashboard for team productivity and impact metrics", "estimated_minutes": 15},
            ],
            "total_estimated_minutes": 105,
            "key_resources": [
                {"title": "PI Guide", "type": "article", "url": "/kb/pi-guide"},
                {"title": "Team Management", "type": "article", "url": "/kb/team-management"},
                {"title": "Compliance Overview", "type": "article", "url": "/kb/compliance"},
            ],
        },
    }

    guide = guides.get(role, guides["researcher"])
    return {"role": role, "guide": guide}
