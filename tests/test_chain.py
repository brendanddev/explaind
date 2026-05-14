from __future__ import annotations

import io
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
    """Dry-run / error path — no config/invoker mocking needed."""
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for chain mode")
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
    input_file.write_text("test input for chain mode")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file)] + list(args)

    _outputs = outputs or ["output 1", "output 2", "output 3"]
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


# 1. --chain with 2 abilities dry-run produces 2 prompt blocks
def test_chain_dry_run_two_abilities_two_blocks(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--chain", "causal", "compressive", "--dry-run")
    assert exit_code == 0
    assert stdout.count("=== SYSTEM PROMPT ===") == 2


# 2. --chain with 3 abilities dry-run produces 3 prompt blocks
def test_chain_dry_run_three_abilities_three_blocks(tmp_path):
    stdout, _, exit_code = _invoke(
        tmp_path, "--chain", "causal", "compressive", "skeptical", "--dry-run"
    )
    assert exit_code == 0
    assert stdout.count("=== SYSTEM PROMPT ===") == 3


# 3. pass 2+ scratchpad contains [REASONING HANDOFF] header
def test_chain_pass2_contains_handoff_header(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--chain", "causal", "compressive", "--dry-run")
    assert exit_code == 0
    assert "[REASONING HANDOFF:" in stdout


# 4. handoff header contains correct prev and next ability names
def test_chain_handoff_header_correct_ability_names(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--chain", "causal", "compressive", "--dry-run")
    assert exit_code == 0
    assert "[REASONING HANDOFF: causal → compressive]" in stdout


# 5. pass 1 uses first ability in chain
def test_chain_pass1_uses_first_ability(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--chain", "causal", "skeptical", "--dry-run")
    assert exit_code == 0
    assert "[BIAS: CAUSAL]" in stdout
    assert "[BIAS: SKEPTICAL]" in stdout
    assert stdout.index("[BIAS: CAUSAL]") < stdout.index("[BIAS: SKEPTICAL]")


# 6. final pass uses last ability in chain
def test_chain_final_pass_uses_last_ability(tmp_path):
    stdout, _, exit_code = _invoke(
        tmp_path, "--chain", "causal", "compressive", "skeptical", "--dry-run"
    )
    assert exit_code == 0
    causal_pos = stdout.index("[BIAS: CAUSAL]")
    compressive_pos = stdout.index("[BIAS: COMPRESSIVE]")
    skeptical_pos = stdout.index("[BIAS: SKEPTICAL]")
    assert causal_pos < compressive_pos < skeptical_pos


# 7. --chain with 1 ability exits 1
def test_chain_single_ability_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--chain", "causal")
    assert exit_code == 1
    assert "at least 2" in stderr


# 8. --chain and --compare together exits 1
def test_chain_and_compare_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(
        tmp_path, "--chain", "causal", "compressive", "--compare", "skeptical", "balanced"
    )
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 9. --chain and --honest together exits 1
def test_chain_and_honest_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--chain", "causal", "compressive", "--honest")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 10. --chain and --preset together exits 1
def test_chain_and_preset_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--chain", "causal", "compressive", "--preset", "critic")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 11. --chain and --ability together exits 1
def test_chain_and_ability_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(
        tmp_path, "--chain", "causal", "compressive", "--ability", "skeptical"
    )
    assert exit_code == 1
    assert "mutually exclusive" in stderr


# 12. unknown ability in chain exits 1 before any runs start
def test_chain_unknown_ability_exits_1_before_any_run(tmp_path):
    stdout, stderr, exit_code = _invoke(
        tmp_path, "--chain", "causal", "notanability", "--dry-run"
    )
    assert exit_code == 1
    assert "unknown ability" in stderr
    # No prompt was assembled — no model calls were made
    assert "=== SYSTEM PROMPT ===" not in stdout


# 13. user --scratchpad appears before handoff header in pass 2
def test_chain_user_scratchpad_before_handoff_header(tmp_path):
    scratchpad_file = tmp_path / "notes.md"
    scratchpad_file.write_text("USER SCRATCHPAD CONTENT HERE")
    stdout, _, exit_code = _invoke(
        tmp_path,
        "--chain", "causal", "compressive",
        "--dry-run",
        "--scratchpad", str(scratchpad_file),
    )
    assert exit_code == 0
    assert "USER SCRATCHPAD CONTENT HERE" in stdout
    assert "[REASONING HANDOFF:" in stdout
    user_pos = stdout.index("USER SCRATCHPAD CONTENT HERE")
    handoff_pos = stdout.index("[REASONING HANDOFF:")
    assert user_pos < handoff_pos


# 14. --context passed through on every run (all 3 prompt blocks contain it)
def test_chain_context_passed_to_every_pass(tmp_path):
    context_file = tmp_path / "ctx.md"
    context_file.write_text("UNIQUE CONTEXT SIGNAL XYZ")
    stdout, _, exit_code = _invoke(
        tmp_path,
        "--chain", "causal", "compressive", "skeptical",
        "--dry-run",
        "--context", str(context_file),
    )
    assert exit_code == 0
    assert stdout.count("UNIQUE CONTEXT SIGNAL XYZ") == 3


# 15. scratchpad truncation warning fires when accumulated content exceeds 8000 chars
def test_chain_truncation_warning_on_large_output(tmp_path):
    large_output = "x" * 9000

    call_count = [0]
    def mock_run(content, ability=None, **kwargs):
        idx = call_count[0]
        call_count[0] += 1
        return (large_output if idx == 0 else "pass 2 output", None)

    input_file = tmp_path / "input.txt"
    input_file.write_text("test input")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file), "--chain", "causal", "compressive"]

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
    assert "truncated" in stderr_buf.getvalue()


# 16. --export with --chain produces correctly labelled sections
def test_chain_export_labelled_sections(tmp_path):
    export_file = tmp_path / "chain_export.md"
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for chain export")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = [
        "explaind", str(input_file),
        "--chain", "causal", "compressive", "skeptical",
        "--export", str(export_file),
    ]

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
    md = export_file.read_text(encoding="utf-8")
    assert "## Pass 1: causal" in md
    assert "## Pass 2: compressive" in md
    assert "## Pass 3: skeptical" in md
