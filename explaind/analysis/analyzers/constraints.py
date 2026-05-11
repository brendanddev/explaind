from __future__ import annotations

from explaind.analysis.models import Analyzer, MetricResult


class ConstraintAnalyzer(Analyzer):
    name = "constraints"

    def analyze(self, trace) -> MetricResult:
        meta = trace.metadata or {}
        violation = bool(meta.get("constraint_violation_detected", False))
        schema_valid = bool(meta.get("schema_valid", True))
        retry = bool(meta.get("retry_triggered", False))
        count = int(violation) + int(not schema_valid)
        return MetricResult(
            analyzer=self.name,
            metrics={
                "constraint_violation_count": count,
                "constraint_violation_detected": violation,
                "schema_valid": schema_valid,
                "retry_triggered": retry,
            },
        )
