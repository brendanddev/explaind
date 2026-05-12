import sys
import time
import threading
import argparse

from explaind.config import load_config
from explaind.errors import ConfigError, InputError, ModelInvocationError
from explaind.invoker import build_invoker
from explaind.loader import load_input
from explaind.main import run


_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
_INTERVAL = 0.1


class _Spinner:
    def __init__(self, message: str = "thinking") -> None:
        self._message = message
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._active = sys.stderr.isatty()

    def _spin(self) -> None:
        i = 0
        while not self._stop.is_set():
            frame = _FRAMES[i % len(_FRAMES)]
            print(f"\r{frame} {self._message}...", end="", file=sys.stderr, flush=True)
            i += 1
            self._stop.wait(_INTERVAL)

    def __enter__(self):
        if self._active:
            self._thread.start()
        return self

    def __exit__(self, *_):
        if self._active:
            self._stop.set()
            self._thread.join()
            width = len(self._message) + 10
            print(f"\r{' ' * width}\r", end="", file=sys.stderr, flush=True)


def main():
    parser = argparse.ArgumentParser(
        prog="explaind",
        description="Debugging assistant powered by Gemma 4",
        usage="%(prog)s [file]\n       cat file | %(prog)s\n       %(prog)s < file",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="path to log file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--ability",
        metavar="NAME",
        help="load abilities/<name>.md and inject into prompt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print assembled prompt to stdout without calling the model",
    )
    args = parser.parse_args()

    # --- input ---
    stdin_text = None if (args.file is not None or sys.stdin.isatty()) else sys.stdin.read()

    try:
        content = load_input(file_path=args.file, stdin_text=stdin_text)
    except InputError as e:
        print(f"explaind: {e}", file=sys.stderr)
        sys.exit(1)

    # --- dry-run: assemble only, no config or model needed ---
    if args.dry_run:
        try:
            result, _ = run(content, ability=args.ability, dry_run=True)
        except ValueError as e:
            print(f"explaind: {e}", file=sys.stderr)
            sys.exit(1)
        print(result)
        return

    # --- config + backend selection ---
    try:
        config = load_config()
    except ConfigError as e:
        print(f"explaind: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        invoker = build_invoker(config)
    except ConfigError as e:
        print(f"explaind: {e}", file=sys.stderr)
        sys.exit(1)

    # --- invoke ---
    try:
        with _Spinner("thinking"):
            t0 = time.monotonic()
            result, _ = run(content, ability=args.ability, invoker=invoker)
            latency_ms = round((time.monotonic() - t0) * 1000)
    except ValueError as e:
        print(f"explaind: {e}", file=sys.stderr)
        sys.exit(1)
    except ModelInvocationError as e:
        print(f"explaind: {e}", file=sys.stderr)
        sys.exit(1)

    print(result)
    print(f"\n[model: {config.model_name} · {latency_ms}ms]", file=sys.stderr)
