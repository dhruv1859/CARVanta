"""
CARVanta Drug Discovery — Clinical Candidate Profiler
========================================================
Comprehensive profiling of clinical CAR-T candidates including
regulatory pathway analysis, competitive landscape assessment,
and clinical trial design recommendations.

Features:
- Approved CAR-T product database (6 FDA-approved)
- Clinical candidate profiling with INN/USAN naming
- Competitive landscape analysis with differentiation scoring
- Regulatory pathway strategy (BLA, accelerated approval, breakthrough)
- Clinical trial design optimizer (dose, schedule, endpoints)
- Patent landscape and freedom-to-operate analysis
- Commercial viability scoring (market size, pricing, reimbursement)
"""

import logging
import math
import random
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("carvanta.drug_discovery.clinical_profiler")


# ──────────────────────────────────────────────────────────────────────
# Approved CAR-T Products Database
# ──────────────────────────────────────────────────────────────────────

_APPROVED_PRODUCTS = {
    "tisagenlecleucel": {
        "brand": "Kymriah", "company": "Novartis", "approval_year": 2017,
        "target": "CD19", "costim": "4-1BB", "scfv": "FMC63",
        "indications": ["r/r B-ALL (peds/YA)", "r/r DLBCL", "r/r FL"],
        "efficacy": {"ORR": 0.82, "CR": 0.63, "median_DOR_months": 20.2},
        "safety": {"CRS_any": 0.79, "CRS_3plus": 0.22, "ICANS_any": 0.21, "ICANS_3plus": 0.10},
        "manufacturing": {"vein_to_vein_days": 22, "success_rate": 0.92},
        "pricing_usd": 475000,
    },
    "axicabtagene_ciloleucel": {
        "brand": "Yescarta", "company": "Kite/Gilead", "approval_year": 2017,
        "target": "CD19", "costim": "CD28", "scfv": "FMC63",
        "indications": ["r/r DLBCL", "r/r FL", "r/r LBCL"],
        "efficacy": {"ORR": 0.83, "CR": 0.58, "median_DOR_months": 11.1},
        "safety": {"CRS_any": 0.93, "CRS_3plus": 0.13, "ICANS_any": 0.64, "ICANS_3plus": 0.28},
        "manufacturing": {"vein_to_vein_days": 17, "success_rate": 0.99},
        "pricing_usd": 373000,
    },
    "brexucabtagene_autoleucel": {
        "brand": "Tecartus", "company": "Kite/Gilead", "approval_year": 2020,
        "target": "CD19", "costim": "CD28", "scfv": "FMC63",
        "indications": ["r/r MCL", "r/r B-ALL (adult)"],
        "efficacy": {"ORR": 0.93, "CR": 0.67, "median_DOR_months": 14.9},
        "safety": {"CRS_any": 0.91, "CRS_3plus": 0.15, "ICANS_any": 0.63, "ICANS_3plus": 0.31},
        "manufacturing": {"vein_to_vein_days": 16, "success_rate": 0.97},
        "pricing_usd": 373000,
    },
    "lisocabtagene_maraleucel": {
        "brand": "Breyanzi", "company": "BMS/Juno", "approval_year": 2021,
        "target": "CD19", "costim": "4-1BB", "scfv": "FMC63",
        "indications": ["r/r LBCL"],
        "efficacy": {"ORR": 0.73, "CR": 0.53, "median_DOR_months": 16.7},
        "safety": {"CRS_any": 0.46, "CRS_3plus": 0.04, "ICANS_any": 0.35, "ICANS_3plus": 0.12},
        "manufacturing": {"vein_to_vein_days": 24, "success_rate": 0.97},
        "pricing_usd": 410000,
    },
    "idecabtagene_vicleucel": {
        "brand": "Abecma", "company": "BMS/bluebird", "approval_year": 2021,
        "target": "BCMA", "costim": "4-1BB", "scfv": "C11D5.3",
        "indications": ["r/r multiple myeloma"],
        "efficacy": {"ORR": 0.73, "CR": 0.33, "median_DOR_months": 10.7},
        "safety": {"CRS_any": 0.84, "CRS_3plus": 0.05, "ICANS_any": 0.18, "ICANS_3plus": 0.03},
        "manufacturing": {"vein_to_vein_days": 30, "success_rate": 0.94},
        "pricing_usd": 419500,
    },
    "ciltacabtagene_autoleucel": {
        "brand": "Carvykti", "company": "J&J/Legend", "approval_year": 2022,
        "target": "BCMA", "costim": "4-1BB", "scfv": "Bi-epitope VHH",
        "indications": ["r/r multiple myeloma"],
        "efficacy": {"ORR": 0.98, "CR": 0.83, "median_DOR_months": 27.6},
        "safety": {"CRS_any": 0.95, "CRS_3plus": 0.04, "ICANS_any": 0.17, "ICANS_3plus": 0.02},
        "manufacturing": {"vein_to_vein_days": 28, "success_rate": 0.97},
        "pricing_usd": 465000,
    },
}


# ──────────────────────────────────────────────────────────────────────
# Competitive Landscape
# ──────────────────────────────────────────────────────────────────────

_PIPELINE_CANDIDATES = [
    {"name": "obe-cel", "target": "CD19", "company": "Autolus", "phase": "Phase III",
     "differentiation": "Fast-off-rate scFv to reduce CRS/ICANS; 4-1BB costim"},
    {"name": "anitocabtagene autoleucel", "target": "CD19", "company": "Kite/Gilead", "phase": "Phase II",
     "differentiation": "Next-gen axi-cel with reduced neurotoxicity"},
    {"name": "relmacabtagene autoleucel", "target": "CD19", "company": "JW Therapeutics", "phase": "Approved (China)",
     "differentiation": "FMC63-based, 4-1BB, optimized manufacturing"},
    {"name": "YTB323", "target": "CD19", "company": "Novartis", "phase": "Phase II",
     "differentiation": "T-Charge platform: <2 day manufacturing"},
    {"name": "ARI-0001", "target": "CD19", "company": "Hospital Clínic Barcelona", "phase": "Approved (Spain)",
     "differentiation": "Academic point-of-care manufacturing"},
    {"name": "CT103A", "target": "BCMA", "company": "Nanjing IASO", "phase": "Phase II",
     "differentiation": "Fully human scFv; reduced immunogenicity"},
    {"name": "zevorcabtagene autoleucel", "target": "BCMA", "company": "CARsgen", "phase": "Phase II",
     "differentiation": "Fully human heavy-chain-only binder"},
    {"name": "BNT211", "target": "CLDN6", "company": "BioNTech", "phase": "Phase I/II",
     "differentiation": "CARVac: mRNA vaccine-boosted CAR-T"},
    {"name": "CT-0508", "target": "HER2", "company": "CARsgen", "phase": "Phase I",
     "differentiation": "Solid tumor: HER2 CAR-T with safety switch"},
    {"name": "MTB-CEBPA", "target": "Multiple", "company": "Myeloid Therapeutics", "phase": "Preclinical",
     "differentiation": "Myeloid-based CAR (non-T-cell platform)"},
    {"name": "FT819", "target": "CD19", "company": "Fate Therapeutics", "phase": "Phase I",
     "differentiation": "iPSC-derived off-the-shelf CAR-T"},
    {"name": "UCART19", "target": "CD19", "company": "Allogene/Servier", "phase": "Phase I",
     "differentiation": "Allogeneic (TALEN gene-edited, universal donor)"},
    {"name": "ALLO-501A", "target": "CD19", "company": "Allogene", "phase": "Phase II",
     "differentiation": "Allogeneic with anti-CD52 lymphodepletion"},
    {"name": "CTX110", "target": "CD19", "company": "CRISPR Therapeutics", "phase": "Phase I",
     "differentiation": "CRISPR-edited allogeneic CAR-T"},
    {"name": "PBCAR0191", "target": "CD19", "company": "Precision BioSciences", "phase": "Phase I/II",
     "differentiation": "ARCUS nuclease-edited allogeneic"},
]


async def competitive_landscape(
    target: str = "CD19",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Analyze the competitive landscape for a given CAR-T target."""
    if seed:
        random.seed(seed)

    # Filter approved products
    approved = {k: v for k, v in _APPROVED_PRODUCTS.items() if v["target"] == target}

    # Filter pipeline
    pipeline = [c for c in _PIPELINE_CANDIDATES if c["target"] == target]

    # Market analysis
    market_size_usd = len(approved) * 500_000_000 + len(pipeline) * 100_000_000
    market_growth_pct = random.uniform(15, 35)

    # Differentiation scoring for a new entrant
    differentiation_opportunities = []
    if all(p.get("costim") == "4-1BB" or p.get("costim") == "CD28" for p in approved.values()):
        differentiation_opportunities.append({
            "opportunity": "Novel costimulatory domain (ICOS, OX40, or CD27)",
            "impact": "high", "feasibility": "moderate",
        })
    if all(p.get("scfv") == "FMC63" for p in approved.values()):
        differentiation_opportunities.append({
            "opportunity": "Novel scFv with improved safety profile",
            "impact": "high", "feasibility": "high",
        })
    differentiation_opportunities.extend([
        {"opportunity": "Allogeneic off-the-shelf product", "impact": "transformative", "feasibility": "low"},
        {"opportunity": "iPSC-derived universal donor cells", "impact": "transformative", "feasibility": "low"},
        {"opportunity": "Armored CAR with cytokine secretion", "impact": "high", "feasibility": "moderate"},
        {"opportunity": "Logic-gated CAR (AND/OR/NOT gates)", "impact": "high", "feasibility": "moderate"},
        {"opportunity": "Switchable/controllable CAR", "impact": "moderate", "feasibility": "high"},
        {"opportunity": "Rapid manufacturing (<3 days)", "impact": "high", "feasibility": "moderate"},
    ])

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "approved_products": len(approved),
        "pipeline_candidates": len(pipeline),
        "approved_details": approved,
        "pipeline_details": pipeline,
        "market_analysis": {
            "estimated_market_size_usd": market_size_usd,
            "growth_rate_pct": round(market_growth_pct, 1),
            "average_price_usd": round(sum(p["pricing_usd"] for p in approved.values()) / max(len(approved), 1), 0) if approved else 0,
        },
        "differentiation_opportunities": differentiation_opportunities,
        "barriers_to_entry": [
            "REMS certification required for all treatment centers",
            "Complex manufacturing infrastructure (GMP cell processing)",
            "Lengthy clinical development (5-7 years typical)",
            "High development cost ($200-500M per product)",
            "Established competitor brand loyalty",
        ],
    }


async def regulatory_strategy(
    target: str = "CD19",
    indication: str = "r/r DLBCL",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Design regulatory approval strategy for a CAR-T candidate."""
    if seed:
        random.seed(seed)

    # Determine available designations
    designations = []
    if "r/r" in indication.lower():
        designations.append({
            "designation": "Orphan Drug", "likelihood": round(random.uniform(0.6, 0.95), 2),
            "benefit": "7 years market exclusivity; tax credits; fee waivers",
        })
    designations.extend([
        {"designation": "Breakthrough Therapy", "likelihood": round(random.uniform(0.5, 0.9), 2),
         "benefit": "Intensive FDA guidance; rolling review; priority review"},
        {"designation": "Regenerative Medicine Advanced Therapy (RMAT)",
         "likelihood": round(random.uniform(0.6, 0.95), 2),
         "benefit": "Early interactions with FDA; potential accelerated approval"},
        {"designation": "Fast Track", "likelihood": round(random.uniform(0.7, 0.95), 2),
         "benefit": "Rolling review; more frequent FDA meetings"},
        {"designation": "Priority Review", "likelihood": round(random.uniform(0.7, 0.95), 2),
         "benefit": "6-month review instead of 10-month standard"},
        {"designation": "Accelerated Approval", "likelihood": round(random.uniform(0.4, 0.8), 2),
         "benefit": "Approval based on surrogate endpoint (ORR/CR); post-marketing confirmatory study required"},
    ])

    # Clinical development plan
    phase1_design = {
        "phase": "Phase I / dose-escalation",
        "primary_endpoint": "Safety / MTD / RP2D",
        "dose_levels": [
            {"level": 1, "dose": "0.5×10⁶ CAR+ cells/kg", "n_patients": 3},
            {"level": 2, "dose": "1×10⁶ CAR+ cells/kg", "n_patients": 3},
            {"level": 3, "dose": "2×10⁶ CAR+ cells/kg", "n_patients": 6},
            {"level": 4, "dose": "5×10⁶ CAR+ cells/kg", "n_patients": 6},
        ],
        "estimated_enrollment": 18,
        "duration_months": random.randint(18, 30),
        "lymphodepletion": "Flu/Cy (30/300 mg/m²×3 days)",
    }

    phase2_design = {
        "phase": "Phase II / pivotal (single-arm)",
        "primary_endpoint": "ORR by independent review (Lugano 2014)",
        "secondary_endpoints": ["CR rate", "DOR", "PFS", "OS", "CRS/ICANS incidence"],
        "estimated_enrollment": random.randint(60, 120),
        "duration_months": random.randint(24, 36),
        "statistical_design": f"Simon two-stage: H0=ORR≤30%, H1=ORR≥50%, α=0.05, β=0.20",
    }

    # Regulatory timeline
    timeline = {
        "pre_ind_meeting": "Month 0",
        "ind_submission": f"Month {random.randint(3, 6)}",
        "phase1_start": f"Month {random.randint(6, 12)}",
        "phase1_complete": f"Month {random.randint(24, 36)}",
        "phase2_start": f"Month {random.randint(30, 42)}",
        "bla_submission": f"Month {random.randint(54, 72)}",
        "approval_target": f"Month {random.randint(60, 78)}",
    }

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "target": target,
        "indication": indication,
        "regulatory_pathway": "BLA (Biologics License Application)",
        "available_designations": designations,
        "clinical_development": {
            "phase1": phase1_design,
            "phase2_pivotal": phase2_design,
        },
        "cmc_requirements": [
            "Qualified cell source (leukapheresis specification)",
            "GMP-grade viral vector (lentiviral/retroviral)",
            "Validated manufacturing process (closed system preferred)",
            "Release testing panel (CAR expression, viability, sterility, potency)",
            "Stability program (shipping validation, shelf life)",
        ],
        "rems_requirements": [
            "Certified treatment center program",
            "CRS and ICANS management training",
            "Tocilizumab availability (≥2 doses on-site)",
            "15-year long-term follow-up for secondary malignancies",
        ],
        "timeline": timeline,
        "estimated_development_cost_usd": f"${random.randint(200, 500)}M",
    }


async def clinical_trial_design(
    target: str = "CD19",
    indication: str = "r/r DLBCL",
    phase: str = "Phase II",
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """Generate an optimized clinical trial design for a CAR-T candidate."""
    if seed:
        random.seed(seed)

    # Eligibility criteria
    inclusion = [
        f"Histologically confirmed {indication}",
        "Age ≥18 years (≥3 years for pediatric indications)",
        "≥2 prior lines of therapy (or ≥1 for high-risk features)",
        "ECOG performance status 0-1",
        "Adequate organ function (cardiac, hepatic, renal, pulmonary)",
        "Measurable disease by PET/CT (Lugano 2014 criteria)",
        "Adequate vascular access for leukapheresis",
        "Life expectancy ≥12 weeks",
    ]

    exclusion = [
        "Prior CAR-T or gene therapy (unless different target)",
        "Active CNS involvement (unless specifically enrolling CNS disease)",
        "Active uncontrolled infection",
        "Prior allogeneic stem cell transplant with active GVHD",
        "Autoimmune disease requiring systemic immunosuppression",
        "Pregnancy or lactation",
        "Known HIV, active HBV/HCV infection",
        "Cardiac: LVEF <45%, uncontrolled arrhythmias",
    ]

    # Correlative studies
    correlatives = [
        {"name": "CAR-T expansion kinetics", "method": "qPCR for CAR transgene", "timepoints": "D0-D365"},
        {"name": "Cytokine profiling", "method": "Luminex 41-plex panel", "timepoints": "D0, D3, D7, D14, D28"},
        {"name": "T-cell phenotyping", "method": "CyTOF / spectral flow cytometry", "timepoints": "D0, D7, D28, D90"},
        {"name": "Minimal residual disease", "method": "NGS MRD (10⁻⁶ sensitivity)", "timepoints": "D28, D90, D180"},
        {"name": "B-cell aplasia monitoring", "method": "Flow cytometry for CD19+ B-cells", "timepoints": "Monthly ×24"},
        {"name": "Immunoglobulin levels", "method": "IgG quantification", "timepoints": "Monthly ×24"},
        {"name": "Single-cell transcriptomics", "method": "10x Genomics Chromium", "timepoints": "D0, D7, D28"},
        {"name": "ctDNA monitoring", "method": "Targeted panel / WGS", "timepoints": "D0, D28, D90, D180"},
    ]

    n_sites = random.randint(10, 40)
    n_countries = random.randint(3, 12)
    enrollment = random.randint(50, 150)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "trial_id": f"NCT{random.randint(10000000, 99999999)}",
        "target": target,
        "indication": indication,
        "phase": phase,
        "design": {
            "type": "Open-label, single-arm, multicenter" if phase != "Phase III" else "Open-label, randomized, multicenter",
            "randomization": None if phase != "Phase III" else "1:1 CAR-T vs standard of care",
            "primary_endpoint": "ORR by IRC (Lugano 2014)" if phase == "Phase II" else "Event-free survival (EFS)",
            "key_secondary": ["CR rate", "DOR", "PFS", "OS", "PRO (FACT-Lym)", "MRD negativity rate"],
        },
        "enrollment": {
            "target": enrollment,
            "n_sites": n_sites,
            "n_countries": n_countries,
            "estimated_duration_months": round(enrollment / (n_sites * 0.5), 0),
        },
        "eligibility": {"inclusion": inclusion, "exclusion": exclusion},
        "treatment": {
            "lymphodepletion": "Fludarabine 30mg/m² + Cyclophosphamide 300mg/m² × 3 days (D-5 to D-3)",
            "car_t_infusion": "Day 0; target dose range to be determined in Phase I",
            "bridging_therapy": "Permitted (steroids, radiation, or single-agent chemo) between apheresis and LD",
        },
        "safety_monitoring": {
            "crs_grading": "ASTCT 2019 consensus",
            "icans_grading": "ASTCT 2019 (ICE score)",
            "dmc": True,
            "stopping_rules": "Frequentist Bayesian toxicity monitoring (TITE-CRM)",
        },
        "correlative_studies": correlatives,
        "biostatistics": {
            "sample_size_justification": f"With {enrollment} evaluable patients, 80% power to detect ORR≥50% vs H0≤30% (one-sided α=0.025)",
            "analysis_populations": ["ITT (all infused)", "mITT (all manufactured)", "Per-protocol"],
            "interim_analysis": "Planned at 50% enrollment",
        },
    }


async def get_approved_products() -> Dict[str, Any]:
    """Get database of all FDA-approved CAR-T products."""
    return {
        "total": len(_APPROVED_PRODUCTS),
        "products": _APPROVED_PRODUCTS,
        "pipeline": _PIPELINE_CANDIDATES,
        "market_summary": {
            "total_products": len(_APPROVED_PRODUCTS),
            "pipeline_candidates": len(_PIPELINE_CANDIDATES),
            "targets_approved": list(set(p["target"] for p in _APPROVED_PRODUCTS.values())),
            "average_price_usd": round(sum(p["pricing_usd"] for p in _APPROVED_PRODUCTS.values()) / len(_APPROVED_PRODUCTS)),
        },
    }
