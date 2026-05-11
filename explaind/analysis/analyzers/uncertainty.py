from __future__ import annotations

import json

from explaind.analysis.models import Analyzer, MetricResult

_SENTINEL = "insufficient information"
_STRING_FIELDS = ("failure_type", "root_cause", "causal_chain", "suggested_fix")


class UncertaintyAnalyzer(Analyzer):
    name = "uncertainty"

    def analyze(self, trace) -> MetricResult:
        try:
            data = json.loads(trace.final_output)
        except (json.JSONDecodeError, ValueError):
            return MetricResult(
                analyzer=self.name,
                metrics={"insufficient_info_compliance": 0.0, "fields_with_sentinel": 0, "total_fields": len(_STRING_FIELDS)},
            )

        matches = sum(
            1 for f in _STRING_FIELDS
            if _SENTINEL in str(data.get(f, "")).lower()
        )
        compliance = round(matches / len(_STRING_FIELDS), 4)
        return MetricResult(
            analyzer=self.name,
            metrics={
                "insufficient_info_compliance": compliance,
                "fields_with_sentinel": matches,
                "total_fields": len(_STRING_FIELDS),
            },
        )
