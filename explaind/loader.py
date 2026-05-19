from __future__ import annotations

from pathlib import Path

from explaind.errors import InputError

_NO_INPUT_MSG = "No input provided"

_SCRATCHPAD_HEADER = """\
[ACTIVE WORKING MEMORY]
The following contains current hypotheses, partial reasoning,
and working notes. Treat this as your active thinking state.
Reason from it. Update your conclusions against it.
Do not ignore it in favour of general knowledge."""

_CONTEXT_HEADER = """\
[REFERENCE CONTEXT]
The following is background material, prior analysis, or
reference documentation relevant to this reasoning task.
Ground your reasoning in this material where applicable.
Where this material conflicts with general knowledge,
prefer this material — it is specific, the general knowledge
is not."""


def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise InputError(f"{path}: no such file")
    except PermissionError:
        raise InputError(f"{path}: permission denied")
    except OSError as exc:
        raise InputError(f"{path}: {exc.strerror.lower()}")


def load_scratchpad(path: Path) -> str:
    """Load a scratchpad file and prepend the active working memory header."""
    raw = _read_file(path)
    content = raw.strip()
    if not content:
        raise InputError(f"{path}: scratchpad file is empty")
    return f"{_SCRATCHPAD_HEADER}\n\n{content}"


def load_context(path: Path) -> str:
    """Load a context file and prepend the reference context header."""
    raw = _read_file(path)
    content = raw.strip()
    if not content:
        raise InputError(f"{path}: context file is empty")
    return f"{_CONTEXT_HEADER}\n\n{content}"


def load_input(
    file_path: str | None = None,
    stdin_text: str | None = None,
) -> str:
    """Return validated, normalized input content.

    file_path takes precedence over stdin_text when both are provided.
    Raises InputError for every invalid state — never silently falls back.
    """
    if file_path is not None:
        try:
            raw = Path(file_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise InputError(f"{file_path}: no such file")
        except PermissionError:
            raise InputError(f"{file_path}: permission denied")
        except OSError as exc:
            raise InputError(f"{file_path}: {exc.strerror.lower()}")
    elif stdin_text is not None:
        raw = stdin_text
    else:
        raise InputError(_NO_INPUT_MSG)

    content = raw.strip()
    if not content:
        raise InputError(_NO_INPUT_MSG)

    return content
