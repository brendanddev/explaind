import sys
import time
import threading
import argparse

from pathlib import Path

from explaind.color import print_compare_header, print_error, print_model_meta, print_model_output, print_run_header
from explaind.config import DEFAULTS, load_config
from explaind.errors import ConfigError, InputError, ModelInvocationError
from explaind.invoker import build_invoker
from explaind.loader import load_context, load_input, load_scratchpad
from explaind.main import run
from explaind.trace import TraceData, format_trace


class _Spinner:
    _MESSAGES = [
        (0, "thinking..."),
        (30, "still thinking..."),
        (60, "taking a moment..."),
        (90, "almost there..."),
    ]

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._active = sys.stdout.isatty()

    def _run(self) -> None:
        from rich.console import Console
        from rich.status import Status

        console = Console(stderr=True, highlight=False)
        start = time.monotonic()
        msg_idx = 0

        with Status(self._MESSAGES[0][1], console=console) as status:
            while not self._stop.is_set():
                elapsed = time.monotonic() - start
                new_idx = 0
                for i, (threshold, _) in enumerate(self._MESSAGES):
                    if elapsed >= threshold:
                        new_idx = i
                if new_idx != msg_idx:
                    msg_idx = new_idx
                    status.update(self._MESSAGES[msg_idx][1])
                self._stop.wait(0.5)

    def __enter__(self):
        if self._active:
            self._thread.start()
        return self

    def __exit__(self, *_):
        if self._active:
            self._stop.set()
            self._thread.join()


def _emit_trace(prompt_trace, config, file=sys.stderr) -> None:
    td = TraceData(
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        prompt=prompt_trace,
    )
    print(format_trace(td), file=file)


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
    parser.add_argument(
        "--trace",
        action="store_true",
        help="print prompt-construction trace to stderr (does not affect stdout)",
    )
    parser.add_argument(
        "--compare",
        nargs="+",
        metavar="NAME",
        help="run 2+ abilities on the same input and print results side by side",
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help="enables Gemma 4 native thinking mode for deeper chain-of-thought reasoning",
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        dest="file_flag",
        help="path to input file (alternative to positional file argument)",
    )
    parser.add_argument(
        "--scratchpad",
        metavar="FILE",
        help="path to a markdown file containing active working notes or hypotheses",
    )
    parser.add_argument(
        "--context",
        metavar="FILE",
        help="path to a markdown file containing background material or prior outputs",
    )
    args = parser.parse_args()

    # --compare and --ability are mutually exclusive
    if args.compare and args.ability:
        print_error("explaind: --compare and --ability are mutually exclusive")
        sys.exit(1)

    # --compare requires at least 2 abilities; for a single ability use --ability
    if args.compare and len(args.compare) < 2:
        print_error("explaind: --compare requires at least 2 ability names")
        sys.exit(1)

    # --- input ---
    file_arg = args.file_flag if args.file_flag is not None else args.file
    stdin_text = None if (file_arg is not None or sys.stdin.isatty()) else sys.stdin.read()

    try:
        content = load_input(file_path=file_arg, stdin_text=stdin_text)
    except InputError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)

    # --- optional context injection ---
    scratchpad_content: str | None = None
    context_content: str | None = None

    if args.scratchpad:
        try:
            scratchpad_content = load_scratchpad(Path(args.scratchpad))
        except InputError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

    if args.context:
        try:
            context_content = load_context(Path(args.context))
        except InputError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

    # --- compare: run each ability in sequence, print with headers ---
    if args.compare:
        if args.dry_run:
            try:
                cfg = load_config()
            except ConfigError:
                cfg = DEFAULTS
            for ability in args.compare:
                try:
                    result, prompt_trace = run(
                        content,
                        ability=ability,
                        dry_run=True,
                        trace=args.trace,
                        think=args.think,
                        scratchpad=scratchpad_content,
                        context=context_content,
                    )
                except ValueError as e:
                    print_error(f"explaind: {e}")
                    sys.exit(1)
                print_compare_header(ability)
                print()
                print(result)
                print()
                if args.trace and prompt_trace is not None:
                    _emit_trace(prompt_trace, cfg)
            return

        try:
            config = load_config()
        except ConfigError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        try:
            invoker = build_invoker(config)
        except ConfigError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        for ability in args.compare:
            try:
                with _Spinner():
                    t0 = time.monotonic()
                    result, prompt_trace = run(
                        content,
                        ability=ability,
                        invoker=invoker,
                        trace=args.trace,
                        think=args.think,
                        scratchpad=scratchpad_content,
                        context=context_content,
                    )
                    latency_ms = round((time.monotonic() - t0) * 1000)
            except ValueError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)
            except ModelInvocationError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)

            print_run_header(ability, args.think)
            print_model_output(result)
            print_model_meta(config.model_name, latency_ms, ability=ability)

            if args.trace and prompt_trace is not None:
                _emit_trace(prompt_trace, config)

        return

    # --- dry-run: assemble only, no model invocation ---
    if args.dry_run:
        try:
            result, prompt_trace = run(
                content,
                ability=args.ability,
                dry_run=True,
                trace=args.trace,
                think=args.think,
                scratchpad=scratchpad_content,
                context=context_content,
            )
        except ValueError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)
        print(result)
        if args.trace and prompt_trace is not None:
            try:
                cfg = load_config()
            except ConfigError:
                cfg = DEFAULTS
            _emit_trace(prompt_trace, cfg)
        return

    # --- config + backend selection ---
    try:
        config = load_config()
    except ConfigError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)

    try:
        invoker = build_invoker(config)
    except ConfigError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)

    # --- invoke ---
    try:
        with _Spinner():
            t0 = time.monotonic()
            result, prompt_trace = run(
                content,
                ability=args.ability,
                invoker=invoker,
                trace=args.trace,
                think=args.think,
                scratchpad=scratchpad_content,
                context=context_content,
            )
            latency_ms = round((time.monotonic() - t0) * 1000)
    except ValueError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)
    except ModelInvocationError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)

    print_run_header(args.ability or "balanced", args.think)
    print_model_output(result)
    print_model_meta(config.model_name, latency_ms, ability=args.ability or "balanced")

    if args.trace and prompt_trace is not None:
        _emit_trace(prompt_trace, config)


if __name__ == "__main__":
    main()
