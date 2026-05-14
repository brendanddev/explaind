from __future__ import annotations

from explaind.context import build_context_window_block

LAYER_SEPARATOR = "\n\n"

SYSTEM_PROMPT = """\
You are a reasoning assistant.

You respond clearly, directly, and accurately.

You adapt your reasoning style to the task:
- explanations
- analysis
- problem interpretation
- conceptual reasoning

You follow optional instruction layers:
- GEMMA.md (global reasoning constraints)
- Ability modules (behavior modifiers)

Do not assume any default task type.
Do not impose a structure unless the input clearly requires it.\
"""

_SYSTEM_TEMPLATE = """\
=== SYSTEM PROMPT ===
{content}
=== END SYSTEM PROMPT ===\
"""

_GEMMA_TEMPLATE = """\
=== REASONING CONSTRAINTS ===
{gemma_md}
=== END REASONING CONSTRAINTS ===\
"""

_ABILITY_TEMPLATE = """\
=== ABILITY: {name} ===
{content}
=== END ABILITY ===\
"""

_INPUT_TEMPLATE = """\
<user_input>
{log}
</user_input>\
"""

_TRAJECTORY_MAP: dict[str, str] = {
    "balanced": "balanced",
    "skeptical": "skeptical",
    "causal": "causal",
    "compressive": "compressive",
    "exploratory": "exploratory",
}

_EPISTEMIC_MAP: dict[str, str] = {
    "skeptical": "skeptical",
}


def format_ability(name: str, content: str) -> str:
    """Return a fully formatted ability section, ready to pass to assemble_prompt."""
    return _ABILITY_TEMPLATE.format(name=name, content=content.strip())


def build_bias_field(ability_name: str) -> str:
    """Return a deterministic BIAS FIELD block derived from ability name alone."""
    name = ability_name.lower()
    trajectory = _TRAJECTORY_MAP.get(name, "balanced")
    epistemic = _EPISTEMIC_MAP.get(name, "neutral")
    return (
        f"BIAS FIELD\n"
        f"- [BIAS: {name.upper()}]\n"
        f"- [TRAJECTORY: {trajectory}]\n"
        f"- [EPISTEMIC: {epistemic}]\n"
        f"- [INVARIANTS: ACTIVE]\n"
        f"END BIAS FIELD"
    )


def assemble_prompt(
    system: str,
    gemma_md: str | None,
    ability: str | None,
    context_window: str,
    bias_field: str,
    user_input: str,
    think: bool = False,
    scratchpad: str | None = None,
    context: str | None = None,
) -> str:
    """Pure function. Assembles the full prompt in strict layer order.

    Layer order (non-negotiable):
      1. system
      2. gemma_md       (skipped when None)
      3. ability        (skipped when None)
      4. context_window
      5. bias_field
      6. user_input

    When scratchpad or context are provided, the context_window is rebuilt
    with that content injected. Otherwise context_window is used as-is.

    Performs no I/O, no config access, no global state reads.
    Output is byte-stable for identical inputs.
    """
    if scratchpad is not None or context is not None:
        context_window = build_context_window_block(scratchpad=scratchpad, context=context)

    system_content = system + "\n<|think|>" if think else system
    layers: list[str] = [_SYSTEM_TEMPLATE.format(content=system_content)]

    if gemma_md:
        layers.append(_GEMMA_TEMPLATE.format(gemma_md=gemma_md.strip()))

    if ability:
        layers.append(ability)

    layers.append(context_window)

    layers.append(bias_field)

    layers.append(_INPUT_TEMPLATE.format(log=user_input))

    return LAYER_SEPARATOR.join(layers)
