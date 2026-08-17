# FieldOps AI

**An AI-assisted field operations intelligence platform built around offline-first mobile data collection, deterministic risk assessment, AI-powered contextual analysis, operational analytics, and observability.**

FieldOps AI is a sellable product for organizations that inspect physical assets — electrical infrastructure, buildings, roads, water networks, telecom, construction sites, and industrial equipment.

> **AI assists decision-making; AI does not control critical business rules.**

The mobile app calculates and the backend persists a **deterministic risk score**. Google Gemini (when configured) interprets observations and proposes recommendations. Humans still review, assign work, and close findings.

---

## What you can demo in 4 minutes

1. Sign in as `inspector@fieldops.ai` / `Demo@12345`
2. Open the **map** and select transformer **T-104**
3. Start inspection with the preset story: **91°C**, oil leakage **Yes**, noise **High**, visual damage **Yes**
4. Submit — risk engine returns **CRITICAL** (~87/100)
5. Read the AI insight (Gemini or the built-in heuristic fallback)
6. Open **work orders** (auto-drafted for critical findings) and **analytics**

The same story works **offline**. Inspections are stored on the device and synchronized when the API is reachable.

---

## Repository layout

| Path | Role |
|------|------|
| `backend/` | FastAPI modular backend (identity, assets, inspections, risk, AI, analytics, sync, notifications) |
| `mobile/` | Flutter app (Android + web) — feature-first, Riverpod, offline-capable |
| `docs/` | Product, architecture, data, AI, UX, production, sales, **CI/CD** |
| `infra/` | Prometheus, Grafana, nginx, Dockerfiles |
| `deploy/` | Production env template |
| `docker-compose.yml` | Local demo stack |
| `docker-compose.prod.yml` | Server stack (images + nginx) |

---

## Technology stack

| Layer | Technology |
| ---------------- | ----------------------------------- |
| Mobile | Flutter / Dart |
| State | Riverpod |
| Local cache / queue | SharedPreferences + sync protocol |
| Backend | Python / FastAPI |
| API | REST / JSON |
| Database | PostgreSQL (production) or SQLite (local demo) |
| AI | Google Gemini API behind the backend |
| Authentication | JWT |
| Maps | OpenStreetMap via flutter_map |
| Analytics | Dedicated analytics queries |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Containerization | Docker Compose |
| CI | GitHub Actions |
| Testing | pytest + Flutter tests |

---

## Quick start (local, no Docker)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example ..\.env
cd ..
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --reload --app-dir backend --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Demo users (password `Demo@12345`):

- `inspector@fieldops.ai`
- `supervisor@fieldops.ai`
- `manager@fieldops.ai`
- `admin@fieldops.ai`

### 2. Flutter app

```powershell
cd mobile
flutter pub get
flutter run -d chrome
# or: flutter run   (Android device / emulator)
```

On an Android emulator the default API URL is `http://10.0.2.2:8000`. On web/desktop it is `http://localhost:8000`. You can change it on the login screen.

If the API is down, the same demo credentials still open a full **offline demo tenant**.

### 3. Production-style stack

```powershell
copy .env.example .env
docker compose up --build
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Grafana | http://localhost:3000 (admin / fieldops) |
| Prometheus | http://localhost:9090 |

Set `GEMINI_API_KEY` in `.env` to enable live Gemini. Without it, the heuristic analyzer still returns structured, validated insights so the product never hard-depends on a model vendor.

---

## GitHub Actions → server → nginx

Pushing to GitHub is enough to **test and publish images**. Mapping domains happens on the VPS when DNS exists.

| When | What happens |
|------|----------------|
| Open a pull request | pytest + Flutter tests |
| Push `main` | Same tests, then Docker images to `ghcr.io/<you>/fieldopsai/api` and `.../web` |
| Set variable `ENABLE_DEPLOY=true` | SSH to the VPS, pull those images, `docker compose up` |
| Point `app.` / `api.` / `grafana.` A records at the server | nginx serves them on port 80, then Let's Encrypt on 443 |

Step-by-step (secrets, DNS, TLS, production checklist): **[docs/08-cicd-and-deployment.md](docs/08-cicd-and-deployment.md)**

---

## Architecture in one picture

```text
                 FIELD DATA
                     │
                     ▼
                Flutter App
                     │
          ┌──────────┴──────────┐
          │                     │
       Offline                Online
          │                     │
      Local queue              API
                                │
              ┌─────────────────┼────────────────┐
              │                 │                │
          PostgreSQL       Risk Engine       AI Service
                                                 │
                                               Gemini
              │                 │                │
              └─────────────────┼────────────────┘
                                │
                           Analytics
                                │
                         Prometheus / Grafana
```

The backend is a **modular monolith** with explicit service boundaries (Identity, Assets, Inspections, AI Analysis, Analytics, Notifications, Sync). That is the right shape to sell and operate first; the modules can be split into processes later without rewriting the domain.

---

## Security decisions that matter

- The **Gemini API key never ships in the APK**. Flutter talks only to FieldOps. FieldOps talks to Gemini.
- JWT access + refresh tokens, role-based authorization, org isolation on every query.
- Audit log for inspections, work orders, logins, and asset changes.
- AI output is schema-validated. Shutdown / legal / financial language is rejected.
- Secrets live in environment variables, not source control.

---

## Documentation

1. [Product specification](docs/01-product-specification.md)
2. [System architecture](docs/02-system-architecture.md)
3. [Data model, risk engine & analytics](docs/03-data-and-risk.md)
4. [AI engineering](docs/04-ai-engineering.md)
5. [UX / demo specification](docs/05-ux-and-demo.md)
6. [Production engineering](docs/06-production.md)
7. [Sales & interview pack](docs/07-sales-and-interviews.md)

---

## Tests

```powershell
cd backend
pytest
cd ..\mobile
flutter test
```

---

## License

Copyright © 2026 FieldOps AI. All rights reserved. This repository is a commercial product codebase; contact the owner for licensing.
