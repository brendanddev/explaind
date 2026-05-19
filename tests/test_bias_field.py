import pytest
from explaind.prompts import build_bias_field

_ABILITIES = [
    "balanced",
    "skeptical",
    "causal",
    "compressive",
    "exploratory",
    "calibrator",
    "devil",
    "updater",
]


@pytest.mark.parametrize("ability", _ABILITIES)
def test_bias_field_contains_reasoning_mode(ability):
    result = build_bias_field(ability)
    assert f"[REASONING MODE: {ability.upper()}]" in result


@pytest.mark.parametrize("ability", _ABILITIES)
def test_bias_field_structure(ability):
    result = build_bias_field(ability)
    assert result.startswith("BIAS FIELD")
    assert result.endswith("END BIAS FIELD")


@pytest.mark.parametrize("ability", _ABILITIES)
def test_bias_field_contains_invariants(ability):
    result = build_bias_field(ability)
    assert "[INVARIANTS: ACTIVE]" in result


@pytest.mark.parametrize("ability", _ABILITIES)
def test_bias_field_no_old_format_tokens(ability):
    result = build_bias_field(ability)
    assert "[BIAS:" not in result
    assert "[TRAJECTORY:" not in result
    assert "[EPISTEMIC:" not in result


def test_bias_field_unknown_ability_fallback():
    result = build_bias_field("unknown")
    assert "[REASONING MODE: UNKNOWN]" in result
    assert result.startswith("BIAS FIELD")
    assert result.endswith("END BIAS FIELD")
    assert "[INVARIANTS: ACTIVE]" in result
