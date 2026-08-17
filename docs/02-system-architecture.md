# System architecture

## 1. C4 — context

```text
[Inspector phone] --HTTPS--> [FieldOps API] --HTTPS--> [Gemini]
        |                          |
        |                     [PostgreSQL]
        |                          |
   [Local queue]              [Prometheus → Grafana]
```

Actors: Inspector, Supervisor, Operations Manager, Admin.  
External systems: Gemini, OSM tiles (maps), email/push in a later increment (in-app notifications ship now).

## 2. C4 — containers

| Container | Responsibility |
|-----------|----------------|
| Flutter app | Presentation, local queue, on-device risk preview, maps |
| API (FastAPI modular monolith) | Auth, domain services, AI orchestration, analytics |
| PostgreSQL | System of record |
| Prometheus / Grafana | SLIs for HTTP, AI, sync, inspections |

## 3. Why not 25 microservices

Service boundaries exist **inside the API package** (`identity`, `assets`, `inspections`, `ai`, `analytics`, `notifications`, `sync`). That demonstrates the same domain split a buyer would later deploy as separate processes, without paying distributed-systems tax on day one.

## 4. Flutter architecture

```text
lib/
  core/          network, session, theme, risk engine, models
  features/      authentication, dashboard, assets, inspections,
                 ai_analysis (rendered on inspection detail),
                 analytics, maps, work_orders, notifications,
                 profile, sync
```

Each feature is presentation on top of the shared `SessionController` (application service) which talks to `FieldOpsApi` (data) and the local queue (data). Domain rules for risk live in `RiskEngine` on device **and** `app/engines/risk.py` on the server. The server is authoritative.

## 5. Backend modules

| Module | Owns |
|--------|------|
| Identity | Users, JWT, roles |
| Directory | Assets, types, locations, users admin |
| Inspections | Lifecycle, observations, measurements, media |
| Risk engine | Pure function, versioned rules |
| AI analysis | Prompt, Gemini client, validator, fallback |
| Work orders | Action loop |
| Analytics | Aggregations, not OLTP writes |
| Notifications | Inbox for supervisors / inspectors |
| Sync | Push/pull, conflict |
| Admin | Templates, CSV export, rule catalog |

## 6. Inspection state machine

```text
DRAFT → IN_PROGRESS → SUBMITTED → PROCESSING → ANALYZED → REVIEWED → RESOLVED
                                           ↘ AI_FAILED → PENDING_RETRY → PROCESSING
```

Illegal jumps are rejected. That is a product rule, not a UI convenience.

## 7. Offline sync

Every locally created inspection carries:

`local_id`, `server_id`, `created_at`, `updated_at`, `sync_status`, `version`

`sync_status`: PENDING, SYNCING, SYNCED, FAILED, CONFLICT.

Conflicts are **not** silently last-write-wins when versions diverge. The API returns CONFLICT so a future UI can merge; the current client retries after the user is online with a new version when the server accepted the create.

## 8. Security architecture

- HTTPS in production (compose behind a TLS terminator).
- JWT access + refresh.
- Role checks on review, user admin, export.
- Org-scoped queries.
- Upload size cap.
- Gemini key only in API environment.
- Audit log.

## 9. Request path for submit

```text
Flutter POST /inspections
Flutter POST /inspections/{id}/submit
  → state SUBMITTED → PROCESSING
  → risk engine (deterministic)
  → update asset.current_risk_*
  → AI service (Gemini or heuristic)
  → ANALYZED or AI_FAILED
  → if CRITICAL: notify supervisors + optional work order
  → audit
```
