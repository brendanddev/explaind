from __future__ import annotations

import json

from explaind.analysis.models import Analyzer, MetricResult

_PHRASES = frozenset([
    "likely", "probably", "might be", "could be", "perhaps",
    "possibly", "presumably", "it seems", "appears to be",
    "typically", "usually", "often", "generally", "may be",
    "may indicate", "often indicates",
])


def _output_text(final_output: str) -> str:
    """Flatten all string content from the JSON output into one searchable string."""
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


class SpeculationAnalyzer(Analyzer):
    name = "speculation"

    def analyze(self, trace) -> MetricResult:
        text = _output_text(trace.final_output).lower()
        matched = sorted(p for p in _PHRASES if p in text)
        score = round(len(matched) / len(_PHRASES), 4)
        return MetricResult(
            analyzer=self.name,
            metrics={
                "speculation_score": score,
                "matched_phrases": matched,
            },
        )
