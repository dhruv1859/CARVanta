<p align="center">
  <img src="https://img.shields.io/badge/CARVanta-AI%20Immunotherapy%20Platform-10b981?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJ3aGl0ZSI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDIgMC04LTMuNTgtOC04czMuNTgtOCA4LTggOCAzLjU4IDggOC0zLjU4IDgtOCA4eiIvPjwvc3ZnPg==" alt="CARVanta">
</p>

<h1 align="center">🧬 CARVanta</h1>
<h3 align="center">AI-Augmented CAR-T Cell Target Viability Assessment Platform<br>+ Sentinel HYDRA Bedside Biosensor</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/XGBoost-2.0-FF6600?style=flat-square" alt="XGBoost">
  <img src="https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=flat-square&logo=scikit-learn&logoColor=white" alt="sklearn">
  <img src="https://img.shields.io/badge/License-BUSL--1.1-blue?style=flat-square" alt="License">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/KiCad-10.0-314CB0?style=flat-square&logo=kicad&logoColor=white" alt="KiCad">
  <img src="https://img.shields.io/badge/ESP32--S3-Firmware-E7352C?style=flat-square&logo=espressif&logoColor=white" alt="ESP32">
  <img src="https://img.shields.io/badge/RP2040-Firmware-A22846?style=flat-square&logo=raspberrypi&logoColor=white" alt="RP2040">
  <img src="https://img.shields.io/badge/PlatformIO-Build-FF7F00?style=flat-square&logo=platformio&logoColor=white" alt="PlatformIO">
  <img src="https://img.shields.io/badge/PCB-6_Layer_ENIG-gold?style=flat-square" alt="PCB">
</p>

<p align="center">
  <strong>117,000+ lines of code • 778 source files • 214 Python modules • 45 React pages • 50 firmware files • 6-layer medical PCB</strong>
</p>

---

## 🎯 What is CARVanta?

**CARVanta** is a closed-loop immunotherapy intelligence system — an **AI software platform** connected to a **bedside biosensor device** — that turns CAR-T cell therapy target selection from art into science.

> **The core problem:** Selecting the right antigen target is the most critical decision in CAR-T therapy design. A wrong target leads to years of wasted R&D and patient harm. CARVanta automates this decision with data-driven scoring validated against FDA-approved targets, and monitors treatment in real time to catch antigen escape before it kills.

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
| 🔬 **Sentinel HYDRA** | Real-time 4-channel antigen monitoring with bedside biosensor hardware |

---

## 🏗️ Architecture

```
Patient blood (fingerprick)
        │
        ▼
┌───────────────────────┐
│   SENTINEL HYDRA      │     Bedside device — 95×65mm, ~$79/unit
│   RP2040 + ESP32-S3   │     6-layer medical PCB, ENIG finish
│                       │
│   • 4× potentiostat   │     Sensor data
│   • SpO2 + heart rate │     ─────────────────►
│   • 11-ch spectral    │          WiFi (TLS)
│   • Impedance + temp  │
└───────────┬───────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CARVANTA CLOUD PLATFORM                    │
├─────────────────────────────────────────────────────────────┤
│                    Frontend (React + Vite)                    │
│  45 pages • Clinical Precision UI • Glassmorphism Design     │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI Backend (v5)                       │
│  28 routers • Async • CORS • Rate limiting • Audit logging   │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Scoring  │    ML    │   LLM    │ Genomics │   Validation    │
│ Engine   │ Ensemble │ Insight  │ Pipeline │   & Certify     │
│ (CVS v3) │ (RF+XGB) │(Grok/AI) │(VCF/HLA)│  (ISO 25010)   │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│              Data Layer (SQLite / PostgreSQL)                 │
│        biomarker_database.csv • 500+ scored antigens         │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
  Doctor's phone: "CD19 dropping — antigen escape risk. Switch to CD22."
```

> For a deep dive into the full system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🔬 Sentinel HYDRA — Bedside Biosensor

The **Sentinel HYDRA** is a credit-card-sized medical-grade device that continuously monitors blood biomarkers through a disposable sensor strip. It detects antigen escape — the #1 reason CAR-T fails — in **30 seconds** instead of days via lab tests.

### Hardware Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 95mm × 65mm |
| PCB Layers | **6** (signal/ground/analog/power/high-speed/bottom) |
| MCUs | **ESP32-S3** (main) + **RP2040** (sensor coprocessor) |
| Antigen Channels | **4 simultaneous** (CD19, CD22, BCMA, GPRC5D) |
| ADC | ADS1256 — **24-bit**, 8-channel, 30kSPS |
| Potentiostat | 4× LMP91000 (one per antigen channel) |
| SpO2/Heart Rate | MAX30102 integrated sensor |
| Spectral | AS7341 — **11 wavelength channels** |
| Temperature | TMP117 (±0.1°C) + MLX90614 (contactless IR) |
| IMU | LSM6DSO — 6-axis (fall detection) |
| Display | 2.4" IPS TFT (320×240, ST7789) |
| Connectivity | WiFi + BLE (ESP32-S3) |
| Data Logging | microSD + DS3231 RTC |
| Power | USB-C + LiPo battery (BQ24075 charger) |
| Surface Finish | ENIG (immersion gold) — biocompatible |
| Cost per Unit | **~$79** (complete with battery + display + sensor) |

### Manufacturing Files

Production-ready Gerber files for PCB fabrication are available:

📦 **[Sentinel_HYDRA_Gerbers.zip](hardware/sentinel/kicad/Sentinel_HYDRA/Sentinel_HYDRA_Gerbers.zip)** — Upload directly to JLCPCB / PCBWay

Contains:
- 6 copper layers (Digital_Signals, GND_Plane, Analog_Signals, Power_Planes, HighSpeed, Bottom_GND)
- Front/Back solder mask, silkscreen, paste stencil
- Board outline (Edge.Cuts)
- Excellon drill files (PTH + NPTH separated)
- Drill map files
- Gerber job file

> For the full Bill of Materials, see [BOM.md](hardware/sentinel/BOM.md).

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

### 4. Build Firmware (Optional)

Requires [PlatformIO](https://platformio.org/install):

```bash
# ESP32 main controller
cd hardware/sentinel/firmware/esp32_hydra
pio run

# RP2040 sensor coprocessor
cd hardware/sentinel/firmware/rp2040_hydra
pio run
```

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
├── api/                        # 28 FastAPI routers (v5)
│   ├── main.py                 # App entrypoint
│   ├── auth.py                 # JWT authentication
│   ├── validation_router.py    # Model validation endpoints
│   └── ...
├── scoring/                    # CVS scoring engine (v3)
├── models/                     # ML pipeline (RF + XGBoost)
├── features/                   # Feature engineering + LLM + FHIR
├── validation/                 # Model validation & certification
├── deep_learning/              # Autoencoder, attention, neural models
├── genomics/                   # Variant calling, HLA, TMB
├── digital_twin/               # Patient simulation engine
├── discovery/                  # Drug discovery, scFv design
├── copilot/                    # Research assistant, RAG engine
├── trials/                     # Clinical trial intelligence
├── frontend-react/             # React 18 + Vite + TypeScript
│   └── src/pages/              # 45 page modules
├── hardware/
│   └── sentinel/
│       ├── kicad/
│       │   └── Sentinel_HYDRA/         # 6-layer KiCad PCB project
│       │       ├── *.kicad_sch         # 7 schematic sheets
│       │       ├── Sentinel_HYDRA.kicad_pcb
│       │       ├── gerbers/            # Production Gerber files
│       │       └── Sentinel_HYDRA_Gerbers.zip
│       ├── firmware/
│       │   ├── esp32_hydra/            # ESP32-S3 firmware (50 files)
│       │   └── rp2040_hydra/           # RP2040 firmware
│       ├── BOM.md                      # Bill of materials (~$79/unit)
│       └── README.md                   # Hardware documentation
├── data/                       # Biomarker database + reports
├── ARCHITECTURE.md             # Full system architecture
├── nixpacks.toml               # Railway deployment config
├── railway.json                # Railway service config
└── requirements.txt            # Python dependencies
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

See [security.md](security.md) for vulnerability reporting and [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for HIPAA alignment.

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full system architecture (software + hardware + firmware) |
| [BOM.md](hardware/sentinel/BOM.md) | Sentinel HYDRA bill of materials |
| [ROADMAP.md](ROADMAP.md) | Product roadmap and future plans |
| [MODULES.md](MODULES.md) | Module registry and build order |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [contributing.md](contributing.md) | Contribution guidelines |
| [security.md](security.md) | Security policy |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community code of conduct |
| [MODEL_CARD.md](MODEL_CARD.md) | ML model documentation |
| [ISO_13485_ALIGNMENT.md](ISO_13485_ALIGNMENT.md) | Quality management alignment |
| [PRIVACY_POLICY.md](PRIVACY_POLICY.md) | HIPAA compliance disclosure |

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
