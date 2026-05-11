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
class BehaviorReport:
    """Slice 3.0 — structured summary of one inference trace.

    Fields not yet implemented carry their default values and are populated
    by later slices (3.1+). Do not add logic here — extend via analyzers.
    """

    speculation_score: float
    uncertainty_usage_rate: float
    constraint_violation_flags: list
    structure_validity: bool
    failure_pattern_tags: list = field(default_factory=list)  # Slice 3.1+

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class Analyzer(ABC):
    """Interface every analyzer must implement."""

    name: str = ""

    @abstractmethod
    def analyze(self, trace) -> MetricResult:
        ...
