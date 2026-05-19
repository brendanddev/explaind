from __future__ import annotations

from pathlib import Path

GEMMA_MD_PATH = Path("GEMMA.md")


def load_gemma_md(path: Path = GEMMA_MD_PATH) -> str | None:
    """Load GEMMA.md from the current working directory.

    Returns raw file contents, or None if the file is absent.
    Never raises — missing GEMMA.md is a valid, expected state.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
