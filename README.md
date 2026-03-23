<div align="center">

# ◆ CARVanta

**AI-Augmented Biomarker Intelligence Platform for CAR-T Cell Target Discovery**

[![CI](https://github.com/dhruv/CARVanta/actions/workflows/ci.yml/badge.svg)](https://github.com/dhruv/CARVanta/actions/workflows/ci.yml)
[![CodeQL](https://github.com/dhruv/CARVanta/actions/workflows/codeql.yml/badge.svg)](https://github.com/dhruv/CARVanta/actions/workflows/codeql.yml)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Research_&_Education-green)](#license)
[![Biomarkers](https://img.shields.io/badge/Biomarkers-119%2C816-orange)](#data-sources)
[![Antigens](https://img.shields.io/badge/Antigens-16%2C000+-blue)](#data-sources)

*The world's first comprehensive AI platform for evaluating candidate antigens as CAR-T cell therapy targets.*

</div>

---

> **100% Original.** Every algorithm — from the CARVanta Viability Score to the Antigen Synergy Matrix to the Tissue Risk Heatmap — was designed from scratch and is unique to this platform.

## 🧬 What is CARVanta?

CARVanta combines a proprietary **CAR Viability Score (CVS)** — an 8-feature Adaptive Weighted Scoring algorithm — with ensemble ML models (Random Forest + XGBoost) trained on **69 validated CAR-T targets** and **119,816 biomarker records** sourced from real **TCGA**, **GTEx**, **UniProt**, and **ClinicalTrials.gov** data.

It transforms a months-long manual literature review into a **data-driven, explainable, and reproducible antigen-ranking pipeline** — compressing pre-clinical discovery timelines for next-generation CAR-T immunotherapies.

---

## ✨ Platform Features

| # | Module | Description |
|---|--------|-------------|
| 1 | **Single Antigen Analysis** | Deep CVS scoring with 8-feature radar chart breakdown |
| 2 | **Antigen Comparison** | Head-to-head comparison with winner determination |
| 3 | **Tissue Risk Heatmap** | Organ-level off-tumor toxicity across 15+ organ systems |
| 4 | **Multi-Target Synergy** | Combination CAR-T scoring with escape risk analysis |
| 5 | **Patient Stratification** | Subtype analysis + co-expression markers + eligibility prediction |
| 6 | **NLP Query Search** | Natural language antigen discovery engine |
| 7 | **Clinical Trials** | Phase distribution + trial intelligence per antigen |
| 8 | **Global Leaderboard** | Cancer-type filtered antigen rankings |
| 9 | **Dataset Intelligence** | Biomarker database analytics and quality metrics |
| 10 | **System Status** | API health, model info, endpoint monitoring |

---

## 🏗️ Architecture

```
CARVanta/
├── api/                           # FastAPI REST API (uvicorn)
│   ├── main.py                    # 14+ endpoints — score, rank, multi-target, etc.
│   ├── pdf_report.py              # PDF/text report generator
│   └── rate_limiter.py            # Token bucket rate limiter + API keys
├── config/
│   └── settings.py                # CVS weights, API config, ML params
├── data/
│   ├── biomarker_database.csv     # Main database (119,816 entries)
│   ├── real_data_fetcher.py       # 5-source real data API client
│   ├── build_real_database.py     # Database builder from real bio data
│   └── cache/                     # API response cache (30-day TTL)
├── features/                      # Feature engineering & novel algorithms
│   ├── tumor_features.py          # Expression features & CVS precompute
│   ├── safety_features.py         # Tissue Risk Heatmap + toxicity
│   ├── multi_target.py            # Antigen Synergy Matrix
│   ├── patient_stratification.py  # Biomarker Stratification Engine
│   ├── nlp_query.py               # NLP parser for antigen search
│   └── ai_reasoning.py            # AI insight generation
├── models/                        # ML training & inference
│   ├── train_pipeline.py          # RF + XGBoost with 5-fold CV
│   ├── gnn_module.py              # Protein Interaction Network Scorer
│   └── car_t_model.pkl            # Trained model artifact
├── scoring/                       # Viability scoring
│   ├── cvs_engine.py              # CVS Adaptive Weighted Scoring
│   └── benchmark.py               # Validation with ROC-AUC
├── frontend-react/                # React 19 + TypeScript + Vite 7
│   ├── src/
│   │   ├── pages/                 # 10 clinical dashboard modules (.tsx)
│   │   ├── components/            # Shared UI components
│   │   ├── api/client.ts          # Typed API client
│   │   └── types/api.ts           # TypeScript type definitions
│   ├── tsconfig.json              # Strict TypeScript config
│   └── vite.config.ts             # Vite + React Compiler
├── .devcontainer/                 # GitHub Codespaces (instant dev env)
├── .github/workflows/             # CI/CD + CodeQL + Release automation
├── Dockerfile                     # API container
├── Dockerfile.frontend            # Frontend container
└── docker-compose.yml             # Full-stack orchestration
```

---

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Backend
pip install -r requirements.txt
uvicorn api.main:app --port 8001

# 2. Frontend (new terminal)
cd frontend-react
npm install
npm run dev
```

- **API Dashboard**: http://127.0.0.1:8001
- **React Frontend**: http://localhost:5173
- **API Docs (Swagger)**: http://127.0.0.1:8001/docs

### Option 2: GitHub Codespaces (Zero Install)

Click **"Code" → "Codespaces" → "Create codespace on main"** — the `.devcontainer` auto-installs everything and forwards ports 8001 (API) and 5173 (Frontend).

### Option 3: Docker

```bash
docker-compose up --build
```

---

## 🧮 Scoring System

### CVS — Adaptive Weighted Scoring (8 Features)

```
CVS = 0.25 × tumor_specificity
    + 0.20 × safety_component
    + 0.12 × stability
    + 0.10 × evidence
    + 0.10 × immunogenicity
    + 0.08 × surface_accessibility
    + 0.08 × tissue_risk
    + 0.07 × protein_validation
```

Weights adapt dynamically based on data confidence. Final CVS = 60% rule-based + 40% ML ensemble (RF + XGBoost).

### Tier Classification

| Tier | CVS Range | Label | Action |
|------|-----------|-------|--------|
| 1 | ≥ 0.85 | **Highly Viable** | Advance to preclinical |
| 2 | 0.70 – 0.84 | **Promising** | Further investigation |
| 3 | 0.55 – 0.69 | **Experimental** | Exploratory research |
| 4 | < 0.55 | **High Risk** | Not recommended |

---

## 🔬 Data Sources

| Source | Type | Records |
|--------|------|---------|
| **TCGA (GDC API)** | Tumor gene expression | 11,000+ tumor samples |
| **GTEx (Portal v2)** | Normal tissue expression | 17,382 tissue samples |
| **UniProt (REST)** | Protein topology & structure | Surface accessibility |
| **ClinicalTrials.gov (v2)** | Clinical trial data | Real-time trial counts |
| **Human Protein Atlas** | Protein localization | Membrane validation |

---

## ⚡ API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Interactive HTML dashboard |
| `GET` | `/health` | System status |
| `GET` | `/antigens` | List antigens (`?search=`, `?limit=`) |
| `POST` | `/score` | Full CVS + ML evaluation |
| `GET` | `/rank` | Ranked list (`?cancer_type=`, `?top_n=`) |
| `POST` | `/batch_score` | Batch scoring |

### Advanced Modules

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/multi-target` | Antigen Synergy Matrix |
| `GET` | `/api/safety/{antigen}/toxicity` | Tissue Risk Heatmap |
| `POST` | `/api/stratify` | Patient Stratification |
| `POST` | `/api/query` | NLP Query Search |
| `GET` | `/api/clinical-trials/{antigen}` | Clinical trial intelligence |
| `GET` | `/api/dataset-intelligence` | Database analytics |

---

## 🛡️ Novel Algorithms (CARVanta-Original)

1. **CVS Adaptive Weighted Scoring** — 8-feature composite with confidence-based weight adjustment
2. **Antigen Synergy Matrix** — Multi-target CAR-T combinatorial scoring with escape risk analysis
3. **Tissue Risk Heatmap** — Organ-level off-tumor toxicity prediction across 15+ organ systems
4. **Biomarker Stratification Engine** — Patient subgroup identification via expression quartiles
5. **CARVanta Query Language** — NLP-powered natural language antigen discovery
6. **Protein Interaction Network Scorer** — PPI-aware viability adjustment

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript 5, Vite 7, React Compiler |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **ML** | scikit-learn (Random Forest), XGBoost |
| **Data** | pandas, NumPy |
| **DevOps** | Docker, GitHub Actions, Codespaces |
| **Security** | CodeQL, gitleaks, pip-audit, Dependabot |

---
