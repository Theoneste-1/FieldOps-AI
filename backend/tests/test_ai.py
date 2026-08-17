import pytest

from app.ai.service import build_context, heuristic_analyze, validate_ai_payload, AIValidationError


def test_validator_accepts_well_formed_payload():
    payload = validate_ai_payload(
        {
            "risk_summary": "Elevated temperature and oil leakage suggest cooling or seal degradation.",
            "possible_causes": ["Seal failure", "Overload"],
            "recommendations": ["Inspect oil seal", "Verify operating temperature"],
            "supervisor_brief": "Critical findings on T-104 require supervisor review.",
            "confidence": 0.81,
            "severity": "critical",
        }
    )
    assert payload["severity"] == "critical"
    assert 0 <= payload["confidence"] <= 1


def test_validator_rejects_shutdown_language():
    with pytest.raises(AIValidationError):
        validate_ai_payload(
            {
                "risk_summary": "Equipment is unsafe and you must shut down immediately.",
                "possible_causes": ["Failure"],
                "recommendations": ["Shut down immediately and isolate the feeder"],
                "confidence": 0.9,
                "severity": "critical",
            }
        )


def test_validator_rejects_missing_fields():
    with pytest.raises(AIValidationError):
        validate_ai_payload({"risk_summary": "Too short"})


def test_heuristic_never_claims_authority():
    context = build_context(
        {
            "asset_code": "T-104",
            "asset_name": "Midrand TX 4",
            "risk_score": 87,
            "risk_level": "critical",
            "risk_breakdown": [
                {"key": "temperature_abnormal", "label": "Temperature abnormality"},
                {"key": "oil_leakage", "label": "Oil leakage"},
            ],
            "observations": [{"value_text": "There is oil around the bottom and the machine is unusually noisy."}],
        }
    )
    result = heuristic_analyze(context)
    joined = " ".join([result["risk_summary"], *result["recommendations"]]).lower()
    assert "shut down" not in joined
    assert result["severity"] == "critical"
    assert "supervisor" in joined
