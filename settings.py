"""
CARVanta – Centralized Configuration v4
==========================================
All tuneable constants, paths, hyperparameters, and API settings.

v4: Enterprise-grade — all values loaded from environment variables
    via python-dotenv. Zero hardcoded secrets.
"""

import os
from dotenv import load_dotenv

# Load .env file (no-op if not found)
load_dotenv()

# ─── Environment ───────────────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# ─── Project Paths ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
BIOMARKER_DATABASE_PATH = os.path.join(DATA_DIR, "biomarker_database.csv")
LEGACY_DATABASE_PATH = os.path.join(DATA_DIR, "antigen_database.csv")
TRAINING_REPORT_PATH = os.path.join(DATA_DIR, "training_report.json")
BENCHMARK_REPORT_PATH = os.path.join(DATA_DIR, "benchmark_report.json")
CROSS_VALIDATION_REPORT_PATH = os.path.join(DATA_DIR, "cross_validation_report.json")
REAL_DATA_REPORT_PATH = os.path.join(DATA_DIR, "real_data_report.json")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "car_t_model.pkl")

# ─── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'carvanta.db')}")

# ─── API Server Settings ───────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8001"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ─── CVS v3 Scoring Weights (8-feature Adaptive Weighted Scoring) ──────────────
# CARVanta-Original: 8-feature formula with adaptive confidence adjustment
CVS_V3_WEIGHTS = {
    "tumor_specificity":    0.25,   # TCGA tumor expression differential
    "safety":               0.20,   # GTEx normal tissue risk (inverted)
    "stability":            0.12,   # Expression consistency across samples
    "evidence":             0.10,   # Literature + clinical trial support
    "immunogenicity":       0.10,   # Immune recognition potential
    "surface_accessibility": 0.08,  # Membrane localization (UniProt/HPA)
    "tissue_risk":          0.08,   # GTEx organ-level risk heatmap
    "protein_validation":   0.07,   # HPA protein-level confirmation
}

# Legacy v2 weights (4-feature, kept for backward compatibility)
CVS_WEIGHTS = {
    "tumor_specificity": 0.4,
    "safety": 0.3,
    "stability": 0.2,
    "evidence": 0.1,
}

# ─── Composite Score Weights (ML feature engineering) ───────────────────────────
COMPOSITE_WEIGHTS = {
    "tumor_specificity": 0.25,
    "safety_margin": 0.20,
    "stability_score": 0.15,
    "literature_support": 0.10,
    "immunogenicity_score": 0.10,
    "surface_accessibility": 0.08,
    "tissue_risk_score": 0.07,
    "clinical_boost": 0.05,
}

# ─── Tier Thresholds ───────────────────────────────────────────────────────────
TIER_THRESHOLDS = {
    "Tier 1 - Highly Viable": 0.85,
    "Tier 2 - Promising": 0.70,
    "Tier 3 - Experimental": 0.55,
    # Below 0.55 → "Tier 4 - High Risk"
}

# ─── Decision Thresholds ───────────────────────────────────────────────────────
DECISION_THRESHOLDS = {
    "Recommended": 0.85,
    "Consider": 0.70,
    "Experimental": 0.55,
    # Below 0.55 → "Avoid"
}

CONFIDENCE_THRESHOLDS = {
    "High": 0.90,
    "Medium": 0.80,
    # Below 0.80 → "Low"
}

# ─── Safety Constants ──────────────────────────────────────────────────────────
MAX_NORMAL_EXPRESSION = 10.0
MIN_TUMOR_THRESHOLD = 5.0
SAFETY_RISK_EXPONENT = 1.5

# Critical organ threshold (TPM) — expression above this in heart/brain is a red flag
CRITICAL_ORGAN_TPM_THRESHOLD = 5.0
CRITICAL_ORGANS = ["Brain", "Heart", "Lung", "Liver", "Kidney"]

# ─── ML Hyperparameters ────────────────────────────────────────────────────────
RANDOM_FOREST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 12,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "class_weight": "balanced",
    "random_state": int(os.getenv("RANDOM_SEED", "42")),
    "n_jobs": -1,
}

XGBOOST_PARAMS = {
    "n_estimators": 200,
    "learning_rate": 0.1,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": int(os.getenv("RANDOM_SEED", "42")),
    "eval_metric": "logloss",
    "verbosity": 0,
}

# Cross-validation
CV_FOLDS = 5
CV_SCORING_METRICS = ["accuracy", "precision", "recall", "f1", "roc_auc"]

# ─── Feature Names (v3: must match train_pipeline.py order) ────────────────────
FEATURE_NAMES = [
    "tumor_specificity",
    "normal_expression_risk",
    "safety_margin",
    "stability_score",
    "literature_support",
    "immunogenicity_score",
    "surface_accessibility",
    "clinical_boost",
    "composite_score",
]

# ─── External Data API Endpoints ─────────────────────────────────────────────
TCGA_GDC_BASE_URL = os.getenv("TCGA_GDC_BASE_URL", "https://api.gdc.cancer.gov")
GTEX_API_BASE_URL = os.getenv("GTEX_API_BASE_URL", "https://gtexportal.org/api/v2")
HPA_API_BASE_URL = os.getenv("HPA_API_BASE_URL", "https://www.proteinatlas.org")
UNIPROT_API_BASE_URL = os.getenv("UNIPROT_API_BASE_URL", "https://rest.uniprot.org")
CLINICAL_TRIALS_API_URL = os.getenv("CLINICAL_TRIALS_API_URL", "https://clinicaltrials.gov/api/v2")

# Cache settings
CACHE_MAX_AGE_DAYS = int(os.getenv("CACHE_MAX_AGE_DAYS", "30"))
API_REQUEST_TIMEOUT = int(os.getenv("API_REQUEST_TIMEOUT", "30"))
API_RATE_LIMIT_DELAY = float(os.getenv("API_RATE_LIMIT_DELAY", "0.5"))

# ─── Rate Limiting (API) ──────────────────────────────────────────────────────
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
RATE_LIMIT_BURST_SIZE = int(os.getenv("RATE_LIMIT_BURST_SIZE", "10"))
API_KEY_HEADER = "X-CARVanta-API-Key"

# ─── GNN Configuration ────────────────────────────────────────────────────────
GNN_ENABLED = os.getenv("GNN_ENABLED", "false").lower() == "true"
GNN_HIDDEN_DIM = 64
GNN_NUM_LAYERS = 3
GNN_LEARNING_RATE = 0.001
GNN_EPOCHS = 100

# ─── NLP Query Configuration ──────────────────────────────────────────────────
NLP_MAX_RESULTS = 50
NLP_DEFAULT_TIER_FILTER = None
NLP_DEFAULT_SAFETY_FILTER = None

# ─── Biomarker Generator ──────────────────────────────────────────────────────
GENE_TARGET_COUNT = int(os.getenv("GENE_TARGET_COUNT", "16000"))
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))

# ─── PDF Report Settings ──────────────────────────────────────────────────────
PDF_REPORT_TITLE = "CARVanta Antigen Viability Report"
PDF_REPORT_SUBTITLE = "AI-Augmented Biomarker Intelligence Platform"
PDF_REPORT_FOOTER = "Generated by CARVanta — carvanta.ai"
