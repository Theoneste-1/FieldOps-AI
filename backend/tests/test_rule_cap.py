def test_weights_sum_can_exceed_cap_so_engine_must_cap():
    from app.engines.risk import DEFAULT_RULES

    total = sum(rule.weight for rule in DEFAULT_RULES)
    assert total > 100
