"""Tests for --scratchpad and --context injection."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from explaind.cli import main
from explaind.errors import InputError
from explaind.loader import load_context, load_scratchpad
from explaind.main import run
from explaind.prompts import assemble_prompt, build_bias_field
from explaind.context import build_context_window_block


# ---------------------------------------------------------------------------
# load_scratchpad
# ---------------------------------------------------------------------------

def test_load_scratchpad_missing_file_raises(tmp_path):
    with pytest.raises(InputError, match="no such file"):
        load_scratchpad(tmp_path / "ghost.md")


def test_load_scratchpad_empty_file_raises(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("")
    with pytest.raises(InputError, match="empty"):
        load_scratchpad(f)


def test_load_scratchpad_prepends_semantic_header(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("hypothesis: the queue is full")
    result = load_scratchpad(f)
    assert "[ACTIVE WORKING MEMORY]" in result
    assert "hypothesis: the queue is full" in result
    assert result.index("[ACTIVE WORKING MEMORY]") < result.index("hypothesis: the queue is full")


def test_load_scratchpad_header_contains_reasoning_instruction(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("some notes")
    result = load_scratchpad(f)
    assert "Do not ignore it in favour of general knowledge" in result


def test_load_scratchpad_returns_string(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("content")
    assert isinstance(load_scratchpad(f), str)


# ---------------------------------------------------------------------------
# load_context
# ---------------------------------------------------------------------------

def test_load_context_missing_file_raises(tmp_path):
    with pytest.raises(InputError, match="no such file"):
        load_context(tmp_path / "ghost.md")


def test_load_context_empty_file_raises(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("")
    with pytest.raises(InputError, match="empty"):
        load_context(f)


def test_load_context_prepends_semantic_header(tmp_path):
    f = tmp_path / "prior.md"
    f.write_text("prior analysis result here")
    result = load_context(f)
    assert "[REFERENCE CONTEXT]" in result
    assert "prior analysis result here" in result
    assert result.index("[REFERENCE CONTEXT]") < result.index("prior analysis result here")


def test_load_context_header_contains_prefer_instruction(tmp_path):
    f = tmp_path / "prior.md"
    f.write_text("background material")
    result = load_context(f)
    assert "prefer this material" in result


def test_load_context_returns_string(tmp_path):
    f = tmp_path / "prior.md"
    f.write_text("content")
    assert isinstance(load_context(f), str)


# ---------------------------------------------------------------------------
# assemble_prompt — scratchpad injection
# ---------------------------------------------------------------------------

def _base_kwargs(**overrides) -> dict:
    defaults = dict(
        system="S",
        gemma_md="G",
        ability=None,
        context_window=build_context_window_block(),
        bias_field=build_bias_field("balanced"),
        user_input="U",
    )
    defaults.update(overrides)
    return defaults


def test_assemble_prompt_scratchpad_replaces_none(tmp_path):
    result = assemble_prompt(**_base_kwargs(scratchpad="my hypothesis"))
    assert "[SCRATCHPAD]\nnone" not in result
    assert "my hypothesis" in result


def test_assemble_prompt_scratchpad_appears_under_scratchpad_field():
    result = assemble_prompt(**_base_kwargs(scratchpad="working note"))
    assert "[SCRATCHPAD]\nworking note" in result


def test_assemble_prompt_context_appears_in_context_block():
    loaded = "[REFERENCE CONTEXT]\nsome background"
    result = assemble_prompt(**_base_kwargs(context=loaded))
    assert "some background" in result
    assert "[CONTEXT WINDOW LAYERS]" in result


def test_assemble_prompt_neither_leaves_none_unchanged():
    result = assemble_prompt(**_base_kwargs())
    assert "[SCRATCHPAD]\nnone" in result
    assert "[REASONING TRACE]\nnone" in result


def test_assemble_prompt_both_scratchpad_and_context():
    result = assemble_prompt(**_base_kwargs(
        scratchpad="my notes",
        context="[REFERENCE CONTEXT]\nmy docs",
    ))
    assert "my notes" in result
    assert "my docs" in result


# ---------------------------------------------------------------------------
# run() — scratchpad and context threading
# ---------------------------------------------------------------------------

def test_run_with_scratchpad_appears_in_prompt():
    prompt, _ = run("test input", dry_run=True, scratchpad="my hypothesis")
    assert "my hypothesis" in prompt


def test_run_with_context_appears_in_prompt():
    prompt, _ = run(
        "test input",
        dry_run=True,
        context="[REFERENCE CONTEXT]\nsome reference",
    )
    assert "some reference" in prompt


def test_run_without_scratchpad_shows_none():
    prompt, _ = run("test input", dry_run=True)
    assert "[SCRATCHPAD]\nnone" in prompt


def test_run_scratchpad_trace_records_length():
    content = "hypothesis content"
    _, pt = run("input", dry_run=True, trace=True, scratchpad=content)
    assert pt is not None
    assert pt.scratchpad_len == len(content)


def test_run_context_trace_records_length():
    content = "[REFERENCE CONTEXT]\ndocs"
    _, pt = run("input", dry_run=True, trace=True, context=content)
    assert pt is not None
    assert pt.context_len == len(content)


def test_run_no_scratchpad_trace_shows_none():
    _, pt = run("input", dry_run=True, trace=True)
    assert pt is not None
    assert pt.scratchpad_len is None
    assert pt.context_len is None


# ---------------------------------------------------------------------------
# CLI integration — --dry-run with --scratchpad
# ---------------------------------------------------------------------------

def _invoke(tmp_path, *args):
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input")
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


def test_dry_run_with_scratchpad_shows_injected_content(tmp_path):
    sp = tmp_path / "hypothesis.md"
    sp.write_text("the root cause is X")
    stdout, _, exit_code = _invoke(tmp_path, "--dry-run", "--scratchpad", str(sp))
    assert exit_code == 0
    assert "the root cause is X" in stdout


def test_dry_run_with_context_shows_injected_content(tmp_path):
    ctx = tmp_path / "prior.md"
    ctx.write_text("prior finding: Y was observed")
    stdout, _, exit_code = _invoke(tmp_path, "--dry-run", "--context", str(ctx))
    assert exit_code == 0
    assert "prior finding: Y was observed" in stdout


def test_dry_run_with_missing_scratchpad_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--dry-run", "--scratchpad", str(tmp_path / "ghost.md"))
    assert exit_code == 1
    assert "no such file" in stderr


def test_dry_run_with_missing_context_exits_1(tmp_path):
    _, stderr, exit_code = _invoke(tmp_path, "--dry-run", "--context", str(tmp_path / "ghost.md"))
    assert exit_code == 1
    assert "no such file" in stderr


# ---------------------------------------------------------------------------
# CLI integration — --compare with --scratchpad passes to all abilities
# ---------------------------------------------------------------------------

def test_compare_with_scratchpad_passes_to_all_abilities(tmp_path):
    sp = tmp_path / "hypothesis.md"
    sp.write_text("scratchpad signal xyz")
    stdout, _, exit_code = _invoke(
        tmp_path, "--compare", "causal", "skeptical", "--dry-run", "--scratchpad", str(sp)
    )
    assert exit_code == 0
    # both ability blocks should contain the injected scratchpad
    assert stdout.count("scratchpad signal xyz") == 2


def test_compare_with_context_passes_to_all_abilities(tmp_path):
    ctx = tmp_path / "prior.md"
    ctx.write_text("context signal abc")
    stdout, _, exit_code = _invoke(
        tmp_path, "--compare", "causal", "exploratory", "--dry-run", "--context", str(ctx)
    )
    assert exit_code == 0
    assert stdout.count("context signal abc") == 2
