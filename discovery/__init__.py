"""
CARVanta Discovery — AI-Powered Drug Discovery Engine
=======================================================
Package initializer exposing all discovery sub-engines:
proteome scanning, graph neural networks, novelty detection,
toxicity prediction, scFv design, and CAR construct architecture.

API Version: v5
"""

# ─── Proteome Scanner ───
from discovery.proteome_scanner import (
    scan_full_proteome,
    score_surface_antigen_potential,
    rank_proteome_targets,
    ProteomeScanResult,
)

# ─── Graph Neural Network ───
from discovery.graph_nn import (
    build_protein_interaction_graph,
    run_gnn_inference,
    predict_target_interactions,
    GNNPrediction,
)

# ─── Novelty Detector ───
from discovery.novelty_detector import (
    detect_novel_targets,
    compute_novelty_score,
    compare_to_clinical_landscape,
    NovelTargetResult,
)

# ─── Toxicity Predictor ───
from discovery.toxicity_predictor import (
    predict_off_target_toxicity,
    compute_tissue_expression_risk,
    generate_safety_profile,
    ToxicityProfile,
)

# ─── scFv Designer ───
from discovery.scfv_designer import (
    design_scfv_candidates,
    optimize_binding_affinity,
    predict_developability,
    ScFvCandidate,
)

# ─── CAR Architect ───
from discovery.car_architect import (
    design_car_construct,
    evaluate_construct_fitness,
    compare_car_generations,
    CARConstruct,
)

__all__ = [
    # Proteome
    "scan_full_proteome", "score_surface_antigen_potential",
    "rank_proteome_targets", "ProteomeScanResult",
    # GNN
    "build_protein_interaction_graph", "run_gnn_inference",
    "predict_target_interactions", "GNNPrediction",
    # Novelty
    "detect_novel_targets", "compute_novelty_score",
    "compare_to_clinical_landscape", "NovelTargetResult",
    # Toxicity
    "predict_off_target_toxicity", "compute_tissue_expression_risk",
    "generate_safety_profile", "ToxicityProfile",
    # scFv
    "design_scfv_candidates", "optimize_binding_affinity",
    "predict_developability", "ScFvCandidate",
    # CAR
    "design_car_construct", "evaluate_construct_fitness",
    "compare_car_generations", "CARConstruct",
]
