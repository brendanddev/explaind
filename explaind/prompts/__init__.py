from __future__ import annotations

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
=== INPUT ===
{log}\
"""

_TRAJECTORY_MAP: dict[str, str] = {
    "balanced": "balanced",
    "skeptical": "balanced",
    "causal": "balanced",
    "compressive": "compressive",
    "exploratory": "exploratory",
}

_EPISTEMIC_MAP: dict[str, str] = {
    "skeptical": "skeptical",
}


def build_bias_field(ability_name: str) -> str:
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


def build_prompt(
    log: str,
    gemma_md: str | None = None,
    ability_name: str | None = None,
    ability_content: str | None = None,
) -> str:
    parts: list[str] = []

    if gemma_md:
        parts.append(_GEMMA_TEMPLATE.format(gemma_md=gemma_md.strip()))

    if ability_content:
        parts.append(_ABILITY_TEMPLATE.format(
            name=ability_name or "custom",
            content=ability_content.strip(),
        ))

    parts.append(build_bias_field(ability_name or "balanced"))

    parts.append(_INPUT_TEMPLATE.format(log=log.strip()))

    return "\n\n".join(parts)
