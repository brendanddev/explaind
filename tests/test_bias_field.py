import pytest
from explaind.prompts import build_bias_field

_EXPECTED = {
    "balanced":    {"bias": "BALANCED",    "trajectory": "balanced",    "epistemic": "neutral"},
    "skeptical":   {"bias": "SKEPTICAL",   "trajectory": "skeptical",   "epistemic": "skeptical"},
    "causal":      {"bias": "CAUSAL",      "trajectory": "causal",      "epistemic": "neutral"},
    "compressive": {"bias": "COMPRESSIVE", "trajectory": "compressive", "epistemic": "neutral"},
    "exploratory": {"bias": "EXPLORATORY", "trajectory": "exploratory", "epistemic": "neutral"},
}


@pytest.mark.parametrize("ability,expected", _EXPECTED.items())
def test_bias_field_values(ability, expected):
    result = build_bias_field(ability)
    assert f"[BIAS: {expected['bias']}]" in result
    assert f"[TRAJECTORY: {expected['trajectory']}]" in result
    assert f"[EPISTEMIC: {expected['epistemic']}]" in result
    assert "[INVARIANTS: ACTIVE]" in result


@pytest.mark.parametrize("ability", _EXPECTED.keys())
def test_bias_field_structure(ability):
    result = build_bias_field(ability)
    assert result.startswith("BIAS FIELD")
    assert result.endswith("END BIAS FIELD")


def test_bias_field_unknown_ability_defaults_to_balanced():
    result = build_bias_field("unknown")
    assert "[BIAS: UNKNOWN]" in result
    assert "[TRAJECTORY: balanced]" in result
    assert "[EPISTEMIC: neutral]" in result
    assert "[INVARIANTS: ACTIVE]" in result
