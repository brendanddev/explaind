import sys
import time
import threading
import argparse

from datetime import datetime
from pathlib import Path

from explaind.color import print_about, print_chain_header, print_chain_meta, print_chain_separator, print_compare_header, print_consensus_progress, print_consensus_report, print_error, print_examples, print_export_confirmation, print_honest_header, print_honest_meta, print_honest_separator, print_list_abilities, print_model_meta, print_model_output, print_run_header, print_scaffold_status, print_scaffold_summary, print_warning
from explaind.consensus import run_consensus
from explaind.exporter import build_export
from explaind.scaffold import build_initial_scaffold, parse_scaffold_update, scaffold_to_export_summary, scaffold_to_injection
from explaind.config import DEFAULTS, load_config
from explaind.errors import ConfigError, InputError, ModelInvocationError
from explaind.invoker import build_invoker
from explaind.loader import load_context, load_input, load_scratchpad
from explaind.main import ALLOWED_ABILITIES, run
from explaind.presets import PRESET_MAP, load_preset, preset_description
from explaind.trace import TraceData, format_trace


_CHAIN_SCRATCHPAD_LIMIT = 8000


def _chain_handoff_header(prev_ability: str, next_ability: str) -> str:
    return (
        f"[REASONING HANDOFF: {prev_ability} → {next_ability}]\n"
        f"The following is output from the {prev_ability} reasoning pass.\n"
        f"Apply {next_ability} reasoning to this material.\n"
        f"Do not summarise the previous pass — transform it.\n"
        f"Your full ability specification applies to this handoff."
    )


_INITIAL_RESPONSE_HEADER = """\
[HONEST MODE — SKEPTICAL AUDIT]
The following is a FIRST PASS RESPONSE that requires
full skeptical interrogation.

AUDIT REQUIREMENTS:
1. Identify every claim in the initial response that
   is asserted without adequate evidential support
2. Name every assumption the initial response inherits
   without questioning
3. Find where the initial response converges to a
   comfortable conclusion prematurely
4. State explicitly where confidence in the initial
   response outruns the evidence it cites
5. Do NOT reproduce the initial response — interrogate it

INITIAL RESPONSE TO AUDIT:\
"""

_AUDIT_FOOTER = (
    "\n\nApply full skeptical specification to this audit.\n"
    "Do not summarise. Do not soften. Surface failures."
)


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


def _write_export(question: str, runs: list[dict], model: str, think: bool, path: str, scaffold_summary: str | None = None, consensus_report: dict | None = None) -> None:
    md = build_export(question, runs, model, think, scaffold_summary=scaffold_summary, consensus_report=consensus_report)
    try:
        Path(path).write_text(md, encoding="utf-8")
        print_export_confirmation(path)
    except OSError as e:
        print_warning(f"explaind: export failed: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="explaind",
        description=(
            "explaind — cognitive steering layer for Gemma 4\n"
            "Shape reasoning trajectories through structured prompt physics."
        ),
        epilog=(
            "Run --about for architecture overview.\n"
            "Run --list-abilities to see all reasoning modes.\n"
            "Run --list-presets to see all presets.\n"
            "Run --examples to see usage examples.\n"
            "Run --dry-run to inspect assembled prompts without invoking the model."
        ),
        usage="%(prog)s [file]\n       cat file | %(prog)s\n       %(prog)s < file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
    parser.add_argument(
        "--preset",
        metavar="NAME",
        help="load a named reasoning preset (mutually exclusive with --ability and --compare)",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="print available presets with their mapped ability and description, then exit",
    )
    parser.add_argument(
        "--list-abilities",
        action="store_true",
        help="print all abilities with their trajectory and description, then exit",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="print usage examples for all major features, then exit",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="print architecture overview and exit",
    )
    parser.add_argument(
        "--export",
        nargs="?",
        const=True,
        metavar="FILE",
        help="save reasoning output to a Markdown file (default: explaind_YYYYMMDD_HHMMSS.md)",
    )
    parser.add_argument(
        "--honest",
        action="store_true",
        help="two-pass mode: balanced first, then skeptical critique of the initial response",
    )
    parser.add_argument(
        "--chain",
        nargs="+",
        metavar="NAME",
        help="run abilities in sequence, each pass feeding its output as scratchpad to the next",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="activates persistent cognitive scaffold for --chain runs (requires --chain)",
    )
    parser.add_argument(
        "--consensus",
        type=int,
        metavar="N",
        help="run the same prompt N times (2-10) and surface the most consistent answer",
    )
    args = parser.parse_args()

    export_path: str | None = None
    if args.export is True:
        export_path = datetime.now().strftime("explaind_%Y%m%d_%H%M%S.md")
    elif args.export:
        export_path = args.export

    # info flags: print and exit, no input required
    # all active info flags run in order; exit 0 if any were set
    _info_handled = False
    if args.list_abilities:
        print_list_abilities()
        _info_handled = True
    if args.list_presets:
        name_w = max(len(n) for n in PRESET_MAP) + 2
        ability_w = max(len(a) for a in PRESET_MAP.values()) + 2
        for name, ability in PRESET_MAP.items():
            desc = preset_description(name)
            print(f"{name:<{name_w}} →  {ability:<{ability_w}} {desc}")
        _info_handled = True
    if args.examples:
        print_examples()
        _info_handled = True
    if args.about:
        print_about()
        _info_handled = True
    if _info_handled:
        sys.exit(0)

    # --preset, --ability, --compare are mutually exclusive
    if args.preset and args.ability:
        print_error("explaind: --preset and --ability are mutually exclusive")
        sys.exit(1)
    if args.preset and args.compare:
        print_error("explaind: --preset and --compare are mutually exclusive")
        sys.exit(1)

    # --compare and --ability are mutually exclusive
    if args.compare and args.ability:
        print_error("explaind: --compare and --ability are mutually exclusive")
        sys.exit(1)

    # --compare requires at least 2 abilities; for a single ability use --ability
    if args.compare and len(args.compare) < 2:
        print_error("explaind: --compare requires at least 2 ability names")
        sys.exit(1)

    # --honest is mutually exclusive with --compare and --preset
    if args.honest and args.compare:
        print_error("explaind: --honest and --compare are mutually exclusive")
        sys.exit(1)
    if args.honest and args.preset:
        print_error("explaind: --honest and --preset are mutually exclusive")
        sys.exit(1)

    # --chain is mutually exclusive with --ability, --compare, --preset, --honest
    if args.chain and args.ability:
        print_error("explaind: --chain and --ability are mutually exclusive")
        sys.exit(1)
    if args.chain and args.compare:
        print_error("explaind: --chain and --compare are mutually exclusive")
        sys.exit(1)
    if args.chain and args.preset:
        print_error("explaind: --chain and --preset are mutually exclusive")
        sys.exit(1)
    if args.chain and args.honest:
        print_error("explaind: --chain and --honest are mutually exclusive")
        sys.exit(1)

    # --scaffold requires --chain
    if args.scaffold and not args.chain:
        print_error("explaind: --scaffold requires --chain")
        sys.exit(1)

    # --consensus validation and mutual exclusions
    if args.consensus is not None:
        if args.consensus < 2:
            print_error("explaind: --consensus minimum is 2")
            sys.exit(1)
        if args.consensus > 10:
            print_error("explaind: --consensus maximum is 10")
            sys.exit(1)
        if args.compare:
            print_error("explaind: --consensus and --compare are mutually exclusive")
            sys.exit(1)
        if args.chain:
            print_error("explaind: --consensus and --chain are mutually exclusive")
            sys.exit(1)
        if args.honest:
            print_error("explaind: --consensus and --honest are mutually exclusive")
            sys.exit(1)

    # resolve preset -> ability_name
    preset_ability: str | None = None
    if args.preset:
        try:
            preset_ability, _ = load_preset(args.preset)
        except ValueError as e:
            print_error(f"explaind: {e}")
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

    # --- honest: two-pass balanced → skeptical self-critique ---
    if args.honest:
        if args.dry_run:
            try:
                cfg = load_config()
            except ConfigError:
                cfg = DEFAULTS

            try:
                result1, trace1 = run(
                    content,
                    ability="balanced",
                    dry_run=True,
                    trace=args.trace,
                    think=args.think,
                    scratchpad=scratchpad_content,
                    context=context_content,
                )
            except ValueError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)
            print(result1)
            if args.trace and trace1 is not None:
                _emit_trace(trace1, cfg)

            print()
            print("--- [honest mode: pass 2 (skeptical)] ---")
            print()

            pass2_scratchpad = _INITIAL_RESPONSE_HEADER
            if scratchpad_content:
                pass2_scratchpad = scratchpad_content + "\n\n" + _INITIAL_RESPONSE_HEADER

            try:
                result2, trace2 = run(
                    content,
                    ability="skeptical",
                    dry_run=True,
                    trace=args.trace,
                    think=args.think,
                    scratchpad=pass2_scratchpad,
                    context=context_content,
                    honest_mode=True,
                )
            except ValueError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)
            print(result2)
            if args.trace and trace2 is not None:
                _emit_trace(trace2, cfg)

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

        try:
            with _Spinner():
                t0 = time.monotonic()
                result1, trace1 = run(
                    content,
                    ability="balanced",
                    invoker=invoker,
                    trace=args.trace,
                    think=args.think,
                    scratchpad=scratchpad_content,
                    context=context_content,
                )
                ms1 = round((time.monotonic() - t0) * 1000)
        except ValueError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)
        except ModelInvocationError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        _audit_block = _INITIAL_RESPONSE_HEADER + "\n" + result1 + _AUDIT_FOOTER
        pass2_scratchpad = _audit_block
        if scratchpad_content:
            pass2_scratchpad = scratchpad_content + "\n\n" + _audit_block

        try:
            with _Spinner():
                t0 = time.monotonic()
                result2, trace2 = run(
                    content,
                    ability="skeptical",
                    invoker=invoker,
                    trace=args.trace,
                    think=args.think,
                    scratchpad=pass2_scratchpad,
                    context=context_content,
                    honest_mode=True,
                )
                ms2 = round((time.monotonic() - t0) * 1000)
        except ValueError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)
        except ModelInvocationError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        print_honest_header()
        print_honest_separator("Initial Response")
        print_model_output(result1)
        print_honest_separator("Self-Critique")
        print_model_output(result2)
        print_honest_meta(config.model_name, ms1, ms2)

        if args.trace and trace1 is not None:
            _emit_trace(trace1, config)
        if args.trace and trace2 is not None:
            _emit_trace(trace2, config)

        if export_path:
            _write_export(
                content,
                [
                    {"ability": "balanced", "label": "Initial Response", "preset": None, "output": result1, "duration_ms": ms1},
                    {"ability": "skeptical", "label": "Self-Critique", "preset": None, "output": result2, "duration_ms": ms2},
                ],
                config.model_name,
                args.think,
                export_path,
            )

        return

    # --- chain: sequential ability pipeline ---
    if args.chain:
        if len(args.chain) < 2:
            print_error("explaind: --chain requires at least 2 ability names")
            sys.exit(1)

        for name in args.chain:
            if name not in ALLOWED_ABILITIES:
                allowed = ", ".join(sorted(ALLOWED_ABILITIES))
                print_error(f"explaind: unknown ability '{name}' in --chain (allowed: {allowed})")
                sys.exit(1)

        if args.dry_run:
            try:
                cfg = load_config()
            except ConfigError:
                cfg = DEFAULTS

            scaffold_state = build_initial_scaffold(content, args.chain) if args.scaffold else None

            for i, ability in enumerate(args.chain):
                pass_num = i + 1

                scaffold_injection = scaffold_to_injection(scaffold_state) if scaffold_state is not None else None

                if i == 0:
                    sp = scratchpad_content
                else:
                    handoff = _chain_handoff_header(args.chain[i - 1], ability)
                    sp = handoff
                    if i == 1 and scratchpad_content:
                        sp = scratchpad_content + "\n\n" + handoff

                try:
                    result, trace = run(
                        content,
                        ability=ability,
                        dry_run=True,
                        trace=args.trace,
                        think=args.think,
                        scratchpad=sp,
                        context=context_content,
                        scaffold_context=scaffold_injection,
                    )
                except ValueError as e:
                    print_error(f"explaind: {e}")
                    sys.exit(1)

                print()
                print(f"--- [chain: pass {pass_num} ({ability})] ---")
                print()
                print(result)

                if args.trace and trace is not None:
                    _emit_trace(trace, cfg)

                if scaffold_state is not None:
                    scaffold_state.stage_history.append(ability)
                    if i + 1 < len(args.chain):
                        scaffold_state.current_stage = args.chain[i + 1]

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

        scaffold_state = build_initial_scaffold(content, args.chain) if args.scaffold else None

        chain_results: list[tuple[str, str, int, object]] = []
        prev_output: str | None = None

        for i, ability in enumerate(args.chain):
            pass_num = i + 1

            scaffold_injection = scaffold_to_injection(scaffold_state) if scaffold_state is not None else None

            if i == 0:
                sp = scratchpad_content
            else:
                handoff = _chain_handoff_header(args.chain[i - 1], ability)
                handoff_content = handoff + "\n\n" + (prev_output or "")

                if len(handoff_content) > _CHAIN_SCRATCHPAD_LIMIT:
                    print_warning(
                        f"explaind: scratchpad truncated to {_CHAIN_SCRATCHPAD_LIMIT} chars for pass {pass_num}"
                    )
                    handoff_content = handoff_content[-_CHAIN_SCRATCHPAD_LIMIT:]

                if i == 1 and scratchpad_content:
                    sp = scratchpad_content + "\n\n" + handoff_content
                else:
                    sp = handoff_content

            try:
                with _Spinner():
                    t0 = time.monotonic()
                    result, trace = run(
                        content,
                        ability=ability,
                        invoker=invoker,
                        trace=args.trace,
                        think=args.think,
                        scratchpad=sp,
                        context=context_content,
                        scaffold_context=scaffold_injection,
                    )
                    ms = round((time.monotonic() - t0) * 1000)
            except ValueError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)
            except ModelInvocationError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)

            if scaffold_state is not None:
                scaffold_state, result = parse_scaffold_update(result, scaffold_state)
                if args.trace:
                    print_scaffold_status(ability, pass_num, len(args.chain), scaffold_state.drift_detected)
                scaffold_state.stage_history.append(ability)
                if i + 1 < len(args.chain):
                    scaffold_state.current_stage = args.chain[i + 1]

            prev_output = result
            chain_results.append((ability, result, ms, trace))

        print_chain_header(args.chain)
        for i, (ability, result, ms, trace) in enumerate(chain_results):
            print_chain_separator(ability, i + 1)
            print_model_output(result)
            if args.trace and trace is not None:
                _emit_trace(trace, config)

        print_chain_meta(config.model_name, [ms for _, _, ms, _ in chain_results])

        if args.trace and scaffold_state is not None:
            print_scaffold_summary(scaffold_state.session_id, scaffold_state.drift_detected, len(scaffold_state.stage_history))

        scaffold_export_summary = scaffold_to_export_summary(scaffold_state) if scaffold_state is not None and export_path else None

        if export_path:
            _write_export(
                content,
                [
                    {
                        "label": f"Pass {i + 1}: {ability}",
                        "ability": ability,
                        "preset": None,
                        "output": result,
                        "duration_ms": ms,
                    }
                    for i, (ability, result, ms, _) in enumerate(chain_results)
                ],
                config.model_name,
                args.think,
                export_path,
                scaffold_summary=scaffold_export_summary,
            )

        return

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

        compare_runs: list[dict] = []
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

            compare_runs.append({"ability": ability, "preset": None, "output": result, "duration_ms": latency_ms})

        if export_path:
            _write_export(content, compare_runs, config.model_name, args.think, export_path)

        return

    # --- consensus: self-consistency aggregator ---
    if args.consensus is not None:
        effective_ability = preset_ability if args.preset else args.ability

        if args.dry_run:
            try:
                result, prompt_trace = run(
                    content,
                    ability=effective_ability,
                    dry_run=True,
                    trace=args.trace,
                    think=args.think,
                    scratchpad=scratchpad_content,
                    context=context_content,
                    preset_name=args.preset,
                )
            except ValueError as e:
                print_error(f"explaind: {e}")
                sys.exit(1)
            print(result)
            print(f"\n[consensus: would run {args.consensus} times]")
            if args.trace and prompt_trace is not None:
                try:
                    cfg = load_config()
                except ConfigError:
                    cfg = DEFAULTS
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

        try:
            assembled_prompt, prompt_trace = run(
                content,
                ability=effective_ability,
                dry_run=True,
                trace=args.trace,
                think=args.think,
                scratchpad=scratchpad_content,
                context=context_content,
                preset_name=args.preset,
            )
        except ValueError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        try:
            best_output, consensus_rep = run_consensus(
                invoker,
                assembled_prompt,
                args.consensus,
                on_run_start=print_consensus_progress,
            )
        except ModelInvocationError as e:
            print_error(f"explaind: {e}")
            sys.exit(1)

        latency_ms = consensus_rep["total_ms"]

        print_run_header(effective_ability or "balanced", args.think, preset=args.preset)
        print_model_output(best_output)
        print_model_meta(config.model_name, latency_ms, ability=effective_ability or "balanced")
        print_consensus_report(consensus_rep)

        if args.trace and prompt_trace is not None:
            _emit_trace(prompt_trace, config)

        if export_path:
            _write_export(
                content,
                [{"ability": effective_ability or "balanced", "preset": args.preset, "output": best_output, "duration_ms": latency_ms}],
                config.model_name,
                args.think,
                export_path,
                consensus_report=consensus_rep,
            )

        return

    # effective ability: preset-mapped name takes precedence over --ability
    effective_ability = preset_ability if args.preset else args.ability

    # --- dry-run: assemble only, no model invocation ---
    if args.dry_run:
        try:
            result, prompt_trace = run(
                content,
                ability=effective_ability,
                dry_run=True,
                trace=args.trace,
                think=args.think,
                scratchpad=scratchpad_content,
                context=context_content,
                preset_name=args.preset,
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
                ability=effective_ability,
                invoker=invoker,
                trace=args.trace,
                think=args.think,
                scratchpad=scratchpad_content,
                context=context_content,
                preset_name=args.preset,
            )
            latency_ms = round((time.monotonic() - t0) * 1000)
    except ValueError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)
    except ModelInvocationError as e:
        print_error(f"explaind: {e}")
        sys.exit(1)

    print_run_header(effective_ability or "balanced", args.think, preset=args.preset)
    print_model_output(result)
    print_model_meta(config.model_name, latency_ms, ability=effective_ability or "balanced")

    if args.trace and prompt_trace is not None:
        _emit_trace(prompt_trace, config)

    if export_path:
        _write_export(
            content,
            [{"ability": effective_ability or "balanced", "preset": args.preset, "output": result, "duration_ms": latency_ms}],
            config.model_name,
            args.think,
            export_path,
        )


if __name__ == "__main__":
    main()
