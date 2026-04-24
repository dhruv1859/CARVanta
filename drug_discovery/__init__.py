"""
CARVanta Drug Discovery Sub-Package
=====================================
Advanced computational engines for AI-powered CAR-T drug discovery.

This package provides 10 specialized engines covering the full
drug discovery pipeline from target identification to manufacturing:

Engines:
    lead_optimizer       — Multi-objective CAR construct optimization with Pareto frontiers
    clinical_profiler    — FDA-approved product database, regulatory strategy, trial design
    safety_switch        — 9 safety switch mechanisms with activation kinetics simulation
    epitope_mapper       — B-cell epitope prediction, conservation, cross-reactivity analysis
    admet_predictor      — ADMET property prediction and PK parameter estimation
    molecular_docking    — Binding affinity prediction and pose generation
    manufacturing        — End-to-end GMP manufacturing simulation with COGS analysis
    resistance           — Resistance mechanism prediction and mitigation strategy design
    pk_engine            — CAR-T pharmacokinetics, CRS/ICANS prediction, population PK

Usage:
    from drug_discovery.lead_optimizer import optimize_car_construct
    from drug_discovery.clinical_profiler import competitive_landscape
    from drug_discovery.safety_switch import design_safety_switch
    from drug_discovery.epitope_mapper import predict_epitopes
    from drug_discovery.manufacturing import simulate_manufacturing
    from drug_discovery.resistance import predict_resistance
    from drug_discovery.pk_engine import simulate_pk

API Integration:
    All engines are exposed via ``api/discovery_router.py`` under
    the ``/api/v5/discovery/`` prefix with 35+ REST endpoints.

Architecture:
    Each engine is a standalone module with async-compatible functions.
    Data is generated deterministically using seeded PRNG for reproducible
    results across API calls, enabling consistent demo and testing behavior.

    Engines use domain-specific knowledge bases (e.g., FDA-approved CAR-T
    products, safety switch mechanisms, resistance pathways) embedded as
    Python dataclasses and dictionaries for fast, zero-dependency operation.

Version: 1.0.0
"""

__version__ = "1.0.0"
__all__ = [
    "lead_optimizer",
    "clinical_profiler",
    "safety_switch",
    "epitope_mapper",
    "admet_predictor",
    "molecular_docking",
    "manufacturing",
    "resistance",
    "pk_engine",
]

# Engine metadata for introspection
ENGINE_REGISTRY = {
    "lead_optimizer": {
        "description": "Multi-objective CAR construct optimization",
        "key_functions": [
            "optimize_car_construct",
            "affinity_maturation",
            "predict_stability",
            "assess_immunogenicity",
            "design_combination_therapy",
            "validate_target",
        ],
        "domain_data": {
            "scFv_library_size": 12,
            "costimulatory_domains": 6,
            "hinge_variants": 5,
            "signaling_domains": 2,
        },
    },
    "clinical_profiler": {
        "description": "Clinical candidate profiling and regulatory strategy",
        "key_functions": [
            "competitive_landscape",
            "regulatory_strategy",
            "design_clinical_trial",
            "get_approved_products",
        ],
        "domain_data": {
            "approved_products": 6,
            "pipeline_candidates": 15,
            "regulatory_designations": 4,
        },
    },
    "safety_switch": {
        "description": "Safety switch design and activation simulation",
        "key_functions": [
            "design_safety_switch",
            "simulate_switch_activation",
            "get_all_switches",
        ],
        "domain_data": {
            "switch_mechanisms": 9,
            "switch_types": ["suicide", "reversible_pause", "conditional_activation"],
        },
    },
    "epitope_mapper": {
        "description": "Epitope prediction and cross-reactivity analysis",
        "key_functions": [
            "predict_epitopes",
            "epitope_conservation",
            "cross_reactivity_analysis",
            "epitope_binning",
        ],
        "domain_data": {
            "target_proteins": 8,
            "amino_acid_properties": 20,
        },
    },
    "manufacturing": {
        "description": "GMP manufacturing process simulation",
        "key_functions": [
            "simulate_manufacturing",
            "compare_manufacturing_models",
            "viral_vector_production",
            "batch_failure_analysis",
        ],
        "domain_data": {
            "manufacturing_steps": 13,
            "ipc_tests": 30,
            "failure_modes": 25,
        },
    },
    "resistance": {
        "description": "Resistance mechanism prediction",
        "key_functions": [
            "predict_resistance",
            "exhaustion_trajectory",
            "antigen_escape_model",
            "get_all_resistance_mechanisms",
        ],
        "domain_data": {
            "resistance_mechanisms": 15,
            "categories": ["antigen_loss", "immune_evasion", "tme", "exhaustion", "intrinsic"],
        },
    },
    "pk_engine": {
        "description": "CAR-T pharmacokinetics and toxicity prediction",
        "key_functions": [
            "simulate_pk",
            "dose_response_analysis",
            "population_pk",
        ],
        "domain_data": {
            "pk_phases": ["expansion", "contraction", "persistence"],
            "crs_grades": 4,
            "icans_grades": 4,
        },
    },
}


def get_engine_info(engine_name: str) -> dict:
    """Get metadata about a specific engine."""
    if engine_name not in ENGINE_REGISTRY:
        return {"error": f"Unknown engine: {engine_name}", "available": list(ENGINE_REGISTRY.keys())}
    return ENGINE_REGISTRY[engine_name]


def list_engines() -> list:
    """List all available drug discovery engines."""
    return [
        {"name": name, "description": info["description"]}
        for name, info in ENGINE_REGISTRY.items()
    ]
