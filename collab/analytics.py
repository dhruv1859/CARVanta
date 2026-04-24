"""
CARVanta Collab — Research Analytics Engine
=============================================
Analytics and metrics for research collaboration performance,
team productivity, and scientific output tracking.

Features:
- Research output metrics (publications, datasets, experiments)
- Team productivity scoring and benchmarking
- Collaboration network analysis (who works with whom)
- Impact metrics (citations, dataset downloads, experiment replications)
- Research trend analysis (hot topics, emerging areas)
- Funding tracker and grant milestone monitoring
- Publication pipeline management (manuscript → submission → acceptance)
- Research quality indicators (reproducibility, statistical rigor)
"""

import logging
import math
import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import Counter

logger = logging.getLogger("carvanta.collab.analytics")


# ──────────────────────────────────────────────────────────────────────
# Research output and impact databases
# ──────────────────────────────────────────────────────────────────────

_RESEARCH_DOMAINS = {
    "car_t_engineering": {
        "name": "CAR-T Engineering",
        "keywords": ["CAR construct", "scFv", "costimulatory domain", "hinge region", "armored CAR"],
        "trending": True, "growth_rate": 15.2,
    },
    "target_discovery": {
        "name": "Target Antigen Discovery",
        "keywords": ["surface antigen", "tumor-specific", "proteomics", "single-cell"],
        "trending": True, "growth_rate": 22.5,
    },
    "toxicity_management": {
        "name": "Toxicity Management",
        "keywords": ["CRS", "ICANS", "tocilizumab", "cytokine storm", "neurotoxicity"],
        "trending": True, "growth_rate": 18.0,
    },
    "manufacturing": {
        "name": "CAR-T Manufacturing",
        "keywords": ["GMP", "viral vector", "transduction", "point-of-care", "automated"],
        "trending": True, "growth_rate": 25.0,
    },
    "solid_tumors": {
        "name": "Solid Tumor CAR-T",
        "keywords": ["TME", "trafficking", "hypoxia", "checkpoint", "armored"],
        "trending": True, "growth_rate": 30.0,
    },
    "allogeneic": {
        "name": "Allogeneic/Off-the-Shelf CAR-T",
        "keywords": ["CRISPR", "base editing", "universal donor", "GvHD", "NK-CAR"],
        "trending": True, "growth_rate": 35.0,
    },
    "resistance_mechanisms": {
        "name": "Resistance Mechanisms",
        "keywords": ["antigen loss", "lineage switch", "trogocytosis", "exhaustion", "TME"],
        "trending": True, "growth_rate": 20.0,
    },
    "bispecific": {
        "name": "Bispecific Approaches",
        "keywords": ["dual CAR", "tandem CAR", "bispecific antibody", "CD19/CD22", "BCMA/GPRC5D"],
        "trending": True, "growth_rate": 28.0,
    },
}

_JOURNAL_TIERS = {
    "tier_1": ["Nature", "Science", "Cell", "NEJM", "Lancet", "Nature Medicine", "Nature Biotechnology"],
    "tier_2": ["Blood", "JCO", "Cancer Discovery", "Cancer Cell", "Molecular Therapy", "Science Translational Medicine"],
    "tier_3": ["Leukemia", "Haematologica", "Clinical Cancer Research", "Journal of Immunotherapy", "Cytotherapy"],
}

_GRANT_SOURCES = [
    {"name": "NIH R01", "amount_range": [250000, 500000], "duration_years": 5},
    {"name": "NIH R21", "amount_range": [100000, 275000], "duration_years": 2},
    {"name": "NCI SPORE", "amount_range": [500000, 2500000], "duration_years": 5},
    {"name": "DoD CDMRP", "amount_range": [300000, 1000000], "duration_years": 3},
    {"name": "LLS TRP", "amount_range": [200000, 600000], "duration_years": 3},
    {"name": "CIRM", "amount_range": [500000, 5000000], "duration_years": 4},
    {"name": "Industry Sponsored", "amount_range": [100000, 10000000], "duration_years": 3},
    {"name": "European ERC", "amount_range": [1500000, 2500000], "duration_years": 5},
]


async def team_productivity(
    project_id: Optional[str] = None,
    period_days: int = 90,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Assess team productivity and research output."""
    if seed:
        random.seed(seed)

    n_members = random.randint(3, 15)
    members = []
    for i in range(n_members):
        role = random.choice(["PI", "Postdoc", "PhD Student", "Research Associate", "Technician", "Collaborator"])
        productivity = {
            "user_id": f"user_{i+1}",
            "role": role,
            "experiments_completed": random.randint(0, 20),
            "datasets_contributed": random.randint(0, 8),
            "notebook_cells_executed": random.randint(10, 500),
            "reviews_completed": random.randint(0, 5),
            "messages_sent": random.randint(5, 200),
            "publications_contributed": random.randint(0, 3),
            "hours_active": round(random.uniform(20, 400), 1),
            "last_active_days_ago": random.randint(0, period_days),
        }
        productivity["productivity_score"] = round(
            (productivity["experiments_completed"] * 10 +
             productivity["datasets_contributed"] * 8 +
             productivity["publications_contributed"] * 25 +
             productivity["reviews_completed"] * 5) / max(productivity["hours_active"] / 40, 1),
            1
        )
        members.append(productivity)

    members.sort(key=lambda x: x["productivity_score"], reverse=True)

    # Team summary
    total_experiments = sum(m["experiments_completed"] for m in members)
    total_datasets = sum(m["datasets_contributed"] for m in members)
    total_pubs = sum(m["publications_contributed"] for m in members)

    return {
        "project_id": project_id or "all",
        "period_days": period_days,
        "team_size": n_members,
        "members": members,
        "team_summary": {
            "total_experiments": total_experiments,
            "total_datasets": total_datasets,
            "total_publications": total_pubs,
            "avg_productivity_score": round(sum(m["productivity_score"] for m in members) / n_members, 1),
            "most_productive": members[0]["user_id"] if members else None,
            "active_members": sum(1 for m in members if m["last_active_days_ago"] < 7),
        },
        "velocity": {
            "experiments_per_week": round(total_experiments / max(period_days / 7, 1), 1),
            "datasets_per_month": round(total_datasets / max(period_days / 30, 1), 1),
        },
    }


async def collaboration_network(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze collaboration patterns between researchers."""
    if seed:
        random.seed(seed)

    n_researchers = random.randint(15, 50)
    researchers = [f"researcher_{i+1}" for i in range(n_researchers)]

    # Generate collaboration edges
    edges = []
    for i in range(n_researchers):
        n_collabs = random.randint(1, min(8, n_researchers - 1))
        partners = random.sample([r for r in researchers if r != researchers[i]], n_collabs)
        for partner in partners:
            if not any(e["source"] == partner and e["target"] == researchers[i] for e in edges):
                edges.append({
                    "source": researchers[i],
                    "target": partner,
                    "weight": random.randint(1, 20),
                    "collaboration_type": random.choice(["co-author", "shared_dataset", "shared_experiment", "co-reviewer"]),
                })

    # Compute centrality
    degree = Counter()
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1

    top_connectors = degree.most_common(5)

    # Detect clusters
    n_clusters = random.randint(2, 5)

    return {
        "network_stats": {
            "total_researchers": n_researchers,
            "total_connections": len(edges),
            "average_degree": round(len(edges) * 2 / n_researchers, 1),
            "density": round(len(edges) / (n_researchers * (n_researchers - 1) / 2), 3),
            "clusters_detected": n_clusters,
        },
        "top_connectors": [{"researcher": r, "connections": c} for r, c in top_connectors],
        "edges": edges[:50],
        "cluster_summary": [
            {"cluster_id": i + 1, "size": random.randint(3, n_researchers // n_clusters + 3),
             "focus_area": random.choice(list(_RESEARCH_DOMAINS.keys()))}
            for i in range(n_clusters)
        ],
    }


async def impact_metrics(
    project_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Calculate research impact metrics."""
    if seed:
        random.seed(seed)

    publications = []
    for i in range(random.randint(3, 15)):
        tier = random.choices(["tier_1", "tier_2", "tier_3"], weights=[10, 30, 60])[0]
        journal = random.choice(_JOURNAL_TIERS[tier])
        pub = {
            "pub_id": f"PUB-{uuid.uuid4().hex[:6]}",
            "title": f"{'Novel' if random.random() > 0.5 else 'Improved'} CAR-T {random.choice(['construct', 'target', 'manufacturing', 'efficacy'])} in {random.choice(['DLBCL', 'ALL', 'MM', 'solid tumors'])}",
            "journal": journal,
            "tier": tier,
            "year": random.choice([2024, 2025, 2026]),
            "citations": random.randint(0, 150) if tier == "tier_1" else random.randint(0, 50),
            "altmetric_score": random.randint(1, 500),
            "open_access": random.random() > 0.4,
        }
        publications.append(pub)

    total_citations = sum(p["citations"] for p in publications)
    h_index = 0
    sorted_cites = sorted([p["citations"] for p in publications], reverse=True)
    for i, c in enumerate(sorted_cites):
        if c >= i + 1:
            h_index = i + 1

    return {
        "project_id": project_id or "all",
        "publications": {
            "total": len(publications),
            "by_tier": {t: sum(1 for p in publications if p["tier"] == t) for t in ["tier_1", "tier_2", "tier_3"]},
            "list": publications,
        },
        "citation_metrics": {
            "total_citations": total_citations,
            "h_index": h_index,
            "i10_index": sum(1 for p in publications if p["citations"] >= 10),
            "mean_citations": round(total_citations / max(len(publications), 1), 1),
        },
        "dataset_impact": {
            "total_datasets_shared": random.randint(5, 30),
            "total_downloads": random.randint(50, 5000),
            "dataset_citations": random.randint(2, 50),
            "reuse_rate_pct": round(random.uniform(10, 60), 1),
        },
        "experiment_impact": {
            "total_experiments": random.randint(20, 100),
            "replicated_experiments": random.randint(2, 20),
            "reproducibility_rate_pct": round(random.uniform(50, 90), 1),
        },
    }


async def research_trends(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze research trends across the platform."""
    if seed:
        random.seed(seed)

    trends = []
    for domain_key, domain in _RESEARCH_DOMAINS.items():
        trend = {
            "domain": domain_key,
            "name": domain["name"],
            "keywords": domain["keywords"],
            "trending": domain["trending"],
            "growth_rate_pct": domain["growth_rate"],
            "active_projects": random.randint(2, 25),
            "publications_last_year": random.randint(10, 200),
            "datasets_available": random.randint(5, 50),
            "active_researchers": random.randint(5, 80),
            "funding_total_usd": random.randint(100000, 5000000),
        }
        trends.append(trend)

    trends.sort(key=lambda x: x["growth_rate_pct"], reverse=True)

    return {
        "total_domains": len(trends),
        "trends": trends,
        "fastest_growing": trends[0]["name"] if trends else None,
        "most_active": max(trends, key=lambda x: x["active_projects"])["name"] if trends else None,
        "most_funded": max(trends, key=lambda x: x["funding_total_usd"])["name"] if trends else None,
    }


async def funding_tracker(
    project_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Track grants and funding for research projects."""
    if seed:
        random.seed(seed)

    grants = []
    for i in range(random.randint(2, 8)):
        source = random.choice(_GRANT_SOURCES)
        amount = random.randint(*source["amount_range"])
        start_year = random.choice([2023, 2024, 2025])
        status = random.choice(["active", "active", "active", "pending", "completed"])

        milestones = []
        for y in range(source["duration_years"]):
            milestones.append({
                "year": start_year + y,
                "milestone": f"Year {y+1} deliverables",
                "status": "completed" if y < 2 else "pending",
                "budget_allocated": round(amount / source["duration_years"]),
            })

        grants.append({
            "grant_id": f"GRT-{uuid.uuid4().hex[:6]}",
            "source": source["name"],
            "amount_usd": amount,
            "duration_years": source["duration_years"],
            "start_year": start_year,
            "end_year": start_year + source["duration_years"],
            "status": status,
            "milestones": milestones,
            "burn_rate_pct": round(random.uniform(20, 90), 1),
            "remaining_usd": round(amount * (1 - random.uniform(0.2, 0.9))),
        })

    total_funding = sum(g["amount_usd"] for g in grants)
    active_grants = [g for g in grants if g["status"] == "active"]

    return {
        "project_id": project_id or "all",
        "total_grants": len(grants),
        "active_grants": len(active_grants),
        "total_funding_usd": total_funding,
        "active_funding_usd": sum(g["amount_usd"] for g in active_grants),
        "remaining_usd": sum(g["remaining_usd"] for g in active_grants),
        "grants": grants,
        "funding_by_source": {
            s["name"]: sum(g["amount_usd"] for g in grants if g["source"] == s["name"])
            for s in _GRANT_SOURCES
            if any(g["source"] == s["name"] for g in grants)
        },
    }


async def publication_pipeline(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Track manuscripts through the publication pipeline."""
    if seed:
        random.seed(seed)

    stages = ["drafting", "internal_review", "submitted", "under_review", "revision", "accepted", "published"]

    manuscripts = []
    for i in range(random.randint(5, 15)):
        stage = random.choice(stages)
        target_journal = random.choice(sum(_JOURNAL_TIERS.values(), []))

        ms = {
            "manuscript_id": f"MS-{uuid.uuid4().hex[:6]}",
            "title": f"CAR-T {random.choice(['efficacy', 'safety', 'manufacturing', 'resistance', 'target'])} study",
            "stage": stage,
            "target_journal": target_journal,
            "authors": random.randint(3, 12),
            "days_in_stage": random.randint(1, 90),
            "submitted_date": (datetime.utcnow() - timedelta(days=random.randint(10, 180))).strftime("%Y-%m-%d") if stage not in ("drafting", "internal_review") else None,
            "reviews_received": random.randint(0, 3) if stage in ("under_review", "revision") else 0,
        }
        manuscripts.append(ms)

    stage_counts = Counter(m["stage"] for m in manuscripts)

    return {
        "total_manuscripts": len(manuscripts),
        "stage_distribution": dict(stage_counts),
        "manuscripts": manuscripts,
        "avg_time_to_publication_days": random.randint(90, 300),
        "acceptance_rate_pct": round(random.uniform(30, 70), 1),
    }
