from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from explaind.scaffold import (
    ScaffoldState,
    build_initial_scaffold,
    parse_scaffold_update,
    scaffold_to_export_summary,
    scaffold_to_injection,
)


# ---------------------------------------------------------------------------
# scaffold.py unit tests
# ---------------------------------------------------------------------------


def test_build_initial_scaffold_correct_state():
    state = build_initial_scaffold("test input", ["causal", "compressive"])
    assert state.current_stage == "causal"
    assert state.stage_history == []
    assert state.raw_input == "test input"
    assert state.claims == []
    assert state.causal_graph == {"nodes": [], "edges": [], "confidence": {}}
    assert state.compressive_summary == ""
    assert state.uncertainty_register == []
    assert state.falsification_conditions == []
    assert state.confidence_scores == {}
    assert state.drift_detected is False
    assert state.tokens_used == 0
    assert state.total_passes == 2


def test_scaffold_to_injection_contains_session_id():
    state = build_initial_scaffold("test", ["causal", "compressive"], session_id="abc12345")
    injection = scaffold_to_injection(state)
    assert "abc12345" in injection


def test_scaffold_to_injection_contains_raw_input():
    state = build_initial_scaffold("my unique question here", ["causal", "compressive"])
    injection = scaffold_to_injection(state)
    assert "my unique question here" in injection


def test_scaffold_to_injection_contains_scaffold_update_block():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    injection = scaffold_to_injection(state)
    assert "[SCAFFOLD_UPDATE]" in injection
    assert "[/SCAFFOLD_UPDATE]" in injection


def test_parse_scaffold_update_updates_claims():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    output = 'Some output.\n\n[SCAFFOLD_UPDATE]\n{"claims": ["claim A", "claim B"]}\n[/SCAFFOLD_UPDATE]'
    new_state, clean = parse_scaffold_update(output, state)
    assert "claim A" in new_state.claims
    assert "claim B" in new_state.claims


def test_parse_scaffold_update_updates_compressive_summary():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    output = '[SCAFFOLD_UPDATE]\n{"compressive_summary": "This is the summary."}\n[/SCAFFOLD_UPDATE]'
    new_state, clean = parse_scaffold_update(output, state)
    assert new_state.compressive_summary == "This is the summary."


def test_parse_scaffold_update_malformed_json_drift():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    original = '[SCAFFOLD_UPDATE]\n{invalid json here}\n[/SCAFFOLD_UPDATE]'
    new_state, clean = parse_scaffold_update(original, state)
    assert new_state.drift_detected is True
    assert clean == original


def test_parse_scaffold_update_no_block_drift():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    output = "Normal model output with no scaffold update."
    new_state, clean = parse_scaffold_update(output, state)
    assert new_state.drift_detected is True
    assert clean == output


def test_parse_scaffold_update_merges_claims_no_duplicates():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    state.claims = ["existing claim"]
    output = '[SCAFFOLD_UPDATE]\n{"claims": ["existing claim", "new claim"]}\n[/SCAFFOLD_UPDATE]'
    new_state, _ = parse_scaffold_update(output, state)
    assert new_state.claims.count("existing claim") == 1
    assert "new claim" in new_state.claims


def test_parse_scaffold_update_confidence_scores_override():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    state.confidence_scores = {"claim A": 50.0}
    output = '[SCAFFOLD_UPDATE]\n{"confidence_scores": {"claim A": 80.0, "claim B": 60.0}}\n[/SCAFFOLD_UPDATE]'
    new_state, _ = parse_scaffold_update(output, state)
    assert new_state.confidence_scores["claim A"] == 80.0
    assert new_state.confidence_scores["claim B"] == 60.0


def test_scaffold_to_export_summary_contains_established_claims():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    summary = scaffold_to_export_summary(state)
    assert "Established Claims" in summary


def test_scaffold_to_export_summary_contains_drift_detected():
    state = build_initial_scaffold("test", ["causal", "compressive"])
    summary = scaffold_to_export_summary(state)
    assert "Drift detected" in summary


# ---------------------------------------------------------------------------
# assemble_prompt tests
# ---------------------------------------------------------------------------


def test_assemble_prompt_scaffold_context_position():
    from explaind.context import build_context_window_block
    from explaind.prompts import SYSTEM_PROMPT, assemble_prompt, build_bias_field

    ctx = build_context_window_block()
    bias = build_bias_field("balanced")
    prompt = assemble_prompt(
        system=SYSTEM_PROMPT,
        gemma_md=None,
        ability=None,
        context_window=ctx,
        bias_field=bias,
        user_input="test input",
        scaffold_context="UNIQUE_SCAFFOLD_MARKER",
    )
    assert "UNIQUE_SCAFFOLD_MARKER" in prompt
    ctx_pos = prompt.index("[CONTEXT WINDOW LAYERS]")
    scaffold_pos = prompt.index("UNIQUE_SCAFFOLD_MARKER")
    # Use "END BIAS FIELD" to avoid the false positive at "ABILITY + BIAS FIELD priority."
    # inside the context window instruction text.
    bias_pos = prompt.index("END BIAS FIELD")
    assert ctx_pos < scaffold_pos < bias_pos


def test_assemble_prompt_without_scaffold_context_unchanged():
    from explaind.context import build_context_window_block
    from explaind.prompts import SYSTEM_PROMPT, assemble_prompt, build_bias_field

    ctx = build_context_window_block()
    bias = build_bias_field("balanced")
    kwargs = dict(
        system=SYSTEM_PROMPT,
        gemma_md=None,
        ability=None,
        context_window=ctx,
        bias_field=bias,
        user_input="test input",
    )
    without = assemble_prompt(**kwargs)
    with_none = assemble_prompt(**kwargs, scaffold_context=None)
    assert without == with_none


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def _make_mock_config(model_name="test-model"):
    cfg = MagicMock()
    cfg.model_name = model_name
    cfg.temperature = 0.0
    cfg.max_tokens = 2048
    return cfg


def _invoke_dry(tmp_path, *args):
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for scaffold")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind", str(input_file)] + list(args)
    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf):
        try:
            from explaind.cli import main
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def test_scaffold_without_chain_exits_1(tmp_path):
    _, stderr, exit_code = _invoke_dry(tmp_path, "--scaffold")
    assert exit_code == 1
    assert "--scaffold requires --chain" in stderr


def test_chain_scaffold_dry_run_contains_cognitive_scaffold(tmp_path):
    stdout, _, exit_code = _invoke_dry(
        tmp_path, "--chain", "causal", "compressive", "--scaffold", "--dry-run"
    )
    assert exit_code == 0
    assert "[COGNITIVE SCAFFOLD" in stdout


def test_chain_scaffold_dry_run_pass2_stage_name(tmp_path):
    stdout, _, exit_code = _invoke_dry(
        tmp_path, "--chain", "causal", "compressive", "--scaffold", "--dry-run"
    )
    assert exit_code == 0
    assert "Stage: compressive" in stdout


def test_chain_scaffold_export_contains_scaffold_summary(tmp_path):
    from explaind.cli import main

    export_file = tmp_path / "scaffold_export.md"
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for scaffold export")
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = [
        "explaind", str(input_file),
        "--chain", "causal", "compressive",
        "--scaffold",
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
    assert "Cognitive Scaffold Summary" in md
