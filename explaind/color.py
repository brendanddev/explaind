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


def print_model_meta(text: str) -> None:
    console = _stderr_console()
    if console.is_terminal:
        console.print(text, style="dim", justify="right", markup=False)
    else:
        console.print(text, style="dim", markup=False)


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
