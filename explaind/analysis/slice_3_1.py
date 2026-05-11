from __future__ import annotations

SPECULATION_WORDS: list[str] = [
    "likely", "probably", "might", "could be", "seems",
    "appears", "possibly", "suggests",
]

UNCERTAINTY_MARKERS: list[str] = [
    "insufficient information",
    "cannot determine",
    "not enough evidence",
]


def compute_speculation_score(text: str) -> float:
    """Return the fraction of SPECULATION_WORDS present in text (0.0–1.0).

    Each word counts once regardless of repetition. Score is deterministic
    and purely lexical — no model calls, no external dependencies.
    """
    lowered = text.lower()
    matched = sum(1 for w in SPECULATION_WORDS if w in lowered)
    return round(matched / len(SPECULATION_WORDS), 4)


def compute_uncertainty_rate(text: str) -> float:
    """Return the fraction of UNCERTAINTY_MARKERS present in text (0.0–1.0).

    A high rate means the model correctly signalled ignorance rather than
    guessing. Each marker counts once regardless of repetition.
    """
    lowered = text.lower()
    matched = sum(1 for m in UNCERTAINTY_MARKERS if m in lowered)
    return round(matched / len(UNCERTAINTY_MARKERS), 4)
