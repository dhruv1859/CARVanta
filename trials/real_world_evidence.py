"""
CARVanta Trials — Real-World Evidence & External Control Arms
================================================================
Generate synthetic external control arms, match real-world data
comparators, and model treatment effect sizes for regulatory submission.

Features:
- External control arm (ECA) generation from historical data
- Propensity score matching for RWE comparators
- Indirect treatment comparison (ITC / MAIC)
- Treatment effect estimation (hazard ratios, odds ratios)
- Registry data integration simulation
- Post-marketing outcome surveillance
- Health technology assessment (HTA) evidence package
- NICE/ICER value framework compatibility

Data Sources:
- SCHOLAR-1: R/R DLBCL historical outcomes (Crump et al., Blood 2017)
- ZUMA-1: Axicabtagene ciloleucel in R/R LBCL (Neelapu et al., NEJM 2017)
- JULIET: Tisagenlecleucel in R/R DLBCL (Schuster et al., NEJM 2019)
- TRANSCEND: Lisocabtagene maraleucel in R/R LBCL (Abramson et al., Lancet 2020)
- ELIANA: Tisagenlecleucel in pediatric/YA ALL (Maude et al., NEJM 2018)
- KarMMa: Idecabtagene vicleucel in R/R MM (Munshi et al., NEJM 2021)
- CARTITUDE-1: Ciltacabtagene autoleucel in R/R MM (Berdeja et al., Lancet 2021)

Regulatory Context:
- FDA Draft Guidance: Use of RWE to Support Regulatory Decision-Making (2023)
- ICH E10: Choice of Control Group and Related Issues
- FDA 21st Century Cures Act: RWE pathway for label expansion
"""


import logging
import math
import random
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.trials.real_world_evidence")


# ──────────────────────────────────────────────────────────────────────
# Historical Comparator Data (Published CAR-T Outcomes)
# ──────────────────────────────────────────────────────────────────────

_HISTORICAL_OUTCOMES = {
    "DLBCL": {
        "standard_of_care": {
            "regimen": "R-CHOP salvage → auto-HSCT",
            "orr": 0.26, "cr": 0.07, "median_pfs_months": 3.5, "median_os_months": 12.0,
            "n_patients": 636, "source": "SCHOLAR-1 (Crump et al., Blood 2017)",
        },
        "axi_cel": {
            "regimen": "Axicabtagene ciloleucel (Yescarta®)",
            "orr": 0.83, "cr": 0.58, "median_pfs_months": 5.9, "median_os_months": 25.8,
            "n_patients": 101, "source": "ZUMA-1 (Neelapu et al., NEJM 2017)",
        },
        "tisa_cel": {
            "regimen": "Tisagenlecleucel (Kymriah®)",
            "orr": 0.52, "cr": 0.40, "median_pfs_months": 2.9, "median_os_months": 11.1,
            "n_patients": 93, "source": "JULIET (Schuster et al., NEJM 2019)",
        },
        "liso_cel": {
            "regimen": "Lisocabtagene maraleucel (Breyanzi®)",
            "orr": 0.73, "cr": 0.53, "median_pfs_months": 6.8, "median_os_months": 27.3,
            "n_patients": 192, "source": "TRANSCEND NHL 001 (Abramson et al., Lancet 2020)",
        },
    },
    "ALL": {
        "standard_of_care": {
            "regimen": "Salvage chemotherapy (FLAG-IDA, HyperCVAD, etc.)",
            "orr": 0.31, "cr": 0.14, "median_pfs_months": 2.0, "median_os_months": 5.0,
            "n_patients": 1000, "source": "Historical pooled analysis",
        },
        "tisa_cel_all": {
            "regimen": "Tisagenlecleucel (Kymriah®) - pediatric/YA ALL",
            "orr": 0.82, "cr": 0.63, "median_pfs_months": 11.7, "median_os_months": 19.1,
            "n_patients": 75, "source": "ELIANA (Maude et al., NEJM 2018)",
        },
    },
    "MM": {
        "standard_of_care": {
            "regimen": "Pomalidomide + Dexamethasone",
            "orr": 0.31, "cr": 0.03, "median_pfs_months": 4.0, "median_os_months": 13.1,
            "n_patients": 302, "source": "OPTIMISMM (Richardson et al., 2019)",
        },
        "ide_cel": {
            "regimen": "Idecabtagene vicleucel (Abecma®)",
            "orr": 0.73, "cr": 0.33, "median_pfs_months": 8.8, "median_os_months": 24.5,
            "n_patients": 128, "source": "KarMMa (Munshi et al., NEJM 2021)",
        },
        "cilta_cel": {
            "regimen": "Ciltacabtagene autoleucel (Carvykti®)",
            "orr": 0.98, "cr": 0.83, "median_pfs_months": 27.7, "median_os_months": None,
            "n_patients": 97, "source": "CARTITUDE-1 (Berdeja et al., Lancet 2021)",
        },
    },
}


async def get_historical_outcomes(
    indication: str = "DLBCL",
) -> Dict[str, Any]:
    """Get published historical outcomes for comparison."""
    indication_upper = indication.upper()
    data = _HISTORICAL_OUTCOMES.get(indication_upper, {})

    if not data:
        return {"error": f"No historical data for {indication}", "available": list(_HISTORICAL_OUTCOMES.keys())}

    return {
        "indication": indication,
        "comparators": len(data),
        "outcomes": data,
    }


async def generate_external_control_arm(
    indication: str = "DLBCL",
    comparator: str = "standard_of_care",
    n_patients: int = 100,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate a synthetic external control arm from historical data."""
    if seed:
        random.seed(seed)

    indication_upper = indication.upper()
    hist = _HISTORICAL_OUTCOMES.get(indication_upper, {}).get(comparator)

    if not hist:
        return {"error": f"No data for {indication}/{comparator}"}

    # Generate individual patient data
    patients = []
    for i in range(n_patients):
        age = max(18, int(random.gauss(62, 12)))
        ecog = random.choices([0, 1, 2], weights=[25, 50, 25])[0]
        prior_lines = random.choices([2, 3, 4, 5], weights=[20, 40, 25, 15])[0]

        # Response based on historical rates with variability
        response_prob = hist["orr"] + random.gauss(0, 0.05)
        responded = random.random() < max(0, min(1, response_prob))
        cr_prob = hist["cr"] / max(hist["orr"], 0.01)
        cr = responded and random.random() < cr_prob

        # Survival
        median_pfs = hist["median_pfs_months"]
        pfs = round(random.expovariate(math.log(2) / max(median_pfs, 0.5)), 1)
        if hist["median_os_months"]:
            os = round(pfs + random.expovariate(math.log(2) / max(hist["median_os_months"] - median_pfs, 1)), 1)
        else:
            os = round(pfs + random.expovariate(1 / 24), 1)

        patients.append({
            "id": i + 1, "age": age, "ecog": ecog, "prior_lines": prior_lines,
            "response": "CR" if cr else "PR" if responded else "NR",
            "pfs_months": pfs, "os_months": os, "censored": random.random() < 0.15,
        })

    responses = [p["response"] for p in patients]
    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "indication": indication,
        "comparator": comparator,
        "source": hist["source"],
        "n_patients": n_patients,
        "summary": {
            "orr_pct": round(sum(1 for r in responses if r != "NR") / n_patients * 100, 1),
            "cr_pct": round(sum(1 for r in responses if r == "CR") / n_patients * 100, 1),
            "median_pfs": round(sorted([p["pfs_months"] for p in patients])[n_patients // 2], 1),
            "median_os": round(sorted([p["os_months"] for p in patients])[n_patients // 2], 1),
        },
        "patients": patients[:20],
    }


async def propensity_score_matching(
    treatment_arm: List[Dict],
    control_arm: List[Dict],
    covariates: Optional[List[str]] = None,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Perform propensity score matching between treatment and control arms."""
    if seed:
        random.seed(seed)

    if not covariates:
        covariates = ["age", "ecog", "prior_lines"]

    # Simplified PSM: match on covariates using nearest-neighbor
    matched_pairs = []
    used_controls = set()

    for tx in treatment_arm:
        best_match = None
        best_distance = float("inf")

        for j, ctrl in enumerate(control_arm):
            if j in used_controls:
                continue

            # Calculate distance
            dist = 0
            for cov in covariates:
                tx_val = tx.get(cov, 0)
                ctrl_val = ctrl.get(cov, 0)
                if isinstance(tx_val, (int, float)) and isinstance(ctrl_val, (int, float)):
                    dist += ((tx_val - ctrl_val) / max(abs(tx_val) + abs(ctrl_val), 1)) ** 2

            dist = math.sqrt(dist)
            if dist < best_distance:
                best_distance = dist
                best_match = j

        if best_match is not None and best_distance < 1.0:
            matched_pairs.append({
                "treatment": tx, "control": control_arm[best_match],
                "distance": round(best_distance, 4),
            })
            used_controls.add(best_match)

    # Balance check
    balance = {}
    for cov in covariates:
        tx_vals = [p["treatment"].get(cov, 0) for p in matched_pairs if isinstance(p["treatment"].get(cov, 0), (int, float))]
        ctrl_vals = [p["control"].get(cov, 0) for p in matched_pairs if isinstance(p["control"].get(cov, 0), (int, float))]

        if tx_vals and ctrl_vals:
            tx_mean = sum(tx_vals) / len(tx_vals)
            ctrl_mean = sum(ctrl_vals) / len(ctrl_vals)
            pooled_std = math.sqrt((sum((v - tx_mean) ** 2 for v in tx_vals) + sum((v - ctrl_mean) ** 2 for v in ctrl_vals)) / max(len(tx_vals) + len(ctrl_vals) - 2, 1))
            smd = abs(tx_mean - ctrl_mean) / max(pooled_std, 0.001)
            balance[cov] = {"tx_mean": round(tx_mean, 2), "ctrl_mean": round(ctrl_mean, 2), "smd": round(smd, 4), "balanced": smd < 0.1}

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "treatment_n": len(treatment_arm),
        "control_n": len(control_arm),
        "matched_pairs": len(matched_pairs),
        "matching_rate_pct": round(len(matched_pairs) / max(len(treatment_arm), 1) * 100, 1),
        "covariate_balance": balance,
        "all_balanced": all(b["balanced"] for b in balance.values()) if balance else False,
    }


async def treatment_effect_estimation(
    indication: str = "DLBCL",
    experimental: str = "axi_cel",
    comparator: str = "standard_of_care",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Estimate treatment effect (HR, OR) comparing experimental vs comparator."""
    if seed:
        random.seed(seed)

    hist_exp = _HISTORICAL_OUTCOMES.get(indication.upper(), {}).get(experimental, {})
    hist_ctrl = _HISTORICAL_OUTCOMES.get(indication.upper(), {}).get(comparator, {})

    if not hist_exp or not hist_ctrl:
        return {"error": "Data not found for specified arms"}

    # Odds ratio for ORR
    a = hist_exp["orr"] * 100
    b = (1 - hist_exp["orr"]) * 100
    c = hist_ctrl["orr"] * 100
    d = (1 - hist_ctrl["orr"]) * 100
    odds_ratio = (a * d) / max(b * c, 0.01)

    # Hazard ratio for PFS
    if hist_exp["median_pfs_months"] and hist_ctrl["median_pfs_months"]:
        hr_pfs = math.log(2) / hist_exp["median_pfs_months"] / (math.log(2) / hist_ctrl["median_pfs_months"])
    else:
        hr_pfs = None

    # Hazard ratio for OS
    if hist_exp.get("median_os_months") and hist_ctrl.get("median_os_months"):
        hr_os = math.log(2) / hist_exp["median_os_months"] / (math.log(2) / hist_ctrl["median_os_months"])
    else:
        hr_os = None

    # NNT (number needed to treat)
    ard = hist_exp["orr"] - hist_ctrl["orr"]
    nnt = round(1 / max(abs(ard), 0.001), 1) if ard > 0 else None

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "indication": indication,
        "experimental": {"arm": experimental, "regimen": hist_exp.get("regimen", ""), "source": hist_exp.get("source", "")},
        "comparator": {"arm": comparator, "regimen": hist_ctrl.get("regimen", ""), "source": hist_ctrl.get("source", "")},
        "response": {
            "orr_experimental": hist_exp["orr"],
            "orr_comparator": hist_ctrl["orr"],
            "absolute_difference": round(ard, 3),
            "odds_ratio": round(odds_ratio, 2),
            "nnt": nnt,
        },
        "survival": {
            "pfs_hr": round(hr_pfs, 3) if hr_pfs else None,
            "pfs_improvement_months": round(hist_exp["median_pfs_months"] - hist_ctrl["median_pfs_months"], 1) if hist_exp["median_pfs_months"] else None,
            "os_hr": round(hr_os, 3) if hr_os else None,
            "os_improvement_months": round(hist_exp["median_os_months"] - hist_ctrl["median_os_months"], 1) if hist_exp.get("median_os_months") and hist_ctrl.get("median_os_months") else None,
        },
        "interpretation": f"{experimental} shows {'significant' if odds_ratio > 2 else 'modest'} improvement over {comparator} with OR {odds_ratio:.1f} for ORR{' and HR ' + str(round(hr_pfs, 2)) + ' for PFS' if hr_pfs else ''}.",
    }


async def hta_evidence_package(
    indication: str = "DLBCL",
    target: str = "CD19",
    list_price_usd: int = 373000,
) -> Dict[str, Any]:
    """Generate a health technology assessment evidence package."""
    # Cost-effectiveness estimates
    median_os_gain = 13.8  # months vs SOC (typical for CD19 CAR-T in DLBCL)
    qaly_gain = round(median_os_gain / 12 * 0.75, 2)  # approximate QALY gain
    icer = round(list_price_usd / max(qaly_gain, 0.1), 0)

    return {
        "product": f"{target} CAR-T Cell Therapy",
        "indication": indication,
        "pricing": {
            "list_price_usd": list_price_usd,
            "outcomes_based_contract": f"Payment tied to response at Day 30 (refund if no CR/PR)",
            "indication_based_pricing": True,
        },
        "clinical_value": {
            "median_os_gain_months": median_os_gain,
            "estimated_qaly_gain": qaly_gain,
            "icer_per_qaly": icer,
            "willingness_to_pay_threshold": 150000,
            "cost_effective": icer <= 150000,
        },
        "value_frameworks": {
            "ICER": {
                "rating": "Low" if icer > 200000 else "Intermediate" if icer > 100000 else "High",
                "notes": f"ICER of ${icer:,.0f}/QALY {'exceeds' if icer > 150000 else 'within'} $150K/QALY threshold",
            },
            "NICE": {
                "threshold": "£30,000/QALY (with QALY modifier for end-of-life)",
                "eligible_for_eol": True,
                "notes": "Likely eligible for end-of-life modifier given short life expectancy in R/R setting",
            },
            "ASCO_value": {
                "clinical_benefit": "High (ORR improvement >50% vs SOC)",
                "toxicity": "Moderate (CRS/ICANS manageable with tocilizumab/steroids)",
                "tail_of_curve": "Potential for cure (~30% plateau on KM curve)",
            },
        },
        "budget_impact": {
            "eligible_us_patients_per_year": 3500,
            "uptake_year1_pct": 15,
            "uptake_year5_pct": 45,
            "total_budget_impact_year1": round(list_price_usd * 3500 * 0.15 / 1e6, 1),
            "total_budget_impact_year5": round(list_price_usd * 3500 * 0.45 / 1e6, 1),
        },
    }
