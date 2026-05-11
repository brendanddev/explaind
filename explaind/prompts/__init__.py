from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert software debugging system.

Rules:
- Only use information explicitly present in the provided log, diff, or context.
- Do NOT assume programming language, framework, or runtime unless the log states it verbatim.
- Do NOT infer language or runtime from error message wording alone.
- Do NOT hallucinate missing information: no invented stack traces, variable names, code, or behavior.
- If a field cannot be determined from the log, use the string "insufficient information" as its value.
- Never speculate or guess. Prefer "insufficient information" over any uncertain claim.
- All conclusions must cite specific text from the provided input.

Output format:
You MUST respond with ONLY a valid JSON object. No prose, no markdown, no text outside the JSON.
The object must contain exactly these fields:

{
  "failure_type": "short label for the error class",
  "root_cause": "one sentence grounded in the log",
  "evidence": ["direct quotes or references from the log"],
  "causal_chain": "step-by-step causal sequence derived from the log",
  "suggested_fix": "concrete action derivable from the log"
}

Use "insufficient information" for any string field you cannot determine.
Use [] for evidence if no specific text can be cited.\
"""

_USER_TEMPLATE = """\
Analyze this software failure:

=== LOG ===
{log}

RESPONSE FORMAT — STRICTLY ENFORCED:
- Return ONLY a valid JSON object.
- No markdown, no prose, no explanation outside the JSON.
- Do NOT infer language, runtime, or framework unless stated verbatim in the log.
- Use "insufficient information" for any field you cannot determine from the log alone.\
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
