import pytest
from explaind.trace import PromptTrace, TraceData, format_trace, _ABILITY_ROLES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pt(**kwargs) -> PromptTrace:
    defaults = dict(
        gemma_present=True,
        ability_name=None,
        prompt_char_count=500,
        user_input_length=42,
    )
    defaults.update(kwargs)
    return PromptTrace(**defaults)


def _td(prompt: PromptTrace, **kwargs) -> TraceData:
    defaults = dict(model_name="test-model", temperature=0.0, max_tokens=2048)
    defaults.update(kwargs)
    return TraceData(prompt=prompt, **defaults)


def _fmt(**pt_kwargs) -> str:
    return format_trace(_td(_pt(**pt_kwargs)))


# ---------------------------------------------------------------------------
# Structural markers always present
# ---------------------------------------------------------------------------

def test_trace_start_marker():
    assert "[TRACE START]" in _fmt()


def test_trace_end_marker():
    assert "[TRACE END]" in _fmt()


def test_model_section():
    result = format_trace(_td(_pt(), model_name="gemma4-e2b_q4_k_m:latest"))
    assert "[MODEL]" in result
    assert "gemma4-e2b_q4_k_m:latest" in result


def test_settings_section():
    result = format_trace(_td(_pt(), temperature=0.7, max_tokens=512))
    assert "[SETTINGS]" in result
    assert "temperature=0.7" in result
    assert "max_tokens=512" in result


def test_layers_section():
    assert "[LAYERS]" in _fmt()


def test_prompt_size_section():
    result = _fmt(prompt_char_count=1234)
    assert "[PROMPT SIZE]" in result
    assert "1234 chars" in result


def test_interpretation_map_section():
    assert "[INTERPRETATION MAP]" in _fmt()


# ---------------------------------------------------------------------------
# Layer display
# ---------------------------------------------------------------------------

def test_system_always_present():
    assert "SYSTEM: present" in _fmt()


def test_context_window_always_present():
    assert "CONTEXT WINDOW LAYERS: present" in _fmt()


def test_gemma_present():
    assert "GEMMA: present" in _fmt(gemma_present=True)


def test_gemma_absent():
    assert "GEMMA: absent" in _fmt(gemma_present=False)


def test_ability_none_shows_none():
    assert "ABILITY: none" in _fmt(ability_name=None)


def test_ability_name_shown():
    assert "ABILITY: skeptical" in _fmt(ability_name="skeptical")


def test_bias_field_defaults_to_balanced_when_no_ability():
    assert "BIAS FIELD: balanced" in _fmt(ability_name=None)


def test_bias_field_matches_ability():
    assert "BIAS FIELD: causal" in _fmt(ability_name="causal")


def test_user_input_length():
    result = _fmt(user_input_length=99)
    assert "USER INPUT: 99 chars" in result


# ---------------------------------------------------------------------------
# Interpretation map
# ---------------------------------------------------------------------------

def test_interpretation_map_shows_active_ability():
    result = _fmt(ability_name="skeptical")
    assert "skeptical →" in result
    assert "epistemic pressure" in result


def test_interpretation_map_defaults_to_balanced():
    result = _fmt(ability_name=None)
    assert "balanced →" in result
    assert "neutral prior" in result


def test_all_abilities_have_roles():
    for ability in ("balanced", "skeptical", "causal", "compressive", "exploratory"):
        result = _fmt(ability_name=ability)
        assert f"{ability} →" in result
        assert _ABILITY_ROLES[ability] in result


# ---------------------------------------------------------------------------
# Output properties
# ---------------------------------------------------------------------------

def test_format_trace_is_deterministic():
    pt = _pt(ability_name="causal", gemma_present=True, prompt_char_count=300)
    td = _td(pt, model_name="m", temperature=0.5, max_tokens=1024)
    assert format_trace(td) == format_trace(td)


def test_format_trace_returns_string():
    assert isinstance(_fmt(), str)


def test_start_before_end():
    result = _fmt()
    assert result.index("[TRACE START]") < result.index("[TRACE END]")


def test_layers_before_prompt_size():
    result = _fmt()
    assert result.index("[LAYERS]") < result.index("[PROMPT SIZE]")


# ---------------------------------------------------------------------------
# run() integration — trace=True returns PromptTrace
# ---------------------------------------------------------------------------

def test_run_returns_prompt_trace_when_trace_true():
    from explaind.main import run
    _, pt = run("hello", trace=True, dry_run=True)
    assert pt is not None
    assert isinstance(pt, PromptTrace)
    assert pt.user_input_length == len("hello")


def test_run_returns_none_when_trace_false():
    from explaind.main import run
    _, pt = run("hello", dry_run=True)
    assert pt is None


def test_run_prompt_char_count_is_positive():
    from explaind.main import run
    _, pt = run("some input text", trace=True, dry_run=True)
    assert pt.prompt_char_count > 0


def test_run_gemma_present_reflects_actual_file():
    from explaind.main import run
    from explaind.gemma import load_gemma_md
    _, pt = run("test", trace=True, dry_run=True)
    assert pt.gemma_present == (load_gemma_md() is not None)
