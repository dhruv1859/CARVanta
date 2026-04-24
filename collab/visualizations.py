"""
CARVanta Collab — Data Visualization Engine
=============================================
Server-side chart data generation for collaborative
research dashboards. Produces structured data for
frontend chart rendering (Recharts/Chart.js compatible).

Features:
- Research output timeline charts
- Collaboration heatmaps (who-works-with-whom)
- Experiment success rate trending
- Publication impact scatter plots
- Funding burn-down charts
- Workflow Gantt chart data
- Dataset quality radar charts
- Reproducibility score distribution
- Team activity sparklines
- Comparative benchmarking charts
"""

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.visualizations")


async def research_timeline(
    months: int = 12,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate research output timeline data."""
    if seed:
        random.seed(seed)

    data_points = []
    for m in range(months):
        date = (datetime.utcnow() - timedelta(days=30 * (months - m - 1))).strftime("%Y-%m")
        data_points.append({
            "month": date,
            "experiments": random.randint(2, 20),
            "datasets": random.randint(1, 10),
            "publications": random.randint(0, 3),
            "reviews": random.randint(0, 5),
            "protocols": random.randint(0, 4),
        })

    return {
        "chart_type": "area",
        "title": "Research Output Timeline",
        "x_axis": "month",
        "series": ["experiments", "datasets", "publications", "reviews", "protocols"],
        "colors": {"experiments": "#4CAF50", "datasets": "#2196F3", "publications": "#E91E63",
                   "reviews": "#FF9800", "protocols": "#9C27B0"},
        "data": data_points,
    }


async def collaboration_heatmap(
    n_researchers: int = 10,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate collaboration intensity heatmap data."""
    if seed:
        random.seed(seed)

    researchers = [f"R{i+1}" for i in range(n_researchers)]
    matrix = []

    for i in range(n_researchers):
        row = []
        for j in range(n_researchers):
            if i == j:
                row.append(0)
            elif j > i:
                val = random.choices([0, 0, 0, random.randint(1, 15)], weights=[30, 20, 10, 40])[0]
                row.append(val)
            else:
                row.append(matrix[j][i])
        matrix.append(row)

    return {
        "chart_type": "heatmap",
        "title": "Collaboration Intensity Matrix",
        "labels": researchers,
        "matrix": matrix,
        "color_scale": {"min": "#1a1a2e", "mid": "#16213e", "max": "#50fa7b"},
        "legend": "Number of shared activities (experiments, datasets, publications)",
    }


async def experiment_success_trends(
    months: int = 12,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate experiment success rate trending data."""
    if seed:
        random.seed(seed)

    data = []
    for m in range(months):
        date = (datetime.utcnow() - timedelta(days=30 * (months - m - 1))).strftime("%Y-%m")
        total = random.randint(5, 25)
        successful = random.randint(int(total * 0.4), total)
        data.append({
            "month": date,
            "total_experiments": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round(successful / total * 100, 1),
        })

    avg_rate = round(sum(d["success_rate"] for d in data) / len(data), 1)

    return {
        "chart_type": "combo",
        "title": "Experiment Success Rate Trends",
        "data": data,
        "summary": {"average_success_rate": avg_rate, "total_experiments": sum(d["total_experiments"] for d in data)},
        "bar_series": ["successful", "failed"],
        "line_series": ["success_rate"],
        "colors": {"successful": "#50fa7b", "failed": "#ff5555", "success_rate": "#8be9fd"},
    }


async def impact_scatter(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate publication impact scatter plot data."""
    if seed:
        random.seed(seed)

    publications = []
    for i in range(random.randint(10, 30)):
        tier = random.choices(["tier_1", "tier_2", "tier_3"], weights=[15, 35, 50])[0]
        jif = {"tier_1": random.uniform(20, 70), "tier_2": random.uniform(8, 25), "tier_3": random.uniform(2, 10)}[tier]
        citations = int(jif * random.uniform(0.5, 3) * random.uniform(0.5, 2))

        publications.append({
            "id": f"PUB-{i+1}",
            "title": f"CAR-T Study {i+1}",
            "x": round(jif, 1),
            "y": citations,
            "size": random.randint(3, 12),
            "tier": tier,
            "year": random.choice([2024, 2025, 2026]),
        })

    return {
        "chart_type": "scatter",
        "title": "Publication Impact (JIF vs Citations)",
        "x_label": "Journal Impact Factor",
        "y_label": "Citations",
        "data": publications,
        "color_map": {"tier_1": "#FFD700", "tier_2": "#C0C0C0", "tier_3": "#CD7F32"},
    }


async def funding_burndown(
    months: int = 24,
    total_budget: int = 5000000,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate funding burn-down chart data."""
    if seed:
        random.seed(seed)

    remaining = total_budget
    data = []
    monthly_budget = total_budget / months

    for m in range(months):
        date = (datetime.utcnow() + timedelta(days=30 * m)).strftime("%Y-%m")
        actual_spend = round(monthly_budget * random.uniform(0.6, 1.4))
        remaining -= actual_spend

        data.append({
            "month": date,
            "planned_remaining": round(total_budget - monthly_budget * (m + 1)),
            "actual_remaining": round(max(remaining, 0)),
            "monthly_spend": actual_spend,
            "cumulative_spend": round(total_budget - max(remaining, 0)),
        })

    return {
        "chart_type": "line",
        "title": "Funding Burn-Down",
        "data": data,
        "series": ["planned_remaining", "actual_remaining"],
        "colors": {"planned_remaining": "#aaa", "actual_remaining": "#8be9fd"},
        "total_budget": total_budget,
    }


async def quality_radar(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate data quality radar chart."""
    if seed:
        random.seed(seed)

    dimensions = [
        {"axis": "Completeness", "value": round(random.uniform(60, 100), 1)},
        {"axis": "Consistency", "value": round(random.uniform(60, 100), 1)},
        {"axis": "Accuracy", "value": round(random.uniform(60, 100), 1)},
        {"axis": "Timeliness", "value": round(random.uniform(40, 100), 1)},
        {"axis": "Uniqueness", "value": round(random.uniform(70, 100), 1)},
        {"axis": "FAIR Score", "value": round(random.uniform(50, 100), 1)},
        {"axis": "Reproducibility", "value": round(random.uniform(40, 95), 1)},
        {"axis": "Documentation", "value": round(random.uniform(50, 100), 1)},
    ]

    overall = round(sum(d["value"] for d in dimensions) / len(dimensions), 1)

    return {
        "chart_type": "radar",
        "title": "Research Quality Radar",
        "data": dimensions,
        "overall_score": overall,
        "max_value": 100,
        "color": "#bd93f9",
        "fill_color": "rgba(189,147,249,0.2)",
    }


async def team_sparklines(
    days: int = 30,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate team activity sparkline data."""
    if seed:
        random.seed(seed)

    members = []
    for i in range(random.randint(5, 12)):
        daily_activity = [random.randint(0, 15) for _ in range(days)]
        members.append({
            "user_id": f"user_{i+1}",
            "role": random.choice(["PI", "Postdoc", "PhD Student", "Research Associate"]),
            "sparkline": daily_activity,
            "total_activity": sum(daily_activity),
            "avg_daily": round(sum(daily_activity) / days, 1),
            "trend": "up" if sum(daily_activity[-7:]) > sum(daily_activity[:7]) else "down",
            "active_days": sum(1 for d in daily_activity if d > 0),
        })

    members.sort(key=lambda m: m["total_activity"], reverse=True)

    return {
        "chart_type": "sparkline_table",
        "title": "Team Activity (Last 30 Days)",
        "period_days": days,
        "members": members,
    }


async def benchmark_comparison(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate benchmarking data against peer institutions."""
    if seed:
        random.seed(seed)

    metrics = [
        "Publications/Year", "h-index", "Grant Funding ($M)",
        "Dataset Sharing Rate", "Experiment Success Rate",
        "Avg Reproducibility Score", "Team Collaboration Index",
    ]

    our_scores = [round(random.uniform(40, 95), 1) for _ in metrics]
    peer_avg = [round(random.uniform(30, 80), 1) for _ in metrics]
    top_quartile = [round(min(random.uniform(70, 100), 100), 1) for _ in metrics]

    data = []
    for i, m in enumerate(metrics):
        data.append({
            "metric": m,
            "our_score": our_scores[i],
            "peer_average": peer_avg[i],
            "top_quartile": top_quartile[i],
            "percentile": round(random.uniform(30, 95), 1),
        })

    return {
        "chart_type": "grouped_bar",
        "title": "Institutional Benchmarking",
        "data": data,
        "series": ["our_score", "peer_average", "top_quartile"],
        "colors": {"our_score": "#bd93f9", "peer_average": "#aaa", "top_quartile": "#50fa7b"},
    }
