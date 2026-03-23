# CARVanta — ISO 13485 Quality Management Alignment

**Document Version:** 1.0
**Date:** March 2026
**Scope:** CARVanta AI-Augmented Biomarker Intelligence Platform

## 1. Purpose

This document describes how CARVanta aligns with ISO 13485:2016 (Medical Devices —
Quality Management System) requirements, as applicable to software used in research
contexts. While CARVanta is not currently a registered medical device, this
alignment demonstrates readiness for regulatory pathways (FDA 510(k), CE marking).

## 2. Regulatory Classification

| Item | Status |
|------|--------|
| Current Status | Research Use Only (RUO) |
| Intended Medical Device Class | Class II (with special controls) |
| FDA Pathway (future) | 510(k) — Clinical Decision Support Software |
| EU MDR Classification (future) | Class IIa — Rule 11 (software intended for diagnostic purposes) |

## 3. Quality Management System Alignment

### 3.1 Design and Development (ISO 13485 §7.3)

| Requirement | CARVanta Implementation |
|-------------|------------------------|
| Design inputs | International Roadmap + clinical validation requirements |
| Design outputs | CVS scoring algorithm, ML models, API endpoints |
| Design verification | Automated benchmark against FDA-approved CAR-T targets |
| Design validation | Cross-validation (5-fold), ROC-AUC analysis |
| Design changes | Version-controlled via Git; CHANGELOG.md maintained |

### 3.2 Document Control (ISO 13485 §4.2.4)

| Document | Location | Version Control |
|----------|----------|----------------|
| Source code | GitHub repository | Git + branches |
| Model Card | `MODEL_CARD.md` | Versioned with releases |
| Privacy Policy | `PRIVACY_POLICY.md` | Dated with change tracking |
| Training Reports | `data/training_report.json` | Regenerated per model version |
| Benchmark Reports | `data/benchmark_report.json` | Regenerated per release |
| API Documentation | FastAPI auto-generated `/docs` | Synchronized with code |

### 3.3 Risk Management (ISO 14971 alignment)

| Risk Category | Mitigation |
|---------------|-----------|
| False positive (non-viable scored as viable) | CVS threshold tiering + ML ensemble for dual verification |
| False negative (viable missed) | High recall prioritized in model training (99.94% recall) |
| Off-tumor toxicity not detected | Safety scoring module with normal tissue expression analysis |
| Drug interaction not flagged | Curated drug interaction database (13 antigens, ~30 drugs) |
| Model bias toward well-studied antigens | Model Card documents known biases; confidence scoring reflects data quality |
| Data provenance unclear | `/score` response includes data provenance metadata |

### 3.4 Traceability (ISO 13485 §7.5.3)

| Component | Traceability Method |
|-----------|-------------------|
| Training data | CSV with source annotations (real/validated/synthetic) |
| Model versions | Serialized `.pkl` files with version stamps |
| Scoring decisions | Audit logging via SQLite with request hashing |
| Feature engineering | Version-stamped in code (`v2` feature set) |

### 3.5 Corrective and Preventive Action (ISO 13485 §8.5)

| Process | Implementation |
|---------|---------------|
| Bug tracking | GitHub Issues |
| Performance monitoring | Benchmark v3 automated regression testing |
| Model drift detection | Cross-validation metrics compared across retraining cycles |
| User feedback | API endpoint for issue reporting (planned) |

## 4. Software Lifecycle (IEC 62304 alignment)

| Phase | Activities |
|-------|-----------|
| Requirements | International Roadmap items |
| Architecture | Modular Python: features/, scoring/, models/, api/ |
| Implementation | Test-driven with automated benchmark validation |
| Verification | Unit tests, API integration tests, benchmark suite |
| Release | Version-tagged with CHANGELOG.md |
| Maintenance | Continuous model retraining, data updates |

### Software Safety Classification
- **Class B** (Non-serious injury possible if software fails)
- Rationale: CARVanta provides decision support, not autonomous clinical
  decisions. All outputs require expert interpretation.

## 5. Readiness Assessment

| ISO 13485 Clause | Readiness | Notes |
|-------------------|----------|-------|
| §4.2 Documentation | ✅ High | Model Card, Privacy Policy, README, CHANGELOG |
| §5.6 Management Review | ⚠️ Partial | Needs formal review cadence |
| §6.2 Human Resources | ⚠️ Partial | Needs training records |
| §7.3 Design Control | ✅ High | Version-controlled, benchmarked |
| §7.4 Purchasing | N/A | No purchased components |
| §7.5 Production | ✅ High | Reproducible Docker builds |
| §7.6 Monitoring | ✅ High | Audit logging, performance metrics |
| §8.2 Complaints | ⚠️ Partial | Needs formal complaint process |
| §8.3 Nonconforming Product | ✅ High | Git revert capability |
| §8.5 CAPA | ⚠️ Partial | Informal through Git |

## 6. Next Steps for Full Compliance
1. Establish formal Management Review meetings (quarterly)
2. Create training records for development team
3. Implement formal complaint handling process
4. Conduct internal audit against ISO 13485 checklist
5. Engage Notified Body for formal assessment (CE marking pathway)
