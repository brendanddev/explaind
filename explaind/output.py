from __future__ import annotations

import json

# Fields required in every valid model response, mapped to their expected types.
_SCHEMA: dict[str, type] = {
    "failure_type": str,
    "root_cause": str,
    "evidence": list,
    "causal_chain": str,
    "suggested_fix": str,
}

# Canonical failure object returned when output cannot be validated after retry.
FAILURE_OBJECT: dict = {
    "failure_type": "format_violation",
    "root_cause": "model_output_did_not_match_json_schema",
    "evidence": [],
    "causal_chain": "output failed schema validation step",
    "suggested_fix": "tighten prompt constraints or add retry regeneration",
}


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that models add despite being told not to."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()
    return text


def parse_and_validate(raw: str) -> dict | None:
    """Parse raw model output as JSON and validate it against the required schema.

    Returns the validated dict on success, None on any parse or schema failure.
    Never raises.
    """
    try:
        data = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    for key, expected_type in _SCHEMA.items():
        if key not in data:
            return None
        if not isinstance(data[key], expected_type):
            return None

    return data
