# Data model, risk engine & analytics

## 1. ER (logical)

```text
Organization
 ├── Users (role: inspector | supervisor | operations_manager | admin)
 ├── Teams
 ├── Locations (region → site → zone)
 ├── AssetTypes (thresholds, risk_config)
 ├── InspectionTemplates (JSON schema)
 ├── Assets
 │    ├── InspectionSchedules
 │    └── Inspections
 │         ├── Observations
 │         ├── Measurements
 │         ├── MediaItems
 │         ├── RiskAssessment     (1:1)
 │         └── AIAnalysis         (1:1)
 ├── WorkOrders
 ├── Notifications
 ├── Comments
 ├── AuditLogs
 └── SyncDevices
```

## 2. Indexes that matter

- `assets (organization_id, status)`
- `assets.organization_id + code` unique
- `inspections (organization_id, status)`
- `audit_logs (organization_id, created_at)`
- `notifications.user_id`

## 3. Risk engine (authoritative, server)

Version `1.1`. Weights are configurable per asset type; defaults:

| Rule | Points |
|------|--------|
| Temperature abnormality | 25 |
| Oil leakage | 25 |
| Structural damage | 20 |
| Abnormal sound | 15 |
| Previous failures (180 days high/critical) | 15 |
| Electrical anomaly | 20 |
| Corrosion | 10 |
| Safety hazard | 15 |
| Out-of-range measurement | 20 |
| Immediate danger flag | 40 (also floors score at 81) |

Score is **capped at 100**.

| Score | Level |
|------:|-------|
| 0–30 | LOW |
| 31–60 | MEDIUM |
| 61–80 | HIGH |
| 81–100 | CRITICAL |

Measurements prefer numeric thresholds over language. Free text is only a backstop (“oil around the bottom”).

The engine is a **pure function**. Same inputs → same outputs. That is what you sell to a utility: explainability.

## 4. Analytics (read model)

Analytics does not write inspections. It aggregates:

- inspections completed / pending / critical
- average risk and duration
- open and overdue work orders
- due schedules
- inspections over time
- risk distribution
- issues by observation category
- assets by current risk
- inspector productivity
- resolution time (submit → resolve, hours)
- top failing assets

## 5. Extra product logic included because this is meant to be sold

- **Previous-failure lookback** feeds the risk score so repeat offenders rise faster.
- **Schedules / SLA hours** so “what is due?” is a first-class question.
- **Auto work order on CRITICAL** is an organization setting, not hardcoded forever.
- **Idempotent demo seed** so a trial tenant always contains T-104.
- **CSV export** for the buyer’s existing CMMS.
- **Comments** on any entity for supervisor discussion.
- **Asset hierarchy** (`parent_id`) for bay → transformer.
- **Soft operational states** on assets (active / maintenance / decommissioned).
