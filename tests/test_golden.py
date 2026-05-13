"""Golden file tests for assemble_prompt.

Any change to assemble_prompt that alters its output will fail here.
To intentionally update a golden file, re-run the relevant case with
print(assemble_prompt(...)) and paste the new output into the file.
"""
from pathlib import Path

import pytest

from explaind.context import build_context_window_block
from explaind.prompts import assemble_prompt, build_bias_field, format_ability

_GOLDEN_DIR = Path(__file__).parent / "golden"


def _load(name: str) -> str:
    return (_GOLDEN_DIR / name).read_text(encoding="utf-8")


def _ctx() -> str:
    return build_context_window_block()


def test_golden_balanced():
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=None,
        context_window=_ctx(),
        bias_field=build_bias_field("balanced"),
        user_input="USER INPUT",
    )
    assert result == _load("prompt_balanced.txt")


def test_golden_skeptical():
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=format_ability("skeptical", "ABILITY TEXT"),
        context_window=_ctx(),
        bias_field=build_bias_field("skeptical"),
        user_input="USER INPUT",
    )
    assert result == _load("prompt_skeptical.txt")


def test_golden_no_gemma_md():
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md=None,
        ability=None,
        context_window=_ctx(),
        bias_field=build_bias_field("balanced"),
        user_input="USER INPUT",
    )
    assert "REASONING CONSTRAINTS" not in result
    assert "=== SYSTEM PROMPT ===" in result
    assert "[CONTEXT WINDOW LAYERS]" in result
    assert "BIAS FIELD" in result
    assert "<user_input>" in result


def test_golden_no_ability():
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=None,
        context_window=_ctx(),
        bias_field=build_bias_field("balanced"),
        user_input="USER INPUT",
    )
    assert "=== ABILITY" not in result
    assert "[CONTEXT WINDOW LAYERS]" in result
    assert "BIAS FIELD" in result


def test_golden_layer_order_positions():
    result = assemble_prompt(
        system="SYSTEM",
        gemma_md="GEMMA",
        ability=format_ability("causal", "CAUSAL"),
        context_window=_ctx(),
        bias_field=build_bias_field("causal"),
        user_input="USER INPUT",
    )
    positions = {
        "system":   result.index("=== SYSTEM PROMPT ==="),
        "gemma":    result.index("GEMMA"),
        "ability":  result.index("=== ABILITY: causal ==="),
        "context":  result.index("[CONTEXT WINDOW LAYERS]"),
        "bias":     result.index("BIAS FIELD"),
        "user":     result.index("<user_input>"),
    }
    ordered = sorted(positions, key=positions.__getitem__)
    assert ordered == ["system", "gemma", "ability", "context", "bias", "user"]
