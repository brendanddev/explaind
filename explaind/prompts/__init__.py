from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert software debugging system.

Rules:
- Only use provided logs, diffs, or context.
- Do NOT assume programming language, framework, or runtime.
- Do NOT infer language or runtime from error messages alone.
- Only assume language or context if it is explicitly stated in the input.
- Do NOT hallucinate missing information (stack traces, code, variables, etc).
- If information is missing or ambiguous, explicitly say: "insufficient information".
- Prefer uncertainty over guessing.
- All conclusions must be grounded in evidence from the provided input.

Output format:
- Root cause
- Explanation
- Suggested fix\
"""

_USER_TEMPLATE = """\
Analyze this software failure:

=== LOG ===
{log}

TASK:
1. Identify root cause
2. Explain causal chain
3. Suggest fix

If the log is insufficient to determine any of the above, explicitly state that.\
"""


def build_prompt(log: str, gemma_md: str | None = None) -> str:
    """Assemble the user-turn prompt for one debugging inference.

    Prepends optional GEMMA.md context before the log block when provided,
    so the model reasons within project-specific heuristics without altering
    the strict grounding rules in the system prompt.
    """
    parts: list[str] = []

    if gemma_md:
        parts.append(f"=== CONTEXT (GEMMA.md) ===\n{gemma_md.strip()}")

    parts.append(_USER_TEMPLATE.format(log=log.strip()))

    return "\n\n".join(parts)
