from __future__ import annotations

import sys
import threading
from types import TracebackType


class Spinner:
    """Non-blocking CLI spinner that writes exclusively to stderr.

    stdout remains clean so piped JSON output is never corrupted.
    Suppresses itself silently when stderr is not a TTY (e.g. redirected).
    """

    _FRAMES = ("|", "/", "-", "\\")
    _INTERVAL = 0.1

    def __init__(self, message: str = "analyzing") -> None:
        self._message = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._active = sys.stderr.isatty()

    def _spin(self) -> None:
        i = 0
        while True:
            frame = self._FRAMES[i % len(self._FRAMES)]
            print(f"\r[{frame}] {self._message}...", end="", file=sys.stderr, flush=True)
            i += 1
            if self._stop.wait(self._INTERVAL):
                break

    def __enter__(self) -> Spinner:
        if self._active:
            self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._active:
            self._stop.set()
            self._thread.join()
            width = len(self._message) + 8
            print(f"\r{' ' * width}\r", end="", file=sys.stderr, flush=True)
