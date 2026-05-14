import sys

from rich.console import Console
from rich.text import Text

_ABILITY_COLORS = {
    "skeptical": "bold red",
    "causal": "bold blue",
    "compressive": "bold yellow",
    "exploratory": "bold magenta",
    "balanced": "bold cyan",
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
