import sys
import time
import threading
import argparse

from explaind.main import run, MODEL


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
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"explaind: {args.file}: no such file", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print(f"explaind: {args.file}: permission denied", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print("explaind: no input provided", file=sys.stderr)
        print("usage: explaind [file]  |  cat file | explaind  |  explaind < file", file=sys.stderr)
        sys.exit(1)

    with _Spinner("thinking"):
        t0 = time.monotonic()
        result, usage = run(content, ability=args.ability)
        latency_ms = round((time.monotonic() - t0) * 1000)

    print(result)

    print(f"\n[model: {MODEL} · {latency_ms}ms]", file=sys.stderr)

    if usage:
        lines = ["[model usage]"]
        if "input_tokens" in usage:
            lines.append(f"  input tokens:  {usage['input_tokens']}")
        if "output_tokens" in usage:
            lines.append(f"  output tokens: {usage['output_tokens']}")
        if "total_tokens" in usage:
            lines.append(f"  total tokens:  {usage['total_tokens']}")
        if "context_window" in usage:
            used = usage.get("total_tokens", "?")
            ctx = usage["context_window"]
            pct = f"  {round(used / ctx * 100, 1)}%" if isinstance(used, int) else ""
            lines.append(f"  context usage: {used} / {ctx}{pct}")
        print("\n".join(lines), file=sys.stderr)
    else:
        print("  token usage: unavailable from runtime", file=sys.stderr)
