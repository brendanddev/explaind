from __future__ import annotations

import json

REQUIRED_KEYS: frozenset[str] = frozenset([
    "failure_type", "root_cause", "evidence", "causal_chain", "suggested_fix",
])

_ALLOWED_KEYS = REQUIRED_KEYS

# The root_cause value that uniquely identifies the canonical FAILURE_OBJECT
# defined in explaind/output.py. Checked without importing to avoid coupling.
_FAILURE_OBJECT_ROOT_CAUSE = "model_output_did_not_match_json_schema"

# Placeholder strings not permitted in string fields (outside the allowed sentinel).
# "insufficient information" is the allowed sentinel and is excluded from this set.
_DISALLOWED_PLACEHOLDERS: frozenset[str] = frozenset([
    "unknown", "n/a", "none", "null", "undefined", "tbd", "todo", "placeholder",
])

_STRING_FIELDS: tuple[str, ...] = (
    "failure_type", "root_cause", "causal_chain", "suggested_fix",
)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end]).strip()
    return text


def analyze_constraint_violations(output: dict | str) -> list[str]:
    """Return a list of violation flags for a model output.

    Accepts a dict or raw JSON string. Returns an empty list when the output
    is fully compliant. Never raises — any parse failure becomes a flag.

    Flag vocabulary:
      INVALID_JSON_STRUCTURE   — unparseable JSON (useful when called with raw model text)
      MISSING_REQUIRED_KEYS    — one or more of the five required fields absent
      SCHEMA_DRIFT             — unexpected top-level keys outside required schema
      HALLUCINATED_FIELD       — same event as SCHEMA_DRIFT; distinct signal for reporting
      NON_COMPLIANT_VALUE      — empty string or disallowed placeholder in a string field
      FAILURE_OBJECT_FALLBACK  — output matches the canonical fallback sentinel object
    """
    flags: list[str] = []

    if isinstance(output, str):
        try:
            data = json.loads(_strip_fences(output))
        except (json.JSONDecodeError, ValueError):
            return ["INVALID_JSON_STRUCTURE"]
    else:
        data = output

    if not isinstance(data, dict):
        return ["INVALID_JSON_STRUCTURE"]

    present_keys = set(data.keys())

    # Missing required fields
    if not REQUIRED_KEYS.issubset(present_keys):
        flags.append("MISSING_REQUIRED_KEYS")

    # Unexpected top-level keys — two flags, one structural, one content
    extra_keys = present_keys - _ALLOWED_KEYS
    if extra_keys:
        flags.append("SCHEMA_DRIFT")
        flags.append("HALLUCINATED_FIELD")

    # Empty or disallowed placeholder values in string fields
    for field in _STRING_FIELDS:
        val = data.get(field)
        if isinstance(val, str):
            lowered = val.strip().lower()
            if not lowered or lowered in _DISALLOWED_PLACEHOLDERS:
                flags.append("NON_COMPLIANT_VALUE")
                break

    # Canonical fallback object — model failed to produce valid output
    if data.get("root_cause") == _FAILURE_OBJECT_ROOT_CAUSE:
        flags.append("FAILURE_OBJECT_FALLBACK")

    return flags
