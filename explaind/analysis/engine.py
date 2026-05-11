from __future__ import annotations

from explaind.analysis.models import AnalysisReport, Analyzer, MetricResult
from explaind.analysis.analyzers.speculation import SpeculationAnalyzer
from explaind.analysis.analyzers.constraints import ConstraintAnalyzer
from explaind.analysis.analyzers.uncertainty import UncertaintyAnalyzer
from explaind.analysis.analyzers.structure import StructureAnalyzer


def _default_analyzers() -> list[Analyzer]:
    return [
        SpeculationAnalyzer(),
        ConstraintAnalyzer(),
        UncertaintyAnalyzer(),
        StructureAnalyzer(),
    ]


class AnalysisEngine:
    """Orchestrates all analyzers and returns a unified AnalysisReport.

    Pass a custom list of analyzers to extend or replace the default set
    without modifying this class.
    """

    def __init__(self, analyzers: list[Analyzer] | None = None) -> None:
        self._analyzers: list[Analyzer] = analyzers if analyzers is not None else _default_analyzers()

    def analyze(self, trace) -> AnalysisReport:
        """Run every registered analyzer against the trace and aggregate results."""
        per_results: dict[str, dict] = {}

        for analyzer in self._analyzers:
            result: MetricResult = analyzer.analyze(trace)
            per_results[result.analyzer] = result.metrics

        speculation = per_results.get("speculation", {})
        constraints = per_results.get("constraints", {})
        uncertainty = per_results.get("uncertainty", {})
        structure   = per_results.get("structure",   {})

        return AnalysisReport(
            speculation_score=speculation.get("speculation_score", 0.0),
            constraint_violations=constraints.get("constraint_violation_count", 0),
            insufficient_info_compliance=uncertainty.get("insufficient_info_compliance", 0.0),
            format_stability=structure.get("format_stability", False),
            per_analyzer_results=per_results,
        )
