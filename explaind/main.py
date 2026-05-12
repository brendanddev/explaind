from __future__ import annotations

from pathlib import Path

from explaind.gemma import load_gemma_md
from explaind.invoker import ModelInvoker
from explaind.prompts import SYSTEM_PROMPT, build_prompt

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
) -> tuple[str, None]:
    """Assemble prompt and invoke the model.

    invoker must be provided when dry_run=False.
    """
    gemma_md = load_gemma_md()
    ability_content = load_ability(ability) if ability else None

    prompt = build_prompt(
        input_text,
        gemma_md=gemma_md,
        ability_name=ability,
        ability_content=ability_content,
    )

    if dry_run:
        full = f"=== SYSTEM PROMPT ===\n{SYSTEM_PROMPT}\n=== END SYSTEM PROMPT ===\n\n{prompt}"
        return full, None

    if invoker is None:
        raise ValueError("invoker is required when dry_run=False")

    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    return invoker.invoke(full_prompt), None
