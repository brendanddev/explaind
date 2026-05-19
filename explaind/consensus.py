from __future__ import annotations

import time
from typing import Callable

from explaind.invoker import ModelInvoker


def _jaccard(a: str, b: str) -> float:
    set_a = set(a.lower().split())
    set_b = set(b.lower().split())
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _compute_agreement(outputs: list[str]) -> list[int]:
    scores = []
    for i, a in enumerate(outputs):
        score = sum(
            1 for j, b in enumerate(outputs) if j != i and _jaccard(a, b) > 0.6
        )
        scores.append(score)
    return scores


def run_consensus(
    invoker: ModelInvoker,
    prompt: str,
    n: int,
    on_run_start: Callable[[int, int], None] | None = None,
) -> tuple[str, dict]:
    outputs: list[str] = []
    times_ms: list[int] = []

    for i in range(n):
        if on_run_start is not None:
            on_run_start(i + 1, n)
        t0 = time.monotonic()
        output = invoker.invoke(prompt)
        ms = round((time.monotonic() - t0) * 1000)
        outputs.append(output)
        times_ms.append(ms)

    scores = _compute_agreement(outputs)
    max_score = max(scores)
    candidates = [i for i, s in enumerate(scores) if s == max_score]
    best_idx = max(candidates, key=lambda i: len(outputs[i]))
    best_output = outputs[best_idx]

    agreement = scores[best_idx]
    agreement_pct = agreement / n * 100

    if agreement_pct >= 80:
        confidence = "HIGH"
    elif agreement_pct >= 60:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    total_ms = sum(times_ms)
    divergent_runs = n - agreement

    report = {
        "n": n,
        "agreement": agreement,
        "agreement_pct": agreement_pct,
        "confidence": confidence,
        "divergent_runs": divergent_runs,
        "times_ms": times_ms,
        "total_ms": total_ms,
    }

    return best_output, report


def format_consensus_report(report: dict) -> str:
    n = report["n"]
    agreement = report["agreement"]
    pct = report["agreement_pct"]
    confidence = report["confidence"]
    divergent_runs = report["divergent_runs"]
    total_ms = report["total_ms"]
    avg = round(total_ms / n) if n else 0

    return (
        f"Consensus: {agreement}/{n} runs agree  ({pct:.0f}%)\n"
        f"Confidence: {confidence}\n"
        f"Divergent: {divergent_runs} run(s) took different paths\n"
        f"Time: {total_ms}ms total ({avg}ms avg per run)"
    )
