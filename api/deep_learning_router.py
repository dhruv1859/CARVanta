"""
CARVanta Deep Learning — API Router
=======================================
REST endpoints for all 5 deep learning models:
  1. GNN Target Discovery
  2. Protein Transformer
  3. Neural Scorer (MLP)
  4. Multi-Omics VAE
  5. LSTM Treatment Simulator
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

router = APIRouter(prefix="/api/v5/deep-learning", tags=["Deep Learning Suite"])


# ═══════════════════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════════════════

class GNNPredictRequest(BaseModel):
    top_k: int = Field(10, ge=1, le=30)

class GNNNovelTargetRequest(BaseModel):
    expression: float = Field(0.7, ge=0, le=1)
    safety: float = Field(0.6, ge=0, le=1)
    specificity: float = Field(0.7, ge=0, le=1)
    stability: float = Field(0.5, ge=0, le=1)
    immunogenicity: float = Field(0.5, ge=0, le=1)
    surface_accessibility: float = Field(0.7, ge=0, le=1)
    literature_support: float = Field(0.5, ge=0, le=1)

class TransformerAnalyzeRequest(BaseModel):
    target: str = Field("CD19", max_length=20)
    sequence: Optional[str] = Field(None, max_length=500)

class TransformerCompareRequest(BaseModel):
    targets: List[str] = Field(default=["CD19", "BCMA", "HER2", "MSLN"])

class NeuralScorerRequest(BaseModel):
    antigen: str = Field("CD19", max_length=20)

class NeuralBatchRequest(BaseModel):
    antigens: List[str] = Field(default=["CD19", "BCMA", "HER2", "MSLN", "GPC3"])

class VAEAnalyzeRequest(BaseModel):
    target: str = Field("CD19", max_length=20)
    cancer_type: str = Field("DLBCL", max_length=30)

class VAEClusterRequest(BaseModel):
    targets: List[str] = Field(default=["CD19", "CD22", "BCMA", "HER2", "MSLN",
                                         "GPC3", "DLL3", "EGFR", "PSMA", "B7H3"])
    cancer_type: str = Field("DLBCL", max_length=30)

class LSTMSimulateRequest(BaseModel):
    dose: float = Field(1e8, ge=1e6, le=1e10)
    tumor_burden: float = Field(50.0, ge=5, le=200)
    age: int = Field(55, ge=1, le=100)
    weight: float = Field(70.0, ge=20, le=200)
    antigen_expression: float = Field(0.7, ge=0, le=1)
    days: int = Field(180, ge=30, le=365)

class LSTMCompareRequest(BaseModel):
    scenarios: List[Dict[str, Any]] = Field(default=[
        {"label": "Standard Dose", "params": {"dose": 1e8, "tumor_burden": 50}},
        {"label": "High Dose", "params": {"dose": 5e8, "tumor_burden": 50}},
        {"label": "High Burden", "params": {"dose": 1e8, "tumor_burden": 120}},
    ])


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GNN Target Discovery
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/gnn/predict", summary="GNN target viability prediction")
def gnn_predict(req: GNNPredictRequest) -> Dict:
    """Run GNN message-passing to predict and rank antigen target viability."""
    from deep_learning.gnn_target_discovery import GNNTargetDiscovery
    model = GNNTargetDiscovery()
    result = model.predict_targets(top_k=req.top_k)
    _add_llm_insight(result, "gnn_target_discovery", result)
    return result

@router.post("/gnn/novel-target", summary="Predict novel target viability")
def gnn_novel_target(req: GNNNovelTargetRequest) -> Dict:
    """Predict viability of a novel antigen target using GNN."""
    from deep_learning.gnn_target_discovery import GNNTargetDiscovery
    model = GNNTargetDiscovery()
    return model.predict_novel_target(req.dict())

@router.get("/gnn/network", summary="Get protein interaction network")
def gnn_network() -> Dict:
    """Get the protein-protein interaction network for visualization."""
    from deep_learning.gnn_target_discovery import GNNTargetDiscovery
    model = GNNTargetDiscovery()
    return model.get_interaction_network()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Protein Transformer
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/transformer/analyze", summary="Analyze protein sequence")
def transformer_analyze(req: TransformerAnalyzeRequest) -> Dict:
    """Run transformer encoder on a protein sequence for viability prediction."""
    from deep_learning.protein_transformer import ProteinTransformer
    model = ProteinTransformer()
    result = model.analyze_sequence(req.target, req.sequence)
    _add_llm_insight(result, "protein_transformer", result)
    return result

@router.post("/transformer/compare", summary="Compare protein sequences")
def transformer_compare(req: TransformerCompareRequest) -> Dict:
    """Compare multiple antigen protein sequences using transformer."""
    from deep_learning.protein_transformer import ProteinTransformer
    model = ProteinTransformer()
    return model.compare_sequences(req.targets)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Neural Scorer (MLP)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/mlp/score", summary="Neural network antigen scoring")
def mlp_score(req: NeuralScorerRequest) -> Dict:
    """Score an antigen using 4-layer MLP with Monte Carlo dropout uncertainty."""
    from deep_learning.neural_scorer import NeuralScorer
    model = NeuralScorer()
    result = model.predict(req.antigen)
    _add_llm_insight(result, "neural_scorer", result)
    return result

@router.post("/mlp/batch", summary="Batch neural scoring")
def mlp_batch(req: NeuralBatchRequest) -> Dict:
    """Score and rank multiple antigens using neural network."""
    from deep_learning.neural_scorer import NeuralScorer
    model = NeuralScorer()
    return model.batch_predict(req.antigens)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Multi-Omics VAE
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/vae/analyze", summary="Multi-omics VAE analysis")
def vae_analyze(req: VAEAnalyzeRequest) -> Dict:
    """Encode multi-omics data through VAE for integration and anomaly detection."""
    from deep_learning.omics_autoencoder import OmicsAutoencoder
    model = OmicsAutoencoder()
    result = model.analyze_target(req.target, req.cancer_type)
    _add_llm_insight(result, "omics_autoencoder", result)
    return result

@router.post("/vae/cluster", summary="Cluster targets in latent space")
def vae_cluster(req: VAEClusterRequest) -> Dict:
    """Cluster antigen targets in VAE latent space."""
    from deep_learning.omics_autoencoder import OmicsAutoencoder
    model = OmicsAutoencoder()
    return model.cluster_targets(req.targets, req.cancer_type)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. LSTM Treatment Simulator
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/lstm/simulate", summary="LSTM treatment simulation")
def lstm_simulate(req: LSTMSimulateRequest) -> Dict:
    """Simulate CAR-T treatment dynamics using LSTM time-series model."""
    from deep_learning.lstm_simulator import LSTMSimulator
    model = LSTMSimulator()
    params = {
        "dose": req.dose, "tumor_burden": req.tumor_burden,
        "age": req.age, "weight": req.weight,
        "antigen_expression": req.antigen_expression,
    }
    result = model.simulate(params, days=req.days)
    _add_llm_insight(result, "lstm_simulator", result)
    return result

@router.post("/lstm/compare", summary="Compare treatment scenarios")
def lstm_compare(req: LSTMCompareRequest) -> Dict:
    """Compare multiple treatment scenarios using LSTM predictions."""
    from deep_learning.lstm_simulator import LSTMSimulator
    model = LSTMSimulator()
    return model.compare_scenarios(req.scenarios)


# ═══════════════════════════════════════════════════════════════════════════════
# Suite Overview
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status", summary="Deep learning suite status")
def dl_status() -> Dict:
    """Get status and specs of all 5 deep learning models."""
    from deep_learning.gnn_target_discovery import GNNTargetDiscovery
    from deep_learning.protein_transformer import ProteinTransformer
    from deep_learning.neural_scorer import NeuralScorer
    from deep_learning.omics_autoencoder import OmicsAutoencoder
    from deep_learning.lstm_simulator import LSTMSimulator

    gnn = GNNTargetDiscovery()
    trans = ProteinTransformer()
    mlp = NeuralScorer()
    vae = OmicsAutoencoder()
    lstm = LSTMSimulator()

    total_params = (gnn._count_params() + trans._count_params() +
                    mlp._count_params() + vae._count_params() + lstm._count_params())

    return {
        "suite": "CARVanta Deep Learning Suite",
        "implementation": "Pure NumPy (no PyTorch/TensorFlow dependency)",
        "total_parameters": total_params,
        "models": [
            {
                "name": "Graph Neural Network",
                "type": "GNN-3Layer-MessagePassing",
                "purpose": "Protein interaction network target discovery",
                "parameters": gnn._count_params(),
                "status": "active",
            },
            {
                "name": "Protein Transformer",
                "type": "TransformerEncoder-2L-4H",
                "purpose": "Amino acid sequence viability prediction",
                "parameters": trans._count_params(),
                "status": "active",
            },
            {
                "name": "Neural Scorer",
                "type": "MLP-4Layer-MCDropout",
                "purpose": "Antigen scoring with uncertainty estimation",
                "parameters": mlp._count_params(),
                "status": "active",
            },
            {
                "name": "Multi-Omics VAE",
                "type": "VariationalAutoencoder",
                "purpose": "Multi-omics integration and anomaly detection",
                "parameters": vae._count_params(),
                "status": "active",
            },
            {
                "name": "LSTM Simulator",
                "type": "LSTM-2Layer-Stacked",
                "purpose": "Time-series treatment dynamics prediction",
                "parameters": lstm._count_params(),
                "status": "active",
            },
        ],
        "total_endpoints": 12,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Insight Helper
# ═══════════════════════════════════════════════════════════════════════════════

def _add_llm_insight(result: Dict, model_name: str, data: Dict):
    """Add LLM-generated interpretation to deep learning results."""
    try:
        from features.llm_insight import call_llm, is_llm_available
        if not is_llm_available():
            return

        # Build a concise summary for the LLM
        summary = f"Deep learning model '{model_name}' produced these results:\n"
        for key in ["predictions", "outcome", "anomaly_detection", "graph_stats"]:
            if key in data:
                summary += f"  {key}: {data[key]}\n"

        prompt = f"""Interpret these CARVanta deep learning results for a researcher:

{summary}

Provide a brief (3-4 sentences) clinical interpretation of what these
deep learning predictions mean for CAR-T therapy development.
Highlight any surprising findings and suggest next steps."""

        insight = call_llm(prompt)
        if insight:
            result["ai_insight"] = insight
            result["ai_insight_source"] = "llm"
    except Exception:
        pass
