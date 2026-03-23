# CARVanta Universe — Module Registry
> Your roadmap to building the world's first open immunotherapy intelligence platform.

---

## ✅ Module 10: Enterprise Auth & User Management
**Status:** COMPLETE | **Est. Lines:** 8K  
**What it does:** User accounts, JWT login, role-based access control, profile management.  
**Who uses it:** Everyone — it's the foundation.  
**Files:**
- `db/models.py` — User, UserSession, PatientProfile, ResearchProject, Collaboration, GenomicUpload
- `api/auth.py` — JWT + PBKDF2 password handler
- `api/auth_router.py` — 10 API endpoints (register, login, logout, profile, etc.)
- `frontend-react/src/pages/LoginPage.tsx` — Login & Register UI
- `frontend-react/src/pages/ProfilePage.tsx` — User profile page
- `frontend-react/src/context/AuthContext.tsx` — React auth state
- `frontend-react/src/styles/auth.css` — Auth page styling

---

## ⬜ Module 1: Multi-Omics Intelligence Engine
**Status:** NOT STARTED | **Est. Lines:** 12K  
**What it does:** Integrates 5 data layers — Transcriptomics, Proteomics, Epigenomics, Metabolomics, Single-cell RNA. Cross-references Human Protein Atlas, COSMIC, ClinVar. Computes multi-dimensional target scores.  
**Who uses it:** Researchers who need deeper biological evidence.  
**Key files to create:**
- `omics/transcriptomics.py` — RNA-seq processing
- `omics/proteomics.py` — Protein abundance scoring
- `omics/epigenomics.py` — Methylation analysis
- `omics/metabolomics.py` — Metabolic pathway impact
- `omics/single_cell.py` — Single-cell heterogeneity
- `omics/integrator.py` — Multi-omics fusion algorithm
- Frontend: Multi-omics radar chart, genome browser, violin plots

---

## ✅ Module 2: Patient Digital Twin Simulator
**Status:** COMPLETE | **Est. Lines:** 15K  
**What it does:** Upload a patient's profile (age, cancer type, genomic markers, lab values). Simulates CAR-T treatment outcomes over 12 months. Predicts cytokine release syndrome risk. Compares different antigen targets for that specific patient.  
**Who uses it:** Oncologists choosing between treatments. Patients wanting to visualize outcomes.  
**Key files to create:**
- `digital_twin/patient_model.py` — Patient state representation
- `digital_twin/immune_dynamics.py` — T-cell expansion/exhaustion ODEs
- `digital_twin/tumor_model.py` — Tumor growth/regression simulation
- `digital_twin/crs_predictor.py` — Cytokine storm risk model
- `digital_twin/treatment_simulator.py` — Monte Carlo outcome simulation
- Frontend: Patient intake wizard, animated tumor simulation, 12-month outcome timeline

---

## ⬜ Module 3: AI-Powered Drug Discovery Engine
**Status:** NOT STARTED | **Est. Lines:** 10K  
**What it does:** Scans entire human proteome (20K+ proteins) for novel CAR-T targets. Uses Graph Neural Networks on protein interaction networks. Predicts off-target toxicity. Suggests antibody fragment designs.  
**Who uses it:** Pharma companies, biotech startups, drug discovery researchers.  
**Key files to create:**
- `discovery/proteome_scanner.py` — Full proteome scan
- `discovery/graph_nn.py` — GNN on STRING network
- `discovery/novelty_detector.py` — Unexplored target finder
- `discovery/toxicity_predictor.py` — Off-target tissue analysis
- `discovery/car_architect.py` — CAR construct design
- Frontend: Proteome heatmap, novel target cards, CAR designer

---

## ⬜ Module 4: Clinical Trial Matcher
**Status:** NOT STARTED | **Est. Lines:** 8K  
**What it does:** Real-time sync with ClinicalTrials.gov (400K+ trials). AI-powered patient-to-trial matching. Geographic proximity search. Automatic eligibility pre-screening.  
**Who uses it:** Patients looking for trials. Oncologists referring patients.  
**Key files to create:**
- `trials/clinicaltrials_sync.py` — ClinicalTrials.gov API
- `trials/matcher.py` — NLP patient-trial matching
- `trials/eligibility_checker.py` — Auto criteria checking
- `trials/geo_proximity.py` — Geographic distance
- Frontend: Trial map view, match score cards, eligibility checklist

---

## ⬜ Module 5: Real-Time Genomic Analyzer
**Status:** NOT STARTED | **Est. Lines:** 12K  
**What it does:** Upload FASTA/FASTQ/VCF files. Real-time variant calling. Neoantigen prediction. HLA typing. Tumor mutational burden. FASTA sequence error detection (your idea!).  
**Who uses it:** Every molecular biology lab on earth. Genomics researchers.  
**Key files to create:**
- `genomics/file_processor.py` — FASTA/FASTQ/VCF parser
- `genomics/fasta_validator.py` — Sequence error detection (invalid bases, frameshifts, stop codons)
- `genomics/variant_caller.py` — SNV/indel detection
- `genomics/neoantigen_predictor.py` — MHC binding prediction
- `genomics/hla_typer.py` — HLA allele determination
- `genomics/tmb_calculator.py` — Tumor mutational burden
- Frontend: File upload, variant browser, neoantigen dashboard, circos plot

---

## ⬜ Module 6: Research Collaboration Hub
**Status:** NOT STARTED | **Est. Lines:** 10K  
**What it does:** GitHub-like collaboration for biotech. Shared experiments, datasets, notebooks. Peer review for community-submitted targets. PubMed integration. Lab-to-lab messaging.  
**Who uses it:** Research teams, academic labs, multi-site clinical studies.  
**Key files to create:**
- `collab/projects.py` — Research project management
- `collab/experiments.py` — Shared experiment tracking
- `collab/notebooks.py` — Jupyter-like notebook system
- `collab/peer_review.py` — Target review workflow
- `collab/pubmed_linker.py` — PubMed API integration
- Frontend: Project dashboard, notebook editor, peer review UI

---

## ⬜ Module 7: Health Economics Engine
**Status:** NOT STARTED | **Est. Lines:** 8K  
**What it does:** Cost-effectiveness analysis for CAR-T (it costs $400K-$500K per patient). QALY calculator. Budget impact modeling. Manufacturing cost estimator. Market size estimation.  
**Who uses it:** Hospital administrators, insurance companies, health ministries, pharma pricing teams.  
**Key files to create:**
- `economics/cea_model.py` — Cost-effectiveness analysis
- `economics/qaly_calculator.py` — Quality-adjusted life years
- `economics/budget_impact.py` — Healthcare budget modeling
- `economics/manufacturing_cost.py` — Production cost estimator
- Frontend: Cost-effectiveness plots, QALY charts, budget waterfall

---

## ⬜ Module 8: Global Disease Atlas
**Status:** NOT STARTED | **Est. Lines:** 10K  
**What it does:** Interactive world map of cancer incidence. Antigen expression by population/ethnicity. Treatment access gaps. Epidemiological trends. Regulatory landscape by country. Multi-language.  
**Who uses it:** WHO, NGOs, global health researchers, every person checking cancer stats.  
**Key files to create:**
- `atlas/incidence_data.py` — WHO/GLOBOCAN data
- `atlas/prevalence_analyzer.py` — Antigen prevalence by population
- `atlas/access_gaps.py` — Treatment access inequality
- `atlas/trends.py` — Epidemiological trend modeling
- `atlas/i18n.py` — Internationalization (20+ languages)
- Frontend: Choropleth world map, regional profiles, trend timelines

---

## ⬜ Module 9: AI Research Copilot
**Status:** NOT STARTED | **Est. Lines:** 10K  
**What it does:** Chat interface for immunotherapy questions. RAG over 50K+ research papers. Auto-generates literature reviews. Suggests experimental designs. Voice-enabled for hands-free lab use.  
**Who uses it:** Every researcher, clinician, and student in immunotherapy.  
**Key files to create:**
- `copilot/rag_engine.py` — Vector database + retrieval
- `copilot/paper_index.py` — PubMed paper indexer
- `copilot/chat_handler.py` — Conversational AI
- `copilot/lit_reviewer.py` — Literature review generator
- `copilot/voice_handler.py` — Speech-to-text/text-to-speech
- Frontend: Chat interface, cited answers, voice toggle

---

## Build Order (Recommended)

| Priority | Module | Why |
|----------|--------|-----|
| ✅ Done | 10. Enterprise Auth | Foundation for everything |
| 🔜 Next | 2. Patient Digital Twin | Most impressive feature |
| 3rd | 9. AI Research Copilot | Everyone can use it |
| 4th | 4. Clinical Trial Matcher | Immediate patient impact |
| 5th | 5. Genomic Analyzer | Researcher magnet (FASTA!) |
| 6th | 1. Multi-Omics Engine | Deep science upgrade |
| 7th | 3. AI Drug Discovery | Pharma will pay for this |
| 8th | 8. Global Disease Atlas | Global reach |
| 9th | 6. Collaboration Hub | Community growth |
| 10th | 7. Health Economics | Enterprise sales |

---

## Line Count Estimate

| Component | Current | After All Modules |
|-----------|---------|-------------------|
| Python Backend | ~6K | ~70K |
| React Frontend | ~10K | ~47K |
| CSS/Styles | ~3K | ~8K |
| **Total** | **~19K** | **~125K** |

---

*Edit this file anytime to change priorities, add new modules, or modify features.*
