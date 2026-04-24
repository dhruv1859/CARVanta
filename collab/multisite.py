"""
CARVanta Collab — Multi-Site Coordination Engine
===================================================
Tools for coordinating multi-site CAR-T research across
institutions, managing site communications, data harmonization,
and cross-site analytics.

Features:
- Site registry with capabilities and accreditation status
- Cross-site data harmonization (CDM mapping)
- Multi-site enrollment tracking
- Site performance benchmarking
- Central monitoring dashboard
- Data transfer agreement management
- Site qualification and initiation tracking
- Cross-site safety signal detection
- Federated analysis support (no data movement)
- Regulatory submission harmonization across jurisdictions
"""

import logging
import random
import uuid
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("carvanta.collab.multisite")

# In-memory stores
_SITES: Dict[str, Dict] = {}

# Site registry database
_SITE_DATABASE = {
    "mskcc": {
        "name": "Memorial Sloan Kettering Cancer Center",
        "city": "New York", "state": "NY", "country": "USA",
        "latitude": 40.7648, "longitude": -73.9568,
        "accreditation": {"FACT": True, "NCI": True, "ASCO": True, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "bcma_cart", "phase_1", "pediatric",
                         "bridging_therapy", "icu_monitoring"],
        "cart_experience_years": 8,
        "annual_cart_patients": 150,
        "pi": "Dr. Michel Sadelain",
        "specialties": ["CD19 CAR-T", "Allogeneic approaches", "CAR-T in ALL"],
    },
    "upenn": {
        "name": "University of Pennsylvania / Abramson Cancer Center",
        "city": "Philadelphia", "state": "PA", "country": "USA",
        "latitude": 39.9496, "longitude": -75.1933,
        "accreditation": {"FACT": True, "NCI": True, "ASCO": True, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "bcma_cart", "phase_1", "phase_2",
                         "manufacturing", "bridging_therapy"],
        "cart_experience_years": 10,
        "annual_cart_patients": 200,
        "pi": "Dr. Carl June",
        "specialties": ["Pioneer CAR-T", "CTL019/Kymriah", "Solid tumor CAR-T"],
    },
    "fred_hutch": {
        "name": "Fred Hutchinson Cancer Center",
        "city": "Seattle", "state": "WA", "country": "USA",
        "latitude": 47.6275, "longitude": -122.3377,
        "accreditation": {"FACT": True, "NCI": True, "ASCO": True, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "bcma_cart", "cd22_cart", "phase_1",
                         "allogeneic", "manufacturing"],
        "cart_experience_years": 9,
        "annual_cart_patients": 180,
        "pi": "Dr. Cameron Turtle",
        "specialties": ["CD19/CD22 dual targeting", "Defined composition products"],
    },
    "nci": {
        "name": "National Cancer Institute (NIH Clinical Center)",
        "city": "Bethesda", "state": "MD", "country": "USA",
        "latitude": 39.0003, "longitude": -77.1058,
        "accreditation": {"FACT": True, "NCI": True, "ASCO": False, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "her2_cart", "gd2_cart", "phase_1",
                         "pediatric", "manufacturing", "solid_tumor"],
        "cart_experience_years": 12,
        "annual_cart_patients": 100,
        "pi": "Dr. James Kochenderfer",
        "specialties": ["Anti-CD19 pioneering", "Solid tumor CARs", "Anti-BCMA"],
    },
    "mdanderson": {
        "name": "MD Anderson Cancer Center",
        "city": "Houston", "state": "TX", "country": "USA",
        "latitude": 29.7076, "longitude": -95.3974,
        "accreditation": {"FACT": True, "NCI": True, "ASCO": True, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "bcma_cart", "phase_1", "phase_2",
                         "bridging_therapy", "icu_monitoring", "long_term_follow_up"],
        "cart_experience_years": 7,
        "annual_cart_patients": 160,
        "pi": "Dr. Sattva Neelapu",
        "specialties": ["Axi-cel (ZUMA trials)", "Lymphoma", "CRS management"],
    },
    "great_ormond": {
        "name": "Great Ormond Street Hospital",
        "city": "London", "state": "", "country": "UK",
        "latitude": 51.5225, "longitude": -0.1201,
        "accreditation": {"FACT": False, "NCI": False, "ASCO": False, "JACIE": True},
        "capabilities": ["leukapheresis", "cd19_cart", "phase_1", "pediatric",
                         "allogeneic", "gene_editing"],
        "cart_experience_years": 6,
        "annual_cart_patients": 50,
        "pi": "Dr. Waseem Qasim",
        "specialties": ["Pediatric ALL", "CRISPR-edited universal CAR-T", "UCART19"],
    },
    "sheba_medical": {
        "name": "Sheba Medical Center",
        "city": "Ramat Gan", "state": "", "country": "Israel",
        "latitude": 32.0469, "longitude": 34.8427,
        "accreditation": {"FACT": True, "NCI": False, "ASCO": False, "JACIE": True},
        "capabilities": ["leukapheresis", "cd19_cart", "phase_1", "academic_manufacturing",
                         "bridging_therapy"],
        "cart_experience_years": 5,
        "annual_cart_patients": 40,
        "pi": "Dr. Arnon Nagler",
        "specialties": ["Academic CAR-T manufacturing", "Point-of-care production"],
    },
    "peking_university": {
        "name": "Peking University Cancer Hospital",
        "city": "Beijing", "state": "", "country": "China",
        "latitude": 39.9822, "longitude": 116.3536,
        "accreditation": {"FACT": False, "NCI": False, "ASCO": False, "JACIE": False},
        "capabilities": ["leukapheresis", "cd19_cart", "bcma_cart", "cd22_cart", "phase_1",
                         "phase_2", "manufacturing", "large_scale"],
        "cart_experience_years": 6,
        "annual_cart_patients": 300,
        "pi": "Dr. Jun Zhu",
        "specialties": ["Large-scale CAR-T programs", "BCMA + CD19 sequential", "Low-cost manufacturing"],
    },
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


async def list_sites(
    country: Optional[str] = None,
    capability: Optional[str] = None,
) -> Dict[str, Any]:
    """List all registered research sites."""
    sites = []
    for key, site in _SITE_DATABASE.items():
        if country and site["country"] != country:
            continue
        if capability and capability not in site["capabilities"]:
            continue
        sites.append({"site_id": key, **site})

    countries = list(set(s["country"] for s in _SITE_DATABASE.values()))
    all_caps = list(set(c for s in _SITE_DATABASE.values() for c in s["capabilities"]))

    return {
        "total_sites": len(sites),
        "sites": sites,
        "countries": countries,
        "available_capabilities": sorted(all_caps),
    }


async def site_performance(
    site_id: Optional[str] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get site performance metrics and benchmarking."""
    if seed:
        random.seed(seed)

    sites_to_report = [site_id] if site_id and site_id in _SITE_DATABASE else list(_SITE_DATABASE.keys())

    performance = []
    for sid in sites_to_report:
        site = _SITE_DATABASE[sid]
        perf = {
            "site_id": sid,
            "name": site["name"],
            "enrollment_metrics": {
                "target": random.randint(20, 80),
                "enrolled": random.randint(5, 60),
                "screen_fail_rate_pct": round(random.uniform(10, 40), 1),
                "enrollment_rate_per_month": round(random.uniform(1, 8), 1),
            },
            "quality_metrics": {
                "protocol_deviations": random.randint(0, 15),
                "query_rate_per_100_crfs": round(random.uniform(2, 20), 1),
                "query_resolution_days": round(random.uniform(3, 21), 1),
                "data_entry_lag_days": round(random.uniform(1, 14), 1),
            },
            "safety_metrics": {
                "sae_count": random.randint(0, 10),
                "crs_grade_3_4_pct": round(random.uniform(5, 30), 1),
                "icans_any_grade_pct": round(random.uniform(10, 50), 1),
                "icu_admission_pct": round(random.uniform(20, 60), 1),
            },
            "manufacturing_metrics": {
                "manufacturing_success_pct": round(random.uniform(85, 100), 1),
                "vein_to_vein_days": random.randint(21, 45),
                "out_of_spec_pct": round(random.uniform(0, 10), 1),
            },
            "overall_score": round(random.uniform(60, 95), 1),
        }
        performance.append(perf)

    return {
        "total_sites": len(performance),
        "performance": performance,
        "top_performer": max(performance, key=lambda p: p["overall_score"])["name"] if performance else None,
    }


async def cross_site_enrollment(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Get cross-site enrollment tracking dashboard."""
    if seed:
        random.seed(seed)

    enrollment = []
    total_target = 0
    total_enrolled = 0

    for sid, site in _SITE_DATABASE.items():
        target = random.randint(15, 60)
        enrolled = random.randint(3, target)
        total_target += target
        total_enrolled += enrolled

        monthly_enrollment = [random.randint(0, 5) for _ in range(12)]

        enrollment.append({
            "site_id": sid,
            "name": site["name"],
            "country": site["country"],
            "target": target,
            "enrolled": enrolled,
            "pct_of_target": round(enrolled / target * 100, 1),
            "monthly_enrollment": monthly_enrollment,
            "active": enrolled < target,
            "projected_completion_months": round((target - enrolled) / max(sum(monthly_enrollment[-3:]) / 3, 0.1), 1) if enrolled < target else 0,
        })

    return {
        "total_sites": len(enrollment),
        "total_target": total_target,
        "total_enrolled": total_enrolled,
        "overall_pct": round(total_enrolled / total_target * 100, 1),
        "enrollment_by_site": enrollment,
        "enrollment_by_country": {
            country: sum(e["enrolled"] for e in enrollment if _SITE_DATABASE[e["site_id"]]["country"] == country)
            for country in set(s["country"] for s in _SITE_DATABASE.values())
        },
    }


async def data_harmonization(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Assess data harmonization across sites."""
    if seed:
        random.seed(seed)

    domains = [
        {"domain": "Demographics", "fields": 12, "harmonized_pct": round(random.uniform(85, 100), 1)},
        {"domain": "Tumor Assessment", "fields": 18, "harmonized_pct": round(random.uniform(70, 100), 1)},
        {"domain": "Laboratory Results", "fields": 45, "harmonized_pct": round(random.uniform(60, 95), 1)},
        {"domain": "Adverse Events", "fields": 22, "harmonized_pct": round(random.uniform(75, 100), 1)},
        {"domain": "Concomitant Meds", "fields": 15, "harmonized_pct": round(random.uniform(65, 95), 1)},
        {"domain": "CAR-T Manufacturing", "fields": 30, "harmonized_pct": round(random.uniform(50, 90), 1)},
        {"domain": "Biomarkers", "fields": 25, "harmonized_pct": round(random.uniform(40, 85), 1)},
        {"domain": "Response Assessment", "fields": 10, "harmonized_pct": round(random.uniform(80, 100), 1)},
    ]

    overall = round(sum(d["harmonized_pct"] * d["fields"] for d in domains) / sum(d["fields"] for d in domains), 1)

    cdm_standards = {
        "CDISC_SDTM": {"version": "3.4", "compliance_pct": round(random.uniform(70, 95), 1)},
        "CDISC_ADaM": {"version": "2.1", "compliance_pct": round(random.uniform(60, 90), 1)},
        "HL7_FHIR": {"version": "R4", "compliance_pct": round(random.uniform(40, 75), 1)},
        "OMOP_CDM": {"version": "5.4", "compliance_pct": round(random.uniform(50, 85), 1)},
    }

    return {
        "overall_harmonization_pct": overall,
        "domains": domains,
        "cdm_standards": cdm_standards,
        "total_fields": sum(d["fields"] for d in domains),
        "issues": [
            {"domain": d["domain"], "issue": f"{100 - d['harmonized_pct']:.1f}% fields need harmonization"}
            for d in domains if d["harmonized_pct"] < 80
        ],
    }


async def find_nearest_sites(
    latitude: float = 40.7128,
    longitude: float = -74.0060,
    max_distance_km: float = 5000,
    capability: Optional[str] = None,
) -> Dict[str, Any]:
    """Find nearest CAR-T research sites to a location."""
    results = []
    for sid, site in _SITE_DATABASE.items():
        if capability and capability not in site["capabilities"]:
            continue
        dist = _haversine(latitude, longitude, site["latitude"], site["longitude"])
        if dist <= max_distance_km:
            results.append({
                "site_id": sid,
                "name": site["name"],
                "city": site["city"],
                "country": site["country"],
                "distance_km": round(dist, 1),
                "capabilities": site["capabilities"],
                "annual_patients": site["annual_cart_patients"],
            })

    results.sort(key=lambda s: s["distance_km"])

    return {
        "search_location": {"latitude": latitude, "longitude": longitude},
        "max_distance_km": max_distance_km,
        "total_found": len(results),
        "sites": results,
    }


async def federated_analysis_plan(
    analysis_type: str = "survival",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate a federated analysis plan (data stays at each site)."""
    if seed:
        random.seed(seed)

    analysis_types = {
        "survival": {
            "name": "Federated Survival Analysis",
            "method": "Meta-analytic Kaplan-Meier with stratified log-rank",
            "required_variables": ["time_to_event", "event_status", "treatment_arm", "site_id",
                                  "age", "sex", "disease_stage", "prior_lines"],
            "statistical_model": "Cox proportional hazards with site as stratum",
            "privacy_level": "Summary statistics only — no individual patient data shared",
        },
        "response_rate": {
            "name": "Federated Response Rate Comparison",
            "method": "Mantel-Haenszel meta-analysis of response rates",
            "required_variables": ["response_status", "treatment_arm", "site_id"],
            "statistical_model": "Random-effects meta-analysis (DerSimonian-Laird)",
            "privacy_level": "Aggregate counts only — no patient-level data",
        },
        "biomarker": {
            "name": "Federated Biomarker Discovery",
            "method": "Meta-analysis of site-level association statistics",
            "required_variables": ["biomarker_value", "response_status", "site_id"],
            "statistical_model": "Fisher's method for combining p-values across sites",
            "privacy_level": "Effect sizes and standard errors only",
        },
    }

    plan = analysis_types.get(analysis_type, analysis_types["survival"])

    participating_sites = random.sample(list(_SITE_DATABASE.keys()), k=min(5, len(_SITE_DATABASE)))
    site_details = []
    total_n = 0
    for sid in participating_sites:
        n = random.randint(20, 100)
        total_n += n
        site_details.append({
            "site_id": sid,
            "name": _SITE_DATABASE[sid]["name"],
            "n_patients": n,
            "data_ready": random.random() > 0.2,
            "last_data_lock": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
        })

    return {
        "analysis_plan": plan,
        "participating_sites": site_details,
        "total_patients": total_n,
        "estimated_power": round(min(1 - (1 / (1 + 0.01 * total_n)), 0.99), 2),
        "timeline": {
            "data_harmonization": "2 weeks",
            "site_level_analysis": "1 week per site",
            "meta_analysis": "1 week",
            "total_estimated": f"{len(participating_sites) + 3} weeks",
        },
        "available_analyses": list(analysis_types.keys()),
    }
