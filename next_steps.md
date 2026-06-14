# CARVanta — The Real Roadmap

> **Goal:** Transform CARVanta from a 100K-line proof-of-concept into a validated immunotherapy intelligence tool that a researcher would actually use.

> [!CAUTION]
> This document is brutally honest. It identifies what's real, what's fake, and what needs to happen — in order — to make CARVanta competitive.

---

## Part 1: Honest Assessment — What We Have vs What We Claim

### What's real (keep)
| Component | Why it's real |
|-----------|--------------|
| **Architecture** | 11 modular subsystems, clean API layer, React frontend — genuinely well-engineered |
| **CVS Scoring Formula** | Weighted multi-factor approach (specificity, safety, stability, evidence, immunogenicity) is scientifically sound in concept |
| **ML Pipeline** | RF + XGBoost ensemble trained on features — the pipeline works, just needs real training data |
| **NLP Query Engine** | Natural language antigen search — unique feature, works today |
| **Frontend UX** | 45 pages, functional UI — better than most academic tools |
| **API Design** | 451 routes, versioned, documented — production-grade structure |

### What's fake (must fix)
| Component | The problem |
|-----------|------------|
| **Expression data** | `generate_features()` uses `hash(antigen_name)` and `random.uniform()` to create fake tumor specificity, safety margins, etc. A researcher would spot this instantly |
| **Multi-omics engines** | `omics/transcriptomics.py` through `single_cell.py` generate plausible-looking data structures but contain zero real biological data |
| **Digital twin ODEs** | The differential equations look right but aren't parameterized from real clinical data. No validation against actual patient outcomes |
| **Clinical trials data** | `clinical_trials_endpoint()` generates fake NCT numbers and randomized phase distributions instead of calling the real ClinicalTrials.gov API |
| **Drug interactions** | Hardcoded list of ~20 interactions. Real tools use DrugBank (13K+ interactions) |
| **Safety profiles** | Normal tissue expression is randomly generated. Should come from GTEx (real tissue-specific expression) |
| **Neoantigen prediction** | `genomics/neoantigen_predictor.py` simulates MHC binding. Real tools use NetMHCpan or MHCflurry |
| **Literature/PubMed** | `collab/pubmed_linker.py` likely generates fake citations. PubMed has a free E-utilities API |
| **Patent data** | Generated, not from real patent databases |
| **SHAP explanations** | May use approximate/fake SHAP values instead of actual model explanations |

### What doesn't matter (cut or deprioritize)
| Component | Why |
|-----------|-----|
| **Line count targets** | Nobody cares about 127K lines. A 20K-line tool with real data beats a 200K-line tool with fake data |
| **Health Economics module** | Nice-to-have. No researcher picks a tool because it has QALY calculators |
| **Collaboration Hub (22 engines)** | Massively over-engineered. Real collaboration = share a link. You don't need 22 sub-engines |
| **Voice handler** | Nobody uses voice in a lab with a biosafety cabinet running |
| **Multi-tenant architecture** | Premature. Get 1 user before worrying about 1000 |
| **Billing/Stripe integration** | Way premature. The tool isn't validated yet |
| **i18n / 20 languages** | Premature. English-only is fine for v1 |

---

## Part 2: The Four Phases

### Phase 1: Real Data Foundation (Weeks 1-4)

**The single most important thing.** Every number in CARVanta must trace back to a real data source.

#### 1.1 — TCGA Gene Expression (Week 1)

**What:** Download preprocessed TCGA pan-cancer expression data and use it as CARVanta's truth layer.

**Source:** [UCSC Xena Browser](https://xenabrowser.net/datapages/) — free, no login required
- File: `TCGA-PANCAN/HiSeqV2.gz` (~800MB) — gene expression for 11,060 samples across 33 cancer types
- Format: TSV, genes × samples matrix

**How:**
```
data/
  tcga_expression.tsv.gz    ← download once, ship with repo (or download on first run)
  gtex_expression.tsv.gz
  antigen_metadata.json     ← curated list of known CAR-T targets with ground truth labels
```

**What changes in code:**
- `scoring/feature_generator.py` (or wherever `generate_features()` lives) stops using `hash()` and starts querying the real expression matrix
- `tumor_specificity` = median expression in tumor samples / median in normal samples (real ratio)
- `normal_expression_risk` = max expression across GTEx normal tissues (real safety signal)
- `stability_score` = coefficient of variation across tumor samples (real consistency measure)

**Validation:** After this step, when someone scores CD19:
- Tumor expression comes from real TCGA DLBCL samples
- Normal expression comes from real GTEx tissues
- The score MEANS something

#### 1.2 — GTEx Normal Tissue Expression (Week 1)

**What:** Download GTEx median expression per tissue type. This is what makes safety scoring real.

**Source:** [GTEx Portal](https://gtexportal.org/home/downloads/adult-gtex/bulk_tissue_expression) — free with registration
- File: `GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_median_tpm.gct.gz`
- Contains median TPM for every gene across 54 human tissues

**What changes:**
- `features/safety.py` uses real tissue expression to flag dangerous targets
- If CD19 has high expression in heart tissue (it doesn't, but if it did), the safety score drops
- This replaces ALL the `random.uniform()` calls in safety assessment

#### 1.3 — ClinicalTrials.gov Live API (Week 2)

**What:** Replace the fake trial generator with real API calls.

**API:** `https://clinicaltrials.gov/api/v2/studies`
**Cost:** Free, no API key needed
**Rate limit:** 100 requests/minute (generous)

**What changes:**
- `trials/clinicaltrials_sync.py` makes real HTTP requests
- `clinical_trials_endpoint()` returns real NCT IDs, real trial titles, real phase distributions
- Cache results in SQLite (already have the DB layer) to avoid hitting the API on every request

**Example query:**
```
GET https://clinicaltrials.gov/api/v2/studies?query.term=CAR-T+CD19&pageSize=50
```

Returns real trials with real NCT numbers. This is the easiest win — the API is free, well-documented, and returns JSON.

#### 1.4 — UniProt Protein Data (Week 2)

**What:** For each antigen, pull real protein data: subcellular location, molecular function, tissue specificity.

**API:** `https://rest.uniprot.org/uniprotkb/search?query=gene:CD19+AND+organism_id:9606`
**Cost:** Free, no key

**What changes:**
- `discovery/proteome_scanner.py` queries real protein metadata
- `surface_accessibility` comes from actual UniProt subcellular location annotations
- `immunogenicity_score` can be informed by protein length, glycosylation sites, etc.

#### 1.5 — Curated Ground Truth Dataset (Week 3)

**What:** Create a hand-curated JSON file of ~50 well-characterized CAR-T targets with known clinical outcomes.

```json
{
  "CD19": {
    "fda_approved": true,
    "approved_products": ["Kymriah", "Yescarta", "Tecartus", "Breyanzi"],
    "best_indication": "B-ALL, DLBCL",
    "overall_response_rate": 0.83,
    "complete_response_rate": 0.54,
    "grade3_crs_rate": 0.23,
    "known_limitations": ["antigen loss", "lineage switch"],
    "clinical_evidence_level": "Phase III",
    "references": ["PMID:29385376", "PMID:28983556"]
  },
  "BCMA": {
    "fda_approved": true,
    "approved_products": ["Abecma", "Carvykti"]
  }
}
```

**This is the most important file in the entire project.** It's what you validate against. Every claim CARVanta makes must be testable against this ground truth.

Sources for this data:
- FDA approval letters (public)
- Published Phase III trial results (PubMed — free)
- ASCO/ASH conference abstracts (public)

#### 1.6 — Retrain ML Models on Real Data (Week 4)

**What:** Once you have real TCGA/GTEx expression data:
1. Generate real features for all ~500 antigens in your database
2. Label them using the curated ground truth (FDA-approved = viable, failed Phase III = not viable)
3. Retrain RF + XGBoost on real features with real labels
4. Cross-validate properly (leave-one-out for the small validated set)

**After Phase 1, CARVanta's numbers mean something.** Every score traces to TCGA, GTEx, UniProt, or ClinicalTrials.gov. That's the foundation.

---

### Phase 2: Scientific Validation (Weeks 5-8)

#### 2.1 — Benchmark Against FDA-Approved Targets

There are currently **6 FDA-approved CAR-T products** targeting **2 antigens** (CD19 and BCMA), plus ~15 targets in late-stage clinical trials:

| Antigen | Status | Expected CARVanta ranking |
|---------|--------|--------------------------|
| CD19 | FDA-approved (4 products) | Should be top 5% |
| BCMA | FDA-approved (2 products) | Should be top 5% |
| CD22 | Phase II | Should be top 15% |
| HER2 | Phase I/II (solid tumors) | Should be top 20% |
| GD2 | Phase I/II (neuroblastoma) | Should be top 20% |
| EGFR | Phase I (glioblastoma) | Should be top 25% |
| Claudin18.2 | Phase I/II (gastric) | Should be top 25% |
| GPRC5D | Phase I/II (myeloma) | Should rank near BCMA |
| FLT3 | Phase I (AML) | Should be top 30% |

**The test:** Run CARVanta's scoring on ALL antigens in the database. Do the FDA-approved ones come out on top? If CD19 scores 0.948 and some random gene scores 0.96, something is wrong.

**Metric:** Spearman rank correlation between CARVanta CVS score and clinical stage (FDA-approved > Phase III > Phase II > Phase I > Preclinical > No trials).

**Target:** ρ ≥ 0.75 would be publishable. ρ ≥ 0.85 would be impressive.

#### 2.2 — Validate Safety Predictions

Using GTEx normal tissue expression:
- Targets with high normal tissue expression SHOULD get lower safety scores
- CD19's known on-target/off-tumor toxicity (B-cell aplasia) should be reflected in the safety module
- Compare your safety rankings against published toxicity reviews (several exist in Nature Reviews Cancer)

#### 2.3 — Cross-Cancer Validation

Your platform scores antigens per cancer type. Test:
- Does CD19 score highest in B-cell malignancies (where it's actually used)?
- Does HER2 score highest in breast/gastric cancer?
- Does PSMA score highest in prostate cancer?

If the cancer-type contextual scoring works correctly with real data, that's a unique feature.

#### 2.4 — Failure Case Analysis

**Equally important:** identify what CARVanta gets WRONG and document it honestly.
- Does it rank any dangerous target too high?
- Does it miss any good target?
- What are the failure modes?

Honest failure analysis is what separates science from marketing.

---

### Phase 3: Scientific Credibility (Weeks 9-12)

#### 3.1 — Write a Preprint

**Title suggestion:** *"CARVanta: An Open-Source AI Platform for Multi-Factor Evaluation of CAR-T Cell Therapy Antigen Targets"*

**Structure:**
1. **Introduction** — The antigen selection bottleneck in CAR-T development
2. **Methods** — CVS scoring algorithm, data sources (TCGA, GTEx, UniProt), ML ensemble
3. **Results** — Benchmark against FDA-approved targets, cross-cancer validation
4. **Discussion** — Limitations, failure cases, future directions
5. **Availability** — Open source, GitHub link

**Where to publish:**
- **bioRxiv** (preprint, instant, free) — gets you visibility immediately
- **Bioinformatics** (Oxford, peer-reviewed) — respected in computational biology
- **JITC** (Journal of Immunotherapy of Cancer) — if clinical validation is strong
- **NAR Webserver issue** (Nucleic Acids Research) — specifically for tools/platforms

#### 3.2 — Open Source Properly

Your GitHub repo needs:
- Clear README with installation instructions that actually work
- `pip install carvanta` or at minimum `docker compose up`
- Example notebooks showing real analyses
- Contributing guide
- License (already have — good)
- CI/CD with tests that pass

#### 3.3 — Get Real Users

1. **Post on Twitter/X** — tag computational immunology researchers
2. **Post on Reddit** — r/bioinformatics, r/immunology
3. **Post on Hacker News** — "Show HN: Open-source AI platform for CAR-T target evaluation"
4. **Submit to bio.tools** — the registry of bioinformatics tools
5. **Email 5 immunology PhD students** — offer to run their antigens through CARVanta for free

One real user's feedback > 10,000 lines of code.

#### 3.4 — Conference Presentation

- **AACR** (American Association for Cancer Research) — poster abstract
- **ASH** (American Society of Hematology) — relevant for CAR-T
- **ISMB/ECCB** — computational biology audience

Even a poster at a regional conference gives CARVanta scientific legitimacy.

---

### Phase 4: Product Hardening (Weeks 13-16)

Only after Phases 1-3. Code that serves real data to real users.

#### 4.1 — Fix What Matters

| Priority | Task | Why |
|----------|------|-----|
| P0 | Make ALL frontend pages work correctly with real backend data | Broken pages = zero credibility |
| P0 | Make `start.bat` reliably start the entire stack | If it doesn't start in 1 command, nobody uses it |
| P1 | Add proper error handling (no blank pages, no "Query failed") | User trust |
| P1 | Cache expensive computations (TCGA queries, ML scoring) | Performance |
| P2 | Add loading states and progress indicators everywhere | UX polish |
| P2 | Mobile-responsive layout | Accessibility |

#### 4.2 — Cut What Doesn't Matter

**Be ruthless.** These add lines but not value:

| Cut/Deprioritize | Reason |
|------------------|--------|
| 22-engine Collaboration Hub | Reduce to: projects, experiments, peer review. Cut the rest |
| Voice handler | Nobody uses this |
| Health Economics (QALY, budget impact) | Nice-to-have, not core |
| Multi-tenant architecture | Premature |
| Billing/Stripe | Premature |
| i18n / language support | Premature |
| Manufacturing simulator | Not core to antigen selection |

#### 4.3 — Deployment

| Option | Cost | Difficulty | Best for |
|--------|------|-----------|----------|
| **Railway.app** | $5/mo | Easy | Full stack with DB |
| **Render** | Free tier | Medium | Backend API |
| **Fly.io** | Free tier | Medium | Docker deployment |

---

## Part 3: Priority Stack — What To Do Monday Morning

### This week
1. Download TCGA pan-cancer expression matrix from UCSC Xena
2. Download GTEx median tissue expression
3. Build `data/ground_truth.json` with 50 curated CAR-T targets
4. Replace `generate_features()` with real TCGA/GTEx lookups

### Next week
5. Retrain ML models on real features
6. Run validation benchmark (do FDA-approved targets rank highest?)
7. Connect to ClinicalTrials.gov API for live trial data

### Week after
8. Fix all broken frontend pages
9. Write benchmark results into a document
10. Start drafting the preprint

---

## Part 4: The Competitive Landscape

| Tool | What it does | CARVanta's advantage |
|------|-------------|---------------------|
| **cBioPortal** | Cancer genomics browser | They show data. You SCORE and RANK targets |
| **CIViC** | Clinical variant interpretation | Manually curated, slow. You're automated |
| **OncoKB** | Precision oncology knowledge base | Drug-focused, not CAR-T specific |
| **IEDB** | Immune epitope database | Epitopes, not CAR-T target selection |
| **Internal pharma tools** | Proprietary, closed | You're open source. That matters |

**CARVanta's unique position:** No open-source tool specifically ranks antigens for CAR-T therapy potential using multi-factor scoring. cBioPortal shows you expression data. CIViC tells you about variants. Neither says "CD19 is your best target for B-ALL, and here's why, scored against 500 alternatives." **That's your moat.**

---

## Part 5: What Success Looks Like

### 3 months from now
- CARVanta scores based on real TCGA/GTEx data
- Benchmark published: correctly ranks FDA-approved targets
- Preprint on bioRxiv
- 5-10 users who aren't you

### 6 months from now
- Peer-reviewed publication
- 100+ GitHub stars
- 1 collaboration with an academic lab

### 12 months from now
- Used by researchers at 3+ institutions
- Cited in at least 1 other paper
- Conference presentation
- Either: seed funding conversation OR lab partnership OR acquisition interest

---

> [!IMPORTANT]
> **The bottom line:** CARVanta's engineering is already competitive. What's missing is truth — real data, real validation, real users. The data is free, the validation is doable, and the users are out there.
>
> 100K lines of synthetic code = impressive project.
> 20K lines of validated code = real tool.
> You have the 100K. Now make 20K of it real.
