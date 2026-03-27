# CARVanta — Code Quality & Security Checklist

> **MANDATORY**: Every code edit must satisfy ALL items below.

## 🔐 1. Don't Expose API Keys
- [ ] All secrets stored in `.env` (gitignored)
- [ ] No hardcoded keys, tokens, or passwords in source code
- [ ] `.env.example` has placeholders only (no real values)
- [ ] `docker-compose` uses `env_file:` not inline secrets

## 🛡️ 2. Sanitize Inputs (Block SQLi & XSS)
- [ ] All user inputs validated and sanitized before processing
- [ ] SQLAlchemy ORM used (no raw SQL with string interpolation)
- [ ] HTML output escaped — no `dangerouslySetInnerHTML` without sanitization
- [ ] File paths validated — no path traversal (`../`)
- [ ] Request body size limits enforced

## ⚡ 3. Backend Scalability (Billions of Users)
- [ ] Async endpoints where possible (`async def`)
- [ ] Database connection pooling enabled
- [ ] Heavy computation offloaded to background tasks
- [ ] Caching layer for expensive queries (Redis-ready)
- [ ] Stateless API design (no server-side session state)
- [ ] Pagination on all list endpoints

## 🤖 4. Rate Limiting (Protect AI Endpoints from Bots)
- [ ] Global rate limiter active on all endpoints
- [ ] Stricter limits on AI/compute-heavy endpoints
- [ ] Per-user and per-IP rate tracking
- [ ] 429 Too Many Requests returned with `Retry-After` header
- [ ] API key tier-based quotas (Dev / Pro / Enterprise)

## 🔑 5. Prebuilt Auth (Firebase / Supabase)
- [ ] Authentication via proven provider (Firebase Auth / Supabase Auth)
- [ ] No custom JWT signing or session management in production
- [ ] OAuth2 / SSO support (Google, GitHub, ORCID)
- [ ] MFA support enabled
- [ ] Password hashing via bcrypt/argon2 (not SHA-256)

## 📌 6. API Versioning
- [ ] All endpoints under `/api/v5/` (current version)
- [ ] Breaking changes go to new version (`/api/v6/`)
- [ ] Old versions maintained for backward compatibility
- [ ] Version documented in API response headers
- [ ] Deprecation warnings added before removal

## 📁 7. Secure Uploads
- [ ] File type validated (whitelist: `.vcf`, `.bam`, `.fastq`, `.csv`, `.pdf`)
- [ ] File size limits enforced (configurable per tier)
- [ ] Uploaded files stored in isolated directory (not in app root)
- [ ] No executable files accepted (`.exe`, `.sh`, `.bat`, `.py` blocked)
- [ ] Virus/malware scan on uploaded files (ClamAV-ready)
- [ ] Filenames sanitized (no special characters)

## 📦 8. Scan Dependencies
- [ ] Dependabot enabled on GitHub (`.github/dependabot.yml`)
- [ ] No pinned versions older than 6 months without justification
- [ ] `pip audit` / `npm audit` run before each release
- [ ] Known CVEs patched within 48 hours
- [ ] Lock files committed (`package-lock.json`, `requirements.txt`)

---

> **Rule**: From this point forward, every code change must be cross-checked against this list. If a change violates any item, it must be fixed before merging.
