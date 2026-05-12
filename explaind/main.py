from __future__ import annotations

from pathlib import Path

import ollama

from explaind.gemma import load_gemma_md
from explaind.prompts import SYSTEM_PROMPT, build_prompt

MODEL = "gemma4-e2b_q4_k_m:latest"
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


_ctx_cache: dict[str, int | None] = {}


def _get_context_window(model: str) -> int | None:
    """Return the model's context window size via ollama.show(), cached per process."""
    if model in _ctx_cache:
        return _ctx_cache[model]
    try:
        info = ollama.show(model)
        # Honour an explicit num_ctx override in the parameters string first.
        for line in (getattr(info, "parameters", None) or "").splitlines():
            parts = line.strip().split()
            if len(parts) == 2 and parts[0].lower() == "num_ctx":
                _ctx_cache[model] = int(parts[1])
                return _ctx_cache[model]
        # Fall back to the architecture-specific context_length in modelinfo.
        for key, val in (getattr(info, "modelinfo", None) or {}).items():
            if key.endswith(".context_length") and val is not None:
                _ctx_cache[model] = int(val)
                return _ctx_cache[model]
    except Exception:
        pass
    _ctx_cache[model] = None
    return None


def _extract_usage(response) -> dict | None:
    """Pull token counts from the Ollama response object (or dict).

    Returns None if neither field is present so callers can print a fallback.
    """
    def _get(key: str):
        val = getattr(response, key, None)
        if val is None:
            try:
                val = response.get(key)
            except AttributeError:
                pass
        return val

    inp = _get("prompt_eval_count")
    out = _get("eval_count")

    if inp is None and out is None:
        return None

    usage: dict = {}
    if inp is not None:
        usage["input_tokens"] = inp
    if out is not None:
        usage["output_tokens"] = out
    if inp is not None and out is not None:
        usage["total_tokens"] = inp + out
    return usage


def run(input_text: str, ability: str | None = None, dry_run: bool = False) -> tuple[str, dict | None]:
    """Return (response_text, usage_dict). usage_dict is None when Ollama
    does not include token counts in the response."""
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

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        options={"temperature": 0},
    )

    text = response["message"]["content"]
    usage = _extract_usage(response)
    if usage is not None:
        ctx = _get_context_window(MODEL)
        if ctx is not None:
            usage["context_window"] = ctx
    return text, usage
