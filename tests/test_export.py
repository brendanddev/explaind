from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from explaind.cli import main
from explaind.exporter import build_export


# ---------------------------------------------------------------------------
# build_export unit tests
# ---------------------------------------------------------------------------


def test_build_export_single_run_contains_question():
    md = build_export(
        question="What causes inflation?",
        runs=[{"ability": "skeptical", "preset": None, "output": "Model output here.", "duration_ms": 1000}],
        model="test-model",
    )
    assert "What causes inflation?" in md
    assert "Skeptical" in md
    assert "Model output here." in md


def test_build_export_single_run_valid_markdown():
    md = build_export(
        question="Test question",
        runs=[{"ability": "causal", "preset": None, "output": "Some output.", "duration_ms": 500}],
        model="test-model",
    )
    assert md.startswith("# explaind Reasoning Chain")
    assert "## Ability: Causal" in md
    assert "## Question" in md
    assert "> Test question" in md


def test_build_export_multiple_runs_all_sections_present():
    md = build_export(
        question="Multi-run question",
        runs=[
            {"ability": "skeptical", "preset": None, "output": "Skeptical output.", "duration_ms": 1000},
            {"ability": "causal", "preset": None, "output": "Causal output.", "duration_ms": 900},
        ],
        model="test-model",
    )
    assert "## Ability: Skeptical" in md
    assert "## Ability: Causal" in md
    assert "Skeptical output." in md
    assert "Causal output." in md


def test_build_export_multiple_runs_order_preserved():
    md = build_export(
        question="Order test",
        runs=[
            {"ability": "skeptical", "preset": None, "output": "first", "duration_ms": 100},
            {"ability": "causal", "preset": None, "output": "second", "duration_ms": 200},
        ],
        model="test-model",
    )
    assert md.index("Skeptical") < md.index("Causal")
    assert md.index("first") < md.index("second")


def test_build_export_think_true_shows_enabled():
    md = build_export(
        question="Think test",
        runs=[{"ability": "balanced", "preset": None, "output": "output", "duration_ms": 50}],
        model="test-model",
        think=True,
    )
    assert "**Thinking mode:** enabled" in md


def test_build_export_think_false_shows_disabled():
    md = build_export(
        question="No think test",
        runs=[{"ability": "balanced", "preset": None, "output": "output", "duration_ms": 50}],
        model="test-model",
        think=False,
    )
    assert "**Thinking mode:** disabled" in md


def test_build_export_summary_notes_section_present():
    md = build_export(
        question="Summary test",
        runs=[{"ability": "balanced", "preset": None, "output": "output", "duration_ms": 50}],
        model="test-model",
    )
    assert "## Summary Notes" in md
    assert "intentionally blank" in md


def test_build_export_preset_run_uses_preset_name():
    md = build_export(
        question="Preset test",
        runs=[{"ability": "exploratory", "preset": "philosopher", "output": "Preset output.", "duration_ms": 800}],
        model="test-model",
    )
    assert "## Preset: Philosopher" in md
    assert "Preset output." in md


def test_build_export_inference_time_included():
    md = build_export(
        question="Timing test",
        runs=[{"ability": "skeptical", "preset": None, "output": "out", "duration_ms": 52413}],
        model="test-model",
    )
    assert "52413ms" in md


def test_build_export_model_name_included():
    md = build_export(
        question="Model test",
        runs=[{"ability": "balanced", "preset": None, "output": "out", "duration_ms": 100}],
        model="gemma4-e2b_q4_k_m:latest",
    )
    assert "gemma4-e2b_q4_k_m:latest" in md


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def _make_mock_config(model_name="test-model"):
    cfg = MagicMock()
    cfg.model_name = model_name
    cfg.temperature = 0.0
    cfg.max_tokens = 2048
    return cfg


def _run_main_with_export(tmp_path, extra_args, mock_output="mock model output"):
    input_file = tmp_path / "input.txt"
    input_file.write_text("test question for export")

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0

    argv = ["explaind", str(input_file)] + list(extra_args)

    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("explaind.cli.load_config", return_value=_make_mock_config()), \
         patch("explaind.cli.build_invoker", return_value=MagicMock()), \
         patch("explaind.cli.run", return_value=(mock_output, None)):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def test_export_with_filename_writes_to_that_file(tmp_path):
    export_file = tmp_path / "chain.md"
    _, _, exit_code = _run_main_with_export(tmp_path, ["--ability", "balanced", "--export", str(export_file)])
    assert exit_code == 0
    assert export_file.exists()
    content = export_file.read_text(encoding="utf-8")
    assert "# explaind Reasoning Chain" in content
    assert "test question for export" in content


def test_export_with_filename_contains_model_output(tmp_path):
    export_file = tmp_path / "out.md"
    _run_main_with_export(
        tmp_path,
        ["--ability", "skeptical", "--export", str(export_file)],
        mock_output="specific model response text",
    )
    content = export_file.read_text(encoding="utf-8")
    assert "specific model response text" in content


def test_export_auto_filename_matches_timestamp_pattern(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, _, exit_code = _run_main_with_export(tmp_path, ["--ability", "balanced", "--export"])
    assert exit_code == 0
    md_files = list(tmp_path.glob("explaind_*.md"))
    assert len(md_files) == 1
    assert re.match(r"explaind_\d{8}_\d{6}\.md", md_files[0].name)


def test_export_write_failure_exits_0(tmp_path):
    export_file = tmp_path / "out.md"
    input_file = tmp_path / "input.txt"
    input_file.write_text("test question for export")

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0

    argv = ["explaind", str(input_file), "--ability", "balanced", "--export", str(export_file)]

    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("explaind.cli.load_config", return_value=_make_mock_config()), \
         patch("explaind.cli.build_invoker", return_value=MagicMock()), \
         patch("explaind.cli.run", return_value=("mock output", None)), \
         patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    assert exit_code == 0
    assert "export failed" in stderr_buf.getvalue()


def test_export_confirmation_printed_to_stderr(tmp_path):
    export_file = tmp_path / "chain.md"
    _, stderr, exit_code = _run_main_with_export(
        tmp_path, ["--ability", "balanced", "--export", str(export_file)]
    )
    assert exit_code == 0
    assert "exported" in stderr


def test_export_compare_writes_all_abilities(tmp_path):
    export_file = tmp_path / "compare.md"
    input_file = tmp_path / "input.txt"
    input_file.write_text("test compare question")

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0

    argv = ["explaind", str(input_file), "--compare", "skeptical", "causal", "--export", str(export_file)]

    call_count = 0

    def mock_run(content, ability=None, **kwargs):
        nonlocal call_count
        call_count += 1
        return (f"{ability} output", None)

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
    assert "skeptical output" in content
    assert "causal output" in content
