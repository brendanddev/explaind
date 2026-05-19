from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from explaind.cli import main
from explaind.consensus import _compute_agreement, format_consensus_report, run_consensus


# ---------------------------------------------------------------------------
# consensus.py unit tests
# ---------------------------------------------------------------------------


def _make_invoker(outputs):
    invoker = MagicMock()
    invoker.invoke.side_effect = outputs
    return invoker


def test_run_consensus_calls_invoke_n_times():
    invoker = _make_invoker(["out1", "out2", "out3"])
    run_consensus(invoker, "prompt", 3)
    assert invoker.invoke.call_count == 3


def test_compute_agreement_identical_outputs_returns_max_score():
    outputs = ["the cat sat on the mat"] * 5
    scores = _compute_agreement(outputs)
    assert all(s == 4 for s in scores)


def test_compute_agreement_completely_different_outputs_returns_zero():
    outputs = [
        "alpha beta gamma delta epsilon",
        "one two three four five",
        "red green blue yellow purple",
    ]
    scores = _compute_agreement(outputs)
    assert all(s == 0 for s in scores)


def test_compute_agreement_returns_correct_winner_on_mixed_outputs():
    # Two very similar outputs, one totally different
    similar_a = "the quick brown fox jumps over the lazy dog"
    similar_b = "the quick brown fox jumps over lazy dog there"
    outlier = "completely unrelated alpha beta zeta omega"
    outputs = [similar_a, similar_b, outlier]
    scores = _compute_agreement(outputs)
    # similar_a and similar_b should each score 1, outlier scores 0
    assert scores[0] == 1
    assert scores[1] == 1
    assert scores[2] == 0


def test_format_consensus_report_high_confidence():
    report = {
        "n": 5,
        "agreement": 4,
        "agreement_pct": 80.0,
        "confidence": "HIGH",
        "divergent_runs": 1,
        "times_ms": [100, 110, 105, 95, 115],
        "total_ms": 525,
    }
    text = format_consensus_report(report)
    assert "4/5" in text
    assert "80%" in text
    assert "HIGH" in text
    assert "1 run(s)" in text
    assert "525ms" in text


def test_format_consensus_report_low_confidence():
    report = {
        "n": 5,
        "agreement": 2,
        "agreement_pct": 40.0,
        "confidence": "LOW",
        "divergent_runs": 3,
        "times_ms": [100, 110, 105, 95, 115],
        "total_ms": 525,
    }
    text = format_consensus_report(report)
    assert "2/5" in text
    assert "40%" in text
    assert "LOW" in text
    assert "3 run(s)" in text


def test_confidence_threshold_high():
    # 4/5 = 80% → HIGH
    invoker = _make_invoker(["a b c d e f g"] * 5)
    _, report = run_consensus(invoker, "prompt", 5)
    assert report["confidence"] == "HIGH"
    assert report["agreement"] == 4


def test_confidence_threshold_medium():
    # 4 copies of shared out of 5 → each shared scores 3 (3 others agree)
    # agreement=3, pct = 3/5*100 = 60% >= 60% → MEDIUM
    shared = "alpha beta gamma delta epsilon zeta"
    diff1 = "one two three four five six seven eight"
    outputs = [shared, shared, shared, shared, diff1]
    invoker = _make_invoker(outputs)
    _, report = run_consensus(invoker, "prompt", 5)
    assert report["confidence"] == "MEDIUM"
    assert report["agreement"] == 3  # 3 other copies of shared agree


def test_confidence_threshold_low():
    # All different → agreement = 0 → 0% → LOW
    outputs = [
        "alpha beta gamma delta epsilon",
        "one two three four five six",
        "red blue green yellow purple orange",
        "cat dog bird fish snake turtle",
        "piano guitar violin drums flute harp",
    ]
    invoker = _make_invoker(outputs)
    _, report = run_consensus(invoker, "prompt", 5)
    assert report["confidence"] == "LOW"


def test_best_output_is_longest_on_tie():
    short = "the quick brown fox"
    long_ = "the quick brown fox jumps over the lazy dog and runs away"
    # both have same agreement score (they agree with each other)
    outputs = [short, long_]
    invoker = _make_invoker(outputs)
    best, _ = run_consensus(invoker, "prompt", 2)
    assert best == long_


# ---------------------------------------------------------------------------
# cli.py integration tests
# ---------------------------------------------------------------------------


def _make_mock_config(model_name="test-model"):
    cfg = MagicMock()
    cfg.model_name = model_name
    cfg.temperature = 0.7
    cfg.max_tokens = 2048
    return cfg


def _cli(tmp_path, *args, stdin_text="test input"):
    input_file = tmp_path / "input.txt"
    input_file.write_text(stdin_text)
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


def _cli_live(tmp_path, *args, invoke_outputs=None, stdin_text="test input"):
    input_file = tmp_path / "input.txt"
    input_file.write_text(stdin_text)
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file)] + list(args)

    _outputs = invoke_outputs or ["consensus output A", "consensus output B", "consensus output C"]
    call_index = [0]

    mock_invoker = MagicMock()

    def _invoke(prompt):
        idx = call_index[0]
        call_index[0] += 1
        return _outputs[idx % len(_outputs)]

    mock_invoker.invoke.side_effect = _invoke

    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("explaind.cli.load_config", return_value=_make_mock_config()), \
         patch("explaind.cli.build_invoker", return_value=mock_invoker):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0

    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code, mock_invoker


def test_consensus_too_low_exits_1(tmp_path):
    _, stderr, exit_code = _cli(tmp_path, "--consensus", "1")
    assert exit_code == 1
    assert "minimum" in stderr.lower() or "minimum 2" in stderr


def test_consensus_too_high_exits_1(tmp_path):
    _, stderr, exit_code = _cli(tmp_path, "--consensus", "11")
    assert exit_code == 1
    assert "maximum" in stderr.lower() or "maximum 10" in stderr


def test_consensus_and_compare_exits_1(tmp_path):
    _, stderr, exit_code = _cli(tmp_path, "--consensus", "3", "--compare", "skeptical", "causal")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


def test_consensus_and_chain_exits_1(tmp_path):
    _, stderr, exit_code = _cli(tmp_path, "--consensus", "3", "--chain", "causal", "compressive")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


def test_consensus_and_honest_exits_1(tmp_path):
    _, stderr, exit_code = _cli(tmp_path, "--consensus", "3", "--honest")
    assert exit_code == 1
    assert "mutually exclusive" in stderr


def test_consensus_dry_run_prints_prompt_and_note(tmp_path):
    stdout, _, exit_code = _cli(tmp_path, "--consensus", "3", "--dry-run")
    assert exit_code == 0
    assert "=== SYSTEM PROMPT ===" in stdout
    assert "[consensus: would run 3 times]" in stdout


def test_consensus_dry_run_prints_prompt_once(tmp_path):
    stdout, _, exit_code = _cli(tmp_path, "--consensus", "5", "--dry-run")
    assert exit_code == 0
    assert stdout.count("=== SYSTEM PROMPT ===") == 1


def test_consensus_live_calls_invoke_n_times(tmp_path):
    _, _, exit_code, mock_invoker = _cli_live(tmp_path, "--consensus", "3")
    assert exit_code == 0
    assert mock_invoker.invoke.call_count == 3


def test_consensus_export_includes_report(tmp_path):
    export_file = tmp_path / "out.md"
    _, _, exit_code, _ = _cli_live(
        tmp_path, "--consensus", "3", "--export", str(export_file)
    )
    assert exit_code == 0
    assert export_file.exists()
    content = export_file.read_text(encoding="utf-8")
    assert "## Consensus Analysis" in content
    assert "Agreement" in content
    assert "Confidence" in content
