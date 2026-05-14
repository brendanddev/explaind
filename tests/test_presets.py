import io
import sys
import pytest
from unittest.mock import patch

from explaind.presets import PRESET_MAP, ALLOWED_PRESETS, load_preset
from explaind.main import run
from explaind.cli import main


# ---------------------------------------------------------------------------
# load_preset unit tests
# ---------------------------------------------------------------------------


def test_load_preset_valid_returns_ability_name():
    ability_name, _ = load_preset("philosopher")
    assert ability_name == "exploratory"


def test_load_preset_valid_all_presets():
    for name, expected_ability in PRESET_MAP.items():
        ability_name, description = load_preset(name)
        assert ability_name == expected_ability
        assert isinstance(description, str)
        assert len(description) > 0


def test_load_preset_unknown_raises_value_error():
    with pytest.raises(ValueError, match="unknown preset"):
        load_preset("nonexistent")


def test_load_preset_unknown_includes_allowed_list():
    with pytest.raises(ValueError) as exc_info:
        load_preset("ghost")
    assert "analyst" in str(exc_info.value)
    assert "critic" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Prompt assembly: [PRESET: X] marker in bias field
# ---------------------------------------------------------------------------


def test_preset_dry_run_contains_preset_marker():
    result, _ = run("test input", ability="exploratory", dry_run=True, preset_name="philosopher")
    assert "[PRESET: PHILOSOPHER]" in result


def test_preset_dry_run_marker_is_uppercase():
    result, _ = run("test input", ability="causal", dry_run=True, preset_name="engineer")
    assert "[PRESET: ENGINEER]" in result


def test_no_preset_marker_when_preset_name_is_none():
    result, _ = run("test input", ability="skeptical", dry_run=True)
    assert "[PRESET:" not in result


def test_preset_marker_inside_bias_field():
    result, _ = run("test input", ability="balanced", dry_run=True, preset_name="synthesiser")
    bias_start = result.index("BIAS FIELD")
    bias_end = result.index("END BIAS FIELD")
    marker_pos = result.index("[PRESET: SYNTHESISER]")
    assert bias_start < marker_pos < bias_end


# ---------------------------------------------------------------------------
# CLI: --preset flag
# ---------------------------------------------------------------------------


def _invoke(*args):
    """Run main() with args, returning (stdout, stderr, exit_code)."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    with patch("sys.argv", ["explaind"] + list(args)), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("sys.stdin.isatty", return_value=True):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def _invoke_with_file(tmp_path, *args):
    """Run main() with a temp input file."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for preset")
    return _invoke(str(input_file), *args)


def test_preset_dry_run_contains_preset_marker_via_cli(tmp_path):
    stdout, _, exit_code = _invoke_with_file(tmp_path, "--preset", "philosopher", "--dry-run")
    assert exit_code == 0
    assert "[PRESET: PHILOSOPHER]" in stdout


def test_preset_dry_run_uses_mapped_ability(tmp_path):
    stdout, _, exit_code = _invoke_with_file(tmp_path, "--preset", "critic", "--dry-run")
    assert exit_code == 0
    # critic maps to skeptical
    assert "[BIAS: SKEPTICAL]" in stdout
    assert "[PRESET: CRITIC]" in stdout


def test_preset_and_ability_together_exits_1(tmp_path):
    _, stderr, exit_code = _invoke_with_file(
        tmp_path, "--preset", "philosopher", "--ability", "skeptical", "--dry-run"
    )
    assert exit_code == 1
    assert "mutually exclusive" in stderr


def test_preset_and_compare_together_exits_1(tmp_path):
    _, stderr, exit_code = _invoke_with_file(
        tmp_path, "--preset", "philosopher", "--compare", "skeptical", "causal", "--dry-run"
    )
    assert exit_code == 1
    assert "mutually exclusive" in stderr


def test_preset_unknown_exits_1(tmp_path):
    _, stderr, exit_code = _invoke_with_file(tmp_path, "--preset", "nobody", "--dry-run")
    assert exit_code == 1
    assert "unknown preset" in stderr


# ---------------------------------------------------------------------------
# CLI: --list-presets
# ---------------------------------------------------------------------------


def test_list_presets_exits_0():
    _, _, exit_code = _invoke("--list-presets")
    assert exit_code == 0


def test_list_presets_contains_all_six_names():
    stdout, _, _ = _invoke("--list-presets")
    for name in ALLOWED_PRESETS:
        assert name in stdout


def test_list_presets_contains_mapped_abilities():
    stdout, _, _ = _invoke("--list-presets")
    for ability in set(PRESET_MAP.values()):
        assert ability in stdout


def test_list_presets_no_input_required():
    # --list-presets should work without any input file or stdin
    stdout, _, exit_code = _invoke("--list-presets")
    assert exit_code == 0
    assert len(stdout) > 0
