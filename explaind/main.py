from __future__ import annotations

from pathlib import Path

import ollama

from explaind.gemma import load_gemma_md
from explaind.prompts import SYSTEM_PROMPT, build_prompt

MODEL = "gemma4-e2b_q4_k_m:latest"

ABILITIES_DIR = Path("abilities")


def load_ability(name: str) -> str | None:
    path = ABILITIES_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def run(input_text: str, ability: str | None = None) -> str:
    gemma_md = load_gemma_md()
    ability_content = load_ability(ability) if ability else None

    prompt = build_prompt(
        input_text,
        gemma_md=gemma_md,
        ability_name=ability,
        ability_content=ability_content,
    )

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0},
    )
    return response["message"]["content"]
