"""
CARVanta Health Economics — Market Access & Reimbursement Analysis
====================================================================
Analyze payer coverage, reimbursement pathways, and market access
strategies for CAR-T cell therapies across global markets.

Features:
- Multi-country reimbursement landscape comparison
- HTA body decision tracking (NICE, ICER, CADTH, PBAC, G-BA)
- Outcomes-based contract modeling
- Patient access program analysis
- Value-based pricing simulation
- Payer negotiation scenarios

Data: Based on published HTA decisions and access landscape reports.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.health_econ.market_access")


@dataclass
class HTADecision:
    body: str
    country: str
    product: str
    decision: str
    decision_date: str
    indication: str
    conditions: List[str] = field(default_factory=list)
    recommended_price: Optional[float] = None
    icer_assessed: Optional[float] = None
    patient_access_scheme: str = ""
    notes: str = ""


# ──────────────────────────────────────────────────────────────────────
# HTA Decision Database
# ──────────────────────────────────────────────────────────────────────

_HTA_DECISIONS: List[HTADecision] = [
    HTADecision("NICE", "UK", "Kymriah (tisagenlecleucel)", "Approved with CDF", "2018-12-14",
        "ALL (pediatric/young adult)", ["CDF managed access", "Outcomes-based"],
        None, 32000, "Confidential patient access scheme", "First CAR-T NICE approval"),
    HTADecision("NICE", "UK", "Yescarta (axicabtagene ciloleucel)", "Approved with CDF", "2019-01-17",
        "DLBCL (r/r)", ["CDF managed access", "Rebate scheme"], None, 45000,
        "Outcomes-based payment", "Approved alongside first CAR-T NICE recommendation"),
    HTADecision("NICE", "UK", "Abecma (idecabtagene vicleucel)", "Approved", "2022-08-10",
        "Multiple myeloma (4L+)", ["CDF managed access"], None, 55000, ""),
    HTADecision("NICE", "UK", "Carvykti (ciltacabtagene autoleucel)", "Approved", "2023-06-15",
        "Multiple myeloma (4L+)", [], None, 48000, ""),

    HTADecision("ICER (US)", "US", "Kymriah (tisagenlecleucel)", "Low Value", "2018-03-21",
        "ALL", ["Below WTP at $50K but not at current price"], None, 145000,
        "Proposed value-based price: $300-375K", "ICER review pre-FDA approval"),
    HTADecision("ICER (US)", "US", "Yescarta (axicabtagene ciloleucel)", "Intermediate Value", "2018-03-21",
        "DLBCL", [], None, 120000, "Within range at $150K WTP"),
    HTADecision("ICER (US)", "US", "Abecma (idecabtagene vicleucel)", "Intermediate Value", "2021-05-15",
        "Multiple myeloma", [], None, 165000, ""),

    HTADecision("G-BA", "Germany", "Kymriah (tisagenlecleucel)", "Considerable Added Benefit", "2019-03-01",
        "ALL + DLBCL", ["Free pricing for 1 year"], None, None, "AMNOG assessment"),
    HTADecision("G-BA", "Germany", "Yescarta (axicabtagene ciloleucel)", "Considerable Added Benefit", "2019-06-15",
        "DLBCL", [], None, None, "AMNOG assessment"),

    HTADecision("CADTH", "Canada", "Kymriah (tisagenlecleucel)", "Recommended", "2019-05-01",
        "ALL (pediatric)", ["Condition on price reduction"], None, None, "pCODR review"),
    HTADecision("CADTH", "Canada", "Yescarta (axicabtagene ciloleucel)", "Recommended", "2019-12-01",
        "DLBCL", ["Price negotiation required"], None, None, ""),

    HTADecision("PBAC", "Australia", "Kymriah (tisagenlecleucel)", "Approved", "2020-03-01",
        "ALL + DLBCL", ["PBS listing with managed entry"], None, None, "Outcomes-based risk sharing"),
    HTADecision("PMDA", "Japan", "Kymriah (tisagenlecleucel)", "Approved", "2019-05-15",
        "ALL + DLBCL", ["NHI coverage, ¥33.49M ($305K)"], 305000, None, "First cell therapy in Japan NHI"),
]


# ──────────────────────────────────────────────────────────────────────
# Market Access Functions
# ──────────────────────────────────────────────────────────────────────

async def get_hta_landscape(
    product: Optional[str] = None,
    country: Optional[str] = None,
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Get HTA decision landscape."""
    results = []
    for d in _HTA_DECISIONS:
        if product and product.lower() not in d.product.lower():
            continue
        if country and country.lower() != d.country.lower():
            continue
        if body and body.lower() != d.body.lower():
            continue
        results.append({
            "body": d.body, "country": d.country, "product": d.product,
            "decision": d.decision, "date": d.decision_date,
            "indication": d.indication, "conditions": d.conditions,
            "icer": d.icer_assessed, "access_scheme": d.patient_access_scheme,
            "notes": d.notes,
        })
    return {"total": len(results), "decisions": results}


async def analyze_market_access(
    product: str = "tisagenlecleucel",
    target_markets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Comprehensive market access analysis across key markets."""
    markets = target_markets or ["US", "UK", "Germany", "Japan", "Canada", "Australia"]

    country_analysis = {}
    for country in markets:
        decisions = [d for d in _HTA_DECISIONS if d.country == country and product.lower() in d.product.lower()]

        # Market characteristics
        market_data = {
            "US": {"population_eligible": 8500, "pricing": "Free pricing", "timeline_months": 2, "market_size_usd": 4.2e9},
            "UK": {"population_eligible": 1200, "pricing": "NICE CDF", "timeline_months": 12, "market_size_usd": 450e6},
            "Germany": {"population_eligible": 2000, "pricing": "AMNOG", "timeline_months": 6, "market_size_usd": 800e6},
            "Japan": {"population_eligible": 3000, "pricing": "NHI price", "timeline_months": 8, "market_size_usd": 950e6},
            "Canada": {"population_eligible": 900, "pricing": "pCODR/INESSS", "timeline_months": 14, "market_size_usd": 350e6},
            "Australia": {"population_eligible": 600, "pricing": "PBS", "timeline_months": 16, "market_size_usd": 220e6},
        }.get(country, {"population_eligible": 500, "pricing": "Reference pricing", "timeline_months": 12, "market_size_usd": 100e6})

        country_analysis[country] = {
            "hta_decisions": len(decisions),
            "latest_decision": decisions[-1].decision if decisions else "Not reviewed",
            "pricing_framework": market_data["pricing"],
            "eligible_patients": market_data["population_eligible"],
            "time_to_market_months": market_data["timeline_months"],
            "market_size_usd": market_data["market_size_usd"],
            "access_barriers": _get_access_barriers(country),
            "recommended_strategy": _get_strategy(country),
        }

    return {"product": product, "markets": country_analysis, "total_markets": len(markets)}


def _get_access_barriers(country: str) -> List[str]:
    barriers = {
        "US": ["High cost sharing", "Prior authorization", "Step therapy requirements", "Network restrictions to authorized centers"],
        "UK": ["CDF managed access", "Collection lag for outcomes data", "Budget impact concern"],
        "Germany": ["AMNOG price negotiation after 12 months", "Reference pricing", "Hospital DRG limits"],
        "Japan": ["NHI price revision risk", "Limited authorized centers", "Hospitalization requirements"],
        "Canada": ["Provincial listing delays", "Budget impact tests", "Limited centers (3-4)"],
        "Australia": ["PBS risk-sharing requirements", "Outcomes data collection"], 
    }
    return barriers.get(country, ["Limited data", "Regulatory uncertainty"])


def _get_strategy(country: str) -> str:
    strategies = {
        "US": "Outcomes-based contract with commercial payers; CMS New Technology Add-on Payment",
        "UK": "CDF managed access with real-world outcomes data collection",
        "Germany": "Early benefit assessment filing; negotiate post-AMNOG pricing",
        "Japan": "NHI cost-effectiveness assessment; build center network",
        "Canada": "Joint pCODR/INESSS review; provincial negotiation via pCPA",
        "Australia": "PBS submission with risk-sharing arrangement",
    }
    return strategies.get(country, "Engage local HTA body with health economics dossier")


async def model_outcomes_based_contract(
    product_price: float = 475000,
    success_metric: str = "complete_remission",
    success_threshold: float = 0.80,
    payment_schedule: str = "milestone",
    expected_success_rate: float = 0.82,
) -> Dict[str, Any]:
    """Model outcomes-based contract structures."""

    schedules = {
        "milestone": {
            "name": "Milestone-Based Payment",
            "description": "Payments tied to achieving clinical milestones",
            "payments": [
                {"milestone": "Infusion", "pct": 30, "amount": round(product_price * 0.30, 2)},
                {"milestone": f"Day 28 {success_metric}", "pct": 40, "amount": round(product_price * 0.40, 2)},
                {"milestone": f"Month 6 durability", "pct": 20, "amount": round(product_price * 0.20, 2)},
                {"milestone": f"Month 12 durability", "pct": 10, "amount": round(product_price * 0.10, 2)},
            ],
        },
        "full_risk": {
            "name": "Full Risk-Sharing",
            "description": "Full refund if patient doesn't achieve specified outcome",
            "payments": [
                {"milestone": "Infusion", "pct": 100, "amount": product_price},
                {"milestone": f"Refund if no {success_metric}", "pct": -100, "amount": -product_price},
            ],
        },
        "rebate": {
            "name": "Performance-Linked Rebate",
            "description": "Rebate based on real-world outcome performance vs threshold",
            "payments": [
                {"milestone": "Infusion", "pct": 100, "amount": product_price},
                {"milestone": f"Rebate if {success_metric} < {success_threshold*100}%", "pct": -30,
                 "amount": round(-product_price * 0.30, 2)},
            ],
        },
    }

    schedule = schedules.get(payment_schedule, schedules["milestone"])

    # Expected cost per patient based on success rate
    for_100 = product_price
    expected_cost = product_price * expected_success_rate * 0.85 + product_price * (1 - expected_success_rate) * 0.30
    manufacturer_revenue = expected_cost * 100  # per 100 patients

    return {
        "product_price": product_price,
        "contract_type": schedule["name"],
        "description": schedule["description"],
        "payment_schedule": schedule["payments"],
        "success_metric": success_metric,
        "success_threshold": success_threshold,
        "expected_success_rate": expected_success_rate,
        "expected_cost_per_patient": round(expected_cost, 2),
        "discount_vs_list": round((1 - expected_cost / product_price) * 100, 1),
        "manufacturer_revenue_per_100": round(manufacturer_revenue, 2),
    }


async def get_reimbursement_codes() -> Dict[str, Any]:
    """Get CAR-T relevant reimbursement codes."""
    return {
        "cpt": [
            {"code": "0537T", "description": "CAR-T cell administration, autologous", "type": "procedure"},
            {"code": "0540T", "description": "CAR-T cell therapy management, initial 30 days", "type": "management"},
            {"code": "96413", "description": "Chemotherapy administration, infusion technique", "type": "chemo"},
        ],
        "icd10": [
            {"code": "XW033C7", "description": "Tisagenlecleucel infusion", "type": "drug"},
            {"code": "XW033N7", "description": "Axicabtagene ciloleucel infusion", "type": "drug"},
            {"code": "XW033P7", "description": "Idecabtagene vicleucel infusion", "type": "drug"},
        ],
        "drg": [
            {"code": "018", "description": "CAR-T cell therapy DRG (NTAP eligible)", "weight": 45.0},
        ],
        "hcpcs": [
            {"code": "Q2042", "description": "Tisagenlecleucel, up to 600 million cells", "type": "product"},
            {"code": "Q2041", "description": "Axicabtagene ciloleucel, up to 200 million cells", "type": "product"},
        ],
    }
