from __future__ import annotations

from explaind.analysis.models import Analyzer, MetricResult
from explaind.output import parse_and_validate

_FORMAT_VIOLATION_TYPE = "format_violation"


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
