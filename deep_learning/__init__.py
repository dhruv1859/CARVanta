"""
CARVanta Deep Learning Suite
================================
Five neural network architectures implemented in pure NumPy
for lightweight deployment (no PyTorch/TensorFlow required).

Modules:
  1. GNN — Graph Neural Network for protein interaction network target discovery
  2. ProteinTransformer — Transformer encoder for amino acid sequence analysis
  3. NeuralScorer — Multi-layer perceptron for CAR-T target scoring
  4. OmicsAutoencoder — Variational autoencoder for multi-omics integration
  5. LSTMSimulator — LSTM for time-series treatment simulation
"""

from deep_learning.gnn_target_discovery import GNNTargetDiscovery
from deep_learning.protein_transformer import ProteinTransformer
from deep_learning.neural_scorer import NeuralScorer
from deep_learning.omics_autoencoder import OmicsAutoencoder
from deep_learning.lstm_simulator import LSTMSimulator

__all__ = [
    "GNNTargetDiscovery",
    "ProteinTransformer",
    "NeuralScorer",
    "OmicsAutoencoder",
    "LSTMSimulator",
]
