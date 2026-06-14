# CARVanta — The AI That's Racing to Save Cancer Patients Before Time Runs Out

## The Moment That Changes Everything

A doctor sits across from a family and says five words: *"Your child has blood cancer."*

What follows is a race against time. The cancer is growing. The clock is ticking. And somewhere in the world, there's a treatment that could save this child's life — **CAR-T cell therapy** — where doctors reprogram the patient's own immune cells to hunt and destroy cancer.

But here's what nobody tells the family:

**Finding the right target for that therapy takes 5–10 years of research. And a single treatment costs $500,000.**

**CARVanta was built to change that.**

---

## What Is CAR-T Therapy?

Your immune system has T-cells — soldiers that patrol your body looking for invaders. Cancer is clever: it disguises itself so T-cells walk right past it.

CAR-T therapy is the hack. Doctors extract the patient's T-cells, genetically engineer them by adding a "GPS antenna" (a **C**himeric **A**ntigen **R**eceptor) that locks onto a specific marker on the cancer cell, multiply millions of these cells, and infuse them back. These supercharged T-cells now recognize and kill the cancer — a biological guided missile.

**But the entire therapy depends on picking the right target marker.** Pick the wrong one, and the missile misses. Or worse — it attacks healthy organs.

---

## What CARVanta Does

CARVanta is two connected systems solving one problem: **keeping cancer patients alive.**

### 🖥️ The Software: AI Target Discovery Platform

**117,000 lines of code. 45 pages. 214 Python modules. 30+ API endpoints.**

A cloud-deployed platform where a doctor or researcher:

1. **Types a cancer antigen name** — CARVanta instantly scores it across 8 scientific dimensions using real data from TCGA, GTEx, and the Human Protein Atlas
2. **Machine learning models** (Random Forest + XGBoost) trained on FDA-approved targets predict viability
3. **An LLM** writes a clinical reasoning summary explaining *why* in plain English
4. **A Digital Twin** simulates how *this specific patient* responds to *this specific target*
5. **A Trial Matcher** finds every qualifying clinical trial worldwide, ranked by proximity

What used to take researchers 3–5 years now takes **minutes**.

### 🔬 The Hardware: Sentinel HYDRA

**50 firmware files. 6-layer medical PCB. Dual-processor architecture.**

A credit-card-sized device at the patient's bedside that **continuously monitors** blood biomarkers through a disposable sensor strip:

- **4 antigen levels simultaneously** — catches cancer escaping the therapy
- **SpO2 + heart rate** — early cytokine storm warning
- **11 spectral channels** — optical biomarker analysis
- **Impedance spectroscopy** — cell health assessment
- **Results in 30 seconds → WiFi upload to CARVanta cloud → doctor alerted instantly**

---

## Why 117,000 Lines?

Because biology doesn't play by simple rules:

| What's Needed | Lines of Code | Why |
|--------------|--------------|-----|
| Genomic variant caller | ~49,000 lines | Parsing VCF/FASTA, detecting SNVs, indels, CNVs, gene fusions |
| Digital Twin engine | ~35,000 lines | PK/PD modeling, immune simulation, tumor dynamics, CRS prediction |
| 45 React UI pages | ~25,000 lines | From login to genomic profiler to 3D neural bridge |
| Clinical trials intelligence | ~15,000 lines | ClinicalTrials.gov sync, eligibility matching, DSMB reports |
| Embedded firmware (C++) | ~5,000 lines | Dual-MCU sensor control, electrochemistry, PID heater, WiFi |
| Drug discovery pipeline | ~12,000 lines | scFv design, molecular docking, ADMET, toxicity prediction |
| Everything else | ~25,000 lines | Auth, billing, NLP, LLM, collaboration, safety, compliance |

---

## How It All Connects

```
Patient blood (fingerprick)
        │
        ▼
┌───────────────────────┐
│   SENTINEL HYDRA      │     Bedside device
│   Measures 4 antigens │     95×65mm, ~$50/unit
│   + vitals + spectral │
└───────────┬───────────┘
            │ WiFi
            ▼
┌───────────────────────────────────────┐
│        CARVANTA CLOUD                  │
│                                        │
│  📊 Real-time biomarker trends         │
│  🤖 AI: "CD19 dropping — escape risk"  │
│  🧬 Genomic: "Switch to CD22 target"   │
│  🧑‍⚕️ Twin: "85% response if switched"   │
│  🏥 Trials: "3 CD22 trials nearby"     │
│  🔔 → Doctor's phone: "Act now"        │
└───────────────────────────────────────┘
```

---

## Why This Is a Gamechanger

**1. It closes the loop** — Software picks the target → hardware monitors the treatment → data improves the AI. A continuous learning cycle.

**2. It turns days into seconds** — Detecting antigen escape (the #1 reason CAR-T fails) currently takes days via lab tests. The Sentinel detects it in 30 seconds.

**3. It democratizes access** — A researcher in Mumbai uses the same AI as Harvard. The hardware costs ~$50, not $50,000.

**4. 4 antigens, not 1** — Cancer downregulates one antigen and escapes through another. HYDRA monitors 4 simultaneously, catching escape mutations before they kill.

---

## The Numbers

| Metric | Value |
|--------|-------|
| Lines of code | **117,000+** |
| Source files | **778** |
| Python AI modules | **214** |
| React UI pages | **45** |
| API endpoints | **30+** |
| Scored biomarkers | **500+** |
| Firmware files | **50** |
| PCB layers | **6** |
| Simultaneous antigen channels | **4** |
| Measurement cycle | **30 seconds** |
| Hardware cost target | **~$50/unit** |

---

## The Vision

> **A world where no cancer patient dies because their doctor didn't know the treatment was failing.**

CARVanta isn't software. It isn't hardware. It's an **ecosystem** — an AI brain connected to a bedside sentinel — that turns immunotherapy from a gamble into a guided science.

The software shortens years of research into minutes.
The hardware catches treatment failure in seconds instead of days.
Together, they save lives.

---

*Built by Dhruv · CARVanta AI Platform*
