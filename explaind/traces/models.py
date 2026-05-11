from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TraceSession:
    """A single inference artifact capturing all reasoning data for one run.

    Fields are intentionally model-agnostic so traces stay useful if the
    underlying model or provider changes.
    """

    id: str
    timestamp: str
    input_content: str
    system_prompt: str
    user_prompt: str
    model_name: str
    final_output: str
    latency_ms: float
    gemma_context: Optional[str] = None
    thinking_trace: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    analysis_report: Optional[dict] = None
