# CARVanta — Login & Authentication Walkthrough

This document explains how to access and authenticate with the CARVanta platform across all interfaces.

---

## 1. React Frontend (No Login Required — Open Access)

The React dashboard at `http://localhost:5173` is currently **open access** — no login wall.

**How to access:**
```bash
# Terminal 1: Start the API backend
cd CARVanta
py -m uvicorn api.main:app --port 8001

# Terminal 2: Start the React frontend
cd CARVanta/frontend-react
npm run dev
```
Then open **http://localhost:5173** in your browser.

> All 10 modules (Single Analysis, Comparison, Heatmap, Synergy, Stratification, NLP Search, Clinical Trials, Leaderboard, Dataset Intelligence, System Status) are immediately accessible from the sidebar.

---

## 2. API Access (API Key Authentication)

The FastAPI backend at `http://localhost:8001` uses **API key authentication** via the `X-CARVanta-API-Key` header.

### Available API Key Tiers

| Tier | Env Variable | Default Dev Key | Rate Limit |
|------|-------------|-----------------|------------|
| Free | `CARVANTA_API_KEY_DEV` | `carvanta-dev-key-001` | 60 req/min |
| Pro | `CARVANTA_API_KEY_PRO` | `carvanta-pro-key-001` | 300 req/min |
| Enterprise | `CARVANTA_API_KEY_ENTERPRISE` | `carvanta-enterprise-001` | 1,000 req/min |

### How to authenticate API requests

```bash
# Using curl
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -H "X-CARVanta-API-Key: carvanta-dev-key-001" \
  -d '{"antigen_name": "CD19"}'

# Using Python requests
import requests
r = requests.post(
    "http://localhost:8001/score",
    json={"antigen_name": "CD19"},
    headers={"X-CARVanta-API-Key": "carvanta-dev-key-001"}
)
print(r.json())
```

### How to configure your own keys

1. Open `.env` in the project root
2. Set your custom keys:
   ```
   CARVANTA_API_KEY_DEV=your-custom-dev-key
   CARVANTA_API_KEY_PRO=your-custom-pro-key
   CARVANTA_API_KEY_ENTERPRISE=your-custom-enterprise-key
   ```
3. Restart the API server — keys are loaded from environment variables at startup

---

## 3. Docker Deployment Access

When running via Docker Compose, the services are exposed on the same ports:

```bash
# Production (PostgreSQL + API + Frontend)
docker-compose up --build

# Development (SQLite + live reload)
docker-compose -f docker-compose.dev.yml up --build
```

| Service | URL | Auth |
|---------|-----|------|
| Frontend | http://localhost:8501 (Streamlit) or http://localhost:5173 (React) | None |
| API | http://localhost:8001 | API Key header |
| Database | localhost:5432 | PostgreSQL user/pass from `.env` |

### PostgreSQL credentials (production Docker)

Set in `.env` or `docker-compose.yml`:
```
POSTGRES_USER=carvanta
POSTGRES_PASSWORD=carvanta_secure_pw
```

---

## 4. Future: Enterprise SSO / OAuth Integration

For hospital-grade deployment, the platform is architected to support:

- **OAuth 2.0 / OIDC** via FastAPI middleware (Auth0, Okta, Azure AD)
- **SAML 2.0** for enterprise healthcare SSO
- **Role-Based Access Control (RBAC)** — Admin, Researcher, Clinician, Viewer
- **Session management** with JWT tokens stored in httpOnly cookies

> This is not yet implemented but the architecture supports it via the existing `RateLimitMiddleware` and `APIKey` database model.

---

## Quick Start Summary

| What you want | How to do it |
|---------------|-------------|
| View the dashboard | Open http://localhost:5173 |
| Call the API | Add `X-CARVanta-API-Key: carvanta-dev-key-001` header |
| Change API keys | Edit `.env` → restart server |
| Docker production | `docker-compose up --build` |
| Check system health | Visit http://localhost:8001/health |
