from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import ollama

from explaind.gemma import load_gemma_md
from explaind.prompts import SYSTEM_PROMPT, build_prompt
from explaind.traces.models import TraceSession
from explaind.traces.logger import save_session

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


def check_constraint_violation(output: str, input_text: str) -> bool:
    """Return True if output shows signs of violating grounding constraints.

    Checks for speculative language and language/runtime names that were not
    present in the input. Never raises — violation detection must not crash the CLI.
    """
    out = output.lower()
    inp = input_text.lower()

    if any(phrase in out for phrase in _SPECULATIVE_PHRASES):
        return True

    if any(lang in out and lang not in inp for lang in _LANGUAGE_MARKERS):
        return True

    return False


def run_model(user_prompt: str) -> str:
    """Send a fully assembled prompt to the model and return its response."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0},
    )
    return response["message"]["content"]


def run(input_text: str) -> str:
    """Run one full inference cycle and persist a trace session artifact."""
    gemma_md = load_gemma_md()
    user_prompt = build_prompt(input_text, gemma_md=gemma_md)

    start = time.monotonic()
    output = run_model(user_prompt)
    latency_ms = round((time.monotonic() - start) * 1000, 2)

    violation = check_constraint_violation(output, input_text)

    session = TraceSession(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        input_content=input_text,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        gemma_context=gemma_md,
        model_name=MODEL,
        final_output=output,
        latency_ms=latency_ms,
        metadata={"constraint_violation_detected": violation},
    )

    try:
        save_session(session)
    except Exception:
        pass

    return output
