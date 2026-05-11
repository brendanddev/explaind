from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

import ollama

from explaind.analysis import AnalysisEngine
from explaind.gemma import load_gemma_md
from explaind.output import FAILURE_OBJECT, parse_and_validate
from explaind.prompts import SYSTEM_PROMPT, build_prompt
from explaind.traces.models import TraceSession
from explaind.traces.logger import save_session

_engine = AnalysisEngine()

MODEL = "gemma4-e2b_q4_k_m:latest"

# Phrases that indicate the model is speculating beyond provided evidence.
_SPECULATIVE_PHRASES = frozenset([
    "likely", "probably", "might be", "could be", "perhaps",
    "possibly", "presumably", "it seems", "appears to be",
    "typically", "usually", "often", "generally", "may be",
    "may indicate", "often indicates",
])

# Language/runtime names the model should not introduce unless present in input.
_LANGUAGE_MARKERS = frozenset([
    "javascript", "typescript", "java", "python", "ruby", "golang",
    "rust", "c++", "c#", ".net", "php", "swift", "kotlin",
    "node.js", "nodejs", "react", "angular", "django",
    "flask", "spring", "rails",
])


def check_constraint_violation(result: dict, input_text: str) -> bool:
    """Return True if the validated output shows signs of violating grounding constraints.

    Checks string values in the result dict for speculative language and
    language/runtime names that were not present in the input.
    Never raises — violation detection must not crash the CLI.
    """
    text = " ".join(
        v if isinstance(v, str) else " ".join(v)
        for v in result.values()
        if isinstance(v, (str, list))
    ).lower()
    inp = input_text.lower()

    if any(phrase in text for phrase in _SPECULATIVE_PHRASES):
        return True

    if any(lang in text and lang not in inp for lang in _LANGUAGE_MARKERS):
        return True

    return False


def run_model(user_prompt: str) -> str:
    """Send a fully assembled prompt to the model and return its raw response."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0},
    )
    return response["message"]["content"]


def run(input_text: str) -> dict:
    """Run one full inference cycle and persist a trace session artifact.

    Returns a validated dict conforming to the output schema, or the canonical
    FAILURE_OBJECT if validation fails after one retry.
    """
    gemma_md = load_gemma_md()
    user_prompt = build_prompt(input_text, gemma_md=gemma_md)

    start = time.monotonic()

    raw = run_model(user_prompt)
    result = parse_and_validate(raw)

    retry_triggered = False
    if result is None:
        retry_triggered = True
        raw = run_model(user_prompt)
        result = parse_and_validate(raw)

    if result is None:
        result = FAILURE_OBJECT

    latency_ms = round((time.monotonic() - start) * 1000, 2)
    violation = check_constraint_violation(result, input_text)

    session = TraceSession(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_content=input_text,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        gemma_context=gemma_md,
        model_name=MODEL,
        final_output=json.dumps(result),
        latency_ms=latency_ms,
        metadata={
            "constraint_violation_detected": violation,
            "retry_triggered": retry_triggered,
            "schema_valid": result is not FAILURE_OBJECT,
        },
    )

    try:
        session.analysis_report = _engine.analyze(session).to_dict()
        save_session(session)
    except Exception:
        pass

    return result
