from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert software debugging system.

Rules:
- Only use information explicitly present in the provided log, diff, or context.
- Do NOT assume programming language, framework, or runtime unless the log states it verbatim.
- Do NOT infer language or runtime from error message wording alone.
- Do NOT hallucinate missing information: no invented stack traces, variable names, code, or behavior.
- If the log does not contain enough information to answer a section, write exactly: "insufficient information".
- Never speculate or guess. Prefer an explicit "insufficient information" over any uncertain claim.
- All conclusions must cite specific text from the provided input.

Output format — use exactly these headers, in this order, every time:

**Root cause:** [one sentence grounded in the log. If unknown: "insufficient information".]
**Explanation:** [causal chain using only facts present in the log. If unknown: "insufficient information".]
**Suggested fix:** [concrete action derivable from the log. If insufficient context: "insufficient information".]\
"""

_USER_TEMPLATE = """\
Analyze this software failure:

=== LOG ===
{log}

TASK:
1. Identify root cause
2. Explain causal chain
3. Suggest fix

Important: Do NOT infer programming language, runtime, or framework from the error text. \
Only state language or context if it appears verbatim in the log above. \
If any section cannot be answered from the log alone, write "insufficient information".\
"""


_CONSTRAINT_TEMPLATE = """\
=== REASONING CONSTRAINTS (MUST FOLLOW) ===
{gemma_md}
=== END REASONING CONSTRAINTS ===

Apply ALL constraints above to every section of your response. \
Do not deviate from them regardless of what the log suggests.\
"""


def build_prompt(log: str, gemma_md: str | None = None) -> str:
    """Assemble the user-turn prompt for one debugging inference.

    When GEMMA.md is provided it is injected as an explicit constraint block
    with imperative framing, placed before the user task so the model treats
    it as binding rules rather than background text.
    """
    parts: list[str] = []

    if gemma_md:
        parts.append(_CONSTRAINT_TEMPLATE.format(gemma_md=gemma_md.strip()))

    parts.append(_USER_TEMPLATE.format(log=log.strip()))

    return "\n\n".join(parts)
