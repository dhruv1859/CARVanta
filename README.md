<p align="center">
  <img src="https://img.shields.io/badge/CARVanta-AI%20Immunotherapy%20Platform-10b981?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDIgMC04LTMuNTgtOC04czMuNTgtOCA4LTggOCAzLjU4IDggOC0zLjU4IDgtOCA4eiIvPjwvc3ZnPg==" alt="CARVanta">
</p>

<h1 align="center">🧬 CARVanta</h1>
<h3 align="center">AI-Augmented CAR-T Cell Target Viability Assessment Platform</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/XGBoost-2.0-FF6600?style=flat-square" alt="XGBoost">
  <img src="https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="sklearn">
  <img src="https://img.shields.io/badge/License-BUSL--1.1-blue?style=flat-square" alt="License">
</p>

<p align="center">
  <strong>211 Python modules • 45 React pages • 28 API routers • 500+ scored antigens</strong>
</p>

---

## 🎯 What is CARVanta?

**CARVanta** is an end-to-end AI platform for evaluating CAR-T cell therapy antigen targets. It combines an **8-feature Adaptive Weighted Scoring algorithm** with ensemble machine learning (Random Forest + XGBoost) and **LLM-powered clinical reasoning** (Grok/Groq) to rank antigen targets by clinical viability.

> **The core problem:** Selecting the right antigen target is the most critical decision in CAR-T therapy design. A wrong target leads to years of wasted R&D and patient harm. CARVanta automates this decision with data-driven scoring validated against FDA-approved targets.

### Key Capabilities

| Module | Description |
|--------|-------------|
| 🔬 **CVS Scoring Engine** | 8-feature adaptive weighted algorithm with multi-source consensus |
| 🤖 **ML Ensemble** | Random Forest + XGBoost classifier + regression ranker |
| 🧠 **LLM Integration** | Grok/Groq/Gemini/OpenAI for dynamic clinical reasoning |
| 🧬 **Genomic Profiler** | Variant calling, HLA typing, TMB calculation, neoantigen prediction |
| 🧑‍⚕️ **Digital Twin** | Patient-specific CRS/ICANS simulation with pharmacokinetic modeling |
| 📊 **Clinical Trials** | Safety monitoring, DSMB reports, RWE analysis, regulatory intelligence |
| 🔍 **NLP Search** | Natural language antigen discovery with semantic intent detection |
| 🏆 **Model Validation** | 5-fold CV, FDA ground-truth validation, ISO/IEC 25010 certification |
| 🌐 **Neural Bridge** | 3D knowledge graph visualization of antigen-disease relationships |
| 💊 **Drug Discovery** | scFv designer, toxicity prediction, CAR construct architecture |
| 📈 **Deep Learning** | Autoencoder anomaly detection, attention mechanisms, neural scoring |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                    │
│  45 pages • Clinical Precision UI • Glassmorphism Design     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend (v5)                       │
│  28 routers • Async • CORS • Rate limiting                   │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Scoring  │    ML    │   LLM    │ Genomics │   Validation    │
│ Engine   │ Ensemble │ Insight  │ Pipeline │   & Certify     │
│ (CVS v3) │ (RF+XGB) │(Grok/AI) │(VCF/HLA)│  (ISO 25010)   │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│              Data Layer (SQLite / PostgreSQL)                 │
│        biomarker_database.csv • 500+ scored antigens         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/dhruv1859/CARVanta.git
cd CARVanta

# Backend
pip install -r requirements.txt
copy .env.example .env
# Edit .env — add your XAI_API_KEY or GROQ_API_KEY for LLM features

# Frontend
cd frontend-react
npm install
```

### 2. Run Locally

```bash
# Terminal 1 — Backend
py -m uvicorn api.main:app --host 0.0.0.0 --port 8001

# Terminal 2 — Frontend
cd frontend-react
npm run dev
```

Open **http://localhost:5173** → full platform is live.

### 3. Train ML Models (Optional)

```bash
py models/train_pipeline.py
```

This runs 5-fold stratified cross-validation and trains the RF+XGBoost ensemble + regression ranker.

---

## 🧪 Scoring Algorithm

### CVS (CAR-T Viability Score) v3

CARVanta's **original** 8-feature Adaptive Weighted Scoring:

| Feature | Weight | Source |
|---------|--------|--------|
| Tumor Specificity | 25% | TCGA differential expression |
| Safety Score | 20% | GTEx normal tissue risk (inverted) |
| Stability | 12% | Expression consistency |
| Evidence | 10% | Published clinical support |
| Immunogenicity | 10% | Immune recognition potential |
| Surface Accessibility | 8% | UniProt/HPA membrane localization |
| Tissue Risk | 8% | GTEx organ-level heatmap |
| Protein Validation | 7% | HPA protein-level confirmation |

**Adaptive Weight Adjustment:** When real data sources (TCGA, GTEx, HPA) are available, feature weights dynamically shift to give more credence to features backed by real data vs. estimated values.

### ML Ensemble (v4)

The final score blends rule-based CVS with ML predictions:

```
Adaptive Score = (1 - α) × CVS + α × ML_score
```

Where `α` is dynamically adjusted based on data confidence (range: 0.20–0.40).

---

## 🏆 Model Validation & Certification

CARVanta includes a **production-grade validation suite** aligned with ISO/IEC 25010:

| Test | Method | What It Proves |
|------|--------|----------------|
| **Classifier CV** | 5-fold Stratified K-Fold | Accuracy, F1, AUC-ROC, Precision, Recall |
| **Ranker CV** | 5-fold K-Fold Regression | R², MAE, RMSE, Spearman ρ |
| **FDA Ground-Truth** | CD19, BCMA, CD22, GPRC5D | All approved targets must score Tier 1 |
| **Negative Controls** | TP53, RB1, BRCA1, PTEN, APC | Non-viable targets rejected correctly |
| **Robustness** | ±5% feature perturbation | Measures prediction stability |
| **Statistical Significance** | Paired t-test + Wilcoxon | Model vs. 3 random baselines (p < 0.01) |
| **Calibration** | Brier score + log loss | Probability reliability |

Run validation: `GET /api/v5/validation/run`

---

## 🤖 LLM Integration

CARVanta uses LLMs to generate **dynamic clinical reasoning** instead of hardcoded insights:

- **Supported Providers:** Grok (xAI) → Groq → DeepSeek → Gemini → OpenAI
- **Fallback:** If no LLM key is configured, rule-based insights are served
- **Provenance:** Every AI insight displays a badge showing `🤖 LLM Generated` or `📐 Rule-Based`

Set one key in `.env`:
```
XAI_API_KEY=your-grok-key
# or
GROQ_API_KEY=your-groq-key
```

---

## ☁️ Deploy to Railway

### One-Click Deploy

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Select `dhruv1859/CARVanta`
3. Railway auto-detects `nixpacks.toml` and builds
4. Add environment variables in Railway dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `XAI_API_KEY` | ✅ | Grok API key for LLM insights |
| `CARVANTA_ENV` | Optional | Set to `production` |
| `DATABASE_URL` | Optional | PostgreSQL URL (defaults to SQLite) |

5. Railway assigns a public URL → your API is live

### Frontend Deployment

Deploy the React frontend separately on **Vercel** or **Netlify**:

```bash
cd frontend-react
npm run build
# Upload dist/ to Vercel/Netlify
# Set VITE_API_URL to your Railway backend URL
```

---

## 📁 Project Structure

```
CARVanta/
├── api/                    # 28 FastAPI routers
│   ├── main.py             # App entrypoint (v5)
│   ├── validation_router.py# Model validation endpoints
│   ├── deep_learning_router.py
│   ├── genomics_router.py
│   └── ...
├── scoring/                # CVS scoring engine (v3)
├── models/                 # ML pipeline (RF + XGBoost)
│   ├── train_pipeline.py   # Training with 5-fold CV
│   ├── car_t_model.pkl     # Trained classifier
│   └── car_t_ranker.pkl    # Trained regression ranker
├── features/               # Feature engineering + LLM
│   ├── tumor_features.py   # TCGA/GTEx/HPA feature generation
│   └── llm_insight.py      # Multi-provider LLM integration
├── validation/             # Model validation & certification
├── deep_learning/          # Autoencoder, attention, neural models
├── genomics/               # Variant calling, HLA, TMB
├── digital_twin/           # Patient simulation engine
├── discovery/              # Drug discovery, scFv design
├── copilot/                # Research assistant, RAG engine
├── trials/                 # Clinical trial intelligence
├── frontend-react/         # React 18 + Vite + TypeScript
│   └── src/pages/          # 45 page modules
├── data/                   # Biomarker database + reports
├── nixpacks.toml           # Railway deployment config
├── railway.json            # Railway service config
└── requirements-render.txt # Cloud deployment dependencies
```

---

## 🔑 API Endpoints

### Core Scoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v5/score` | POST | Score a single antigen |
| `/api/v5/batch_score` | POST | Score multiple antigens |
| `/api/v5/rankings` | GET | Global antigen leaderboard |
| `/api/v5/nlp/query` | POST | Natural language search |

### Validation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v5/validation/run` | GET | Full validation suite |
| `/api/v5/validation/quick` | GET | Quick classifier + FDA check |
| `/api/v5/validation/fda-targets` | GET | FDA ground-truth only |
| `/api/v5/validation/certification` | GET | ISO/IEC 25010 report |

### Clinical
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v5/digital-twin/simulate` | POST | Patient simulation |
| `/api/v5/trials/clinical-trials` | GET | Trial lookup by antigen |
| `/api/v5/genomics/analyze-variants` | POST | Genomic variant analysis |

Full API docs: `http://localhost:8001/docs` (Swagger UI)

---

## 🛡️ Security & Compliance

- **ISO/IEC 25010** aligned model validation and certification
- **FDA 21 CFR Part 11** concepts for electronic records
- **GAMP 5** risk-based approach compliance framework
- **LLM Provenance** — all AI outputs labeled with origin (LLM vs Rule-Based)
- **Audit Logging** — all scoring requests logged with timestamps
- **CORS + Rate Limiting** middleware (configurable)

---

## 📄 License

Business Source License 1.1 (BUSL-1.1). See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Dhruv** — [@dhruv1859](https://github.com/dhruv1859)

---

<p align="center">
  <strong>CARVanta</strong> — Turning immunotherapy target selection from art into science.
</p>
