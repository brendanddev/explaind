from __future__ import annotations

_TYPE_ERROR_KEYWORDS: frozenset[str] = frozenset([
    "typeerror", "type error", "invalid type", "type mismatch",
    "wrong type", "not callable", "attributeerror",
    "expected string", "expected int", "expected list",
    "cannot read property",
])

_NULL_KEYWORDS: frozenset[str] = frozenset([
    "nullpointerexception", "null pointer", "null reference",
    "is null", "nonetype", "none type",
    "undefined variable", "referenceerror",
])

_JSON_ERROR_KEYWORDS: frozenset[str] = frozenset([
    "jsondecodeerror", "json.decoder", "invalid json",
    "json parse", "malformed json", "unexpected token",
    "json format error",
])


def _flatten(output: dict) -> str:
    """Flatten all string content from output dict into one lowercase string."""
    parts: list[str] = []
    for v in output.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(i) for i in v)
    return " ".join(parts).lower()


def tag_failure_patterns(final_output: dict, analysis_metadata: dict) -> list[str]:
    """Classify recurring failure patterns from a model output and its analysis signals.

    final_output     — parsed dict from trace.final_output
    analysis_metadata — pre-computed signals: speculation_score, uncertainty_usage_rate,
                        constraint_violation_flags, structure_report

    Returns a deterministic list of tag strings. Empty list = no patterns detected.
    """
    tags: list[str] = []

    text = _flatten(final_output)

    violation_flags: list[str] = analysis_metadata.get("constraint_violation_flags", [])
    structure_report: dict = analysis_metadata.get("structure_report", {})
    speculation_score: float = analysis_metadata.get("speculation_score", 0.0)
    uncertainty_rate: float = analysis_metadata.get("uncertainty_usage_rate", 0.0)
    evidence: list = final_output.get("evidence", [])

    # TYPE_ERROR_HANDLING
    # Fires on type-error keywords in output text OR when structure analysis
    # found fields with the wrong value type.
    if any(kw in text for kw in _TYPE_ERROR_KEYWORDS) or bool(structure_report.get("type_errors")):
        tags.append("TYPE_ERROR_HANDLING")

    # NULL_OR_UNDEFINED_HANDLING
    # Fires on null/undefined keywords in output text OR when required fields
    # were absent from the model output.
    if any(kw in text for kw in _NULL_KEYWORDS) or bool(structure_report.get("missing_fields")):
        tags.append("NULL_OR_UNDEFINED_HANDLING")

    # JSON_PARSING_FAILURE
    # Fires when violation flags indicate the model's output itself was not
    # valid JSON, OR when JSON-error keywords appear in the analyzed content.
    if (
        "FAILURE_OBJECT_FALLBACK" in violation_flags
        or "INVALID_JSON_STRUCTURE" in violation_flags
        or any(kw in text for kw in _JSON_ERROR_KEYWORDS)
    ):
        tags.append("JSON_PARSING_FAILURE")

    # INSUFFICIENT_CONTEXT_RESPONSE
    # Fires when the model explicitly used uncertainty markers (scored by
    # Slice 3.1), OR when evidence is empty alongside an "insufficient" signal.
    if uncertainty_rate > 0.0 or (not evidence and "insufficient" in text):
        tags.append("INSUFFICIENT_CONTEXT_RESPONSE")

    # OVERCONFIDENT_SPECULATION
    # Fires when the model used speculative language without citing any evidence,
    # OR when strong speculation appeared without any uncertainty acknowledgment.
    if (speculation_score > 0.0 and not evidence) or (
        speculation_score >= 0.25 and uncertainty_rate == 0.0
    ):
        tags.append("OVERCONFIDENT_SPECULATION")

    return tags
