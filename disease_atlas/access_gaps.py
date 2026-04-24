"""
CARVanta Disease Atlas — Treatment Access & Regulatory Map
============================================================
Analyses global treatment access gaps, regulatory approval status,
and reimbursement landscapes for cell & gene therapies.

Features:
  ▸ Country-by-country regulatory approval tracker
  ▸ Treatment access inequality scoring
  ▸ Manufacturing capacity gap analysis
  ▸ Reimbursement coverage mapping
  ▸ Healthcare infrastructure readiness index
  ▸ Patient journey mapping (referral → treatment → follow-up)
  ▸ Global access equity dashboard data
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Regulatory Approval Data
# ═══════════════════════════════════════════════════════════════════════════════

REGULATORY_BODIES = {
    "US": {"name": "FDA", "pathway": "BLA", "review_months": 6, "priority_review": True},
    "EU": {"name": "EMA", "pathway": "ATMP", "review_months": 12, "priority_review": True},
    "UK": {"name": "MHRA", "pathway": "ILAP", "review_months": 8, "priority_review": True},
    "JP": {"name": "PMDA", "pathway": "SAKIGAKE", "review_months": 9, "priority_review": True},
    "CN": {"name": "NMPA", "pathway": "IND/NDA", "review_months": 12, "priority_review": False},
    "IN": {"name": "CDSCO", "pathway": "New Drug", "review_months": 18, "priority_review": False},
    "BR": {"name": "ANVISA", "pathway": "ATMP", "review_months": 12, "priority_review": False},
    "KR": {"name": "MFDS", "pathway": "BLA", "review_months": 10, "priority_review": True},
    "AU": {"name": "TGA", "pathway": "Biologicals", "review_months": 8, "priority_review": True},
    "CA": {"name": "Health Canada", "pathway": "NOC/c", "review_months": 8, "priority_review": True},
    "IL": {"name": "MOH", "pathway": "New Drug", "review_months": 15, "priority_review": False},
    "SG": {"name": "HSA", "pathway": "NDA", "review_months": 10, "priority_review": False},
}

APPROVED_PRODUCTS = {
    "tisagenlecleucel": {
        "approvals": {
            "US": {"date": "2017-08", "indications": ["r/r B-ALL (peds)", "r/r DLBCL"]},
            "EU": {"date": "2018-08", "indications": ["r/r B-ALL (peds)", "r/r DLBCL"]},
            "JP": {"date": "2019-03", "indications": ["r/r B-ALL", "r/r DLBCL"]},
            "CA": {"date": "2018-09", "indications": ["r/r B-ALL", "r/r DLBCL"]},
            "AU": {"date": "2021-01", "indications": ["r/r DLBCL"]},
            "UK": {"date": "2018-08", "indications": ["r/r B-ALL", "r/r DLBCL"]},
            "CN": {"date": "2024-01", "indications": ["r/r DLBCL"]},
        },
    },
    "axicabtagene_ciloleucel": {
        "approvals": {
            "US": {"date": "2017-10", "indications": ["r/r LBCL"]},
            "EU": {"date": "2018-08", "indications": ["r/r DLBCL", "r/r PMBCL"]},
            "CA": {"date": "2019-02", "indications": ["r/r LBCL"]},
            "UK": {"date": "2018-08", "indications": ["r/r DLBCL"]},
            "IL": {"date": "2019-06", "indications": ["r/r DLBCL"]},
        },
    },
    "idecabtagene_vicleucel": {
        "approvals": {
            "US": {"date": "2021-03", "indications": ["r/r Multiple Myeloma"]},
            "EU": {"date": "2021-08", "indications": ["r/r Multiple Myeloma"]},
            "JP": {"date": "2022-01", "indications": ["r/r Multiple Myeloma"]},
        },
    },
    "ciltacabtagene_autoleucel": {
        "approvals": {
            "US": {"date": "2022-02", "indications": ["r/r Multiple Myeloma"]},
            "EU": {"date": "2022-05", "indications": ["r/r Multiple Myeloma"]},
            "JP": {"date": "2022-09", "indications": ["r/r Multiple Myeloma"]},
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Healthcare Infrastructure Readiness
# ═══════════════════════════════════════════════════════════════════════════════

INFRASTRUCTURE_SCORES = {
    "US": {"gmp_facilities": 45, "qualified_centres": 180, "hematologists_per_100k": 2.8, "icu_beds_per_100k": 34.7, "readiness_score": 0.95},
    "EU": {"gmp_facilities": 30, "qualified_centres": 120, "hematologists_per_100k": 2.1, "icu_beds_per_100k": 11.5, "readiness_score": 0.88},
    "UK": {"gmp_facilities": 8, "qualified_centres": 15, "hematologists_per_100k": 1.8, "icu_beds_per_100k": 6.6, "readiness_score": 0.82},
    "JP": {"gmp_facilities": 12, "qualified_centres": 25, "hematologists_per_100k": 1.5, "icu_beds_per_100k": 7.3, "readiness_score": 0.85},
    "CN": {"gmp_facilities": 20, "qualified_centres": 50, "hematologists_per_100k": 0.4, "icu_beds_per_100k": 3.6, "readiness_score": 0.60},
    "IN": {"gmp_facilities": 5, "qualified_centres": 12, "hematologists_per_100k": 0.1, "icu_beds_per_100k": 2.3, "readiness_score": 0.35},
    "BR": {"gmp_facilities": 3, "qualified_centres": 8, "hematologists_per_100k": 0.3, "icu_beds_per_100k": 2.1, "readiness_score": 0.40},
    "KR": {"gmp_facilities": 8, "qualified_centres": 18, "hematologists_per_100k": 1.2, "icu_beds_per_100k": 10.6, "readiness_score": 0.80},
    "AU": {"gmp_facilities": 4, "qualified_centres": 10, "hematologists_per_100k": 1.9, "icu_beds_per_100k": 8.9, "readiness_score": 0.78},
    "CA": {"gmp_facilities": 5, "qualified_centres": 12, "hematologists_per_100k": 1.6, "icu_beds_per_100k": 12.9, "readiness_score": 0.80},
}


# ═══════════════════════════════════════════════════════════════════════════════
# Access Gap Analysis
# ═══════════════════════════════════════════════════════════════════════════════

async def get_regulatory_map(
    product: Optional[str] = None,
) -> Dict[str, Any]:
    """Country-by-country regulatory approval status for CAR-T products."""
    if product and product in APPROVED_PRODUCTS:
        products = {product: APPROVED_PRODUCTS[product]}
    else:
        products = APPROVED_PRODUCTS

    results = []
    for prod_name, prod_data in products.items():
        approvals = prod_data["approvals"]
        countries_approved = list(approvals.keys())
        countries_not = [c for c in REGULATORY_BODIES if c not in countries_approved]

        results.append({
            "product": prod_name,
            "total_approvals": len(approvals),
            "approved_countries": [
                {
                    "country": c,
                    "regulatory_body": REGULATORY_BODIES[c]["name"],
                    "approval_date": info["date"],
                    "indications": info["indications"],
                }
                for c, info in approvals.items()
            ],
            "not_yet_approved": [
                {
                    "country": c,
                    "regulatory_body": REGULATORY_BODIES[c]["name"],
                    "expected_review_months": REGULATORY_BODIES[c]["review_months"],
                    "priority_review_available": REGULATORY_BODIES[c]["priority_review"],
                }
                for c in countries_not
            ],
        })

    return {"products": results, "total_regulatory_bodies": len(REGULATORY_BODIES)}


async def access_gap_analysis(
    cancer_type: str = "dlbcl",
) -> Dict[str, Any]:
    """
    Analyse treatment access inequality across countries.
    Combines regulatory, infrastructure, and reimbursement factors.
    """
    from disease_atlas.prevalence_analyzer import INCIDENCE_PER_100K, POPULATION_MILLIONS

    incidence = INCIDENCE_PER_100K.get(cancer_type, 5.0)
    country_data = []

    for country, infra in INFRASTRUCTURE_SCORES.items():
        pop = POPULATION_MILLIONS.get(country, 50)
        annual_cases = int(pop * incidence / 100_000 * 1_000_000)
        rr_cases = int(annual_cases * 0.35)

        # Check how many products are approved
        n_approved = sum(
            1 for prod in APPROVED_PRODUCTS.values()
            if country in prod["approvals"]
        )

        # Treatment capacity (how many patients can actually be treated)
        capacity = infra["qualified_centres"] * 20  # ~20 patients/centre/year
        treatment_gap = max(0, rr_cases - capacity)
        gap_pct = round(treatment_gap / max(rr_cases, 1) * 100, 1)

        # Composite access score (0-100)
        access_score = round(
            (infra["readiness_score"] * 40) +
            (min(n_approved / 4, 1) * 30) +
            (min(capacity / max(rr_cases, 1), 1) * 30),
            1,
        )

        country_data.append({
            "country": country,
            "readiness_score": infra["readiness_score"],
            "annual_rr_cases": rr_cases,
            "treatment_capacity": capacity,
            "treatment_gap": treatment_gap,
            "gap_pct": gap_pct,
            "approved_products": n_approved,
            "qualified_centres": infra["qualified_centres"],
            "composite_access_score": access_score,
        })

    country_data.sort(key=lambda x: x["composite_access_score"], reverse=True)

    scores = [c["composite_access_score"] for c in country_data]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "cancer_type": cancer_type,
        "incidence_per_100k": incidence,
        "countries": country_data,
        "global_average_access_score": avg_score,
        "highest_access": country_data[0]["country"] if country_data else "N/A",
        "lowest_access": country_data[-1]["country"] if country_data else "N/A",
        "total_global_gap": sum(c["treatment_gap"] for c in country_data),
    }


async def infrastructure_readiness(
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """Healthcare infrastructure readiness for cell therapy delivery."""
    if country and country in INFRASTRUCTURE_SCORES:
        data = {country: INFRASTRUCTURE_SCORES[country]}
    else:
        data = INFRASTRUCTURE_SCORES

    countries = []
    for c, infra in data.items():
        countries.append({
            "country": c,
            **infra,
            "bottleneck": (
                "GMP manufacturing" if infra["gmp_facilities"] < 5
                else "Qualified treatment centres" if infra["qualified_centres"] < 15
                else "Specialist workforce" if infra["hematologists_per_100k"] < 0.5
                else "ICU capacity" if infra["icu_beds_per_100k"] < 5
                else "No critical bottleneck"
            ),
        })

    countries.sort(key=lambda x: x["readiness_score"], reverse=True)
    return {"countries": countries}


# ═══════════════════════════════════════════════════════════════════════════════
# Patient Journey Mapping
# ═══════════════════════════════════════════════════════════════════════════════

async def patient_journey(
    country: str = "US",
    cancer_type: str = "dlbcl",
) -> Dict[str, Any]:
    """
    Map the typical patient journey from diagnosis to CAR-T treatment,
    identifying bottlenecks and wait times at each stage.
    """
    # Base journey steps with typical US timelines
    base_journey = [
        {"step": "Initial Diagnosis", "days": 7, "category": "diagnosis"},
        {"step": "Pathology & Staging", "days": 14, "category": "diagnosis"},
        {"step": "First-Line Treatment", "days": 180, "category": "treatment"},
        {"step": "Relapse Detection", "days": 30, "category": "diagnosis"},
        {"step": "Referral to CAR-T Centre", "days": 21, "category": "referral"},
        {"step": "Insurance Pre-Authorization", "days": 14, "category": "access"},
        {"step": "Eligibility Assessment", "days": 7, "category": "assessment"},
        {"step": "Apheresis", "days": 1, "category": "manufacturing"},
        {"step": "Manufacturing & QC", "days": 28, "category": "manufacturing"},
        {"step": "Bridging Therapy (if needed)", "days": 21, "category": "treatment"},
        {"step": "Lymphodepletion", "days": 5, "category": "treatment"},
        {"step": "CAR-T Infusion", "days": 1, "category": "treatment"},
        {"step": "Acute Monitoring (CRS/ICANS)", "days": 14, "category": "monitoring"},
        {"step": "Post-Infusion Follow-Up", "days": 90, "category": "monitoring"},
    ]

    # Country-specific adjustments
    multipliers = {
        "US": 1.0, "EU": 1.2, "UK": 1.3, "JP": 1.1,
        "CN": 1.5, "IN": 2.0, "BR": 1.8,
    }
    mult = multipliers.get(country, 1.3)

    steps = []
    cumulative = 0
    for s in base_journey:
        adj_days = round(s["days"] * mult)
        if s["category"] == "manufacturing":
            adj_days = s["days"]  # manufacturing time is global
        cumulative += adj_days
        steps.append({
            **s,
            "days": adj_days,
            "cumulative_days": cumulative,
            "is_bottleneck": adj_days > 25,
        })

    bottlenecks = [s for s in steps if s["is_bottleneck"]]

    return {
        "country": country,
        "cancer_type": cancer_type,
        "journey_steps": steps,
        "total_days": cumulative,
        "total_weeks": round(cumulative / 7, 1),
        "bottlenecks": [b["step"] for b in bottlenecks],
        "n_bottlenecks": len(bottlenecks),
    }
