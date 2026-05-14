from __future__ import annotations

from pathlib import Path

from explaind.context import build_context_window_block
from explaind.gemma import load_gemma_md
from explaind.invoker import ModelInvoker
from explaind.prompts import SYSTEM_PROMPT, assemble_prompt, build_bias_field, format_ability
from explaind.trace import PromptTrace

ABILITIES_DIR = Path("abilities")

ALLOWED_ABILITIES = {
    "balanced",
    "skeptical",
    "causal",
    "compressive",
    "exploratory",
}


def load_ability(name: str) -> str:
    if name not in ALLOWED_ABILITIES:
        allowed = ", ".join(sorted(ALLOWED_ABILITIES))
        raise ValueError(f"unknown ability '{name}' (allowed: {allowed})")
    path = ABILITIES_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ValueError(f"ability file missing: {path}")


def run(
    input_text: str,
    ability: str | None = None,
    dry_run: bool = False,
    invoker: ModelInvoker | None = None,
    trace: bool = False,
    think: bool = False,
    scratchpad: str | None = None,
    context: str | None = None,
) -> tuple[str, PromptTrace | None]:
    """Assemble prompt and invoke the model.

    invoker must be provided when dry_run=False.
    Returns (result_text, PromptTrace) — PromptTrace is None when trace=False.
    scratchpad and context, when provided, are injected into the context window.
    """
    gemma_md = load_gemma_md()

    ability_content = load_ability(ability) if ability else None
    formatted_ability = format_ability(ability, ability_content) if ability_content else None

    context_window = build_context_window_block()
    bias_field = build_bias_field(ability or "balanced")

    full_prompt = assemble_prompt(
        system=SYSTEM_PROMPT,
        gemma_md=gemma_md,
        ability=formatted_ability,
        context_window=context_window,
        bias_field=bias_field,
        user_input=input_text,
        think=think,
        scratchpad=scratchpad,
        context=context,
    )

    prompt_trace = PromptTrace(
        gemma_present=gemma_md is not None,
        ability_name=ability,
        prompt_char_count=len(full_prompt),
        user_input_length=len(input_text),
        think=think,
        scratchpad_len=len(scratchpad) if scratchpad is not None else None,
        context_len=len(context) if context is not None else None,
    ) if trace else None

    if dry_run:
        return full_prompt, prompt_trace

    if invoker is None:
        raise ValueError("invoker is required when dry_run=False")

    return invoker.invoke(full_prompt), prompt_trace
