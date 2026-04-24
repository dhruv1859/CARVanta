# CARVanta — Login & Authentication Walkthrough

This document explains how to access and authenticate with the CARVanta platform across all interfaces.

---

## 1. Quick Start (Recommended)

```bash
# Double-click start.bat or run:
cd CARVanta
start.bat
```

This launches both servers:
- **Backend API:** http://localhost:8001
- **Frontend Dashboard:** http://localhost:5173

> Wait ~15 seconds for the backend to finish loading, then open the frontend URL in your browser.

---

## 2. React Frontend (JWT Authentication)

The React dashboard at `http://localhost:5173` includes a full **login/registration system**.

### First Time — Create an Account

1. Open http://localhost:5173
2. Click **"Create Account"** tab
3. Fill in: Full Name, Username, Email, Password (min 8 chars), Role, Country
4. Click **"Create Account"**
5. In development mode, the account is **auto-verified** — you'll be logged in immediately
6. In production, a **6-digit email verification code** is sent to your email

### Returning User — Sign In

1. Open http://localhost:5173
2. Enter your **email or username** + password
3. Click **"Sign In"**

### Auth Bypass (Current Dev State)

> The login wall is currently **bypassed** for convenience during development. All modules are accessible without logging in. The auth system is fully functional and can be re-enabled by uncommenting the auth gate in `App.tsx`.

### Available Roles

| Role | Description | Access Level |
|------|-------------|-------------|
| 🔬 Researcher | Academic / lab researcher | Full analysis access |
| 🧑‍⚕️ Clinician | Medical professional | Full analysis + patient tools |
| 🩺 Patient | Patient self-service | Limited access |
| 🔑 Admin | Platform administrator | Full access + admin panel |

---

## 3. API Access (API Key Authentication)

The FastAPI backend at `http://localhost:8001` supports **API key authentication** via the `X-CARVanta-API-Key` header.

### Available API Key Tiers

| Tier | Env Variable | Default Dev Key | Rate Limit |
|------|-------------|-----------------|------------|
| Free | `CARVANTA_API_KEY_DEV` | `carvanta-dev-key-001` | 60 req/min |
| Pro | `CARVANTA_API_KEY_PRO` | `carvanta-pro-key-001` | 300 req/min |
| Enterprise | `CARVANTA_API_KEY_ENTERPRISE` | `carvanta-enterprise-001` | 1,000 req/min |

### How to authenticate API requests

```bash
# Using curl
curl -X POST http://localhost:8001/api/v5/score \
  -H "Content-Type: application/json" \
  -H "X-CARVanta-API-Key: carvanta-dev-key-001" \
  -d '{"antigen_name": "CD19"}'

# Using Python requests
import requests
r = requests.post(
    "http://localhost:8001/api/v5/score",
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

## 4. JWT Token Authentication (Programmatic)

For programmatic access with user-level auth:

```bash
# Register a new user
curl -X POST http://localhost:8001/api/v5/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user1", "password": "securepass123", "full_name": "Test User", "role": "researcher"}'

# Login and get JWT token
curl -X POST http://localhost:8001/api/v5/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username": "user@example.com", "password": "securepass123"}'

# Use the JWT token for authenticated requests
curl http://localhost:8001/api/v5/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 5. Docker Deployment Access

When running via Docker Compose, the services are exposed on the same ports:

```bash
# Production (PostgreSQL + API + Frontend)
docker-compose up --build

# Development (SQLite + live reload)
docker-compose -f docker-compose.dev.yml up --build
```

| Service | URL | Auth |
|---------|-----|------|
| Frontend | http://localhost:5173 (React) | JWT Login |
| API | http://localhost:8001 | API Key / JWT |
| API Docs | http://localhost:8001/docs | None |
| Database | localhost:5432 | PostgreSQL user/pass from `.env` |

---

## 6. Manual Start (Without start.bat)

```bash
# Terminal 1: Start the API backend
cd CARVanta
C:\Users\dhruv\carvanta_env\Scripts\python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8001

# Terminal 2: Start the React frontend
cd CARVanta/frontend-react
npm run dev
```

---

## 7. Enterprise Features (Built, Not Yet Deployed)

The platform includes enterprise auth infrastructure:

- **OAuth 2.0 / SSO** — Google, GitHub, Azure AD integration (`api/oauth2_sso.py`)
- **Multi-Factor Authentication** — TOTP-based MFA (`api/mfa_totp.py`)
- **Role-Based Access Control** — Admin, Researcher, Clinician, Patient roles (`api/auth.py`)
- **Email Verification** — 6-digit code via SMTP (`api/email_verification.py`)
- **Rate Limiting** — Per-user, per-endpoint, plan-aware (`api/rate_limiter.py`)
- **Audit Trail** — Tamper-proof, blockchain-style chained logging (`api/audit_logger.py`)
- **Billing** — Stripe-style subscription management (`api/billing.py`)

---

## Quick Start Summary

| What you want | How to do it |
|---------------|-------------|
| Launch everything | Run `start.bat` |
| View the dashboard | Open http://localhost:5173 |
| Call the API | Add `X-CARVanta-API-Key: carvanta-dev-key-001` header |
| Interactive API docs | Open http://localhost:8001/docs |
| Change API keys | Edit `.env` → restart server |
| Docker production | `docker-compose up --build` |
| Check system health | Visit http://localhost:8001/api/v5/health |
