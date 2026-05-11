from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import ollama

from explaind.prompts import SYSTEM_PROMPT, build_prompt
from explaind.traces.models import TraceSession
from explaind.traces.logger import save_session

MODEL = "gemma4-e2b_q4_k_m:latest"


def run_model(user_prompt: str) -> str:
    """Send a fully assembled prompt to the model and return its response."""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"]


def run(input_text: str, gemma_md: str | None = None) -> str:
    """Run one full inference cycle and persist a trace session artifact."""
    user_prompt = build_prompt(input_text, gemma_md=gemma_md)

    start = time.monotonic()
    output = run_model(user_prompt)
    latency_ms = round((time.monotonic() - start) * 1000, 2)

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
    )

    try:
        save_session(session)
    except Exception:
        pass

    return output
