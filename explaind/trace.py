from __future__ import annotations

from dataclasses import dataclass

_ABILITY_ROLES: dict[str, str] = {
    "balanced":    "neutral prior — default reasoning trajectory, no bias applied",
    "skeptical":   "epistemic pressure — questions assumptions, resists confident conclusions",
    "causal":      "mechanism tracing — follows causal chains, identifies root causes",
    "compressive": "signal reduction — extracts key information, suppresses noise",
    "exploratory": "synthesis — expands possibilities, generates competing interpretations",
}


@dataclass(frozen=True)
class PromptTrace:
    gemma_present: bool
    ability_name: str | None
    prompt_char_count: int
    user_input_length: int
    think: bool = False
    scratchpad_len: int | None = None
    context_len: int | None = None


@dataclass(frozen=True)
class TraceData:
    model_name: str
    temperature: float
    max_tokens: int
    prompt: PromptTrace


def format_trace(data: TraceData) -> str:
    """Return a formatted prompt-construction trace string.

    Pure function. No I/O. Deterministic for identical inputs.
    Intended for stderr output only — never touches stdout.
    """
    pt = data.prompt
    ability = pt.ability_name or "none"
    bias_name = pt.ability_name or "balanced"

    lines = [
        "[TRACE START]",
        "",
        "[MODEL]",
        data.model_name,
        "",
        "[SETTINGS]",
        f"temperature={data.temperature}",
        f"max_tokens={data.max_tokens}",
        "",
        "[LAYERS]",
        "SYSTEM: present",
        f"GEMMA: {'present' if pt.gemma_present else 'absent'}",
        f"ABILITY: {ability}",
        "CONTEXT WINDOW LAYERS: present",
        f"BIAS FIELD: {bias_name}",
        "PRIMACY ANCHOR: active",
        "PERIODIC REFRESHES: 2 injections",
        "RECENCY FIELD: enhanced",
        f"USER INPUT: {pt.user_input_length} chars",
        f"SCRATCHPAD: {pt.scratchpad_len} chars" if pt.scratchpad_len is not None else "SCRATCHPAD: none",
        f"CONTEXT: {pt.context_len} chars" if pt.context_len is not None else "CONTEXT: none",
        *( ["THINKING MODE: enabled"] if pt.think else [] ),
        "",
        "[PROMPT SIZE]",
        f"{pt.prompt_char_count} chars",
        "",
        "[INTERPRETATION MAP]",
        f"{bias_name} → {_ABILITY_ROLES.get(bias_name, 'unknown ability')}",
        "",
        "[TRACE END]",
    ]
    return "\n".join(lines)
