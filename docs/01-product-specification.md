# Product specification

**Product:** FieldOps AI  
**Document type:** Software Requirements Specification (product layer)  
**Audience:** buyers, domain SMEs, interviewers

## 1. Problem

Field organizations still collect evidence on paper, spreadsheets, chat threads, and disconnected databases. That produces three failures:

1. **Poor data quality** — “transformer hot”, “temperature high”, and “seems overheated” are the same event described four ways.
2. **Delayed decisions** — a dangerous condition can sit on a device or in a notebook for hours.
3. **No historical intelligence** — thousands of inspections exist, but nobody can answer which assets fail, where, or whether a category is trending up.

## 2. Product vision

Turn field observations into structured operational intelligence.

```text
Physical world → Field worker → Mobile app → Structured data
        → Risk engine → AI analysis → Analytics → Business decision
```

## 3. Objectives

| ID | Objective | Success measure |
|----|-----------|-----------------|
| O1 | Capture structured inspections offline | Inspector completes T-104 with no network |
| O2 | Score risk deterministically | Same inputs always produce the same score |
| O3 | Assist, not replace, supervisors | AI never shuts down plant or approves work |
| O4 | Close the loop | Critical finding can become a work order |
| O5 | Make operations visible | KPI dashboard updates after submit |
| O6 | Be operable | Metrics, logs, health, and audit exist |

## 4. Personas

**Field inspector** — captures observations, photos, measurements; needs the app to work in basements, rural feeders, and substations with no signal.

**Supervisor** — reviews critical findings the same morning, assigns follow-up, reads AI briefs without trusting them blindly.

**Operations manager** — watches trends, failing assets, resolution time, inspector productivity.

**Administrator** — users, roles, templates, risk configuration, organization settings.

## 5. User stories (priority slice)

1. As an inspector, I can sign in and see my organization’s assets on a map.
2. As an inspector, I can start an inspection on an asset with no connectivity.
3. As an inspector, I can record temperature, leakage, noise, damage, notes, and a photo.
4. As the system, I calculate a 0–100 risk score from explicit rules before any model is called.
5. As an inspector, I see a meaningful message if the network or AI is down — data is not lost.
6. As a supervisor, I am notified when risk is CRITICAL.
7. As a supervisor, I can review an inspection and resolve it.
8. As a supervisor, I can assign, progress, complete, and verify a work order.
9. As a manager, I can see KPIs, risk distribution, issue categories, and failing assets.
10. As an admin, I can create users and export inspections to CSV.
11. As the device, I can push pending records and pull server changes with conflict detection.
12. As the organization, I can configure measurement thresholds per asset type.

## 6. Functional requirements

| ID | Requirement |
|----|-------------|
| FR-01 | JWT login, refresh, and role-aware API access |
| FR-02 | Multi-tenant isolation by `organization_id` |
| FR-03 | Asset register with type, location, GPS, current risk |
| FR-04 | Inspection templates as JSON form schemas |
| FR-05 | Inspection lifecycle state machine (draft → … → resolved, plus AI failure path) |
| FR-06 | Observations, measurements, and media as first-class records |
| FR-07 | Deterministic risk engine with versioned rules and cap at 100 |
| FR-08 | AI analysis service with prompt, validation, retry, fallback |
| FR-09 | Auto-notify supervisors on CRITICAL; optional auto-draft work order |
| FR-10 | Work order lifecycle separate from inspection lifecycle |
| FR-11 | Analytics KPIs computed from operational data |
| FR-12 | Map API with risk filter and bounding box |
| FR-13 | Sync push/pull with `local_id`, `version`, `sync_status` |
| FR-14 | Audit log for sensitive mutations |
| FR-15 | CSV export for inspections |
| FR-16 | Recurring inspection schedules and due lists |

## 7. Non-functional requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | Offline capture | Full inspection without API |
| NFR-02 | Auth | Tokens expire; passwords hashed with bcrypt |
| NFR-03 | AI isolation | Model credentials only on the server |
| NFR-04 | Observability | Prometheus metrics + structured logs + /health /ready |
| NFR-05 | Validation | Pydantic in, schema check on AI out |
| NFR-06 | Resilience | Gemini timeout, retry, heuristic fallback |
| NFR-07 | Performance | Inspection submit path < 3s excluding model latency |
| NFR-08 | Auditability | Who changed what, when, old/new value |
| NFR-09 | Portability | SQLite demo, PostgreSQL production |
| NFR-10 | Accessibility of demo | Four roles, one password, one wow-path |

## 8. Acceptance criteria — wow path

Given inspector Thabo is on T-104  
When he records 91°C, oil leakage, high noise, visual damage and submits  
Then risk is CRITICAL (≥ 81)  
And an AI insight with causes and recommendations is stored  
And a supervisor notification exists  
And a draft critical work order can be opened  
And analytics critical count increases  

## 9. Out of scope for v1 (explicit)

- Billing / payments
- Native iOS App Store submission (code is ready; signing is a release step)
- Full CMMS inventory of spare parts
- Automated plant shutdown
- Legal compliance determination
- Drone / IoT telemetry ingest (architecture allows a future telemetry table)
