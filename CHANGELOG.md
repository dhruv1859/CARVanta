# Changelog

All notable changes to the CARVanta platform will be documented in this file.

## [5.0.0] — 2026-03-16

### 🚀 International Recognition Roadmap Release

#### New Backend Modules
- **`api/audit_logger.py`** — SQLite-backed audit logging middleware for HIPAA compliance
- **`features/drug_interactions.py`** — Drug-antigen interaction checker (13 antigens, ~30 drugs)
- **`features/explainability.py`** — SHAP-based explainability with TreeExplainer + fallback
- **`features/fhir_export.py`** — FHIR R4 DiagnosticReport/Observation bundle export
- **`features/ip_landscape.py`** — Curated patent landscape data for 9 key antigens
- **`features/notation_standards.py`** — HUGO/NCBI/UniProt/Ensembl gene ID mappings (20 antigens)
- **`features/score_history.py`** — SQLite-backed score time-series tracker

#### New Regulatory Documents
- **`PRIVACY_POLICY.md`** — HIPAA compliance disclosure and privacy policy
- **`ISO_13485_ALIGNMENT.md`** — ISO 13485 quality management alignment report
- **`MODEL_CARD.md`** — Google-standard model card documentation

#### New API Endpoints (20 total)
- `GET /api/drug-interactions/{antigen}` — Drug interaction check
- `GET /api/drug-interactions` — All catalogued interactions
- `GET /api/explain/{antigen}` — SHAP explainability
- `POST /api/batch-upload` — Score up to 500 genes
- `GET /api/model-card` — Model card (JSON)
- `GET /api/cite/{antigen}` — Citation generator (APA/MLA/BibTeX/RIS)
- `GET /api/audit-log` — Regulatory audit trail
- `GET /api/fhir/{antigen}` — FHIR R4 export
- `GET /api/patents/{antigen}` — Patent landscape
- `GET /api/patents` — All patent summaries
- `GET /api/gene-ids/{antigen}` — Gene notation lookup
- `GET /api/gene-ids` — All gene identifiers
- `GET /api/score-history/{antigen}` — Historical scores
- `GET /api/score-history` — All tracked antigens
- `POST /api/score-snapshot` — Record score snapshot
- `POST /api/community/submit` — Community antigen submission
- `GET /api/dataset/benchmarks` — Published benchmarks
- `GET /api/privacy-policy` — Privacy policy (JSON)
- `GET /api/sdk-info` — API marketplace info

#### New Frontend Pages (5 total)
- **Drug Interactions** — Browse all antigen-drug interactions with risk levels
- **Patent Explorer** — Patent landscape with FTO assessments
- **Community Submit** — Submit new antigens for automated scoring
- **Batch Upload** — Score up to 500 genes at once with tier distribution
- **Audit Log** — Regulatory compliance request viewer with stats

#### Enhanced Single Analysis Page
- Gene ID badges (HUGO/NCBI/UniProt/Ensembl + external links)
- Drug interaction warning cards with risk-level coloring
- SHAP explainability bars with narrative explanation
- Patent landscape badge (FTO + key patents)
- Score history timeline with trend indicator
- Citation modal (APA/MLA/BibTeX/RIS + copy-to-clipboard)
- FHIR R4 JSON export button
- Save Snapshot button for time-series tracking

#### Frontend Improvements
- Dark/Light mode toggle with localStorage persistence
- PWA manifest for mobile installability
- Apple mobile web app meta tags
- Updated version to v5

#### Configuration
- Added `pyrightconfig.json` to suppress false-positive linter errors
- Added `shap>=0.43.0` to `requirements.txt`

## [4.0.0] — 2026-02-27

### ML & Data Upgrade
- Replaced synthetic data with 100K+ real biomarkers (TCGA/GTEx)
- Trained Random Forest + XGBoost ensemble models
- Implemented 8-feature Clinical Viability Score (CVS) engine
- Added benchmark validation against FDA-approved CAR-T targets

## [3.0.0] — 2026-02-25

### Platform Launch
- React frontend with 10 pages
- FastAPI backend with scoring, safety, and analysis endpoints
- Patient stratification and multi-target synergy analysis
- NLP query search and clinical trials integration
