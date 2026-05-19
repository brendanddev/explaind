"""Tests for the three-position BIAS FIELD system (primacy, periodic, recency)."""
import pytest

from explaind.context import build_context_window_block
from explaind.prompts import (
    _PRIMACY_ANCHORS,
    _PERIODIC_REFRESHES,
    assemble_prompt,
    build_bias_field,
    format_ability,
)

_ALL_ABILITIES = [
    "balanced",
    "skeptical",
    "causal",
    "compressive",
    "exploratory",
    "calibrator",
    "devil",
    "updater",
]


def _make_prompt(ability_name: str | None = None, ability_content: str = "ABILITY TEXT") -> str:
    ability = format_ability(ability_name, ability_content) if ability_name else None
    return assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=ability,
        context_window=build_context_window_block(),
        bias_field=build_bias_field(ability_name or "balanced"),
        user_input="USER INPUT",
    )


# 1. assemble_prompt with ability="skeptical" contains the skeptical primacy anchor text
def test_primacy_anchor_in_prompt():
    result = _make_prompt("skeptical")
    assert "Default to doubt." in result
    assert "Prioritize evidence quality" in result


# 2. Primacy anchor appears BEFORE === END SYSTEM PROMPT ===
def test_primacy_anchor_before_end_system_prompt():
    result = _make_prompt("skeptical")
    primacy_text = _PRIMACY_ANCHORS["skeptical"]
    anchor_pos = result.index(primacy_text)
    end_system_pos = result.index("=== END SYSTEM PROMPT ===")
    assert anchor_pos < end_system_pos


# 3. Periodic refresh appears AFTER === END REASONING CONSTRAINTS === (first injection)
def test_periodic_after_reasoning_constraints():
    result = _make_prompt("skeptical")
    periodic_text = _PERIODIC_REFRESHES["skeptical"]
    constraints_end_pos = result.index("=== END REASONING CONSTRAINTS ===")
    periodic_pos = result.index(periodic_text)
    assert constraints_end_pos < periodic_pos


# 4. Periodic refresh appears AFTER === END ABILITY === (second injection)
def test_periodic_after_end_ability():
    result = _make_prompt("skeptical")
    periodic_text = _PERIODIC_REFRESHES["skeptical"]
    end_ability_pos = result.index("=== END ABILITY ===")
    first_pos = result.index(periodic_text)
    second_pos = result.index(periodic_text, first_pos + 1)
    assert end_ability_pos < second_pos


# 5. Recency field contains [REASONING MODE: SKEPTICAL]
def test_recency_field_contains_reasoning_mode():
    result = _make_prompt("skeptical")
    assert "[REASONING MODE: SKEPTICAL]" in result


# 6. Recency field does NOT contain old format tokens
def test_recency_field_no_old_format_tokens():
    result = _make_prompt("skeptical")
    assert "[BIAS: SKEPTICAL]" not in result
    assert "[TRAJECTORY: skeptical]" not in result
    assert "[EPISTEMIC: skeptical]" not in result


# 7. All 8 abilities produce their correct primacy text
@pytest.mark.parametrize("ability", _ALL_ABILITIES)
def test_all_abilities_primacy_text(ability):
    result = _make_prompt(ability)
    expected_primacy = _PRIMACY_ANCHORS[ability]
    assert expected_primacy in result


# 8. All 8 abilities produce their correct periodic text
@pytest.mark.parametrize("ability", _ALL_ABILITIES)
def test_all_abilities_periodic_text(ability):
    result = _make_prompt(ability)
    expected_periodic = _PERIODIC_REFRESHES[ability]
    assert expected_periodic in result


# 9. Unknown ability falls back to default in all 3 positions
def test_unknown_ability_fallback_all_positions():
    ability = format_ability("unknownx", "CONTENT")
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=ability,
        context_window=build_context_window_block(),
        bias_field=build_bias_field("unknownx"),
        user_input="USER INPUT",
    )
    assert "[REASONING FRAME: UNKNOWNX — active throughout]" in result
    assert "[REFRESH] UNKNOWNX protocol: active." in result
    assert "[REASONING MODE: UNKNOWNX]" in result


# 10. --dry-run output shows all three positions visibly
def test_dry_run_shows_all_three_positions():
    from explaind.main import run
    result, _ = run("test input", ability="skeptical", dry_run=True)
    primacy = _PRIMACY_ANCHORS["skeptical"]
    periodic = _PERIODIC_REFRESHES["skeptical"]
    assert primacy in result
    assert result.index("=== SYSTEM PROMPT ===") < result.index(primacy)
    first_periodic = result.index(periodic)
    second_periodic = result.index(periodic, first_periodic + 1)
    assert first_periodic < second_periodic
    recency_pos = result.index("[REASONING MODE: SKEPTICAL]")
    user_pos = result.index("<user_input>")
    assert recency_pos < user_pos
