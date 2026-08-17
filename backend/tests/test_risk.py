from app.engines.lifecycle import InspectionStateMachine
from app.engines.risk import calculate_risk, classify
from app.exceptions import InvalidStateError
from app.models.entities import InspectionStatus, RiskLevel
import pytest


def test_critical_transformer_story():
    result = calculate_risk(
        observations=[
            {"field_key": "oil_leakage", "category": "leakage", "label": "Oil leakage", "value_bool": True, "value_text": "Yes"},
            {"field_key": "noise", "category": "noise", "label": "Noise", "value_text": "High"},
            {"field_key": "visual_damage", "category": "structural", "label": "Visual damage", "value_bool": True, "value_text": "Yes"},
        ],
        measurements=[
            {"field_key": "temperature", "label": "Temperature", "value": 91, "unit": "°C", "max_threshold": 80},
        ],
        previous_high_or_critical=1,
    )
    assert result.score >= 81
    assert result.level == RiskLevel.CRITICAL
    keys = {item["key"] for item in result.breakdown}
    assert "temperature_abnormal" in keys
    assert "oil_leakage" in keys
    assert "out_of_range_measurement" in keys


def test_clean_inspection_is_low():
    result = calculate_risk(
        observations=[
            {"field_key": "oil_leakage", "category": "leakage", "label": "Oil leakage", "value_bool": False, "value_text": "No"},
            {"field_key": "noise", "category": "noise", "label": "Noise", "value_text": "normal"},
        ],
        measurements=[{"field_key": "temperature", "label": "Temperature", "value": 62, "unit": "°C", "max_threshold": 80}],
    )
    assert result.level == RiskLevel.LOW
    assert result.score <= 30


def test_immediate_danger_floors_critical():
    result = calculate_risk(
        observations=[
            {"field_key": "immediate_danger", "category": "safety", "label": "Immediate danger", "value_bool": True, "value_text": "Yes"}
        ]
    )
    assert result.score >= 81
    assert result.level == RiskLevel.CRITICAL


def test_classify_bands():
    assert classify(0) == RiskLevel.LOW
    assert classify(30) == RiskLevel.LOW
    assert classify(31) == RiskLevel.MEDIUM
    assert classify(80) == RiskLevel.HIGH
    assert classify(81) == RiskLevel.CRITICAL


def test_lifecycle_happy_path():
    status = InspectionStatus.DRAFT.value
    for target in [
        InspectionStatus.IN_PROGRESS.value,
        InspectionStatus.SUBMITTED.value,
        InspectionStatus.PROCESSING.value,
        InspectionStatus.ANALYZED.value,
        InspectionStatus.REVIEWED.value,
        InspectionStatus.RESOLVED.value,
    ]:
        status = InspectionStateMachine.transition(status, target)
    assert status == InspectionStatus.RESOLVED.value


def test_lifecycle_rejects_illegal_jump():
    with pytest.raises(InvalidStateError):
        InspectionStateMachine.transition(InspectionStatus.DRAFT.value, InspectionStatus.RESOLVED.value)


def test_ai_failure_path():
    status = InspectionStateMachine.transition(InspectionStatus.SUBMITTED.value, InspectionStatus.PROCESSING.value)
    status = InspectionStateMachine.transition(status, InspectionStatus.AI_FAILED.value)
    status = InspectionStateMachine.transition(status, InspectionStatus.PENDING_RETRY.value)
    status = InspectionStateMachine.transition(status, InspectionStatus.PROCESSING.value)
    assert status == InspectionStatus.PROCESSING.value
