from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from explaind.cli import main


def _make_mock_config(model_name="test-model"):
    cfg = MagicMock()
    cfg.model_name = model_name
    cfg.temperature = 0.0
    cfg.max_tokens = 2048
    return cfg


def _invoke(tmp_path, *args):
    """Dry-run or exit-before-model invocation. No config/invoker mocking needed."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for honest mode")
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


def _invoke_live(tmp_path, *args, outputs=None):
    """Live mock: patches load_config, build_invoker, and run."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for honest mode")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file)] + list(args)

    _outputs = outputs or ["balanced output", "skeptical output"]
    call_count = [0]

    def mock_run(content, ability=None, **kwargs):
        idx = call_count[0]
        call_count[0] += 1
        return (_outputs[idx % len(_outputs)], None)

    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("explaind.cli.load_config", return_value=_make_mock_config()), \
         patch("explaind.cli.build_invoker", return_value=MagicMock()), \
         patch("explaind.cli.run", side_effect=mock_run):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


# 1. dry-run produces two prompt blocks
def test_honest_dry_run_two_prompt_blocks(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--honest", "--dry-run")
    assert exit_code == 0
    assert stdout.count("=== SYSTEM PROMPT ===") == 2


# 2. pass 2 scratchpad contains [INITIAL RESPONSE — under review] header
def test_honest_pass2_scratchpad_contains_initial_response_header(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--honest", "--dry-run")
    assert exit_code == 0
    assert "[INITIAL RESPONSE — under review]" in stdout


# 3. pass 2 uses skeptical ability regardless of --ability flag
def test_honest_pass2_uses_skeptical_regardless_of_ability(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--honest", "--dry-run", "--ability", "causal")
    assert exit_code == 0
    assert "[REASONING MODE: SKEPTICAL]" in stdout
    assert "[REASONING MODE: CAUSAL]" not in stdout


# 4. pass 1 uses balanced ability regardless of --ability flag
def test_honest_pass1_uses_balanced_regardless_of_ability(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--honest", "--dry-run", "--ability", "causal")
    assert exit_code == 0
    assert "[REASONING MODE: BALANCED]" in stdout
    assert "[REASONING MODE: CAUSAL]" not in stdout


# 5. --honest and --compare together exits 1
def test_honest_and_compare_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--honest", "--compare", "skeptical", "causal")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 6. --honest and --preset together exits 1
def test_honest_and_preset_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--honest", "--preset", "critic")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 7. footer shows combined inference time format
def test_honest_footer_combined_inference_time(tmp_path):
    _, stderr, exit_code = _invoke_live(tmp_path, "--honest")
    assert exit_code == 0
    assert "honest" in stderr
    assert re.search(r"\d+ms \+ \d+ms", stderr)


# 8. user --scratchpad content appears before INITIAL RESPONSE block in pass 2
def test_honest_user_scratchpad_before_initial_response(tmp_path):
    scratchpad_file = tmp_path / "notes.md"
    scratchpad_file.write_text("USER SCRATCHPAD CONTENT HERE")
    stdout, _, exit_code = _invoke(
        tmp_path, "--honest", "--dry-run", "--scratchpad", str(scratchpad_file)
    )
    assert exit_code == 0
    assert "USER SCRATCHPAD CONTENT HERE" in stdout
    assert "[INITIAL RESPONSE — under review]" in stdout
    user_pos = stdout.index("USER SCRATCHPAD CONTENT HERE")
    header_pos = stdout.index("[INITIAL RESPONSE — under review]")
    assert user_pos < header_pos


# 9. --export with --honest produces two labelled sections
def test_honest_export_two_labelled_sections(tmp_path):
    export_file = tmp_path / "honest_export.md"
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for honest export")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file), "--honest", "--export", str(export_file)]

    call_count = [0]

    def mock_run(content, ability=None, **kwargs):
        idx = call_count[0]
        call_count[0] += 1
        return (f"output {idx + 1}", None)

    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("explaind.cli.load_config", return_value=_make_mock_config()), \
         patch("explaind.cli.build_invoker", return_value=MagicMock()), \
         patch("explaind.cli.run", side_effect=mock_run):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    assert exit_code == 0
    assert export_file.exists()
    content = export_file.read_text(encoding="utf-8")
    assert "## Initial Response" in content
    assert "## Self-Critique" in content
