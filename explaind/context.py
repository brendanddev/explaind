from __future__ import annotations

_CONTEXT_TEMPLATE = """\
[CONTEXT WINDOW LAYERS]

[SCRATCHPAD]
{scratchpad}

[REASONING TRACE]
{trace}

[COMPETING INTERPRETATIONS]
{interpretations}

[CONTEXT INSTRUCTION]
Treat all above as persistent working memory within this single inference.
Resolve conflicts using ABILITY + BIAS FIELD priority.\
"""


def build_context_window_block(
    trace: str | None = None,
    scratchpad: str | None = None,
    interpretations: str | None = None,
) -> str:
    """Return a deterministic CONTEXT WINDOW LAYERS block.

    Pure function. No I/O, no global state.
    Absent fields render as the literal string 'none'.
    """
    return _CONTEXT_TEMPLATE.format(
        scratchpad=scratchpad.strip() if scratchpad else "none",
        trace=trace.strip() if trace else "none",
        interpretations=interpretations.strip() if interpretations else "none",
    )
