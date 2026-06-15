# Changelog

All notable changes to the CARVanta platform will be documented in this file.

## [5.1.0] — 2026-06-15

### 🔬 Sentinel HYDRA Hardware Release

#### Gerber Manufacturing Package
- **Production Gerber files** generated for 6-layer PCB via KiCad CLI
  - 6 copper layers: Digital_Signals (F.Cu), GND_Plane (In1), Analog_Signals (In2), Power_Planes (In3), HighSpeed (In4), Bottom_GND (B.Cu)
  - Front/Back solder mask, silkscreen, paste stencil, fabrication layers
  - Board outline (Edge.Cuts)
- **Excellon drill files** with PTH and NPTH separated
- **Drill map files** in Gerber X2 format
- **`Sentinel_HYDRA_Gerbers.zip`** — manufacturing-ready archive for JLCPCB/PCBWay upload

#### Board Statistics (from KiCad export)
- 135 components (123 SMD + 11 THT)
- 641 SMD pads + 72 through-hole pads + 9 NPTH
- 225 through-hole vias
- 1.6mm stackup thickness, ENIG surface finish

#### Dual-MCU Firmware (50 files, 114KB)
- **ESP32-S3 firmware** (`esp32_hydra/`) — WiFi, display, cloud, storage, power management
- **RP2040 firmware** (`rp2040_hydra/`) — Real-time sensor acquisition, PID control, spectral analysis
- UART inter-MCU protocol at 921600 baud with CRC

#### Documentation Overhaul
- **`README.md`** — Complete rewrite with Sentinel HYDRA hardware section, updated stats (117K+ LOC, 778 files), hardware badges, manufacturing files link, firmware build instructions, documentation index
- **`ARCHITECTURE.md`** — New comprehensive architecture document covering software stack, 6-layer PCB stackup, dual-MCU design, I2C bus topology, SPI bus sharing, power architecture, sensor subsystems, firmware structure, inter-MCU protocol, data flow, and deployment
- **`CODE_OF_CONDUCT.md`** — Full Contributor Covenant v2.1 with medical-adjacent patient safety commitments and enforcement guidelines
- **`contributing.md`** — Expanded guide covering software (Python/React), hardware (KiCad PCB design rules), and firmware (PlatformIO ESP32/RP2040) contributions, PR process, commit convention
- **`security.md`** — Expanded security policy with version support matrix, hardware security considerations, HIPAA alignment, CVSS severity classification, and response timelines

---

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
