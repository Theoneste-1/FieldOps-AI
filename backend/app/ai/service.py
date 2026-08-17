"""Gemini-backed analysis with a deterministic fallback.

The AI service never calculates risk scores, never shuts down equipment, and never
approves work. It interprets observations and proposes recommendations that a human
must still accept.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from app.config import get_settings
from app.logging import get_logger
from app.metrics import ai_request_failures, ai_request_latency, ai_requests_total

PROMPT_VERSION = "1.1"
logger = get_logger("ai")

REQUIRED_FIELDS = ("risk_summary", "possible_causes", "recommendations", "confidence", "severity")
ALLOWED_SEVERITY = {"low", "medium", "high", "critical"}
FORBIDDEN_PHRASES = (
    "shut down immediately",
    "you must isolate",
    "legally non-compliant",
    "approved for maintenance",
    "authorize expenditure",
)

SYSTEM_INSTRUCTIONS = """You are FieldOps AI, a decision-support assistant for field inspections.
You interpret structured inspection data. You do NOT make operational, legal, financial, or emergency decisions.

Never instruct the operator to shut down equipment, declare legal compliance, classify an emergency,
approve maintenance, or make financial commitments. Phrase recommendations as suggestions for a qualified supervisor.

Return ONLY valid JSON with this schema:
{
  "risk_summary": string,
  "possible_causes": string[3-6],
  "recommendations": string[3-6],
  "supervisor_brief": string,
  "confidence": number between 0 and 1,
  "severity": "low" | "medium" | "high" | "critical"
}
"""


class AIValidationError(Exception):
    pass


def build_context(inspection: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset": {
            "code": inspection.get("asset_code"),
            "name": inspection.get("asset_name"),
            "type": inspection.get("asset_type"),
            "category": inspection.get("asset_category"),
        },
        "risk": {
            "score": inspection.get("risk_score"),
            "level": inspection.get("risk_level"),
            "breakdown": inspection.get("risk_breakdown") or [],
        },
        "observations": inspection.get("observations") or [],
        "measurements": inspection.get("measurements") or [],
        "notes": inspection.get("notes"),
        "weather": inspection.get("weather"),
        "history": {
            "previous_high_or_critical": inspection.get("previous_high_or_critical", 0),
            "open_work_orders": inspection.get("open_work_orders", 0),
        },
        "constraints": {
            "ai_does_not_decide_shutdown": True,
            "ai_does_not_decide_compliance": True,
            "human_review_required": True,
        },
    }


def build_prompt(context: dict[str, Any]) -> str:
    return (
        SYSTEM_INSTRUCTIONS
        + "\n\nInspection context:\n"
        + json.dumps(context, default=str, indent=2)
        + "\n\nWrite a concise supervisor brief (max 80 words)."
    )


def validate_ai_payload(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise AIValidationError(f"Missing fields: {', '.join(missing)}")

    summary = str(payload.get("risk_summary") or "").strip()
    if len(summary) < 12:
        raise AIValidationError("risk_summary is too short")

    causes = payload.get("possible_causes")
    recs = payload.get("recommendations")
    if not isinstance(causes, list) or len(causes) < 1:
        raise AIValidationError("possible_causes must be a non-empty list")
    if not isinstance(recs, list) or len(recs) < 1:
        raise AIValidationError("recommendations must be a non-empty list")

    try:
        confidence = float(payload["confidence"])
    except (TypeError, ValueError) as exc:
        raise AIValidationError("confidence must be numeric") from exc
    if not 0 <= confidence <= 1:
        raise AIValidationError("confidence must be between 0 and 1")

    severity = str(payload.get("severity", "")).lower()
    if severity not in ALLOWED_SEVERITY:
        raise AIValidationError("severity is not an allowed value")

    joined = " ".join([summary, *map(str, causes), *map(str, recs), str(payload.get("supervisor_brief") or "")]).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in joined:
            raise AIValidationError(f"Response contains a disallowed operational decision: {phrase}")

    return {
        "risk_summary": summary,
        "possible_causes": [str(item).strip() for item in causes if str(item).strip()][:6],
        "recommendations": [str(item).strip() for item in recs if str(item).strip()][:6],
        "supervisor_brief": str(payload.get("supervisor_brief") or summary).strip(),
        "confidence": round(confidence, 3),
        "severity": severity,
    }


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise AIValidationError("Response was not valid JSON")
    data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise AIValidationError("JSON root must be an object")
    return data


def heuristic_analyze(context: dict[str, Any]) -> dict[str, Any]:
    """Offline-capable analyzer used when Gemini is unavailable.

    This is still advisory. It maps deterministic risk evidence to human-readable
    interpretation so the product remains demoable and resilient.
    """
    risk = context.get("risk") or {}
    level = str(risk.get("level") or "medium")
    score = int(risk.get("score") or 0)
    breakdown = risk.get("breakdown") or []
    keys = {item.get("key") for item in breakdown}
    observations = context.get("observations") or []
    blob = " ".join(str(item.get("value_text") or item.get("label") or "") for item in observations).lower()

    causes: list[str] = []
    recs: list[str] = []
    if "temperature_abnormal" in keys or "temp" in blob:
        causes.append("Possible cooling or overload condition driving elevated operating temperature")
        recs.append("Verify operating temperature against the asset nameplate and cooling system")
    if "oil_leakage" in keys or "oil" in blob:
        causes.append("Potential seal, gasket, or tank integrity failure")
        recs.append("Inspect oil sealing system, catchments, and insulation fluid level")
    if "abnormal_sound" in keys or "noise" in blob:
        causes.append("Possible mechanical degradation, loose fittings, or incipient electrical discharge")
        recs.append("Perform a close mechanical and acoustic inspection under safe conditions")
    if "structural_damage" in keys or "damage" in blob:
        causes.append("Physical impact, foundation movement, or long-term structural fatigue")
        recs.append("Photograph damage extents and schedule a structural follow-up")
    if "electrical_anomaly" in keys:
        causes.append("Insulation stress or protection-system activity")
        recs.append("Review protection events and insulation condition with a qualified technician")
    if "previous_failures" in keys:
        causes.append("Recurring defect pattern on this asset")
        recs.append("Compare with the last three inspections before closing the finding")
    if not causes:
        causes.append("No dominant failure mode isolated from the captured evidence")
        recs.append("Complete the remaining checklist items and keep the asset on the normal inspection cadence")

    recs.append("A qualified supervisor should review this analysis before any operational action")
    summary = (
        f"Deterministic risk is {level.upper()} ({score}/100). "
        "AI assistance interpreted the captured observations; it did not change the risk score."
    )
    brief = (
        f"{context.get('asset', {}).get('code') or 'Asset'} inspected with {level} risk. "
        f"Primary evidence: {', '.join(item.get('label', '') for item in breakdown[:3]) or 'routine findings'}. "
        "Recommendations are advisory pending supervisor review."
    )
    confidence = 0.62 if breakdown else 0.4
    return validate_ai_payload(
        {
            "risk_summary": summary,
            "possible_causes": causes[:5],
            "recommendations": recs[:5],
            "supervisor_brief": brief,
            "confidence": confidence,
            "severity": level if level in ALLOWED_SEVERITY else "medium",
        }
    )


async def analyze_with_gemini(prompt: str) -> tuple[dict[str, Any], str, int]:
    settings = get_settings()
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent"
    )
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
        response = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            },
        )
    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        raise AIValidationError(f"Gemini HTTP {response.status_code}: {response.text[:400]}")
    body = response.json()
    text = (
        body.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    if not text:
        raise AIValidationError("Gemini returned an empty candidate")
    return extract_json(text), text, latency_ms


async def run_analysis(inspection_context: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    context = build_context(inspection_context)
    prompt = build_prompt(context)
    last_error = "unknown"

    if settings.gemini_api_key:
        for attempt in range(settings.gemini_max_retries + 1):
            started = time.perf_counter()
            try:
                raw_json, raw_text, latency_ms = await analyze_with_gemini(prompt)
                payload = validate_ai_payload(raw_json)
                ai_requests_total.labels(status="success").inc()
                ai_request_latency.observe(latency_ms / 1000)
                return {
                    **payload,
                    "provider": "gemini",
                    "model": settings.gemini_model,
                    "prompt_version": PROMPT_VERSION,
                    "raw_response": raw_text,
                    "latency_ms": latency_ms,
                    "used_fallback": False,
                    "status": "completed",
                    "error_message": None,
                    "retry_count": attempt,
                }
            except Exception as exc:  # noqa: BLE001 — convert any provider failure into fallback
                last_error = str(exc)
                logger.warning("gemini_attempt_failed", attempt=attempt, error=last_error)
                ai_request_failures.labels(reason="gemini").inc()
                ai_request_latency.observe(time.perf_counter() - started)

    fallback = heuristic_analyze(context)
    ai_requests_total.labels(status="fallback").inc()
    return {
        **fallback,
        "provider": "heuristic",
        "model": "fieldops-heuristic-1.1",
        "prompt_version": PROMPT_VERSION,
        "raw_response": json.dumps(fallback),
        "latency_ms": 5,
        "used_fallback": True,
        "status": "completed",
        "error_message": None if not settings.gemini_api_key else f"Fell back after Gemini error: {last_error}",
        "retry_count": settings.gemini_max_retries if settings.gemini_api_key else 0,
    }
