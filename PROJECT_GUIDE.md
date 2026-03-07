# CARVanta — Project Guide & Website Walkthrough
### *Your Complete Guide to Understanding AI-Powered CAR-T Target Discovery*

---

## What Is CARVanta?

**CARVanta** is an AI-powered platform that helps scientists find the best targets for a cutting-edge cancer treatment called **CAR-T cell therapy**.

### Wait — What Is CAR-T Therapy?

Imagine you could teach your own immune cells to hunt down and kill cancer. That's exactly what CAR-T therapy does:

1. **Doctors take immune cells** (T-cells) from a patient's blood
2. **Engineers modify them** in a lab to recognize a specific protein on cancer cells (called an **antigen**)
3. **The modified T-cells** are put back into the patient, where they seek out and destroy cancer

The big challenge? **Picking the RIGHT target (antigen)**. If you pick the wrong one:
- The T-cells might attack healthy organs (dangerous side effects)
- The cancer might not express enough of the target (treatment fails)
- The target might be unstable (cancer escapes)

**CARVanta solves this problem** using data science and machine learning to score and rank thousands of potential targets — saving researchers months of manual analysis.

---

## How It Works (The Engine Under the Hood)

CARVanta uses a **multi-layer scoring system** to evaluate each antigen:

```
┌──────────────────────────────────────────┐
│          CARVanta v4 Scoring             │
├──────────────────────────────────────────┤
│                                          │
│  Layer 1: Rule-Based CVS Score           │
│  ├─ Tumor Specificity (30%)              │
│  ├─ Safety / Normal Tissue Risk (25%)    │
│  ├─ Protein Stability (15%)              │
│  ├─ Published Research Evidence (10%)    │
│  ├─ Immunogenicity (10%)                 │
│  └─ Surface Accessibility (10%)          │
│                                          │
│  Layer 2: ML Regression Ranker           │
│  ├─ XGBoost model trained on 120K+       │
│  │   biomarker records                   │
│  └─ Predicts "Clinical Success Prob."    │
│                                          │
│  Layer 3: Adaptive Blend                 │
│  └─ 60% CVS + 40% ML = Final Score      │
│                                          │
│  Layer 4: Cancer-Context Awareness       │
│  └─ Scores change per cancer type        │
│     (CD19 scores differently for         │
│      Leukemia vs. Melanoma)              │
│                                          │
└──────────────────────────────────────────┘
```

### The Tier System

Every antigen gets sorted into one of four tiers:

| Tier | Score Range | What It Means |
|------|-----------|---------------|
| 🟢 **Tier 1** — Highly Viable | ≥ 0.85 | Ready for clinical trials. Strong evidence, safe, specific to tumors |
| 🔵 **Tier 2** — Promising | 0.70 – 0.84 | Good candidate. Some concerns but worth investigating further |
| 🟡 **Tier 3** — Experimental | 0.55 – 0.69 | Needs more research. Moderate specificity or safety concerns |
| 🔴 **Tier 4** — High Risk | < 0.55 | Not recommended. Poor specificity, high toxicity risk, weak evidence |

---

## The Data Behind It

CARVanta is powered by a database of **120,000+ biomarker records** covering:

- **16,000 unique antigens** (potential targets)
- **18 cancer types** (Leukemia, Breast Cancer, Melanoma, Glioblastoma, etc.)
- **Expression data** showing how much each protein appears on tumor cells vs. healthy cells
- **Safety metrics** — does this target also appear on your heart, brain, or lungs?
- **Clinical trial counts** — has this target already been tested in real patients?

Key antigens you'll see often (these are the stars of CAR-T research):

| Antigen | Primary Cancer | Status |
|---------|---------------|--------|
| **CD19** | Leukemia / Lymphoma | ✅ FDA-approved CAR-T products |
| **BCMA** | Multiple Myeloma | ✅ FDA-approved |
| **HER2** | Breast / Gastric Cancer | 🔬 Clinical trials |
| **GD2** | Neuroblastoma | 🔬 Clinical trials |
| **EGFR** | Lung Cancer / Glioblastoma | 🔬 Clinical trials |
| **MSLN** | Mesothelioma / Pancreatic | 🔬 Clinical trials |
| **PSMA** | Prostate Cancer | 🔬 Clinical trials |

---

## Website Walkthrough — Every Page Explained

When you open CARVanta, you'll see a **sidebar on the left** with 9 modules. Here's what each one does:

---

### 🔬 1. Single Antigen Analysis

**What it does:** Deep-dive analysis of ONE specific antigen.

**How to use it:**
1. Type an antigen name in the search box (e.g., "CD19")
2. Select the antigen from the dropdown
3. Optionally select a specific cancer type
4. Click **"Analyze"**

**What you'll see:**
- **Core Metrics** — CVS Score, Adaptive Score (v4 blend), ML Ranking, Tier
- **Score Breakdown** — A radar chart showing each scoring component
- **Safety Profile** — Risk level, safety margin, toxicity flags
- **ML Prediction** — Whether the ML model thinks this target is viable, and how confident it is
- **AI Insights** — Auto-generated interpretation of the results
- **📥 Download PDF** — Export a professional report

**Example:** Search "CD19" with "Leukemia" → You'll see a Tier 1 score (~0.92) because CD19 is the gold standard CAR-T target for blood cancers.

---

### ⚖️ 2. Antigen Comparison

**What it does:** Compare 2 or more antigens side-by-side.

**How to use it:**
1. Select multiple antigens from the dropdown
2. Choose a cancer type
3. Click **"Compare"**

**What you'll see:**
- Side-by-side score comparison
- Visual bar charts showing which antigen scores higher on each metric
- A clear winner for the selected cancer type

**Use case:** "Should I target CD19 or CD22 for B-ALL?" → Compare them head-to-head.

---

### 🧫 3. Tissue Risk Heatmap

**What it does:** Shows how much an antigen is expressed in HEALTHY organs — this predicts **side effects**.

**How to use it:**
1. Select an antigen
2. Click **"Generate Heatmap"**

**What you'll see:**
- A table of organs (Heart, Brain, Liver, Lung, Kidney, etc.)
- Each organ gets a **risk score** from negligible to critical
- **⚠️ Critical Organ Alerts** — warnings if the target is highly expressed in vital organs
- **Safety Recommendation** — overall assessment

**Why it matters:** If CD19 is highly expressed in brain tissue, targeting it could cause neurological damage. This heatmap reveals those hidden dangers.

---

### 🎯 4. Multi-Target Synergy

**What it does:** Scores multi-antigen CAR-T combinations (targeting 2-4 antigens simultaneously).

**How to use it:**
1. Select 2-4 antigens
2. Click **"Score Combination"**

**What you'll see:**
- **Synergy Score** — How well the combination works together
- **Complementarity** — Do the antigens cover each other's weaknesses?
- **Escape Risk Reduction** — Can the cancer evade by downregulating one target?
- **Coverage** — What % of cancer cells are covered?
- **Aggregate Safety** — Combined toxicity risk

**Use case:** "Is CD19 + CD22 a better dual-target than CD19 alone?" → The synergy score will show if the combination reduces antigen escape risk.

---

### 👥 5. Patient Stratification

**What it does:** Predicts how different patient subgroups would respond to a specific CAR-T therapy.

**How to use it:**
1. Enter an antigen name
2. Enter a cancer type
3. Click **"Stratify"**

**What you'll see:**
- Patient subgroups (High Responders, Moderate, Low, Non-Responders)
- Biomarker profiles for each group
- Recommended patient selection criteria

**Use case:** "Which myeloma patients would benefit most from BCMA-targeted CAR-T?" → The tool identifies high-responder patient profiles.

---

### 🔍 6. NLP Query Search

**What it does:** Search for antigens using **plain English** instead of technical parameters.

**How to use it:**
1. Type a natural language query, like:
   - *"Find safe targets for leukemia"*
   - *"Best surface antigens for glioblastoma Tier 1 only"*
   - *"Top 10 immunogenic targets for melanoma with low toxicity"*
2. Click **"Search"**

**What you'll see:**
- **Query Interpretation** — What the AI understood from your query (cancer type, safety preference, tier filter)
- **Ranked Results** — Antigens matching your criteria, ranked by adaptive score
- **Search Engine** — Whether keyword or semantic search was used

**Why it's powerful:** Instead of manually filtering through 16,000 antigens, just describe what you need in plain English.

---

### 💊 7. Clinical Trials

**What it does:** Shows clinical trial information for a specific antigen.

**How to use it:**
1. Enter an antigen name
2. Click **"Search Trials"**

**What you'll see:**
- Number of registered trials
- Trial phases (Phase I, II, III)
- Cancer types being investigated
- Trial status and sponsors

---

### 🏆 8. Global Leaderboard

**What it does:** Ranks ALL antigens globally or per cancer type using the v4 adaptive scoring.

**How to use it:**
1. Select how many targets to show (10-100)
2. **Select a cancer type** (or "All Global")
3. Click **"Load Leaderboard"**

**What you'll see:**
- Ranked list of top antigens with Score, ML prediction, and Tier
- Different cancer types show DIFFERENT #1 targets:
  - **Leukemia** → CD19 is #1
  - **Multiple Myeloma** → BCMA is #1
  - **Neuroblastoma** → GD2 is #1
  - **Melanoma** → GD2/CSPG4 are top

**This is the flagship feature** — it demonstrates that CARVanta produces genuinely cancer-specific, intelligent rankings.

---

### 📊 9. System Status

**What it does:** Health check dashboard for the platform.

**What you'll see:**
- API status (online/offline)
- Version number (v4)
- Number of loaded antigens and cancer types
- Scoring engine details
- Available endpoints

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    USER (Browser)                    │
│              Streamlit Frontend (Port 8501)          │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP requests
                        ▼
┌─────────────────────────────────────────────────────┐
│               FastAPI Backend (Port 8001)            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Scoring      │  │ ML Models    │  │ NLP Query  │ │
│  │ Engine (CVS) │  │ (XGBoost +   │  │ Parser     │ │
│  │              │  │  RandomForest)│  │            │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                │                │         │
│         └────────────────┼────────────────┘         │
│                          ▼                          │
│  ┌──────────────────────────────────────────────┐   │
│  │        Biomarker Database (120K+ rows)        │  │
│  │     data/biomarker_database.csv               │  │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Start the API Server
```bash
cd C:\Users\dhruv\CARVanta
C:\Users\dhruv\carvanta_env\Scripts\python.exe -m uvicorn api.main:app --port 8001 --reload
```

### 2. Start the Frontend (separate terminal)
```bash
cd C:\Users\dhruv\CARVanta
C:\Users\dhruv\carvanta_env\Scripts\python.exe -m streamlit run frontend/app.py
```

### 3. Open in Browser
Go to **http://localhost:8501**

---

## Key Terminology Glossary

| Term | Plain English Meaning |
|------|----------------------|
| **Antigen** | A protein on the surface of a cell. CAR-T cells are designed to recognize specific antigens on cancer cells |
| **CAR-T** | Chimeric Antigen Receptor T-cell — an immune cell engineered to fight cancer |
| **CVS** | CAR-T Viability Score — CARVanta's composite score combining multiple factors |
| **Tumor Specificity** | How much more the antigen appears on cancer cells vs. healthy cells. Higher = better |
| **Normal Expression** | How much the antigen appears on healthy tissue. Lower = safer |
| **Immunogenicity** | How strongly the immune system reacts to this antigen. Higher = more effective |
| **Surface Accessibility** | Whether the antigen is on the cell surface (where CAR-T can reach it) vs. inside the cell |
| **Stability Score** | How consistently the antigen is expressed. Stable = reliable target |
| **Literature Support** | How much published research exists for this target |
| **Therapeutic Index** | Ratio of tumor expression to normal expression — higher means safer |
| **Off-tumor toxicity** | Side effects from CAR-T attacking healthy cells that also have the antigen |
| **Antigen escape** | When cancer cells stop producing the target antigen to avoid being killed |

---

## What Makes CARVanta Unique?

1. **120,000+ Biomarker Database** — Not just a handful of targets; comprehensive coverage
2. **ML-Driven Adaptive Scoring** — XGBoost regression model trained on real biomarker features
3. **Cancer-Context Awareness** — Same antigen gets different scores for different cancers
4. **Natural Language Search** — Ask questions in plain English
5. **Multi-Target Synergy** — Score combination therapies, not just single targets
6. **Patient Stratification** — Predict who will respond best
7. **Professional PDF Reports** — Export findings for presentations and publications

---

*CARVanta v4 — AI-Powered CAR-T Cell Target Viability Assessment Platform*
*© CARVanta — carvanta.ai*
