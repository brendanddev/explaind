from __future__ import annotations

from explaind.analysis.models import Analyzer, MetricResult
from explaind.output import parse_and_validate

_FORMAT_VIOLATION_TYPE = "format_violation"

_REQUIRED_FIELDS: tuple[str, ...] = (
    "failure_type", "root_cause", "evidence", "causal_chain", "suggested_fix",
)

# Each field gets one presence check + one type check.
_TOTAL_CHECKS: int = len(_REQUIRED_FIELDS) * 2


def analyze_structure(output: dict) -> dict:
    """Validate the structural integrity of a model output dict.

    Returns a result dict with:
      structure_validity  — float 0.0–1.0 (1.0 = fully valid)
      missing_fields      — fields absent from output
      type_errors         — fields present but with wrong or empty value
      is_valid            — True only when both lists are empty
    """
    missing_fields: list[str] = []
    type_errors: list[str] = []
    errors = 0

    for field in _REQUIRED_FIELDS:
        if field not in output:
            missing_fields.append(field)
            errors += 2  # fails both presence and type check
            continue

        val = output[field]

        if field == "evidence":
            if not isinstance(val, list):
                type_errors.append(field)
                errors += 1
        else:
            if val is None or not isinstance(val, str) or not val.strip():
                type_errors.append(field)
                errors += 1

    validity = round(max(0.0, min(1.0, 1.0 - errors / _TOTAL_CHECKS)), 4)

    return {
        "structure_validity": validity,
        "missing_fields": missing_fields,
        "type_errors": type_errors,
        "is_valid": not missing_fields and not type_errors,
    }


class StructureAnalyzer(Analyzer):
    name = "structure"

    def analyze(self, trace) -> MetricResult:
        validated = parse_and_validate(trace.final_output)
        is_stable = validated is not None
        is_failure_object = is_stable and validated.get("failure_type") == _FORMAT_VIOLATION_TYPE
        return MetricResult(
            analyzer=self.name,
            metrics={
                "format_stability": is_stable,
                "is_failure_object": is_failure_object,
                "schema_fields_present": list(validated.keys()) if validated else [],
            },
        )
