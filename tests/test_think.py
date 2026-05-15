import io
import sys
from unittest.mock import patch

import pytest

from explaind.cli import main
from explaind.context import build_context_window_block
from explaind.prompts import SYSTEM_PROMPT, assemble_prompt, build_bias_field


def _base_kwargs(**overrides):
    defaults = dict(
        system=SYSTEM_PROMPT,
        gemma_md=None,
        ability=None,
        context_window=build_context_window_block(),
        bias_field=build_bias_field("balanced"),
        user_input="test input",
    )
    defaults.update(overrides)
    return defaults


def _invoke(tmp_path, *args):
    input_file = tmp_path / "input.txt"
    input_file.write_text("test input for think")
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


def test_think_true_contains_token():
    result = assemble_prompt(**_base_kwargs(think=True))
    assert "<|think|>" in result


def test_think_false_omits_token():
    result = assemble_prompt(**_base_kwargs(think=False))
    assert "<|think|>" not in result


def test_think_token_after_model_turn_start():
    result = assemble_prompt(**_base_kwargs(think=True))
    think_pos = result.index("<|think|>")
    model_turn_pos = result.index("<start_of_turn>model")
    end_system_pos = result.index("=== END SYSTEM PROMPT ===")
    # <|think|> must be AFTER <start_of_turn>model, not inside the system prompt block
    assert think_pos > model_turn_pos
    assert think_pos > end_system_pos
    # and it must be the very next content after <start_of_turn>model\n
    model_turn_end = model_turn_pos + len("<start_of_turn>model\n")
    assert result[model_turn_end:model_turn_end + len("<|think|>")] == "<|think|>"


def test_think_dry_run_shows_token(tmp_path):
    stdout, _, exit_code = _invoke(tmp_path, "--dry-run", "--think")
    assert exit_code == 0
    assert "<|think|>" in stdout


def test_think_compare_dry_run_all_abilities(tmp_path):
    stdout, _, exit_code = _invoke(
        tmp_path, "--compare", "skeptical", "causal", "--dry-run", "--think"
    )
    assert exit_code == 0
    assert stdout.count("<|think|>") == 2
