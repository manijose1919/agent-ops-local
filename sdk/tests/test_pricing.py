from agentops_local.pricing import compute_cost, reset_warnings


def test_known_model_cost_math():
    prices = {"gpt-4o": {"input": 2.50, "output": 10.00}}
    assert compute_cost("gpt-4o", 1_000_000, 0, prices) == 2.50
    assert compute_cost("gpt-4o", 0, 1_000_000, prices) == 10.00
    expected = round(1000 * 2.5 / 1e6 + 500 * 10.0 / 1e6, 8)
    assert compute_cost("gpt-4o", 1000, 500, prices) == expected


def test_unknown_model_returns_zero_and_warns_once(caplog):
    reset_warnings()
    with caplog.at_level("WARNING", logger="agentops_local"):
        assert compute_cost("mystery-model", 100, 100, {}) == 0.0
        assert compute_cost("mystery-model", 100, 100, {}) == 0.0
    warns = [r for r in caplog.records if "mystery-model" in r.getMessage()]
    assert len(warns) == 1  # warned exactly once, not per call


def test_none_model_returns_zero():
    assert compute_cost(None, 10, 10, {}) == 0.0
