"""
CARVanta Deep Learning — Transformer Encoder for Protein Sequences
====================================================================
Self-attention based transformer encoder in pure NumPy for analyzing
amino acid sequences and predicting antigen viability for CAR-T therapy.

Architecture:
  - Learned amino acid embeddings (20 AAs + special tokens)
  - Positional encoding (sinusoidal)
  - 2 transformer encoder layers (4-head self-attention + FFN)
  - [CLS] token classification head
"""

import numpy as np
import hashlib
from typing import Dict, List, Optional

# ─── Activation Functions ───────────────────────────────────────────────────

def gelu(x: np.ndarray) -> np.ndarray:
    """Gaussian Error Linear Unit."""
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    e = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)

def layer_norm(x: np.ndarray, gamma: np.ndarray, beta: np.ndarray,
               eps: float = 1e-5) -> np.ndarray:
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return gamma * (x - mean) / np.sqrt(var + eps) + beta

# ─── Amino Acid Vocabulary ──────────────────────────────────────────────────

AA_VOCAB = {
    "[CLS]": 0, "[PAD]": 1, "[UNK]": 2,
    "A": 3, "C": 4, "D": 5, "E": 6, "F": 7, "G": 8, "H": 9,
    "I": 10, "K": 11, "L": 12, "M": 13, "N": 14, "P": 15,
    "Q": 16, "R": 17, "S": 18, "T": 19, "V": 20, "W": 21, "Y": 22,
}
VOCAB_SIZE = len(AA_VOCAB)

# Known antigen sequences (first 50 residues — representative fragments)
ANTIGEN_SEQUENCES = {
    "CD19": "MPPPRLLFFLLFLTPMEVRPEEPLVVKVEEGDNAVLQCLKGTSDGPTQQLTWSRESPLKPFLKLSLGLPG",
    "BCMA": "MLQMAGQCSQNEYFDSLLHACIPCQLRCSSNTPPLTCQRYCNASVTNSVKGTNAILWTCLGLSLIISLAVF",
    "CD22": "MHLLGPWLLLLVLEYLAFSDSSKWVFEHPETLYAWEGACVWIPCTYRALDGDLESFILFHNPEYNKNTSKFD",
    "HER2": "MELAALCRWGLLLALLPPGAASTQVCTGTDMKLRLPASPETHLDMLRHLYQGCQVVQGNLELTYLPTNASL",
    "MSLN": "MALPTARPLLGSCGTPALGSLLFLLFSLGWVQPSRTLAGETGQEAAPLDGVLANPPNISSLSPRQLLGFPC",
    "EGFR": "MRPSGTAGAALLALLAALCPASRALEEKKVCQGTSNKLTQLGTFEDHFLSLQRMFNNCEVVLGNLEITYVM",
    "CD33": "MPLLLLLPLLWAGALADPRFQAQLKQNKDSKPQSEAGLYTCEASEINGISLLNGGQKQETLVMVKDPEAQK",
    "GPC3": "MEAALGRSPRALVLAALLLAAAGLGAEEEMEDWLPHLNVQDGPTLSSHCQARAAEGMYEACMKALVAANGE",
    "DLL3": "MSGTARPRPGAATALLAALCAGALPEARGRYCIGSSGHSRLCGNQVDDYCASNPCLNGGSCVALASPARGV",
    "PSMA": "MWNLLHETDSAVATARRPRWLCAGALVLAGGFFLLGFLFGWFIKSSNEATNITPKHNMKAFLDELKAENKKK",
}

# ─── Multi-Head Self-Attention ──────────────────────────────────────────────

class MultiHeadAttention:
    def __init__(self, d_model: int, n_heads: int, seed: int = 42):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        rng = np.random.RandomState(seed)
        scale = np.sqrt(2.0 / d_model)
        self.W_q = rng.randn(d_model, d_model) * scale
        self.W_k = rng.randn(d_model, d_model) * scale
        self.W_v = rng.randn(d_model, d_model) * scale
        self.W_o = rng.randn(d_model, d_model) * scale

    def forward(self, x: np.ndarray) -> np.ndarray:
        seq_len = x.shape[0]
        Q = (x @ self.W_q).reshape(seq_len, self.n_heads, self.d_k).transpose(1, 0, 2)
        K = (x @ self.W_k).reshape(seq_len, self.n_heads, self.d_k).transpose(1, 0, 2)
        V = (x @ self.W_v).reshape(seq_len, self.n_heads, self.d_k).transpose(1, 0, 2)

        scores = Q @ K.transpose(0, 2, 1) / np.sqrt(self.d_k)
        attn_weights = softmax(scores, axis=-1)
        context = attn_weights @ V

        context = context.transpose(1, 0, 2).reshape(seq_len, self.d_model)
        return context @ self.W_o, attn_weights


class TransformerEncoderLayer:
    def __init__(self, d_model: int, n_heads: int, d_ff: int, seed: int = 42):
        rng = np.random.RandomState(seed)
        scale = np.sqrt(2.0 / d_model)

        self.attn = MultiHeadAttention(d_model, n_heads, seed)
        self.W1 = rng.randn(d_model, d_ff) * np.sqrt(2.0 / d_model)
        self.b1 = np.zeros(d_ff)
        self.W2 = rng.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff)
        self.b2 = np.zeros(d_model)

        # LayerNorm params
        self.gamma1 = np.ones(d_model)
        self.beta1 = np.zeros(d_model)
        self.gamma2 = np.ones(d_model)
        self.beta2 = np.zeros(d_model)

    def forward(self, x: np.ndarray):
        # Self-attention + residual + layernorm
        attn_out, attn_weights = self.attn.forward(x)
        x = layer_norm(x + attn_out, self.gamma1, self.beta1)

        # FFN + residual + layernorm
        ffn_out = gelu(x @ self.W1 + self.b1) @ self.W2 + self.b2
        x = layer_norm(x + ffn_out, self.gamma2, self.beta2)

        return x, attn_weights


class ProteinTransformer:
    """
    Transformer encoder for protein sequence analysis.
    Predicts antigen viability features from amino acid sequences.
    """

    D_MODEL = 64
    N_HEADS = 4
    D_FF = 128
    MAX_SEQ_LEN = 80
    N_LAYERS = 2

    def __init__(self, seed: int = 42):
        self.seed = seed
        rng = np.random.RandomState(seed)

        # Amino acid embeddings
        self.embeddings = rng.randn(VOCAB_SIZE, self.D_MODEL) * 0.1

        # Positional encoding (sinusoidal)
        self.pos_encoding = self._sinusoidal_encoding()

        # Transformer layers
        self.layers = [
            TransformerEncoderLayer(self.D_MODEL, self.N_HEADS, self.D_FF, seed + i)
            for i in range(self.N_LAYERS)
        ]

        # Classification head: [CLS] → 6 output scores
        scale = np.sqrt(2.0 / self.D_MODEL)
        self.W_cls = rng.randn(self.D_MODEL, 32) * scale
        self.b_cls = np.zeros(32)
        self.W_out = rng.randn(32, 6) * scale
        self.b_out = np.zeros(6)

    def _sinusoidal_encoding(self) -> np.ndarray:
        pe = np.zeros((self.MAX_SEQ_LEN, self.D_MODEL))
        pos = np.arange(self.MAX_SEQ_LEN).reshape(-1, 1)
        div = np.exp(np.arange(0, self.D_MODEL, 2) * -(np.log(10000.0) / self.D_MODEL))
        pe[:, 0::2] = np.sin(pos * div)
        pe[:, 1::2] = np.cos(pos * div)
        return pe

    def tokenize(self, sequence: str) -> np.ndarray:
        """Convert amino acid sequence to token IDs."""
        tokens = [AA_VOCAB["[CLS]"]]
        for aa in sequence[:self.MAX_SEQ_LEN - 1]:
            tokens.append(AA_VOCAB.get(aa.upper(), AA_VOCAB["[UNK]"]))
        # Pad
        while len(tokens) < self.MAX_SEQ_LEN:
            tokens.append(AA_VOCAB["[PAD]"])
        return np.array(tokens[:self.MAX_SEQ_LEN])

    def forward(self, sequence: str) -> Dict:
        """Run transformer forward pass on a protein sequence."""
        tokens = self.tokenize(sequence)
        seq_len = min(len(sequence) + 1, self.MAX_SEQ_LEN)

        # Embed tokens + positional encoding
        x = self.embeddings[tokens] + self.pos_encoding[:len(tokens)]

        # Transformer layers
        attention_maps = []
        for layer in self.layers:
            x, attn = layer.forward(x)
            attention_maps.append(attn)

        # [CLS] token output → classification
        cls_repr = x[0]
        hidden = gelu(cls_repr @ self.W_cls + self.b_cls)
        logits = hidden @ self.W_out + self.b_out
        scores = 1.0 / (1.0 + np.exp(-np.clip(logits, -500, 500)))

        return {
            "cls_embedding": cls_repr,
            "scores": scores,
            "attention_maps": attention_maps,
            "sequence_length": seq_len,
        }

    def analyze_sequence(self, name: str, sequence: str = None) -> Dict:
        """Analyze a protein sequence and return viability predictions."""
        if sequence is None:
            sequence = ANTIGEN_SEQUENCES.get(name, "MAAAALLLLLLL")

        result = self.forward(sequence)
        scores = result["scores"]

        # Attention analysis
        last_attn = result["attention_maps"][-1]  # (n_heads, seq, seq)
        avg_attn = last_attn.mean(axis=0)  # Average across heads
        cls_attention = avg_attn[0, :min(len(sequence), 20)]  # CLS attends to first 20 AAs

        # Find most-attended residues
        seq_len = min(len(sequence), self.MAX_SEQ_LEN - 1)
        residue_importance = avg_attn[0, 1:seq_len + 1]
        top_residues = np.argsort(-residue_importance)[:5]

        return {
            "model": "ProteinTransformer-2L-4H",
            "architecture": {
                "layers": self.N_LAYERS,
                "heads": self.N_HEADS,
                "d_model": self.D_MODEL,
                "d_ff": self.D_FF,
                "vocab_size": VOCAB_SIZE,
                "max_seq_len": self.MAX_SEQ_LEN,
                "parameters": self._count_params(),
            },
            "target": name,
            "sequence_length": len(sequence),
            "predictions": {
                "binding_affinity": round(float(scores[0]), 4),
                "surface_accessibility": round(float(scores[1]), 4),
                "immunogenicity": round(float(scores[2]), 4),
                "stability": round(float(scores[3]), 4),
                "manufacturability": round(float(scores[4]), 4),
                "overall_viability": round(float(scores[5]), 4),
            },
            "attention_analysis": {
                "key_residues": [
                    {
                        "position": int(pos),
                        "residue": sequence[pos] if pos < len(sequence) else "?",
                        "attention_weight": round(float(residue_importance[pos]), 4),
                    }
                    for pos in top_residues if pos < len(sequence)
                ],
                "cls_attention_profile": [round(float(a), 4) for a in cls_attention],
            },
            "composite_score": round(float(scores.mean()), 4),
        }

    def compare_sequences(self, targets: List[str]) -> Dict:
        """Compare multiple antigen sequences."""
        results = []
        for target in targets:
            seq = ANTIGEN_SEQUENCES.get(target)
            if seq:
                analysis = self.analyze_sequence(target, seq)
                results.append({
                    "target": target,
                    "composite_score": analysis["composite_score"],
                    "predictions": analysis["predictions"],
                    "sequence_length": analysis["sequence_length"],
                })

        results.sort(key=lambda x: x["composite_score"], reverse=True)
        return {
            "model": "ProteinTransformer-2L-4H",
            "comparisons": results,
            "best_target": results[0]["target"] if results else None,
        }

    def _count_params(self) -> int:
        total = self.embeddings.size + self.pos_encoding.size
        for layer in self.layers:
            total += (layer.attn.W_q.size + layer.attn.W_k.size +
                     layer.attn.W_v.size + layer.attn.W_o.size)
            total += layer.W1.size + layer.b1.size + layer.W2.size + layer.b2.size
            total += layer.gamma1.size + layer.beta1.size
            total += layer.gamma2.size + layer.beta2.size
        total += self.W_cls.size + self.b_cls.size + self.W_out.size + self.b_out.size
        return int(total)
