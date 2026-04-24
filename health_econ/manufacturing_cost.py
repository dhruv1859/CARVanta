"""
CARVanta Health Economics — Manufacturing Cost Estimator
=========================================================
Models the complete cost structure of CAR-T cell therapy manufacturing,
from apheresis through final product release.

Covers:
  ▸ Per-step manufacturing cost breakdown (15 steps)
  ▸ Facility cost modelling (centralised vs decentralised)
  ▸ Personnel cost calculator (GMP specialists, QC, QA)
  ▸ Raw materials & consumables pricing
  ▸ Vein-to-vein timeline estimation
  ▸ Batch failure cost analysis
  ▸ Scale-up economics (autologous vs allogeneic)
  ▸ Technology platform comparison (viral vector vs non-viral)
  ▸ Geographic manufacturing cost differentials
  ▸ Learning-curve cost reduction modelling

Data sources: Published CART manufacturing studies (Hernandez 2022,
Lopes 2020, Ran 2020), FDA CBER guidance, ISCT White Papers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Manufacturing Step Costs (USD)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ManufacturingStep:
    name: str
    category: str       # "collection", "manufacturing", "testing", "logistics"
    base_cost: float    # USD per patient
    duration_hours: float
    failure_rate: float # 0.0–1.0
    consumables: float  # Materials cost
    labor_hours: float
    notes: str = ""

    def total_cost(self, labor_rate: float = 150.0) -> float:
        return self.base_cost + self.consumables + (self.labor_hours * labor_rate)


# Standard CAR-T manufacturing pipeline (axicabtagene / tisagenlecleucel class)
MANUFACTURING_PIPELINE: List[ManufacturingStep] = [
    ManufacturingStep(
        name="Apheresis Collection",
        category="collection",
        base_cost=3_500,
        duration_hours=4,
        failure_rate=0.02,
        consumables=1_200,
        labor_hours=8,
        notes="Leukapheresis at clinical site; requires certified operator",
    ),
    ManufacturingStep(
        name="Cryopreservation & Shipping (Outbound)",
        category="logistics",
        base_cost=2_800,
        duration_hours=24,
        failure_rate=0.01,
        consumables=800,
        labor_hours=4,
        notes="Controlled-rate freezing; chain-of-custody documentation",
    ),
    ManufacturingStep(
        name="T-Cell Enrichment & Activation",
        category="manufacturing",
        base_cost=5_200,
        duration_hours=24,
        failure_rate=0.03,
        consumables=3_500,
        labor_hours=12,
        notes="CD3/CD28 bead activation; anti-CD3/IL-2 stimulation",
    ),
    ManufacturingStep(
        name="Lentiviral Vector Production",
        category="manufacturing",
        base_cost=45_000,
        duration_hours=168,
        failure_rate=0.08,
        consumables=25_000,
        labor_hours=80,
        notes="HEK293T transient transfection; ultracentrifugation purification",
    ),
    ManufacturingStep(
        name="Transduction",
        category="manufacturing",
        base_cost=8_500,
        duration_hours=24,
        failure_rate=0.05,
        consumables=2_000,
        labor_hours=16,
        notes="MOI 5-10; retronectin-coated plates or spinoculation",
    ),
    ManufacturingStep(
        name="Ex-Vivo Expansion",
        category="manufacturing",
        base_cost=15_000,
        duration_hours=240,
        failure_rate=0.04,
        consumables=8_000,
        labor_hours=40,
        notes="7-14 day expansion in bioreactor; G-Rex or Prodigy",
    ),
    ManufacturingStep(
        name="Harvest & Concentration",
        category="manufacturing",
        base_cost=3_000,
        duration_hours=8,
        failure_rate=0.02,
        consumables=1_500,
        labor_hours=8,
        notes="Cell counting, viability check, wash steps",
    ),
    ManufacturingStep(
        name="Formulation & Fill",
        category="manufacturing",
        base_cost=4_500,
        duration_hours=4,
        failure_rate=0.01,
        consumables=2_000,
        labor_hours=8,
        notes="Cryopreservation media; controlled-rate freezing",
    ),
    ManufacturingStep(
        name="Quality Control Testing",
        category="testing",
        base_cost=18_000,
        duration_hours=168,
        failure_rate=0.03,
        consumables=5_000,
        labor_hours=60,
        notes="Sterility, mycoplasma, RCL, endotoxin, potency, identity",
    ),
    ManufacturingStep(
        name="Lot Release Testing",
        category="testing",
        base_cost=8_000,
        duration_hours=72,
        failure_rate=0.02,
        consumables=3_000,
        labor_hours=24,
        notes="Final QC battery; certificate of analysis generation",
    ),
    ManufacturingStep(
        name="Cryopreservation & Shipping (Return)",
        category="logistics",
        base_cost=5_500,
        duration_hours=48,
        failure_rate=0.01,
        consumables=1_500,
        labor_hours=6,
        notes="LN2 dry shipper; 72-hour monitoring; chain-of-identity",
    ),
    ManufacturingStep(
        name="Lymphodepletion Chemotherapy",
        category="clinical",
        base_cost=8_000,
        duration_hours=72,
        failure_rate=0.05,
        consumables=2_500,
        labor_hours=12,
        notes="Flu/Cy regimen; required 3-5 days before infusion",
    ),
    ManufacturingStep(
        name="Infusion & Monitoring",
        category="clinical",
        base_cost=12_000,
        duration_hours=24,
        failure_rate=0.01,
        consumables=800,
        labor_hours=24,
        notes="ICU bed; tocilizumab on standby for CRS",
    ),
    ManufacturingStep(
        name="Adverse Event Management (CRS/ICANS)",
        category="clinical",
        base_cost=35_000,
        duration_hours=168,
        failure_rate=0.0,
        consumables=15_000,
        labor_hours=48,
        notes="Mean cost; 30-50% patients experience Grade ≥2 CRS",
    ),
    ManufacturingStep(
        name="Post-Infusion Follow-Up (30 days)",
        category="clinical",
        base_cost=6_000,
        duration_hours=720,
        failure_rate=0.0,
        consumables=500,
        labor_hours=20,
        notes="REMS monitoring; weekly labs and assessment",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Facility Cost Models
# ═══════════════════════════════════════════════════════════════════════════════

FACILITY_MODELS = {
    "centralized_large": {
        "name": "Centralised GMP Facility (Large)",
        "annual_overhead": 12_000_000,
        "capacity_patients_year": 500,
        "cleanroom_suites": 8,
        "staff_fte": 120,
        "capex": 80_000_000,
        "amortization_years": 15,
        "regions": ["US", "EU"],
    },
    "centralized_small": {
        "name": "Centralised GMP Facility (Small)",
        "annual_overhead": 4_500_000,
        "capacity_patients_year": 150,
        "cleanroom_suites": 3,
        "staff_fte": 45,
        "capex": 25_000_000,
        "amortization_years": 15,
        "regions": ["US", "EU", "JP"],
    },
    "decentralized_pod": {
        "name": "Decentralised Point-of-Care Pod",
        "annual_overhead": 1_200_000,
        "capacity_patients_year": 50,
        "cleanroom_suites": 1,
        "staff_fte": 12,
        "capex": 5_000_000,
        "amortization_years": 10,
        "regions": ["US", "EU", "JP", "CN", "IN"],
    },
    "academic_gmp": {
        "name": "Academic GMP Core",
        "annual_overhead": 2_000_000,
        "capacity_patients_year": 30,
        "cleanroom_suites": 1,
        "staff_fte": 15,
        "capex": 8_000_000,
        "amortization_years": 20,
        "regions": ["US", "EU"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Regional Cost Factors
# ═══════════════════════════════════════════════════════════════════════════════

REGIONAL_MULTIPLIERS = {
    "US": {"labor": 1.0, "materials": 1.0, "overhead": 1.0, "regulatory": 1.0},
    "EU": {"labor": 0.85, "materials": 1.05, "overhead": 0.9, "regulatory": 1.1},
    "UK": {"labor": 0.80, "materials": 1.0, "overhead": 0.85, "regulatory": 1.05},
    "JP": {"labor": 0.90, "materials": 1.15, "overhead": 0.95, "regulatory": 1.2},
    "CN": {"labor": 0.40, "materials": 0.70, "overhead": 0.50, "regulatory": 0.8},
    "IN": {"labor": 0.25, "materials": 0.65, "overhead": 0.35, "regulatory": 0.7},
    "BR": {"labor": 0.35, "materials": 0.80, "overhead": 0.45, "regulatory": 0.75},
    "KR": {"labor": 0.65, "materials": 0.90, "overhead": 0.70, "regulatory": 1.0},
    "AU": {"labor": 0.95, "materials": 1.10, "overhead": 0.90, "regulatory": 1.0},
    "IL": {"labor": 0.75, "materials": 1.0, "overhead": 0.80, "regulatory": 0.95},
}


# ═══════════════════════════════════════════════════════════════════════════════
# Technology Platform Comparison
# ═══════════════════════════════════════════════════════════════════════════════

PLATFORMS = {
    "lentiviral": {
        "name": "Lentiviral Vector",
        "vector_cost_per_patient": 45_000,
        "transduction_efficiency": 0.40,
        "manufacturing_time_days": 12,
        "scalability": "moderate",
        "ip_landscape": "crowded",
        "safety_profile": "established",
    },
    "retroviral": {
        "name": "Retroviral Vector (γ-RV)",
        "vector_cost_per_patient": 35_000,
        "transduction_efficiency": 0.50,
        "manufacturing_time_days": 10,
        "scalability": "moderate",
        "ip_landscape": "moderate",
        "safety_profile": "established",
    },
    "aav": {
        "name": "AAV Vector",
        "vector_cost_per_patient": 55_000,
        "transduction_efficiency": 0.35,
        "manufacturing_time_days": 14,
        "scalability": "difficult",
        "ip_landscape": "crowded",
        "safety_profile": "established",
    },
    "transposon": {
        "name": "Sleeping Beauty / PiggyBac Transposon",
        "vector_cost_per_patient": 8_000,
        "transduction_efficiency": 0.25,
        "manufacturing_time_days": 14,
        "scalability": "good",
        "ip_landscape": "open",
        "safety_profile": "emerging",
    },
    "mrna_electroporation": {
        "name": "mRNA Electroporation",
        "vector_cost_per_patient": 5_000,
        "transduction_efficiency": 0.60,
        "manufacturing_time_days": 3,
        "scalability": "excellent",
        "ip_landscape": "open",
        "safety_profile": "emerging",
    },
    "crispr": {
        "name": "CRISPR/Cas9 Gene Editing",
        "vector_cost_per_patient": 12_000,
        "transduction_efficiency": 0.45,
        "manufacturing_time_days": 7,
        "scalability": "good",
        "ip_landscape": "complex",
        "safety_profile": "emerging",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Core Functions
# ═══════════════════════════════════════════════════════════════════════════════

async def estimate_manufacturing_cost(
    platform: str = "lentiviral",
    facility: str = "centralized_large",
    country: str = "US",
    include_clinical: bool = True,
) -> Dict[str, Any]:
    """
    Full manufacturing cost estimate for one CAR-T product dose.
    """
    region = REGIONAL_MULTIPLIERS.get(country, REGIONAL_MULTIPLIERS["US"])
    fac = FACILITY_MODELS.get(facility, FACILITY_MODELS["centralized_large"])
    plat = PLATFORMS.get(platform, PLATFORMS["lentiviral"])

    steps_detail = []
    total_manufacturing = 0
    total_clinical = 0
    total_testing = 0
    total_logistics = 0
    total_duration_hours = 0
    cumulative_success = 1.0

    for step in MANUFACTURING_PIPELINE:
        if not include_clinical and step.category == "clinical":
            continue

        adjusted_cost = step.total_cost() * region.get(
            "labor" if step.labor_hours > step.consumables else "materials", 1.0
        )

        # Replace vector cost for the selected platform
        if step.name == "Lentiviral Vector Production":
            adjusted_cost = plat["vector_cost_per_patient"] * region["materials"]

        cumulative_success *= (1 - step.failure_rate)

        step_info = {
            "step": step.name,
            "category": step.category,
            "cost_usd": round(adjusted_cost),
            "duration_hours": step.duration_hours,
            "failure_rate": step.failure_rate,
            "notes": step.notes,
        }
        steps_detail.append(step_info)

        if step.category == "manufacturing":
            total_manufacturing += adjusted_cost
        elif step.category == "clinical":
            total_clinical += adjusted_cost
        elif step.category == "testing":
            total_testing += adjusted_cost
        elif step.category in ("logistics", "collection"):
            total_logistics += adjusted_cost

        total_duration_hours += step.duration_hours

    # Facility overhead per patient
    overhead_per_patient = (
        fac["annual_overhead"] + fac["capex"] / fac["amortization_years"]
    ) / fac["capacity_patients_year"] * region["overhead"]

    grand_total = (
        total_manufacturing + total_clinical +
        total_testing + total_logistics + overhead_per_patient
    )

    # Failure-adjusted cost (cost per successful treatment)
    failure_adjusted = grand_total / max(cumulative_success, 0.01)

    return {
        "platform": plat["name"],
        "facility": fac["name"],
        "country": country,
        "steps": steps_detail,
        "cost_breakdown": {
            "manufacturing": round(total_manufacturing),
            "clinical": round(total_clinical),
            "testing": round(total_testing),
            "logistics": round(total_logistics),
            "facility_overhead": round(overhead_per_patient),
        },
        "total_cost_usd": round(grand_total),
        "failure_adjusted_cost_usd": round(failure_adjusted),
        "cumulative_success_rate": round(cumulative_success, 3),
        "total_duration_days": round(total_duration_hours / 24, 1),
        "vein_to_vein_days": round(total_duration_hours / 24 + 5, 0),
    }


async def compare_platforms(
    country: str = "US",
) -> Dict[str, Any]:
    """Compare manufacturing costs across all technology platforms."""
    comparisons = []
    for pid, plat in PLATFORMS.items():
        est = await estimate_manufacturing_cost(platform=pid, country=country)
        comparisons.append({
            "platform_id": pid,
            "platform_name": plat["name"],
            "total_cost_usd": est["total_cost_usd"],
            "manufacturing_time_days": plat["manufacturing_time_days"],
            "transduction_efficiency": plat["transduction_efficiency"],
            "scalability": plat["scalability"],
            "safety_profile": plat["safety_profile"],
        })

    comparisons.sort(key=lambda x: x["total_cost_usd"])
    return {"country": country, "comparisons": comparisons}


async def compare_regions(
    platform: str = "lentiviral",
) -> Dict[str, Any]:
    """Compare manufacturing costs across all regions."""
    comparisons = []
    for country in REGIONAL_MULTIPLIERS:
        est = await estimate_manufacturing_cost(platform=platform, country=country)
        comparisons.append({
            "country": country,
            "total_cost_usd": est["total_cost_usd"],
            "failure_adjusted_cost_usd": est["failure_adjusted_cost_usd"],
            "vein_to_vein_days": est["vein_to_vein_days"],
        })

    comparisons.sort(key=lambda x: x["total_cost_usd"])
    return {"platform": platform, "comparisons": comparisons}


async def learning_curve_projection(
    initial_cost: float = 373_000,
    learning_rate: float = 0.85,
    target_patients: int = 5000,
) -> Dict[str, Any]:
    """
    Wright's learning curve model for cost reduction.
    Every doubling of cumulative production reduces unit cost by (1 - learning_rate).
    """
    projections = []
    cumulative = 1
    while cumulative <= target_patients:
        doublings = math.log2(max(cumulative, 1))
        cost = initial_cost * (learning_rate ** doublings)
        projections.append({
            "cumulative_patients": cumulative,
            "unit_cost_usd": round(cost),
            "cost_reduction_pct": round((1 - cost / initial_cost) * 100, 1),
        })
        if cumulative < 10:
            cumulative += 1
        elif cumulative < 100:
            cumulative += 10
        elif cumulative < 1000:
            cumulative += 100
        else:
            cumulative += 500

    return {
        "initial_cost": initial_cost,
        "learning_rate": learning_rate,
        "projections": projections,
        "cost_at_target": projections[-1]["unit_cost_usd"] if projections else initial_cost,
        "total_reduction_pct": projections[-1]["cost_reduction_pct"] if projections else 0,
    }
