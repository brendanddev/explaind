from __future__ import annotations

from pathlib import Path

from explaind.errors import InputError

_NO_INPUT_MSG = "No input provided"


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
