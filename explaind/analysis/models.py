from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MetricResult:
    """Output of a single analyzer run."""

    analyzer: str
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class AnalysisReport:
    """Aggregated output of all analyzers for one trace."""

    speculation_score: float
    constraint_violations: int
    insufficient_info_compliance: float
    format_stability: bool
    per_analyzer_results: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class Analyzer(ABC):
    """Interface every analyzer must implement."""

    name: str = ""

    @abstractmethod
    def analyze(self, trace) -> MetricResult:
        ...
