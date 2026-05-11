from __future__ import annotations

import json

from explaind.analysis.models import BehaviorReport, Analyzer, MetricResult
from explaind.analysis.analyzers.speculation import SpeculationAnalyzer
from explaind.analysis.analyzers.constraints import ConstraintAnalyzer
from explaind.analysis.analyzers.uncertainty import UncertaintyAnalyzer
from explaind.analysis.analyzers.structure import StructureAnalyzer
from explaind.analysis.slice_3_1 import compute_speculation_score, compute_uncertainty_rate


def _default_analyzers() -> list[Analyzer]:
    return [
        SpeculationAnalyzer(),
        ConstraintAnalyzer(),
        UncertaintyAnalyzer(),
        StructureAnalyzer(),
    ]


def _output_to_text(final_output: str) -> str:
    """Flatten all string values from final_output JSON into one searchable string."""
    try:
        data = json.loads(final_output)
    except (json.JSONDecodeError, ValueError):
        return final_output
    parts: list[str] = []
    for v in data.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            parts.extend(str(i) for i in v)
    return " ".join(parts)


def _build_violation_flags(constraints: dict) -> list[str]:
    """Derive human-readable violation flags from ConstraintAnalyzer metrics."""
    flags = []
    if constraints.get("constraint_violation_detected"):
        flags.append("constraint_violation_detected")
    if not constraints.get("schema_valid", True):
        flags.append("schema_invalid")
    if constraints.get("retry_triggered"):
        flags.append("retry_triggered")
    return flags


class AnalysisEngine:
    """Orchestrates all analyzers and returns a BehaviorReport.

    Pass a custom list of analyzers to extend or replace the default set
    without modifying this class.
    """

    def __init__(self, analyzers: list[Analyzer] | None = None) -> None:
        self._analyzers: list[Analyzer] = analyzers if analyzers is not None else _default_analyzers()

    def analyze(self, trace) -> BehaviorReport:
        """Run every registered analyzer against the trace and return a BehaviorReport."""
        per_results: dict[str, dict] = {}

        for analyzer in self._analyzers:
            result: MetricResult = analyzer.analyze(trace)
            per_results[result.analyzer] = result.metrics

        constraints = per_results.get("constraints", {})
        structure   = per_results.get("structure",   {})

        output_text = _output_to_text(trace.final_output)

        return BehaviorReport(
            speculation_score=compute_speculation_score(output_text),
            uncertainty_usage_rate=compute_uncertainty_rate(output_text),
            constraint_violation_flags=_build_violation_flags(constraints),
            structure_validity=structure.get("format_stability", False),
            failure_pattern_tags=[],  # Slice 3.2+
        )
