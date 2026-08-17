# Sales pack & interview questions

## One-sentence pitch

FieldOps AI is an AI-assisted field operations intelligence platform built around offline-first mobile data collection, deterministic risk assessment, AI-powered contextual analysis, operational analytics, and observability.

## Who buys it

Utilities, municipalities, telecoms, industrial maintenance firms, and EPCs that still run inspections on paper or generic forms products and cannot explain *why* an asset was marked dangerous.

## Differentiation

| Typical forms app | FieldOps AI |
|-------------------|-------------|
| Score is a vibe or a model guess | Score is a published rule table |
| AI in the client with leaked keys | AI behind the API, validated JSON |
| Online-only | Queue + conflict status |
| Pretty charts, no ops | Prometheus/Grafana from day one |
| CRUD screens | State machines for inspections and work |

## Pricing sketch (for conversations, not a commitment)

- **Pilot:** one organization, 25 inspectors, 90 days, hosted by you
- **Team:** per-inspector / month + asset pack
- **Enterprise:** on-prem compose, SSO later, template professional services

## Technical interview questions you should be able to answer

1. Why is the risk engine deterministic if you already have Gemini?  
   *Because operators and regulators need an explainable number. The model interprets; it does not own the score.*

2. What happens when Gemini returns poetry instead of JSON?  
   *Validator rejects, retry, then heuristic fallback. Inspection is already persisted.*

3. How do you avoid duplicate inspections from a flaky radio?  
   *`local_id` on the client, upsert on push, version for conflicts.*

4. Why a modular monolith?  
   *Clear bounded contexts without network partitions between a 12-person product.*

5. Where is the Gemini key?  
   *Only on the server. The APK cannot leak it.*

6. How would you split services later?  
   *AI Analysis and Notifications first (asynchronous, independently scalable). Keep inspections + risk together.*

7. How do you stop the model from ordering a shutdown?  
   *Prompt constraints + phrase denylist + UI copy + human review state.*

8. What is the demo path?  
   *T-104, 91°C, oil, noise, damage, CRITICAL, work order, analytics.*

## Objection handling

**“This is just another Flutter CRUD app.”**  
Walk the state machine, the rule table, the validator, the sync statuses, and Grafana. Those are not CRUD.

**“We cannot use Google.”**  
The interface is `run_analysis()`. Swap the client; keep schema and fallback.

**“We already have SAP / Maximo.”**  
FieldOps is the field capture + intelligence edge. CSV/API export is the handshake. Work orders can later map to theirs.
