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

_PRIMACY_ANCHORS: dict[str, str] = {
    "balanced":    "At each inference step: identify the strongest case for each position before committing to any. Name what the opposing view gets right before stating what it gets wrong.",
    "skeptical":   "Default to doubt. Prioritize evidence quality, logical gaps, and counterarguments over surface claims.",
    "causal":      "Map causal relationships rigorously. Distinguish correlation from causation. Trace mechanisms and dependencies.",
    "compressive": "Distill to core essence. Eliminate redundancy while preserving meaning and logical structure.",
    "exploratory": "At each step ask: what would this look like from a completely different starting assumption? Pursue that. Do not return to the obvious framing.",
    "calibrator":  "Calibrate all confidence rigorously. Ground every claim in evidence strength and unknowns.",
    "devil":       "Adopt strongest possible opposition. Ruthlessly attack weaknesses in reasoning and assumptions.",
    "updater":     "Update beliefs continuously based on new evidence. Override priors when evidence demands it.",
}

_PERIODIC_REFRESHES: dict[str, str] = {
    "balanced":    "[REFRESH] Check: have I named what the strongest opposing view gets right? If not, do that before continuing.",
    "skeptical":   "[REFRESH] Skeptical protocol: challenge every assumption and seek falsifiers.",
    "causal":      "[REFRESH] Causal mode: identify root causes, mechanisms, and downstream effects.",
    "compressive": "[REFRESH] Compress: extract only the essential signal.",
    "exploratory": "[REFRESH] Ask: what assumption in my current reasoning could be inverted? Follow that inversion.",
    "calibrator":  "[REFRESH] Calibrate: assign explicit 0-100 confidence and list key uncertainties.",
    "devil":       "[REFRESH] Devil mode: construct the strongest counterarguments possible.",
    "updater":     "[REFRESH] Updater: revise beliefs according to incoming evidence strength.",
}

_RECENCY_FIELDS: dict[str, str] = {
    "balanced": (
        "BIAS FIELD\n"
        "[REASONING MODE: BALANCED]\n"
        "Apply balanced reasoning immediately. Consider all sides\n"
        "equally. Identify strongest evidence on every side.\n"
        "Avoid over-correction or under-emphasis.\n"
        "Output with calibrated nuance.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "skeptical": (
        "BIAS FIELD\n"
        "[REASONING MODE: SKEPTICAL]\n"
        "Activate full skeptical filter now. Extract claims,\n"
        "evaluate evidence strength, generate counterarguments,\n"
        "identify gaps, and quantify uncertainty.\n"
        "Surface weaknesses first. Do not soften conclusions.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "causal": (
        "BIAS FIELD\n"
        "[REASONING MODE: CAUSAL]\n"
        "Apply causal analysis now. Build explicit cause-effect\n"
        "chains. Flag confounding factors. Distinguish necessary\n"
        "vs sufficient conditions. Output clear causal graph\n"
        "structure in reasoning.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "compressive": (
        "BIAS FIELD\n"
        "[REASONING MODE: COMPRESSIVE]\n"
        "Execute compressive reasoning immediately. Identify core\n"
        "claims and principles. Remove fluff. Produce maximally\n"
        "concise yet complete synthesis. Preserve causal links\n"
        "and uncertainties.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "exploratory": (
        "BIAS FIELD\n"
        "[REASONING MODE: EXPLORATORY]\n"
        "Begin exploratory reasoning now. Brainstorm multiple\n"
        "directions. Make unexpected connections. Suspend\n"
        "criticism. Map the full possibility space before\n"
        "narrowing.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "calibrator": (
        "BIAS FIELD\n"
        "[REASONING MODE: CALIBRATOR]\n"
        "Activate precise calibration now. For every major claim,\n"
        "output confidence percentage and justification.\n"
        "Explicitly list unknowns and falsification conditions.\n"
        "Adjust for overconfidence bias.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "devil": (
        "BIAS FIELD\n"
        "[REASONING MODE: DEVIL]\n"
        "Engage full adversarial protocol immediately. Identify\n"
        "every flaw, weak assumption, and vulnerability.\n"
        "Steelman the opposing case. Attack your own current\n"
        "reasoning hardest. Expose hidden risks.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
    "updater": (
        "BIAS FIELD\n"
        "[REASONING MODE: UPDATER]\n"
        "Execute belief updating now. Compare new input against\n"
        "existing state. Revise conclusions proportionally to\n"
        "evidence. Explicitly note what changed and why.\n"
        "Maintain Bayesian discipline.\n"
        "[INVARIANTS: ACTIVE]\n"
        "END BIAS FIELD"
    ),
}


def _extract_ability_name(ability: str | None) -> str:
    if ability is None:
        return "balanced"
    first_line = ability.split("\n")[0]
    if first_line.startswith("=== ABILITY: "):
        name = first_line[len("=== ABILITY: "):]
        idx = name.rfind(" ===")
        if idx >= 0:
            name = name[:idx]
        return name.strip()
    return "balanced"


def format_ability(name: str, content: str) -> str:
    """Return a fully formatted ability section, ready to pass to assemble_prompt."""
    return _ABILITY_TEMPLATE.format(name=name, content=content.strip())


def build_bias_field(ability_name: str, preset_name: str | None = None) -> str:
    """Return a deterministic recency BIAS FIELD block derived from ability name alone."""
    name = ability_name.lower()
    if name in _RECENCY_FIELDS:
        field = _RECENCY_FIELDS[name]
    else:
        field = (
            f"BIAS FIELD\n"
            f"[REASONING MODE: {name.upper()}]\n"
            f"Apply {name} reasoning now.\n"
            f"[INVARIANTS: ACTIVE]\n"
            f"END BIAS FIELD"
        )
    if preset_name is not None:
        lines = field.split("\n")
        lines.insert(-1, f"[PRESET: {preset_name.upper()}]")
        field = "\n".join(lines)
    return field


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
    scaffold_context: str | None = None,
) -> str:
    """Pure function. Assembles the full prompt in strict layer order.

    Layer order (non-negotiable):
      1. system         (primacy anchor prepended inside system block)
      2. gemma_md       (skipped when None)
      3. periodic       (first injection, skipped when gemma_md is None)
      4. ability        (skipped when None)
      5. periodic       (second injection, skipped when ability is None)
      6. context_window
      7. scaffold_context (skipped when None)
      8. bias_field     (recency position)
      9. user_input

    Performs no I/O, no config access, no global state reads.
    Output is byte-stable for identical inputs.
    """
    if scratchpad is not None or context is not None:
        context_window = build_context_window_block(scratchpad=scratchpad, context=context)

    ability_name = _extract_ability_name(ability)
    primacy = _PRIMACY_ANCHORS.get(
        ability_name, f"[REASONING FRAME: {ability_name.upper()} — active throughout]"
    )
    periodic = _PERIODIC_REFRESHES.get(
        ability_name, f"[REFRESH] {ability_name.upper()} protocol: active."
    )

    system_content = primacy + "\n\n" + system
    layers: list[str] = [_SYSTEM_TEMPLATE.format(content=system_content)]

    if gemma_md:
        layers.append(_GEMMA_TEMPLATE.format(gemma_md=gemma_md.strip()))
        layers.append(periodic)

    if ability:
        layers.append(ability)
        layers.append(periodic)

    layers.append(context_window)

    if scaffold_context is not None:
        layers.append(scaffold_context)

    layers.append(bias_field)
    layers.append(_INPUT_TEMPLATE.format(log=user_input))

    assembled = LAYER_SEPARATOR.join(layers)
    model_prefill = "<|think|>\n" if think else ""
    return f"<start_of_turn>user\n{assembled}\n<end_of_turn>\n<start_of_turn>model\n{model_prefill}"
