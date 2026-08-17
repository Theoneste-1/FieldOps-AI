# AI engineering

## 1. Placement

Gemini is an **AI Analysis Service**, not a widget helper.

```text
Flutter → API → Prompt builder → Context builder → Gemini client
                 → Response validator → Storage
                 → fallback heuristic if the model fails
```

The APK never contains `GEMINI_API_KEY`.

## 2. Responsibilities (allowed)

- Interpret messy observations into a supervisor-readable summary
- Suggest possible causes
- Suggest recommended **next checks**
- Write a short supervisor brief

## 3. Non-responsibilities (forbidden)

Gemini must not independently decide:

- equipment shutdown
- legal compliance
- emergency classification
- final maintenance approval
- financial commitments

The validator rejects those phrases. The UI states the boundary in the insight card.

## 4. Context construction

The model receives structured JSON: asset identity, **already-calculated** risk score and breakdown, observations, measurements, notes, weather, recent high/critical count. It is told the score is not its job.

## 5. Structured output

```text
risk_summary
possible_causes[]
recommendations[]
supervisor_brief
confidence   (0–1)
severity     (low|medium|high|critical)
```

Malformed JSON, missing fields, empty lists, or out-of-range confidence → reject → retry → fallback.

## 6. Fallback

If `GEMINI_API_KEY` is empty or the provider errors, `heuristic_analyze` maps triggered risk rules to readable causes/recommendations. The product remains demoable and operable. `used_fallback` is stored so supervisors know which brain they are reading.

## 7. Evaluation (what we test)

Not “did the model return something?”

- valid JSON
- required fields
- confidence bounds
- forbidden operational language
- timeout / HTTP failure path
- heuristic still advisory (mentions supervisor review)

## 8. Prompt versioning

`PROMPT_VERSION = 1.1` is persisted on `ai_analyses` so you can compare quality after prompt changes.
