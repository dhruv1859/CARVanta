"""
CARVanta Health Economics — Budget Impact & Payer Modelling
============================================================
Comprehensive budget-impact analysis framework for cell & gene
therapies from the healthcare-system payer perspective.

Models:
  ▸ Budget Impact Analysis (BIA) — ISPOR/AMCP framework
  ▸ Multi-year budget forecasting with adoption curves
  ▸ Payer mix modelling (Medicare/Medicaid/Commercial/NHS)
  ▸ Outcomes-based risk-sharing contract simulation
  ▸ Value-based pricing corridors
  ▸ Budget-ceiling analysis (affordability thresholds)
  ▸ Net present value of treatment investment
  ▸ Break-even analysis for payers

References: Sullivan 2014 (ISPOR BIA guidelines),
ICER value framework 2023, NICE TA guidance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Treatment Pricing Data
# ═══════════════════════════════════════════════════════════════════════════════

TREATMENT_PRICES = {
    "tisagenlecleucel": {
        "list_price": 475_000,
        "indication": "r/r DLBCL, r/r ALL",
        "manufacturer": "Novartis",
        "launch_year": 2017,
        "outcomes_contract": True,
        "rebate_pct": 0.0,
    },
    "axicabtagene_ciloleucel": {
        "list_price": 373_000,
        "indication": "r/r LBCL",
        "manufacturer": "Kite/Gilead",
        "launch_year": 2017,
        "outcomes_contract": False,
        "rebate_pct": 0.0,
    },
    "brexucabtagene_autoleucel": {
        "list_price": 373_000,
        "indication": "r/r MCL, r/r ALL",
        "manufacturer": "Kite/Gilead",
        "launch_year": 2020,
        "outcomes_contract": False,
        "rebate_pct": 0.0,
    },
    "lisocabtagene_maraleucel": {
        "list_price": 410_300,
        "indication": "r/r LBCL",
        "manufacturer": "BMS/Juno",
        "launch_year": 2021,
        "outcomes_contract": False,
        "rebate_pct": 0.0,
    },
    "idecabtagene_vicleucel": {
        "list_price": 419_500,
        "indication": "r/r Multiple Myeloma",
        "manufacturer": "BMS/Bluebird",
        "launch_year": 2021,
        "outcomes_contract": False,
        "rebate_pct": 0.0,
    },
    "ciltacabtagene_autoleucel": {
        "list_price": 465_000,
        "indication": "r/r Multiple Myeloma",
        "manufacturer": "J&J/Legend",
        "launch_year": 2022,
        "outcomes_contract": False,
        "rebate_pct": 0.0,
    },
}

# Standard of Care comparators
SOC_COSTS = {
    "standard_chemo_dlbcl": {
        "name": "R-CHOP Salvage Chemo",
        "annual_cost": 45_000,
        "median_os_months": 6.3,
        "response_rate": 0.26,
    },
    "standard_chemo_all": {
        "name": "Blinatumomab/Inotuzumab",
        "annual_cost": 178_000,
        "median_os_months": 7.7,
        "response_rate": 0.44,
    },
    "standard_chemo_mm": {
        "name": "DPd / KPd Regimen",
        "annual_cost": 120_000,
        "median_os_months": 18.0,
        "response_rate": 0.60,
    },
    "bsct": {
        "name": "Autologous Stem Cell Transplant",
        "annual_cost": 250_000,
        "median_os_months": 24.0,
        "response_rate": 0.50,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Payer Mix
# ═══════════════════════════════════════════════════════════════════════════════

PAYER_MIX = {
    "US": {
        "Medicare": 0.45,
        "Medicaid": 0.10,
        "Commercial": 0.40,
        "Uninsured": 0.05,
    },
    "UK": {
        "NHS": 0.95,
        "Private": 0.05,
    },
    "DE": {
        "GKV": 0.88,
        "PKV": 0.12,
    },
    "FR": {
        "Sécurité_Sociale": 0.95,
        "Mutuelle": 0.05,
    },
    "JP": {
        "NHI": 0.98,
        "Private": 0.02,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Adoption Curve (S-curve / Bass Diffusion)
# ═══════════════════════════════════════════════════════════════════════════════

def bass_adoption_curve(
    market_potential: int,
    p: float = 0.03,     # coefficient of innovation
    q: float = 0.38,     # coefficient of imitation
    years: int = 10,
) -> List[Dict[str, Any]]:
    """
    Bass Diffusion Model for therapy adoption forecasting.
    Returns yearly adoption numbers and cumulative patients.
    """
    results = []
    cumulative = 0

    for t in range(1, years + 1):
        # Bass model: n(t) = [p + q*N(t-1)/M] * [M - N(t-1)]
        adoption = (p + q * cumulative / max(market_potential, 1)) * (market_potential - cumulative)
        adoption = max(0, int(adoption))
        cumulative += adoption

        results.append({
            "year": t,
            "new_patients": adoption,
            "cumulative_patients": cumulative,
            "penetration_pct": round(cumulative / max(market_potential, 1) * 100, 1),
        })

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# Budget Impact Analysis
# ═══════════════════════════════════════════════════════════════════════════════

async def budget_impact_analysis(
    product: str = "tisagenlecleucel",
    target: str = "cd19",
    eligible_patients: int = 500,
    adoption_rate_year1: float = 0.15,
    country: str = "US",
    time_horizon_years: int = 5,
    discount_rate: float = 0.03,
) -> Dict[str, Any]:
    """
    ISPOR-compliant Budget Impact Analysis.
    Compares net budget impact of introducing CAR-T vs standard-of-care.
    """
    product_info = TREATMENT_PRICES.get(product, TREATMENT_PRICES["tisagenlecleucel"])
    list_price = product_info["list_price"]

    # Standard comparator
    comparator = SOC_COSTS.get(f"standard_chemo_{target}", SOC_COSTS["standard_chemo_dlbcl"])
    soc_annual = comparator["annual_cost"]

    # Adoption curve
    adoption = bass_adoption_curve(eligible_patients, p=adoption_rate_year1, years=time_horizon_years)

    yearly_analysis = []
    total_cart_cost = 0
    total_soc_cost = 0
    total_net_impact = 0

    for year_data in adoption:
        yr = year_data["year"]
        new_pts = year_data["new_patients"]
        cumulative = year_data["cumulative_patients"]
        remaining_soc = eligible_patients - cumulative

        # CAR-T costs: one-time treatment + monitoring
        cart_cost = new_pts * list_price + cumulative * 15_000  # Follow-up
        soc_cost = remaining_soc * soc_annual

        # Discount
        discount = 1 / ((1 + discount_rate) ** yr)
        cart_cost_pv = cart_cost * discount
        soc_cost_pv = soc_cost * discount

        net = cart_cost_pv - soc_cost_pv

        yearly_analysis.append({
            "year": yr,
            "new_cart_patients": new_pts,
            "cumulative_cart": cumulative,
            "remaining_soc": remaining_soc,
            "cart_cost_usd": round(cart_cost_pv),
            "soc_cost_usd": round(soc_cost_pv),
            "net_budget_impact_usd": round(net),
            "per_member_per_month": round(net / max(eligible_patients * 12, 1), 2),
        })

        total_cart_cost += cart_cost_pv
        total_soc_cost += soc_cost_pv
        total_net_impact += net

    return {
        "product": product_info,
        "comparator": comparator,
        "country": country,
        "eligible_patients": eligible_patients,
        "time_horizon_years": time_horizon_years,
        "discount_rate": discount_rate,
        "yearly_analysis": yearly_analysis,
        "total_cart_cost_usd": round(total_cart_cost),
        "total_soc_cost_usd": round(total_soc_cost),
        "total_net_impact_usd": round(total_net_impact),
        "average_annual_impact_usd": round(total_net_impact / time_horizon_years),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Outcomes-Based Contract Simulation
# ═══════════════════════════════════════════════════════════════════════════════

async def outcomes_based_contract(
    product: str = "tisagenlecleucel",
    n_patients: int = 100,
    response_threshold_months: int = 1,
    full_refund_if_no_response: bool = True,
    milestone_payments: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Simulate outcomes-based risk-sharing contracts between
    manufacturers and payers.

    Novartis pioneered this with Kymriah: full refund if no
    complete remission at 1 month.
    """
    product_info = TREATMENT_PRICES.get(product, TREATMENT_PRICES["tisagenlecleucel"])
    price = product_info["list_price"]

    if milestone_payments is None:
        milestone_payments = [
            {"milestone": "Complete Remission at 1 month", "payment_pct": 0.50, "expected_rate": 0.83},
            {"milestone": "Sustained Remission at 6 months", "payment_pct": 0.30, "expected_rate": 0.60},
            {"milestone": "Sustained Remission at 12 months", "payment_pct": 0.20, "expected_rate": 0.48},
        ]

    scenarios = []
    for ms in milestone_payments:
        n_eligible = int(n_patients * ms["expected_rate"])
        payment = n_eligible * price * ms["payment_pct"]
        scenarios.append({
            "milestone": ms["milestone"],
            "eligible_patients": n_eligible,
            "payment_per_patient": round(price * ms["payment_pct"]),
            "total_payment_usd": round(payment),
        })

    total_obc = sum(s["total_payment_usd"] for s in scenarios)
    total_traditional = n_patients * price
    savings = total_traditional - total_obc

    return {
        "product": product,
        "n_patients": n_patients,
        "list_price": price,
        "contract_type": "outcomes-based milestone",
        "milestones": scenarios,
        "total_obc_cost_usd": round(total_obc),
        "total_traditional_cost_usd": round(total_traditional),
        "payer_savings_usd": round(savings),
        "savings_pct": round(savings / max(total_traditional, 1) * 100, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Value-Based Price Corridor
# ═══════════════════════════════════════════════════════════════════════════════

async def value_based_price_corridor(
    qaly_gain: float = 3.5,
    wtp_low: float = 50_000,
    wtp_high: float = 200_000,
    comparator_cost: float = 150_000,
    n_steps: int = 10,
) -> Dict[str, Any]:
    """
    Determine the acceptable price range for a CAR-T therapy
    based on willingness-to-pay thresholds per QALY gained.

    NICE (UK): £20-30K/QALY
    US (no official threshold): $50-200K/QALY
    """
    corridor = []
    step_size = (wtp_high - wtp_low) / max(n_steps - 1, 1)

    for i in range(n_steps):
        wtp = wtp_low + i * step_size
        max_acceptable_price = comparator_cost + qaly_gain * wtp
        corridor.append({
            "wtp_per_qaly": round(wtp),
            "max_acceptable_price_usd": round(max_acceptable_price),
            "premium_over_soc_usd": round(max_acceptable_price - comparator_cost),
        })

    # Key thresholds
    icer_nice = comparator_cost + qaly_gain * 30_000
    icer_us_low = comparator_cost + qaly_gain * 100_000
    icer_us_high = comparator_cost + qaly_gain * 150_000

    return {
        "qaly_gain": qaly_gain,
        "comparator_cost": comparator_cost,
        "corridor": corridor,
        "key_thresholds": {
            "nice_30k_gbp": round(icer_nice),
            "us_100k_usd": round(icer_us_low),
            "us_150k_usd": round(icer_us_high),
        },
        "recommendation": (
            f"At {qaly_gain} QALYs gained, price should be "
            f"${round(icer_us_low):,}–${round(icer_us_high):,} USD "
            f"to meet US WTP thresholds."
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Break-Even Analysis
# ═══════════════════════════════════════════════════════════════════════════════

async def break_even_analysis(
    cart_cost: float = 475_000,
    soc_annual_cost: float = 45_000,
    cart_os_years: float = 5.0,
    soc_os_years: float = 1.5,
    discount_rate: float = 0.03,
) -> Dict[str, Any]:
    """
    Determine when (if ever) CAR-T becomes cost-neutral vs SOC
    from the payer's perspective, accounting for avoided future
    treatment costs.
    """
    results = []
    cart_cumulative = cart_cost
    soc_cumulative = 0.0
    break_even_year = None

    for yr in range(1, 21):
        discount = 1 / ((1 + discount_rate) ** yr)

        # CAR-T: mostly one-time, small annual follow-up if still alive
        if yr <= cart_os_years:
            cart_annual = 15_000 * discount  # monitoring
        else:
            cart_annual = 0

        # SOC: continuous treatment until death
        if yr <= soc_os_years:
            soc_annual = soc_annual_cost * discount
        else:
            soc_annual = 0

        cart_cumulative += cart_annual
        soc_cumulative += soc_annual

        results.append({
            "year": yr,
            "cart_cumulative_usd": round(cart_cumulative),
            "soc_cumulative_usd": round(soc_cumulative),
            "difference_usd": round(cart_cumulative - soc_cumulative),
        })

        if break_even_year is None and soc_cumulative >= cart_cumulative:
            break_even_year = yr

    return {
        "cart_upfront_cost": cart_cost,
        "soc_annual_cost": soc_annual_cost,
        "break_even_year": break_even_year,
        "break_even_found": break_even_year is not None,
        "yearly_comparison": results,
        "interpretation": (
            f"CAR-T breaks even at year {break_even_year}" if break_even_year
            else "CAR-T does not break even within 20-year horizon at current pricing"
        ),
    }
