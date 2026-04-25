"""
CARVanta Deep Learning — LSTM Simulator for Treatment Time Series
====================================================================
Long Short-Term Memory network in pure NumPy for predicting temporal
dynamics of CAR-T therapy: T-cell expansion, tumor regression,
cytokine storms, and patient outcomes over time.

Architecture:
  - 2-layer stacked LSTM (hidden_size=32)
  - Input: 6 features per timestep
  - Output: 4 predicted variables per timestep
"""

import numpy as np
import hashlib
from typing import Dict, List, Optional

# ─── LSTM Cell ──────────────────────────────────────────────────────────────

class LSTMCell:
    """Single LSTM cell with forget, input, cell, output gates."""

    def __init__(self, input_size: int, hidden_size: int, seed: int = 42):
        self.hidden_size = hidden_size
        rng = np.random.RandomState(seed)
        n = input_size + hidden_size
        scale = np.sqrt(2.0 / n)

        # Combined gate weights [forget, input, cell, output]
        self.W = rng.randn(n, 4 * hidden_size) * scale
        self.b = np.zeros(4 * hidden_size)
        # Initialize forget gate bias to 1 (helps learning)
        self.b[0:hidden_size] = 1.0

    def forward(self, x: np.ndarray, h_prev: np.ndarray,
                c_prev: np.ndarray) -> tuple:
        """
        LSTM forward step.
        x: (input_size,)
        h_prev: (hidden_size,)
        c_prev: (hidden_size,)
        Returns: h_next, c_next
        """
        combined = np.concatenate([x, h_prev])
        gates = combined @ self.W + self.b

        hs = self.hidden_size
        f = self._sigmoid(gates[0:hs])         # Forget gate
        i = self._sigmoid(gates[hs:2*hs])       # Input gate
        g = np.tanh(gates[2*hs:3*hs])           # Cell candidate
        o = self._sigmoid(gates[3*hs:4*hs])     # Output gate

        c_next = f * c_prev + i * g
        h_next = o * np.tanh(c_next)

        return h_next, c_next

    @staticmethod
    def _sigmoid(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))


class LSTMSimulator:
    """
    2-layer stacked LSTM for time-series treatment simulation.
    Predicts: CAR-T cell count, tumor volume, cytokine levels, patient health.
    """

    INPUT_SIZE = 6    # [dose_norm, tumor_norm, age_norm, weight_norm, time_norm, antigen_expr]
    HIDDEN_SIZE = 32
    OUTPUT_SIZE = 4   # [car_t_cells, tumor_volume, cytokine_level, health_score]
    N_LAYERS = 2

    def __init__(self, seed: int = 42):
        self.seed = seed
        rng = np.random.RandomState(seed)

        # Stacked LSTM layers
        self.lstm1 = LSTMCell(self.INPUT_SIZE, self.HIDDEN_SIZE, seed)
        self.lstm2 = LSTMCell(self.HIDDEN_SIZE, self.HIDDEN_SIZE, seed + 1)

        # Output projection
        scale = np.sqrt(2.0 / self.HIDDEN_SIZE)
        self.W_out = rng.randn(self.HIDDEN_SIZE, self.OUTPUT_SIZE) * scale
        self.b_out = np.zeros(self.OUTPUT_SIZE)

    def _generate_input_sequence(self, params: Dict, days: int) -> np.ndarray:
        """Generate input features for each timestep."""
        sequence = np.zeros((days, self.INPUT_SIZE))

        dose = params.get("dose", 1e8)
        tumor = params.get("tumor_burden", 50.0)
        age = params.get("age", 55)
        weight = params.get("weight", 70.0)
        antigen_expr = params.get("antigen_expression", 0.7)

        for t in range(days):
            sequence[t] = [
                np.log10(dose + 1) / 10,          # dose_norm
                tumor / 200.0,                      # tumor_norm
                age / 100.0,                        # age_norm
                weight / 120.0,                     # weight_norm
                t / days,                           # time_norm
                antigen_expr,                       # antigen_expr
            ]
        return sequence

    def forward(self, input_sequence: np.ndarray) -> Dict:
        """Run LSTM forward on full sequence."""
        T = input_sequence.shape[0]

        # Initialize hidden states
        h1 = np.zeros(self.HIDDEN_SIZE)
        c1 = np.zeros(self.HIDDEN_SIZE)
        h2 = np.zeros(self.HIDDEN_SIZE)
        c2 = np.zeros(self.HIDDEN_SIZE)

        outputs = np.zeros((T, self.OUTPUT_SIZE))
        gate_values = {"forget": [], "input": [], "output": []}

        for t in range(T):
            x = input_sequence[t]

            # Layer 1
            h1, c1 = self.lstm1.forward(x, h1, c1)

            # Layer 2
            h2, c2 = self.lstm2.forward(h1, h2, c2)

            # Output projection
            y = h2 @ self.W_out + self.b_out
            outputs[t] = y

        # Apply activation to outputs
        car_t = np.abs(outputs[:, 0]) * 1e9      # CAR-T cell count
        tumor = np.maximum(0, 100 - np.abs(outputs[:, 1]) * 50)  # Tumor volume %
        cytokine = np.abs(outputs[:, 2]) * 500    # pg/mL
        health = 1.0 / (1.0 + np.exp(-outputs[:, 3]))  # 0-1 health score

        return {
            "car_t_cells": car_t,
            "tumor_volume_pct": tumor,
            "cytokine_level": cytokine,
            "health_score": health,
            "raw_outputs": outputs,
        }

    def simulate(self, patient_params: Dict = None, days: int = 180) -> Dict:
        """Run a full treatment simulation."""
        if patient_params is None:
            patient_params = {
                "dose": 1e8, "tumor_burden": 50.0,
                "age": 55, "weight": 70.0,
                "antigen_expression": 0.7,
            }

        input_seq = self._generate_input_sequence(patient_params, days)
        result = self.forward(input_seq)

        car_t = result["car_t_cells"]
        tumor = result["tumor_volume_pct"]
        cytokine = result["cytokine_level"]
        health = result["health_score"]

        # Sample every N days for frontend
        step = max(1, days // 90)
        time_points = list(range(0, days, step))

        # Key events
        peak_car_t_day = int(np.argmax(car_t))
        peak_cytokine_day = int(np.argmax(cytokine))
        min_tumor_day = int(np.argmin(tumor))

        # Response classification
        final_tumor = float(tumor[-1])
        if final_tumor < 10:
            response = "Complete Response (CR)"
        elif final_tumor < 50:
            response = "Partial Response (PR)"
        elif final_tumor < 80:
            response = "Stable Disease (SD)"
        else:
            response = "Progressive Disease (PD)"

        return {
            "model": "LSTM-2Layer-Stacked",
            "architecture": {
                "layers": self.N_LAYERS,
                "hidden_size": self.HIDDEN_SIZE,
                "input_features": self.INPUT_SIZE,
                "output_features": self.OUTPUT_SIZE,
                "parameters": self._count_params(),
                "sequence_length": days,
            },
            "patient_params": patient_params,
            "timeline": {
                "days": time_points,
                "car_t_cells": [round(float(car_t[t]), 0) for t in time_points],
                "tumor_volume_pct": [round(float(tumor[t]), 2) for t in time_points],
                "cytokine_level": [round(float(cytokine[t]), 1) for t in time_points],
                "health_score": [round(float(health[t]), 4) for t in time_points],
            },
            "key_events": {
                "peak_car_t": {"day": peak_car_t_day, "count": round(float(car_t[peak_car_t_day]), 0)},
                "peak_cytokine": {"day": peak_cytokine_day, "level": round(float(cytokine[peak_cytokine_day]), 1)},
                "nadir_tumor": {"day": min_tumor_day, "volume_pct": round(float(tumor[min_tumor_day]), 2)},
            },
            "outcome": {
                "response": response,
                "final_tumor_pct": round(final_tumor, 2),
                "final_health": round(float(health[-1]), 4),
                "car_t_persistence": round(float(car_t[-1]), 0),
            },
        }

    def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Compare multiple treatment scenarios."""
        results = []
        for i, scenario in enumerate(scenarios):
            params = scenario.get("params", {})
            label = scenario.get("label", f"Scenario {i+1}")
            sim = self.simulate(params, days=scenario.get("days", 180))
            results.append({
                "label": label,
                "response": sim["outcome"]["response"],
                "final_tumor": sim["outcome"]["final_tumor_pct"],
                "peak_car_t_day": sim["key_events"]["peak_car_t"]["day"],
                "final_health": sim["outcome"]["final_health"],
            })

        return {
            "model": "LSTM-2Layer-Stacked",
            "scenarios": results,
            "best_scenario": min(results, key=lambda x: x["final_tumor"])["label"],
        }

    def _count_params(self) -> int:
        total = self.lstm1.W.size + self.lstm1.b.size
        total += self.lstm2.W.size + self.lstm2.b.size
        total += self.W_out.size + self.b_out.size
        return int(total)
