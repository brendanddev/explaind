import io
import sys
import pytest
from unittest.mock import patch

from explaind.cli import main


def _invoke(tmp_path, *args):
    """Run main() with a temp input file, return (stdout, stderr, exit_code)."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for compare")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file)] + list(args)
    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def test_compare_dry_run_two_abilities(tmp_path):
    stdout, _, exit_code = _invoke(
        tmp_path, "--compare", "skeptical", "causal", "--dry-run"
    )
    assert exit_code == 0
    assert "═══ ABILITY: SKEPTICAL ═══" in stdout
    assert "═══ ABILITY: CAUSAL ═══" in stdout
    assert stdout.index("SKEPTICAL") < stdout.index("CAUSAL")


def test_compare_dry_run_each_block_contains_prompt(tmp_path):
    stdout, _, exit_code = _invoke(
        tmp_path, "--compare", "balanced", "exploratory", "--dry-run"
    )
    assert exit_code == 0
    # both assembled prompts should contain the common system marker
    assert stdout.count("=== SYSTEM PROMPT ===") == 2


def test_compare_unknown_ability_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(
        tmp_path, "--compare", "skeptical", "nonexistent", "--dry-run"
    )
    assert exit_code == 1
    assert "unknown ability" in stderr


def test_compare_with_ability_flag_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(
        tmp_path, "--compare", "skeptical", "causal", "--ability", "balanced", "--dry-run"
    )
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# --compare requires at least 2 abilities; a single name should use --ability instead
def test_compare_single_ability_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--compare", "skeptical", "--dry-run")
    assert exit_code == 1
    assert "at least 2" in stderr
