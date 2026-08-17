"""Deterministic risk engine.

AI never owns this score. Rules are explicit, versioned, and configurable per
asset type / organization. The engine is pure: given observations, measurements,
and historical context, it returns a reproducible score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from app.models.entities import ObservationCategory, RiskLevel

RULES_VERSION = "1.1"


@dataclass(frozen=True)
class RiskRule:
    key: str
    label: str
    weight: int
    description: str


DEFAULT_RULES: tuple[RiskRule, ...] = (
    RiskRule("temperature_abnormal", "Temperature abnormality", 25, "Measured or observed temperature outside safe range"),
    RiskRule("oil_leakage", "Oil leakage", 25, "Visible oil, coolant, or insulating fluid leak"),
    RiskRule("structural_damage", "Structural damage", 20, "Cracks, deformation, impact, or foundation issues"),
    RiskRule("abnormal_sound", "Abnormal sound", 15, "Unusual noise, vibration, or arcing sound"),
    RiskRule("previous_failures", "Previous failures", 15, "Recent high/critical findings on the same asset"),
    RiskRule("electrical_anomaly", "Electrical anomaly", 20, "Discharge, burning smell, tripped protection, insulation damage"),
    RiskRule("corrosion", "Corrosion / weathering", 10, "Advanced corrosion, rust, or weather deterioration"),
    RiskRule("safety_hazard", "Safety hazard", 15, "Missing guards, exposed conductors, blocked access, PPE gaps"),
    RiskRule("out_of_range_measurement", "Out-of-range measurement", 20, "Any captured measurement outside configured thresholds"),
    RiskRule("immediate_danger", "Immediate danger flag", 40, "Inspector marked an imminent-danger condition"),
)

DEFAULT_THRESHOLDS = {
    "temperature": {"max": 80.0, "unit": "°C"},
    "oil_temperature": {"max": 85.0, "unit": "°C"},
    "load": {"max": 90.0, "unit": "%"},
    "vibration": {"max": 7.1, "unit": "mm/s"},
    "humidity": {"max": 85.0, "unit": "%"},
    "voltage": {"min": 0.0},
}

LEVEL_BANDS = (
    (30, RiskLevel.LOW),
    (60, RiskLevel.MEDIUM),
    (80, RiskLevel.HIGH),
    (100, RiskLevel.CRITICAL),
)


def classify(score: int) -> RiskLevel:
    for upper, level in LEVEL_BANDS:
        if score <= upper:
            return level
    return RiskLevel.CRITICAL


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"yes", "true", "high", "severe", "critical", "present", "1", "leak", "damaged"}


def _positive_finding(item: dict[str, Any]) -> bool:
    """A checklist row is a finding only if the captured value is affirmative.

    Labels such as "Oil leakage" must not score points when the inspector recorded No.
    """
    if item.get("value_bool") is False:
        return False
    if item.get("value_bool") is True:
        return True
    text = str(item.get("value_text") or "").strip().lower()
    if text in {"", "no", "none", "normal", "ok", "n/a", "na", "false", "0", "low"}:
        return False
    return _truthy(text) or text in {"yes", "high", "severe", "critical", "elevated", "present", "damaged"}


def _text_blob(observations: Iterable[dict[str, Any]]) -> str:
    """Free-text evidence only — never field labels, which would false-positive."""
    parts: list[str] = []
    for item in observations:
        if item.get("value_text") and _positive_finding(item):
            parts.append(str(item["value_text"]))
        notes = (item.get("structured") or {}).get("notes") if isinstance(item.get("structured"), dict) else None
        if notes:
            parts.append(str(notes))
    return " ".join(parts).lower()


def _matches_any(blob: str, keywords: tuple[str, ...]) -> bool:
    return any(word in blob for word in keywords)


@dataclass
class RiskResult:
    score: int
    level: RiskLevel
    breakdown: list[dict[str, Any]] = field(default_factory=list)
    rules_version: str = RULES_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level.value,
            "breakdown": self.breakdown,
            "rules_version": self.rules_version,
        }


def calculate_risk(
    observations: list[dict[str, Any]] | None = None,
    measurements: list[dict[str, Any]] | None = None,
    previous_high_or_critical: int = 0,
    risk_config: dict[str, Any] | None = None,
    measurement_thresholds: dict[str, Any] | None = None,
) -> RiskResult:
    """Compute a capped 0–100 score from structured field evidence."""
    observations = observations or []
    measurements = measurements or []
    config = risk_config or {}
    weights = {rule.key: int(config.get("weights", {}).get(rule.key, rule.weight)) for rule in DEFAULT_RULES}
    thresholds = {**DEFAULT_THRESHOLDS, **(measurement_thresholds or {})}

    blob = _text_blob(observations)
    triggered: list[dict[str, Any]] = []

    def fire(key: str, evidence: str) -> None:
        rule = next(item for item in DEFAULT_RULES if item.key == key)
        triggered.append(
            {
                "key": key,
                "label": rule.label,
                "points": weights[key],
                "evidence": evidence,
                "description": rule.description,
            }
        )

    abnormal_measurements: list[str] = []
    temperature_abnormal = False
    for item in measurements:
        value = float(item.get("value", 0))
        key = str(item.get("field_key", "")).lower()
        min_t = item.get("min_threshold")
        max_t = item.get("max_threshold")
        if min_t is None and key in thresholds:
            min_t = thresholds[key].get("min")
        if max_t is None and key in thresholds:
            max_t = thresholds[key].get("max")
        is_abnormal = False
        if min_t is not None and value < float(min_t):
            is_abnormal = True
        if max_t is not None and value > float(max_t):
            is_abnormal = True
        item["is_abnormal"] = is_abnormal
        if is_abnormal:
            label = item.get("label") or key
            abnormal_measurements.append(f"{label}={value}{item.get('unit') or ''}")
            if "temp" in key or "temperature" in key:
                temperature_abnormal = True

    if temperature_abnormal or _matches_any(
        blob, ("overheat", "too hot", "hot equipment", "high temperature", "thermal")
    ):
        evidence = ", ".join(abnormal_measurements) if temperature_abnormal else "Temperature language in observations"
        fire("temperature_abnormal", evidence)

    leak_obs = any(
        (item.get("category") == ObservationCategory.LEAKAGE.value and _positive_finding(item))
        or ("leak" in str(item.get("field_key", "")).lower() and _positive_finding(item))
        for item in observations
    )
    if leak_obs or _matches_any(blob, ("oil leak", "oil leakage", "leaking", "oil around", "fluid leak", "coolant")):
        fire("oil_leakage", "Leakage observation present")

    if any(
        item.get("category") == ObservationCategory.STRUCTURAL.value and _positive_finding(item) for item in observations
    ) or _matches_any(blob, ("crack", "deform", "impact damage", "bent", "foundation")):
        fire("structural_damage", "Structural observation present")

    if any(
        item.get("category") == ObservationCategory.NOISE.value and _positive_finding(item) for item in observations
    ) or _matches_any(blob, ("noisy", "vibration", "humming", "arcing", "buzzing", "unusual sound")):
        fire("abnormal_sound", "Noise / vibration observation present")

    if previous_high_or_critical > 0:
        fire("previous_failures", f"{previous_high_or_critical} recent high/critical inspection(s)")

    if any(
        item.get("category") == ObservationCategory.ELECTRICAL.value and _positive_finding(item) for item in observations
    ) or _matches_any(blob, ("discharge", "burning smell", "flashover", "insulation", "tripped", "spark")):
        fire("electrical_anomaly", "Electrical observation present")

    if any(
        item.get("category") == ObservationCategory.CORROSION.value and _positive_finding(item) for item in observations
    ) or _matches_any(blob, ("corrosion", "rust", "weathered")):
        fire("corrosion", "Corrosion observation present")

    if any(
        item.get("category") == ObservationCategory.SAFETY.value and _positive_finding(item) for item in observations
    ) or _matches_any(blob, ("exposed", "no guard", "blocked access", "ppe", "unsafe")):
        fire("safety_hazard", "Safety observation present")

    if abnormal_measurements:
        fire("out_of_range_measurement", "; ".join(abnormal_measurements))

    danger = any(
        str(item.get("field_key", "")).lower() in {"immediate_danger", "imminent_danger"}
        and _truthy(item.get("value_bool") or item.get("value_text"))
        for item in observations
    ) or _matches_any(blob, ("immediate danger", "imminent failure", "about to fail"))
    if danger:
        fire("immediate_danger", "Inspector flagged imminent danger")

    unique: dict[str, dict[str, Any]] = {}
    for item in triggered:
        unique.setdefault(item["key"], item)
    breakdown = list(unique.values())
    score = min(100, sum(item["points"] for item in breakdown))

    if any(item["key"] == "immediate_danger" for item in breakdown):
        score = max(score, 81)

    return RiskResult(score=score, level=classify(score), breakdown=breakdown)
