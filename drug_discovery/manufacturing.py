"""
CARVanta Drug Discovery — Manufacturing Process Simulator
=============================================================
End-to-end CAR-T manufacturing process simulation covering
apheresis, T-cell isolation, activation, viral transduction,
expansion, harvest, formulation, QC release, and logistics.

Features:
- Full 14-day manufacturing timeline modeling
- GMP process parameter optimization
- Viral vector production & titration
- In-process control (IPC) monitoring
- Quality control release panel simulation
- Batch failure mode analysis
- Cost-of-goods (COGS) estimation
- Supply chain and logistics planning
- Point-of-care vs centralized manufacturing comparison
"""

import logging
import math
import random
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.drug_discovery.manufacturing")


# ──────────────────────────────────────────────────────────────────────
# Manufacturing Process Steps
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ManufacturingStep:
    """Represents a single step in the CAR-T manufacturing process."""
    name: str
    day_start: int
    day_end: int
    critical: bool
    description: str
    success_rate: float
    cost_pct: float
    ipc_tests: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


_MANUFACTURING_STEPS = [
    ManufacturingStep(
        "Apheresis / Leukapheresis", 0, 0, True,
        "Collect peripheral blood mononuclear cells (PBMCs) from patient via apheresis. Target: ≥2×10⁹ total nucleated cells.",
        0.98, 0.05,
        ["Total nucleated cell count", "Viability (≥70%)", "CD3+ percentage"],
        ["Low lymphocyte count (prior chemo)", "Poor venous access", "Apheresis machine malfunction"],
        {"volume_liters": 10, "duration_hours": 3, "target_tnc": 2e9, "anticoagulant": "ACD-A"},
    ),
    ManufacturingStep(
        "Cryopreservation & Shipping", 0, 1, False,
        "Cryopreserve apheresis product and ship to manufacturing facility on liquid nitrogen.",
        0.99, 0.03,
        ["Post-thaw viability", "Temperature excursion log"],
        ["Temperature excursion during transit", "Cryovial breakage", "Shipping delay"],
        {"cryoprotectant": "10% DMSO", "cooling_rate": "1°C/min", "storage_temp": "-196°C"},
    ),
    ManufacturingStep(
        "T-cell Enrichment", 1, 1, True,
        "Enrich CD3+ T-cells using immunomagnetic selection (CliniMACS) or counterflow centrifugal elutriation.",
        0.96, 0.08,
        ["CD3+ purity (≥90%)", "CD3+ recovery (≥70%)", "Viability (≥85%)"],
        ["Low CD3 purity", "Column clogging (CliniMACS)", "High monocyte contamination"],
        {"method": "CliniMACS CD4/CD8 positive selection", "target_purity": 0.90},
    ),
    ManufacturingStep(
        "T-cell Activation", 1, 3, True,
        "Activate T-cells with anti-CD3/CD28 beads (Dynabeads) or TransAct reagent. Triggers proliferation and cytokine production.",
        0.97, 0.06,
        ["Blast formation (microscopy)", "Size increase (>12µm)", "IL-2 production"],
        ["Poor activation (exhausted T-cells)", "Non-specific activation", "Reagent lot failure"],
        {"reagent": "TransAct (Miltenyi)", "bead_ratio": "1:1", "il2_concentration": "100 IU/mL"},
    ),
    ManufacturingStep(
        "Lentiviral Transduction", 3, 4, True,
        "Transduce activated T-cells with lentiviral vector encoding the CAR construct. MOI 5-20.",
        0.92, 0.25,
        ["Transduction efficiency (≥20% CAR+)", "Vector copy number (VCN ≤5)", "RCL testing"],
        ["Low transduction efficiency", "High VCN (insertional mutagenesis risk)", "Mycoplasma contamination", "RCL-positive batch (rare, catastrophic)"],
        {"vector_type": "3rd-gen SIN lentivirus", "moi": 10, "polybrene": "8 µg/mL", "spinoculation": True},
    ),
    ManufacturingStep(
        "CAR-T Expansion", 4, 10, True,
        "Expand transduced T-cells in GMP bioreactor (G-Rex, WAVE, or Prodigy). Target: ≥10⁸ CAR+ cells.",
        0.94, 0.20,
        ["Daily cell count", "Viability (≥70%)", "CAR+ percentage (flow cytometry)", "Phenotype (CD4:CD8 ratio)"],
        ["Insufficient expansion", "Loss of viability", "T-cell exhaustion", "Contamination"],
        {"bioreactor": "G-Rex 100M", "media": "OpTmizer + 5% CTS serum", "il2": "100 IU/mL", "target_fold_expansion": 30},
    ),
    ManufacturingStep(
        "Bead Removal", 10, 10, False,
        "Remove activation beads using DynaMag magnet. Ensure <100 beads per 3×10⁶ cells.",
        0.99, 0.02,
        ["Residual bead count (<100/3×10⁶)", "Cell recovery (≥80%)"],
        ["Incomplete bead removal", "Cell loss during magnetic separation"],
        {"method": "DynaMag-50 magnet", "passes": 2},
    ),
    ManufacturingStep(
        "Harvest & Wash", 10, 11, True,
        "Harvest cells from bioreactor, wash 3x to remove serum/cytokines, and concentrate.",
        0.97, 0.05,
        ["Cell count", "Viability", "Endotoxin (<5 EU/kg)", "Residual protein"],
        ["Cell clumping", "Loss during wash steps", "Endotoxin contamination"],
        {"wash_buffer": "PlasmaLyte-A", "centrifugation": "300g × 10 min", "washes": 3},
    ),
    ManufacturingStep(
        "Formulation & Fill", 11, 11, True,
        "Formulate final product in cryopreservation medium, fill into infusion bags.",
        0.98, 0.04,
        ["Final cell count", "Final viability (≥70%)", "CAR+ percentage", "Volume accuracy"],
        ["Incorrect cell concentration", "Air bubbles in bag", "Bag integrity failure"],
        {"formulation": "CryoStor CS10", "bag_type": "CryoMACS 50mL", "fill_volume_ml": 30},
    ),
    ManufacturingStep(
        "QC Release Testing", 11, 14, True,
        "Comprehensive quality control panel. Must pass all specifications before release.",
        0.90, 0.12,
        ["Identity (CD3+CAR+)", "Purity (T-cell %)", "Potency (cytotoxicity assay)",
         "Sterility (BacT/ALERT 14-day)", "Mycoplasma (qPCR)",
         "Endotoxin (<5 EU/kg)", "VCN (<5 copies/cell)", "RCL (negative)",
         "Viability (≥70%)", "Appearance", "Dose accuracy"],
        ["Sterility failure", "Potency below spec", "VCN above limit",
         "Mycoplasma positive", "Viability below spec"],
        {"sterility_method": "BacT/ALERT", "potency_assay": "Chromium release / xCELLigence",
         "release_criteria_days": 14, "expedited_release_available": True},
    ),
    ManufacturingStep(
        "Cryopreservation & Storage", 14, 14, False,
        "Controlled-rate freeze and transfer to vapor-phase LN2 for storage until patient is ready.",
        0.99, 0.03,
        ["Post-thaw viability (stability)", "Temperature monitoring"],
        ["Freezer malfunction", "Temperature excursion"],
        {"method": "CRF (1°C/min to -80°C, then LN2)", "storage": "Vapor-phase LN2 (-150°C)"},
    ),
    ManufacturingStep(
        "Shipping to Treatment Site", 14, 15, False,
        "Ship frozen product in validated LN2 dry shipper to certified treatment center.",
        0.99, 0.04,
        ["Temperature datalogger", "Chain of identity verification", "Chain of custody documentation"],
        ["Shipping delay", "Temperature excursion", "Wrong patient identity"],
        {"shipper": "CryoPort MVE dry shipper", "max_transit_hours": 72},
    ),
    ManufacturingStep(
        "Thaw & Infusion Preparation", 15, 15, True,
        "Thaw at bedside in 37°C water bath. Inspect, verify identity, and prepare for infusion.",
        0.99, 0.03,
        ["Post-thaw viability (≥70%)", "Patient identity verification (2-person)", "Visual inspection"],
        ["Low post-thaw viability", "Identity mismatch (wrong patient)", "Delayed infusion after thaw"],
        {"thaw_time_seconds": 120, "max_time_to_infusion_minutes": 30},
    ),
]


async def simulate_manufacturing(
    target: str = "CD19",
    car_generation: str = "2nd",
    process_type: str = "centralized",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Simulate a complete CAR-T manufacturing run with realistic
    process parameters, IPC results, and batch outcome prediction.
    """
    if seed:
        random.seed(seed)

    batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
    steps_results = []
    batch_success = True
    total_cost = 0
    base_cost = 45000  # base manufacturing cost in USD

    initial_tnc = random.gauss(2.5e9, 0.5e9)
    current_cells = max(0.5e9, initial_tnc)
    current_viability = random.gauss(95, 3)
    car_positive_pct = 0

    for step in _MANUFACTURING_STEPS:
        step_success = random.random() < step.success_rate
        step_cost = base_cost * step.cost_pct

        # Model step-specific outcomes
        if step.name == "Apheresis / Leukapheresis":
            collected_tnc = random.gauss(2.2e9, 0.6e9)
            current_cells = max(0.5e9, collected_tnc)
            current_viability = random.gauss(92, 4)
            step_data = {"collected_tnc": f"{current_cells:.2e}", "viability": round(current_viability, 1)}

        elif step.name == "T-cell Enrichment":
            cd3_purity = random.gauss(93, 4)
            recovery = random.gauss(75, 8)
            current_cells *= (recovery / 100)
            step_data = {"cd3_purity_pct": round(cd3_purity, 1), "recovery_pct": round(recovery, 1)}

        elif step.name == "T-cell Activation":
            blast_pct = random.gauss(85, 8)
            current_viability = random.gauss(90, 5)
            step_data = {"blast_formation_pct": round(blast_pct, 1), "viability": round(current_viability, 1)}

        elif step.name == "Lentiviral Transduction":
            car_positive_pct = random.gauss(42, 12)
            car_positive_pct = max(10, min(80, car_positive_pct))
            vcn = random.gauss(2.5, 1.0)
            vcn = max(0.5, min(8, vcn))
            step_data = {"car_positive_pct": round(car_positive_pct, 1), "vcn": round(vcn, 2)}
            if vcn > 5:
                step_success = False

        elif step.name == "CAR-T Expansion":
            fold_expansion = random.gauss(25, 8)
            fold_expansion = max(5, min(60, fold_expansion))
            current_cells *= fold_expansion
            current_viability = random.gauss(88, 6)
            doubling_time = random.gauss(36, 6)
            step_data = {
                "fold_expansion": round(fold_expansion, 1),
                "total_cells": f"{current_cells:.2e}",
                "car_positive_cells": f"{current_cells * car_positive_pct / 100:.2e}",
                "viability": round(current_viability, 1),
                "doubling_time_hours": round(doubling_time, 1),
            }

        elif step.name == "QC Release Testing":
            sterility = random.random() > 0.02
            mycoplasma = random.random() > 0.01
            potency_pass = random.random() > 0.05
            endotoxin = random.gauss(1.5, 0.8)
            step_data = {
                "sterility": "PASS" if sterility else "FAIL",
                "mycoplasma": "Negative" if mycoplasma else "POSITIVE",
                "potency": "PASS" if potency_pass else "FAIL",
                "endotoxin_eu_ml": round(max(0.1, endotoxin), 2),
                "viability_pct": round(current_viability, 1),
                "car_positive_pct": round(car_positive_pct, 1),
            }
            if not sterility or not mycoplasma or not potency_pass:
                step_success = False
        else:
            cell_recovery = random.gauss(90, 5) / 100
            current_cells *= cell_recovery
            step_data = {"cell_count": f"{current_cells:.2e}", "viability": round(current_viability, 1)}

        if not step_success and step.critical:
            batch_success = False

        total_cost += step_cost

        steps_results.append({
            "step": step.name,
            "day": f"D{step.day_start}" if step.day_start == step.day_end else f"D{step.day_start}-D{step.day_end}",
            "critical": step.critical,
            "success": step_success,
            "data": step_data,
            "cost_usd": round(step_cost, 0),
        })

    # Final product summary
    final_car_positive = current_cells * (car_positive_pct / 100)

    # COGS breakdown
    cogs = {
        "viral_vector": round(base_cost * 0.30, 0),
        "media_reagents": round(base_cost * 0.15, 0),
        "consumables": round(base_cost * 0.10, 0),
        "qc_testing": round(base_cost * 0.12, 0),
        "labor": round(base_cost * 0.18, 0),
        "facility": round(base_cost * 0.08, 0),
        "logistics": round(base_cost * 0.07, 0),
        "total": round(total_cost, 0),
    }

    return {
        "batch_id": batch_id,
        "target": target,
        "car_generation": car_generation,
        "process_type": process_type,
        "batch_outcome": "PASS" if batch_success else "FAIL",
        "vein_to_vein_days": _MANUFACTURING_STEPS[-1].day_end,
        "steps": steps_results,
        "final_product": {
            "total_cells": f"{current_cells:.2e}",
            "car_positive_cells": f"{final_car_positive:.2e}",
            "car_positive_pct": round(car_positive_pct, 1),
            "viability_pct": round(current_viability, 1),
            "meets_dose_spec": final_car_positive > 1e8,
        },
        "cogs": cogs,
        "steps_passed": sum(1 for s in steps_results if s["success"]),
        "steps_total": len(steps_results),
    }


async def compare_manufacturing_models(
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Compare centralized vs decentralized (point-of-care) manufacturing.
    """
    if seed:
        random.seed(seed)

    centralized = {
        "model": "Centralized Manufacturing",
        "description": "Patient cells shipped to central GMP facility, processed, and shipped back",
        "vein_to_vein_days": random.randint(20, 35),
        "success_rate_pct": round(random.gauss(92, 3), 1),
        "cogs_per_batch_usd": round(random.gauss(45000, 5000), 0),
        "scalability": "high",
        "quality_consistency": "high",
        "regulatory_burden": "single facility = single BLA supplement",
        "logistics_complexity": "high (cryochain required)",
        "geographic_reach": "global (with qualified shippers)",
        "advantages": [
            "Economies of scale", "Standardized process",
            "Single QC lab", "Easier regulatory oversight",
        ],
        "limitations": [
            "Long vein-to-vein time", "Shipping risks",
            "Patient deterioration during manufacturing",
            "High logistics cost",
        ],
    }

    decentralized = {
        "model": "Point-of-Care Manufacturing",
        "description": "Automated closed-system processing at the treatment hospital (e.g., Miltenyi Prodigy)",
        "vein_to_vein_days": random.randint(7, 14),
        "success_rate_pct": round(random.gauss(88, 5), 1),
        "cogs_per_batch_usd": round(random.gauss(55000, 8000), 0),
        "scalability": "moderate (requires device at each site)",
        "quality_consistency": "moderate (operator-dependent)",
        "regulatory_burden": "complex (each site needs compliance)",
        "logistics_complexity": "low (no shipping)",
        "geographic_reach": "limited (requires trained staff at each site)",
        "advantages": [
            "Short vein-to-vein time", "No shipping needed",
            "Fresh (non-cryopreserved) product option",
            "Lower logistics cost",
        ],
        "limitations": [
            "Higher per-batch cost", "Operator variability",
            "Each site needs GMP compliance", "Limited scale",
        ],
    }

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "comparison": [centralized, decentralized],
        "recommendation": (
            "Centralized manufacturing recommended for Phase III and commercial launch. "
            "Consider decentralized for academic/investigator-initiated trials with urgent patient need."
        ),
    }


async def viral_vector_production(
    vector_type: str = "lentiviral",
    target_titer: float = 1e8,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Simulate viral vector production for CAR-T manufacturing.
    Models transient transfection, harvest, purification, and titration.
    """
    if seed:
        random.seed(seed)

    production_steps = [
        {
            "step": "HEK293T Cell Expansion",
            "duration_days": 5,
            "details": {
                "cell_line": "HEK293T/17",
                "culture_vessel": "CellSTACK-10 or HYPERFlask",
                "seeding_density": "2×10⁴ cells/cm²",
                "harvest_density": f"{random.gauss(1.5, 0.3):.1f}×10⁵ cells/cm²",
                "media": "DMEM + 10% FBS",
            },
        },
        {
            "step": "Transient Transfection",
            "duration_days": 1,
            "details": {
                "method": "PEI (polyethylenimine) or lipofection",
                "plasmids": {
                    "transfer": "pCCL-CAR (encodes CAR transgene)",
                    "packaging": "psPAX2 (Gag-Pol)",
                    "envelope": "pMD2.G (VSV-G)",
                    "rev": "pRSV-Rev",
                },
                "dna_ratio": "Transfer:Packaging:Envelope:Rev = 4:3:1.5:1.5",
                "transfection_efficiency": f"{random.gauss(85, 8):.0f}%",
            },
        },
        {
            "step": "Vector Harvest",
            "duration_days": 2,
            "details": {
                "harvest_timepoints": ["48h post-transfection", "72h post-transfection"],
                "crude_titer": f"{random.gauss(5e6, 2e6):.2e} TU/mL",
                "volume_liters": round(random.gauss(10, 3), 1),
            },
        },
        {
            "step": "Clarification & Filtration",
            "duration_days": 1,
            "details": {
                "method": "0.45µm filtration + Benzonase treatment",
                "recovery_pct": round(random.gauss(85, 5), 1),
            },
        },
        {
            "step": "Ultracentrifugation / TFF",
            "duration_days": 1,
            "details": {
                "method": "Tangential flow filtration (100kDa MWCO) or ultracentrifugation (25,000g × 2h)",
                "concentration_factor": round(random.gauss(100, 20), 0),
                "recovery_pct": round(random.gauss(70, 10), 1),
            },
        },
        {
            "step": "Titration & QC",
            "duration_days": 3,
            "details": {
                "titration_methods": ["p24 ELISA", "qPCR (functional titer)", "Flow cytometry (transducing units)"],
                "final_titer": f"{random.gauss(target_titer, target_titer * 0.2):.2e} TU/mL",
                "sterility": "PASS",
                "endotoxin": f"{random.gauss(0.5, 0.2):.2f} EU/mL",
                "rcl_testing": "Negative",
            },
        },
    ]

    total_days = sum(s["duration_days"] for s in production_steps)
    vector_cost = round(random.gauss(15000, 3000), 0)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "vector_type": vector_type,
        "target_titer_tu_ml": f"{target_titer:.0e}",
        "production_days": total_days,
        "steps": production_steps,
        "cost_usd": vector_cost,
        "shelf_life_months": random.randint(12, 24),
        "storage": "-80°C (single-use aliquots)",
    }


async def batch_failure_analysis(
    n_batches: int = 100,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Monte Carlo simulation of batch outcomes to identify
    failure modes and process robustness.
    """
    if seed:
        random.seed(seed)

    results = {"pass": 0, "fail": 0, "failure_reasons": {}}
    batch_details = []

    for i in range(n_batches):
        batch_pass = True
        failures = []

        for step in _MANUFACTURING_STEPS:
            if random.random() > step.success_rate and step.critical:
                batch_pass = False
                failure = random.choice(step.failure_modes) if step.failure_modes else step.name
                failures.append({"step": step.name, "failure": failure})

        if batch_pass:
            results["pass"] += 1
        else:
            results["fail"] += 1
            for f in failures:
                key = f"{f['step']}: {f['failure']}"
                results["failure_reasons"][key] = results["failure_reasons"].get(key, 0) + 1

        if i < 20:
            batch_details.append({
                "batch": i + 1,
                "outcome": "PASS" if batch_pass else "FAIL",
                "failures": failures,
            })

    # Sort failure reasons by frequency
    sorted_failures = sorted(results["failure_reasons"].items(), key=lambda x: x[1], reverse=True)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "n_batches": n_batches,
        "pass": results["pass"],
        "fail": results["fail"],
        "success_rate_pct": round(results["pass"] / n_batches * 100, 1),
        "top_failure_modes": [{"reason": k, "count": v, "frequency_pct": round(v / n_batches * 100, 1)} for k, v in sorted_failures[:10]],
        "batch_details": batch_details,
        "process_robustness": "robust" if results["pass"] / n_batches > 0.85 else "needs improvement",
    }
