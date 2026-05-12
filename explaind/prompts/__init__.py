from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert software debugging assistant.

Analyze the provided log, stack trace, or error message and explain:
- What failed and why
- The likely root cause
- How to fix it

Be concise and direct. Only use information from the provided input.\
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

    parts.append(_INPUT_TEMPLATE.format(log=log.strip()))

    return "\n\n".join(parts)
