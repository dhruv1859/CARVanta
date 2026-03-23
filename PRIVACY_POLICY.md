# CARVanta — Privacy Policy & HIPAA Compliance Disclosure

**Effective Date:** March 2026
**Last Updated:** March 16, 2026

## 1. Overview

CARVanta ("Platform") is a bioinformatics research tool that provides AI-assisted
assessment of antigen targets for CAR-T cell therapy development. This policy
describes how CARVanta handles data in compliance with applicable privacy regulations
including HIPAA (Health Insurance Portability and Accountability Act).

## 2. HIPAA Compliance Status

CARVanta is designed as a **Research Use Only (RUO)** platform.

> **Important:** CARVanta does not directly process, store, or transmit Protected
> Health Information (PHI) as defined under HIPAA. All biomarker data used by
> the platform is derived from de-identified, publicly available datasets.

### 2.1 Data Sources
| Source | Type | PHI Status |
|--------|------|-----------|
| TCGA (The Cancer Genome Atlas) | Tumor expression | De-identified |
| GTEx (Genotype-Tissue Expression) | Normal tissue expression | De-identified |
| Human Protein Atlas | Protein localization | Public |
| ClinicalTrials.gov | Clinical trial metadata | Public |
| CARVanta Synthetic | Computationally derived | No PHI |

### 2.2 Technical Safeguards
- **Audit Logging**: All API requests are logged with timestamps, endpoints, and
  hashed request bodies (SHA-256). Raw request bodies are never stored.
- **Rate Limiting**: API access is rate-limited by tier to prevent abuse.
- **No Patient Data**: The platform does not accept, process, or store individual
  patient data, medical records, or any form of PHI.
- **API Key Authentication**: All API access requires authentication via API keys
  with tier-based permissions.

## 3. Data We Collect

### 3.1 Usage Data (Audit Log)
When you use the CARVanta API, we log:
- Timestamp of request
- API endpoint accessed
- HTTP method and status code
- Response latency
- Client IP address (for rate limiting)
- User-Agent header
- SHA-256 hash of request body (never the raw content)

### 3.2 What We Do NOT Collect
- Patient names, medical record numbers, or any PHI
- Individual patient genomic sequences
- Clinical outcomes or treatment histories
- Insurance or billing information
- Social Security numbers or other government IDs

## 4. Data Retention
- **Audit logs**: Retained for 90 days, then automatically purged
- **Scoring results**: Not persisted server-side; computed on-demand
- **Model artifacts**: ML models are retrained periodically; previous versions
  are archived for reproducibility

## 5. Data Sharing
CARVanta does **not** sell, share, or transfer any user data to third parties.
API usage metadata may be aggregated (anonymized) for platform performance
analysis.

## 6. Security Measures
- All API communication should use HTTPS (TLS 1.2+) in production
- Database encryption at rest for audit logs
- Role-based access control for administrative functions
- Regular dependency auditing via `pip-audit`

## 7. Your Rights
- **Access**: Request a copy of your audit log data
- **Deletion**: Request deletion of your audit log entries
- **Opt-out**: You may use the platform without an API key for limited access

## 8. International Compliance
- **GDPR (EU)**: CARVanta processes only de-identified research data;
  no personal data processing occurs
- **PIPEDA (Canada)**: Same basis — no personal health information processed
- **DISHA (India)**: Platform does not handle digital health data as defined
  under the Act

## 9. Contact
For privacy inquiries or data requests:
- **Email**: privacy@carvanta.ai
- **Website**: https://carvanta.ai/privacy

## 10. Changes to This Policy
We may update this policy periodically. Changes will be reflected in the
"Last Updated" date above. Continued use of the platform constitutes
acceptance of the updated policy.
