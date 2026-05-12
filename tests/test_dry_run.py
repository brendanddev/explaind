from unittest.mock import patch
from explaind.main import run
from explaind.prompts import SYSTEM_PROMPT


def test_dry_run_does_not_invoke_model():
    from unittest.mock import MagicMock
    mock_invoker = MagicMock()
    run("test input", dry_run=True, invoker=mock_invoker)
    mock_invoker.invoke.assert_not_called()


def test_dry_run_usage_is_none():
    _, usage = run("test input", dry_run=True)
    assert usage is None


def test_dry_run_contains_system_prompt_text():
    result, _ = run("test input", dry_run=True)
    assert SYSTEM_PROMPT in result


def test_dry_run_contains_system_prompt_marker():
    result, _ = run("test input", dry_run=True)
    assert "=== SYSTEM PROMPT ===" in result
    assert "=== END SYSTEM PROMPT ===" in result


def test_dry_run_contains_bias_field():
    result, _ = run("test input", dry_run=True)
    assert "BIAS FIELD" in result
    assert "END BIAS FIELD" in result


def test_dry_run_contains_xml_input():
    result, _ = run("my specific input text", dry_run=True)
    assert "<user_input>" in result
    assert "</user_input>" in result
    assert "my specific input text" in result


def test_dry_run_with_ability_contains_ability_content():
    result, _ = run("test input", ability="skeptical", dry_run=True)
    assert "SKEPTICAL" in result
    assert "[EPISTEMIC: skeptical]" in result


def test_dry_run_returns_string_not_none():
    result, _ = run("test input", dry_run=True)
    assert isinstance(result, str)
    assert len(result) > 0
