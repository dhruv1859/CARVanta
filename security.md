# Security Policy

## Supported Versions

| Version | Component | Status |
|---------|-----------|--------|
| 5.x | Platform (API + Frontend) | ✅ Supported |
| 4.x | Platform (API + Frontend) | ⚠️ Security fixes only |
| < 4.0 | Platform | ❌ End of life |
| v2.0 | Sentinel HYDRA (Hardware) | ✅ Supported |
| v1.0 | Sentinel (Hardware) | ❌ End of life |
| Latest | ESP32 Firmware | ✅ Supported |
| Latest | RP2040 Firmware | ✅ Supported |

---

## Reporting a Vulnerability

**⚠️ Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing:

📧 **dhruvagrawal1859@gmail.com**

Use the subject line format: `[SECURITY] Brief description of the issue`

### Please Include

- **Description** of the vulnerability
- **Steps to reproduce** (or proof-of-concept if available)
- **Affected component** (API, frontend, firmware, hardware, ML model)
- **Potential impact** (data exposure, patient safety, system compromise, etc.)
- **Suggested fix** (if any)
- **Your contact information** for follow-up

### Response Timeline

| Action | Timeline |
|--------|----------|
| Acknowledgment of report | Within **48 hours** |
| Initial assessment and severity classification | Within **5 business days** |
| Fix development (Critical/High) | Within **14 days** |
| Fix development (Medium/Low) | Within **30 days** |
| Public disclosure (coordinated) | After fix is released |

---

## Scope

### In Scope

| Area | Examples |
|------|----------|
| **API Security** | Authentication bypass, injection, SSRF, broken access control |
| **Frontend** | XSS, CSRF, open redirect, sensitive data in client-side storage |
| **Data Security** | Patient data exposure, database leaks, scoring data exfiltration |
| **ML/AI** | Model poisoning, adversarial inputs that produce unsafe scores |
| **Firmware** | Buffer overflow, debug port exposure, OTA update hijacking |
| **Hardware** | Design flaws that expose patient data or enable device tampering |
| **Dependencies** | Vulnerabilities in third-party libraries used by CARVanta |

### Out of Scope

- Vulnerabilities in third-party services (Railway, Vercel, GitHub) — report to those providers
- Social engineering attacks
- Denial of service without demonstrated impact
- Issues requiring physical access to a deployed Sentinel device (unless trivially exploitable)
- Reports from automated scanners without proof of exploitability

---

## Security Considerations by Component

### Software Platform

- **Authentication**: JWT with PBKDF2 password hashing; tokens expire after 24 hours
- **API Rate Limiting**: Configurable per-endpoint rate limits
- **CORS**: Whitelisted origins only in production
- **Database**: Parameterized queries; no raw SQL concatenation
- **Secrets**: All API keys stored in `.env` (gitignored); never committed to repository

### Sentinel HYDRA Hardware

- **Debug Ports**: JTAG/SWD header (J8) should be disabled or physically removed in production units
- **Firmware Updates**: OTA updates over HTTPS only; validate firmware checksums before flashing
- **Data in Transit**: All WiFi communication to CARVanta cloud uses TLS 1.2+
- **Data at Rest**: SD card logging uses timestamped CSV — consider encryption for sensitive deployments
- **Physical Security**: Board-level access to I2C/SPI buses could allow sensor spoofing — production enclosures should restrict access

### Patient Data Handling

CARVanta is designed with privacy in mind:

- **No patient PII** is stored in the biomarker database
- Digital Twin simulations use **anonymized patient profiles**
- Audit logging captures request metadata, not patient-identifiable data
- FHIR exports follow **HL7 FHIR R4** standards for interoperability
- See [PRIVACY_POLICY.md](PRIVACY_POLICY.md) for full HIPAA alignment details

---

## Severity Classification

We use the following severity levels (aligned with CVSS v3.1):

| Severity | CVSS | Description |
|----------|------|-------------|
| **Critical** | 9.0–10.0 | Remote code execution, patient data breach, unsafe scoring outputs |
| **High** | 7.0–8.9 | Authentication bypass, privilege escalation, firmware compromise |
| **Medium** | 4.0–6.9 | Information disclosure, limited access control bypass |
| **Low** | 0.1–3.9 | Minor information leaks, low-impact configuration issues |

---

## Acknowledgments

We are grateful to security researchers who report vulnerabilities responsibly. With your permission, we will acknowledge you in our [CHANGELOG.md](CHANGELOG.md) and on our GitHub repository.

---

## Contact

📧 **dhruvagrawal1859@gmail.com** — Security reports and inquiries

For non-security bugs, please use [GitHub Issues](https://github.com/dhruv1859/CARVanta/issues).
