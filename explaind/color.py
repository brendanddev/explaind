import sys

from rich.console import Console
from rich.text import Text

_ABILITY_COLORS = {
    "skeptical": "bold red",
    "causal": "bold blue",
    "compressive": "bold yellow",
    "exploratory": "bold magenta",
    "balanced": "bold cyan",
    "calibrator": "bold green",
    "devil": "bold bright_red",
    "updater": "bold bright_cyan",
}


def _stdout_console() -> Console:
    return Console(file=sys.stdout, highlight=False)


def _stderr_console() -> Console:
    return Console(file=sys.stderr, highlight=False)


def print_compare_header(ability_name: str) -> None:
    color = _ABILITY_COLORS.get(ability_name.lower(), "bold white")
    t = Text()
    t.append("═══", style="dim white")
    t.append(" ABILITY: ", style="default")
    t.append(ability_name.upper(), style=color)
    t.append(" ═══", style="dim white")
    _stdout_console().print(t)


def print_run_header(ability: str, think: bool, preset: str | None = None) -> None:
    from rich.box import SQUARE
    from rich.panel import Panel

    console = _stdout_console()
    if not console.is_terminal:
        think_suffix = " · think" if think else ""
        if preset:
            print(f"[explaind · preset: {preset} ({ability}){think_suffix}]")
        else:
            print(f"[explaind · ability: {ability}{think_suffix}]")
        return

    color = _ABILITY_COLORS.get(ability.lower(), "bold white")
    t = Text()
    t.append("explaind", style="bold")
    if preset:
        t.append("  ·  preset: ", style="dim")
        t.append(preset, style=color)
        t.append(f" ({ability})", style="dim")
    else:
        t.append("  ·  ability: ", style="dim")
        t.append(ability, style=color)
    if think:
        t.append("  · think", style="dim")
    console.print(Panel(t, box=SQUARE, padding=(0, 2)))


def print_model_meta(model_name: str, latency_ms: int, ability: str | None = None) -> None:
    from rich.rule import Rule

    console = _stderr_console()
    ability_str = f" · {ability}" if ability else ""
    footer_text = f"{model_name} · {latency_ms}ms{ability_str}"
    if console.is_terminal:
        console.print(Rule(style="dim"))
        console.print(f"  {footer_text}", style="dim", markup=False)
    else:
        console.print(footer_text, style="dim", markup=False)


def print_demo_title(text: str) -> None:
    _stdout_console().print(text, style="bold white", markup=False)


def print_error(text: str) -> None:
    _stderr_console().print(text, style="bold red", markup=False)


def print_warning(text: str) -> None:
    _stderr_console().print(text, style="yellow", markup=False)


def print_model_output(text: str) -> None:
    from rich.markdown import Markdown

    console = _stdout_console()
    if console.is_terminal:
        console.print(Markdown(text))
    else:
        print(text)


def print_export_confirmation(path: str) -> None:
    console = _stderr_console()
    if console.is_terminal:
        console.print(f"exported → {path}", style="dim green", markup=False)
    else:
        print(f"exported → {path}", file=sys.stderr)


def print_honest_header() -> None:
    from rich.box import SQUARE
    from rich.panel import Panel

    console = _stdout_console()
    if not console.is_terminal:
        print("[explaind · honest mode]")
        return

    t = Text()
    t.append("explaind", style="bold")
    t.append("  ·  honest mode", style="dim")
    console.print(Panel(t, box=SQUARE, padding=(0, 2)))


def print_honest_separator(label: str) -> None:
    from rich.rule import Rule

    console = _stdout_console()
    if not console.is_terminal:
        print(f"\n── {label} ──\n")
        return

    console.print()
    console.print(Rule(f" {label} ", style="dim"))
    console.print()


def print_honest_meta(model_name: str, ms1: int, ms2: int) -> None:
    from rich.rule import Rule

    console = _stderr_console()
    footer_text = f"{model_name} · {ms1}ms + {ms2}ms · honest"
    if console.is_terminal:
        console.print(Rule(style="dim"))
        console.print(f"  {footer_text}", style="dim", markup=False)
    else:
        console.print(footer_text, style="dim", markup=False)


def print_chain_header(abilities: list[str]) -> None:
    from rich.box import SQUARE
    from rich.panel import Panel

    chain_str = " → ".join(abilities)
    console = _stdout_console()

    if not console.is_terminal:
        print(f"[explaind · chain: {chain_str}]")
        return

    t = Text()
    t.append("explaind", style="bold")
    if len(abilities) >= 4:
        first_line = " → ".join(abilities[:2])
        rest_line = " → ".join(abilities[2:])
        t.append(f"  ·  chain: {first_line}", style="dim")
        t.append(f"\n             → {rest_line}", style="dim")
    else:
        t.append(f"  ·  chain: {chain_str}", style="dim")
    console.print(Panel(t, box=SQUARE, padding=(0, 2)))


def print_chain_separator(ability: str, pass_num: int) -> None:
    from rich.rule import Rule

    console = _stdout_console()
    label = f" Pass {pass_num}: {ability} "

    if not console.is_terminal:
        print(f"\n── Pass {pass_num}: {ability} ──\n")
        return

    console.print()
    console.print(Rule(label, style="dim"))
    console.print()


def print_chain_meta(model: str, times: list[int]) -> None:
    from rich.rule import Rule

    console = _stderr_console()
    times_str = " + ".join(f"{ms}ms" for ms in times)
    footer_text = f"{model} · {times_str} · chain"
    if console.is_terminal:
        console.print(Rule(style="dim"))
        console.print(f"  {footer_text}", style="dim", markup=False)
    else:
        console.print(footer_text, style="dim", markup=False)


def print_scaffold_status(stage: str, pass_num: int, total: int, drift: bool) -> None:
    console = _stderr_console()
    status = "DRIFT DETECTED" if drift else "state updated"
    msg = f"scaffold · pass {pass_num}/{total} · {stage} complete · {status}"
    if console.is_terminal:
        console.print(msg, style="dim", markup=False)
    else:
        console.print(msg, markup=False)


def print_scaffold_summary(session_id: str, drift_detected: bool, passes: int = 0) -> None:
    console = _stderr_console()
    drift_str = f"drift detected in {passes} passes" if drift_detected else "clean"
    msg = f"scaffold session {session_id} · {passes} passes · {drift_str}"
    if console.is_terminal:
        console.print(msg, style="dim", markup=False)
    else:
        console.print(msg, markup=False)


def print_consensus_progress(run_num: int, total: int) -> None:
    console = _stderr_console()
    msg = f"  consensus run {run_num}/{total}..."
    if console.is_terminal:
        console.print(msg, style="dim", markup=False)
    else:
        console.print(msg, markup=False)


_ABILITY_DESCRIPTIONS: dict[str, str] = {
    "balanced":    "Integrated analysis across all frameworks",
    "skeptical":   "Epistemic pressure applied to every claim",
    "causal":      "Mechanism tracing from outcome to root cause",
    "compressive": "Maximum signal density, minimum elaboration",
    "exploratory": "Generative inquiry, resists premature closure",
    "calibrator":  "Explicit confidence scoring on every claim",
    "devil":       "Adversarial pressure, argues opposing position",
    "updater":     "Bayesian belief revision from prior to posterior",
}

_ABILITY_ORDER = [
    "balanced",
    "skeptical",
    "causal",
    "compressive",
    "exploratory",
    "calibrator",
    "devil",
    "updater",
]

_EXAMPLES_SECTIONS = [
    ("BASIC USAGE", [
        'echo "Your question" | explaind',
        'echo "Your question" | explaind --ability skeptical',
        'explaind --file document.txt --ability causal',
    ]),
    ("COMPARE ABILITIES", [
        'echo "Was the 2008 crisis preventable?" | explaind --compare skeptical causal compressive',
        'echo "Is AI safe?" | explaind --compare devil calibrator balanced',
    ]),
    ("REASONING CHAINS", [
        'echo "What caused inflation?" | explaind --chain causal compressive skeptical',
        'echo "Analyse this claim" | explaind --chain causal compressive skeptical --scaffold',
    ]),
    ("SELF-CRITIQUE", [
        'echo "Explain quantum entanglement" | explaind --honest',
        'echo "Explain quantum entanglement" | explaind --honest --think',
    ]),
    ("SELF-CONSISTENCY", [
        'echo "What is the root cause of X?" | explaind --ability causal --consensus 5',
        'echo "Is this argument valid?" | explaind --preset critic --consensus 3',
    ]),
    ("PRESETS", [
        'echo "Is consciousness an illusion?" | explaind --preset philosopher',
        'echo "Why is this system failing?" | explaind --preset engineer --think',
    ]),
    ("CONTEXT INJECTION", [
        'echo "What should we conclude?" | explaind --ability updater --scratchpad notes.md',
        'echo "Evaluate this" | explaind --ability skeptical --context background.md',
    ]),
    ("EXPORT", [
        'echo "Your question" | explaind --compare skeptical causal --export analysis.md',
        'echo "Your question" | explaind --chain causal compressive skeptical --scaffold --export chain.md',
    ]),
]

_ABOUT_TEXT_PLAIN = """\
explaind — cognitive steering layer for Gemma 4

A structured prompt physics system that shapes Gemma 4's
reasoning trajectories through layered injection of:
  · System constraints (GEMMA.md invariant layer)
  · Ability bias vectors (8 named reasoning modes)
  · Three-position BIAS FIELD (primacy + periodic + recency)
  · Cognitive scaffold (persistent state across chain passes)

Built around Gemma 4's documented failure modes — not despite
them. Every design decision maps to a specific model behavior.

Abilities:  8 reasoning modes grounded in cognitive science
Presets:    6 named thinking personalities
Chains:     Sequential ability pipelines with handoff state
Scaffold:   Persistent JSON reasoning architecture
Consensus:  Self-consistency aggregation (Wang et al. 2022)

Run --list-abilities to see all reasoning modes.
Run --list-presets to see all presets.
Run --examples to see usage examples."""


def print_list_abilities() -> None:
    name_w = max(len(n) for n in _ABILITY_ORDER) + 2
    traj_w = name_w
    console = _stdout_console()
    if console.is_terminal:
        for name in _ABILITY_ORDER:
            desc = _ABILITY_DESCRIPTIONS[name]
            color = _ABILITY_COLORS.get(name, "bold white")
            t = Text()
            t.append(f"{name:<{name_w}}", style=color)
            t.append("→  ", style="dim")
            t.append(f"{name:<{traj_w}}", style="dim")
            t.append(desc)
            console.print(t, markup=False)
    else:
        for name in _ABILITY_ORDER:
            desc = _ABILITY_DESCRIPTIONS[name]
            print(f"{name:<{name_w}} →  {name:<{traj_w}} {desc}")


def print_examples() -> None:
    console = _stdout_console()
    if console.is_terminal:
        for header, examples in _EXAMPLES_SECTIONS:
            console.print(f"\n{header}", style="bold")
            for ex in examples:
                console.print(f"  {ex}", style="dim", markup=False)
        console.print()
    else:
        for header, examples in _EXAMPLES_SECTIONS:
            print(f"\n{header}")
            for ex in examples:
                print(f"  {ex}")
        print()


def print_about() -> None:
    console = _stdout_console()
    if not console.is_terminal:
        print(_ABOUT_TEXT_PLAIN)
        return

    t = Text()
    t.append("explaind", style="bold")
    t.append(" — cognitive steering layer for Gemma 4\n\n")
    t.append("A structured prompt physics system that shapes Gemma 4's\n")
    t.append("reasoning trajectories through layered injection of:\n")
    t.append("  · System constraints ", style="default")
    t.append("(GEMMA.md invariant layer)\n", style="dim")
    t.append("  · Ability bias vectors ", style="default")
    t.append("(8 named reasoning modes)\n", style="dim")
    t.append("  · Three-position ", style="default")
    t.append("BIAS FIELD", style="bold")
    t.append(" (primacy + periodic + recency)\n", style="dim")
    t.append("  · Cognitive scaffold ", style="default")
    t.append("(persistent state across chain passes)\n", style="dim")
    t.append("\nBuilt around Gemma 4's documented failure modes — not despite\n")
    t.append("them. Every design decision maps to a specific model behavior.\n\n")
    t.append("Abilities:  ", style="dim")
    t.append("8 reasoning modes grounded in cognitive science\n")
    t.append("Presets:    ", style="dim")
    t.append("6 named thinking personalities\n")
    t.append("Chains:     ", style="dim")
    t.append("Sequential ability pipelines with handoff state\n")
    t.append("Scaffold:   ", style="dim")
    t.append("Persistent JSON reasoning architecture\n")
    t.append("Consensus:  ", style="dim")
    t.append("Self-consistency aggregation (Wang et al. 2022)\n\n")
    t.append("Run --list-abilities to see all reasoning modes.\n")
    t.append("Run --list-presets to see all presets.\n")
    t.append("Run --examples to see usage examples.")
    console.print(t)


_DEMO_BORDER = "━" * 52


def print_demo_section_header(num: int, total: int, title: str, question: str, command: str) -> None:
    console = _stdout_console()
    if not console.is_terminal:
        print(_DEMO_BORDER)
        print(f"  Demo {num}/{total} — {title}")
        print()
        print(f'  Question: "{question}"')
        print(f"  Command:  {command}")
        print(_DEMO_BORDER)
        return

    t = Text()
    t.append(_DEMO_BORDER + "\n", style="dim")
    t.append(f"  Demo {num}/{total}", style="bold")
    t.append(f" — {title}\n", style="bold white")
    t.append("\n")
    t.append(f'  Question: "{question}"\n', style="dim")
    t.append("  Command:  ", style="dim")
    t.append(command + "\n", style="dim cyan")
    t.append(_DEMO_BORDER, style="dim")
    console.print(t)


def print_demo_between(demo_num: int) -> None:
    console = _stdout_console()
    msg = f"  ── continuing to Demo {demo_num + 1}/3 ──────────────────────"
    if console.is_terminal:
        console.print(msg, style="dim", markup=False)
    else:
        print(msg)


def print_demo_footer() -> None:
    console = _stdout_console()
    if not console.is_terminal:
        print(_DEMO_BORDER)
        print("  Demo complete.")
        print()
        print("  What you just saw:")
        print("    Demo 1 — Same question steered through three")
        print("             reasoning modes (skeptical, causal, devil)")
        print("    Demo 2 — Gemma 4 critiquing its own reasoning")
        print("             under epistemic pressure")
        print("    Demo 3 — Explicit confidence calibration with")
        print("             falsification conditions")
        print()
        print("  Try your own:")
        print('    echo "your question" | explaind --compare skeptical causal devil')
        print('    echo "your question" | explaind --honest --think')
        print('    echo "your question" | explaind --ability calibrator')
        print('    echo "your question" | explaind --chain causal compressive skeptical')
        print()
        print("  Run --about for architecture overview.")
        print("  Run --examples for full command reference.")
        print(_DEMO_BORDER)
        return

    t = Text()
    t.append(_DEMO_BORDER + "\n", style="dim")
    t.append("  Demo complete.\n\n", style="bold white")
    t.append("  What you just saw:\n", style="bold")
    t.append("    Demo 1 — Same question steered through three\n", style="dim")
    t.append("             reasoning modes (skeptical, causal, devil)\n", style="dim")
    t.append("    Demo 2 — Gemma 4 critiquing its own reasoning\n", style="dim")
    t.append("             under epistemic pressure\n", style="dim")
    t.append("    Demo 3 — Explicit confidence calibration with\n", style="dim")
    t.append("             falsification conditions\n\n", style="dim")
    t.append("  Try your own:\n", style="bold")
    t.append('    echo "your question" | explaind --compare skeptical causal devil\n', style="dim cyan")
    t.append('    echo "your question" | explaind --honest --think\n', style="dim cyan")
    t.append('    echo "your question" | explaind --ability calibrator\n', style="dim cyan")
    t.append('    echo "your question" | explaind --chain causal compressive skeptical\n\n', style="dim cyan")
    t.append("  Run --about for architecture overview.\n", style="dim")
    t.append("  Run --examples for full command reference.\n", style="dim")
    t.append(_DEMO_BORDER, style="dim")
    console.print(t)


def print_full_demo_act_header(act_num: int, total: int, title: str) -> None:
    console = _stdout_console()
    if not console.is_terminal:
        print(_DEMO_BORDER)
        print(f"  Act {act_num} / {total} — {title}")
        print(_DEMO_BORDER)
        return

    t = Text()
    t.append(_DEMO_BORDER + "\n", style="dim")
    t.append(f"  Act {act_num} / {total}", style="bold")
    t.append(f" — {title}\n", style="bold white")
    t.append(_DEMO_BORDER, style="dim")
    console.print(t)


def print_full_demo_closing() -> None:
    console = _stdout_console()
    if not console.is_terminal:
        print(_DEMO_BORDER)
        print("  Full demonstration complete.")
        print()
        print("  What you just saw:")
        print("    Act 1 — What explaind is and why it exists")
        print("    Act 2 — 8 abilities and 6 presets")
        print("    Act 3 — The assembled prompt: layers made visible")
        print("    Act 4 — Same question, different steering")
        print("    Act 5 — Live Gemma 4 cognitive steering")
        print()
        print("  Get started:")
        print('    echo "your question" | explaind --ability skeptical')
        print('    echo "your question" | explaind --compare skeptical causal devil')
        print('    echo "your question" | explaind --honest --think')
        print("    explaind --examples")
        print(_DEMO_BORDER)
        return

    t = Text()
    t.append(_DEMO_BORDER + "\n", style="dim")
    t.append("  Full demonstration complete.\n\n", style="bold white")
    t.append("  What you just saw:\n", style="bold")
    t.append("    Act 1 — What explaind is and why it exists\n", style="dim")
    t.append("    Act 2 — 8 abilities and 6 presets\n", style="dim")
    t.append("    Act 3 — The assembled prompt: layers made visible\n", style="dim")
    t.append("    Act 4 — Same question, different steering\n", style="dim")
    t.append("    Act 5 — Live Gemma 4 cognitive steering\n\n", style="dim")
    t.append("  Get started:\n", style="bold")
    t.append('    echo "your question" | explaind --ability skeptical\n', style="dim cyan")
    t.append('    echo "your question" | explaind --compare skeptical causal devil\n', style="dim cyan")
    t.append('    echo "your question" | explaind --honest --think\n', style="dim cyan")
    t.append("    explaind --examples\n", style="dim cyan")
    t.append(_DEMO_BORDER, style="dim")
    console.print(t)


def print_consensus_report(report: dict) -> None:
    n = report["n"]
    agreement = report["agreement"]
    pct = report["agreement_pct"]
    confidence = report["confidence"]
    divergent_runs = report["divergent_runs"]
    total_ms = report["total_ms"]
    avg = round(total_ms / n) if n else 0

    confidence_styles = {"HIGH": "bold green", "MEDIUM": "bold yellow", "LOW": "bold red"}
    conf_style = confidence_styles.get(confidence, "bold white")

    filled = agreement
    empty = n - agreement
    bar = "█" * filled + "░" * empty

    console = _stderr_console()
    if console.is_terminal:
        from rich.rule import Rule
        from rich.text import Text

        width = 44
        border = "━" * width
        console.print(f"━━━ Consensus ({n} runs) " + "━" * (width - 18 - len(str(n))), style="dim", markup=False)

        agreement_line = Text()
        agreement_line.append("Agreement:  ", style="dim")
        agreement_line.append(f"{agreement}/{n}  {bar}  {pct:.0f}%", style="default")
        console.print(agreement_line)

        conf_line = Text()
        conf_line.append("Confidence: ", style="dim")
        conf_line.append(confidence, style=conf_style)
        console.print(conf_line)

        console.print(f"Divergent:  {divergent_runs} run(s)", style="dim", markup=False)
        console.print(f"Time:       {total_ms}ms total · {avg}ms avg", style="dim", markup=False)
        console.print("━" * width, style="dim", markup=False)
    else:
        console.print(f"Consensus: {agreement}/{n} runs agree  ({pct:.0f}%)", markup=False)
        console.print(f"Confidence: {confidence}", markup=False)
        console.print(f"Divergent: {divergent_runs} run(s)", markup=False)
        console.print(f"Time: {total_ms}ms total · {avg}ms avg", markup=False)
