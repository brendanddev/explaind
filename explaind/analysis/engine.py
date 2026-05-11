from __future__ import annotations

import json

from explaind.analysis.models import BehaviorReport, Analyzer, MetricResult
from explaind.analysis.analyzers.speculation import SpeculationAnalyzer
from explaind.analysis.analyzers.constraints import ConstraintAnalyzer
from explaind.analysis.analyzers.uncertainty import UncertaintyAnalyzer
from explaind.analysis.analyzers.structure import StructureAnalyzer, analyze_structure
from explaind.analysis.scoring import compute_speculation_score, compute_uncertainty_rate
from explaind.analysis.violations import analyze_constraint_violations
from explaind.analysis.failure_tags import tag_failure_patterns


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

        try:
            output_dict = json.loads(trace.final_output)
        except (json.JSONDecodeError, ValueError):
            output_dict = {}

        output_text = _output_to_text(trace.final_output)
        speculation_score = compute_speculation_score(output_text)
        uncertainty_rate = compute_uncertainty_rate(output_text)
        violation_flags = analyze_constraint_violations(trace.final_output)
        structure_report = analyze_structure(output_dict)

        analysis_metadata = {
            "speculation_score": speculation_score,
            "uncertainty_usage_rate": uncertainty_rate,
            "constraint_violation_flags": violation_flags,
            "structure_report": structure_report,
        }

        return BehaviorReport(
            speculation_score=speculation_score,
            uncertainty_usage_rate=uncertainty_rate,
            constraint_violation_flags=violation_flags,
            structure_validity=structure_report["structure_validity"],
            failure_pattern_tags=tag_failure_patterns(output_dict, analysis_metadata),
        )
