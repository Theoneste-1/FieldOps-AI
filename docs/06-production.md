# Production engineering

## Run modes


| Mode       | Database                           | Seed                      | Use                |
| ---------- | ---------------------------------- | ------------------------- | ------------------ |
| Local demo | SQLite `backend/.data/fieldops.db` | Yes                       | Laptop / interview |
| Compose    | PostgreSQL 16                      | Yes                       | Staging-like       |
| Production | PostgreSQL managed                 | No (SEED_DEMO_DATA=false) | Customer           |


## Docker

`docker compose up --build` starts API, Postgres, Prometheus, Grafana.

Grafana datasource is auto-provisioned. Dashboard **FieldOps AI — Operations** shows HTTP rate, inspection submissions, AI requests/failures, latency.

## Metrics

- `http_requests_total` / `http_request_duration_seconds`
- `inspection_submission_total`
- `ai_requests_total` / `ai_request_failures` / `ai_request_latency_seconds`
- `sync_failures`
- `risk_calculations_total`
- `work_orders_created_total`
- `critical_notifications_total`



## Logging

`structlog` JSON in production, console in debug. Startup logs environment and DB dialect, never secrets.

## Health

- `GET /health` liveness
- `GET /ready` database ping
- `GET /metrics` Prometheus scrape



## CI

Pull requests run pytest and Flutter tests.

Pushes to `main` build and publish Docker images to GHCR. Deployment over SSH starts only when you set `ENABLE_DEPLOY=true`.

Full runbook (DNS, nginx, TLS, production tests): [CI/CD and deployment](docs/08-cicd-and-deployment.md).

## Security checklist before a customer deploy

- [ ] Rotate `SECRET_KEY`
- [x] `SEED_DEMO_DATA=false`
- [ ] `APP_DEBUG=false`
- [ ] TLS terminator
- [ ] Restrict `CORS_ORIGINS`
- [ ] Store `GEMINI_API_KEY` in a secret manager
- [ ] Back up PostgreSQL
- [ ] Set upload volume backups
- [ ] Change Grafana admin password



## Testing

Backend: unit tests for risk, lifecycle, AI validator, sync conflicts, health.  
Flutter: risk engine wow-path test.

Add device integration tests in CI with a running API when you have a runner with Docker.

## Deployment sketch

1. Build API image
2. Migrate / `AUTO_CREATE_TABLES` for first install
3. Serve Flutter web from any static host **or** ship Android APK
4. Point the app at the customer API URL (login field)

