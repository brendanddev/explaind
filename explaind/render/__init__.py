from __future__ import annotations

import re

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


_INSUFFICIENT = frozenset({
    "insufficient information",
    "insufficient_information",
    "n/a",
    "none",
    "",
})


def _is_empty(value: str | list | None) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    return value.strip().lower() in _INSUFFICIENT


def _failure_style(failure_type: str) -> tuple[str, str]:
    ft = failure_type.lower()
    if any(k in ft for k in ("crash", "fatal", "panic", "segfault")):
        return "✗", "red"
    if any(k in ft for k in ("test", "assert", "regression", "null", "none",
                              "undefined", "type", "attribute", "runtime")):
        return "✗", "red"
    if any(k in ft for k in ("import", "module", "package", "dependency",
                              "connect", "timeout", "network", "socket",
                              "permission", "auth", "denied", "forbidden",
                              "syntax", "parse", "format", "violation", "schema")):
        return "!", "yellow"
    return "✗", "red"


def _looks_like_code(text: str) -> bool:
    lines = text.splitlines()
    if len(lines) < 2:
        return False
    code_tokens = (
        "def ", "class ", "return ", "import ", "from ",
        "function ", "const ", "let ", "var ",
        "if ", "elif ", "else:", "for ", "while ",
        "=>", "->", "::", "throw ", "raise ", "async ",
        "try:", "except ", "catch ",
    )
    hits = sum(1 for line in lines if any(tok in line for tok in code_tokens))
    indented = any(line.startswith(("    ", "\t")) for line in lines)
    return hits >= 1 and indented


def _detect_language(text: str) -> str:
    text_lower = text.lower()
    if any(k in text_lower for k in ("def ", "raise ", "elif ", "self.", "print(")):
        return "python"
    if any(k in text_lower for k in ("function ", "const ", "let ", "var ", "console.", "=>")):
        return "javascript"
    if any(k in text_lower for k in ("public ", "private ", "void ", "static ", "throws ")):
        return "java"
    if any(k in text_lower for k in ("fn ", "let mut", "println!", "impl ", "use std")):
        return "rust"
    return "python"


def _render_header(failure_type: str, icon: str, color: str, console: Console) -> None:
    label = failure_type.upper().replace("_", " ")
    title = Text()
    title.append(f" {icon}  ", style="bold")
    title.append(label, style=f"bold {color}")
    console.print()
    console.print(Rule(title=title, style=color, align="center"))
    console.print()


def _render_root_cause(root_cause: str, console: Console) -> None:
    if _is_empty(root_cause):
        return
    console.print(
        Panel(
            Text(root_cause, style="white"),
            title="[bold white]Root Cause[/bold white]",
            title_align="left",
            border_style="bright_red",
            padding=(0, 1),
        )
    )
    console.print()


def _render_evidence(evidence: list, console: Console) -> None:
    if not evidence:
        return

    grid = Table.grid(padding=(0, 1))
    grid.add_column(no_wrap=True, min_width=4)
    grid.add_column(style="white")

    for item in evidence:
        if not isinstance(item, str) or not item.strip():
            continue
        match = re.match(r"^(\[.+?\])\s*(.*)", item.strip(), re.DOTALL)
        if match:
            ref, body = match.group(1), match.group(2)
            ref_cell = Text()
            ref_cell.append("• ", style="bold blue")
            ref_cell.append(ref, style="bold blue")
            grid.add_row(ref_cell, body.strip())
        else:
            grid.add_row(Text("•", style="bold blue"), item.strip())

    console.print(
        Panel(
            grid,
            title="[bold white]Evidence[/bold white]",
            title_align="left",
            border_style="blue",
            padding=(0, 1),
        )
    )
    console.print()


def _render_causal_chain(causal_chain: str, console: Console) -> None:
    if _is_empty(causal_chain):
        return
    console.print(
        Panel(
            Text(causal_chain, style="white"),
            title="[bold white]Causal Chain[/bold white]",
            title_align="left",
            border_style="dim white",
            padding=(0, 1),
        )
    )
    console.print()


def _render_suggested_fix(suggested_fix: str, console: Console) -> None:
    if _is_empty(suggested_fix):
        return

    if _looks_like_code(suggested_fix):
        lang = _detect_language(suggested_fix)
        content: Syntax | Text = Syntax(
            suggested_fix,
            lang,
            theme="monokai",
            line_numbers=False,
            background_color="default",
            word_wrap=True,
        )
    else:
        content = Text(suggested_fix, style="green")

    console.print(
        Panel(
            content,
            title="[bold white]Suggested Fix[/bold white]",
            title_align="left",
            border_style="green",
            padding=(0, 1),
        )
    )
    console.print()


def _render_footer(meta: dict, console: Console) -> None:
    parts: list[str] = []

    if meta.get("schema_valid", True):
        parts.append("[green]✓ valid[/green]")
    else:
        parts.append("[red]✗ schema error[/red]")

    if meta.get("constraint_violation_detected"):
        parts.append("[yellow]! constraint flag[/yellow]")

    if meta.get("retry_triggered"):
        parts.append("[dim]retried[/dim]")

    model = meta.get("model")
    if model:
        parts.append(f"[dim]{model}[/dim]")

    latency = meta.get("latency_ms")
    if latency is not None:
        parts.append(f"[dim]{latency:.0f}ms[/dim]")

    if not parts:
        return

    separator = Text("  ·  ", style="dim")
    line = Text()
    for i, markup in enumerate(parts):
        if i > 0:
            line.append_text(separator)
        line.append_text(Text.from_markup(markup))

    console.print(line, justify="right")
    console.print()


def render_result(structured_data: dict, console: Console) -> None:
    """Render a structured debugging result to the terminal using Rich."""
    failure_type = structured_data.get("failure_type") or "unknown error"
    root_cause = structured_data.get("root_cause") or ""
    evidence = structured_data.get("evidence") or []
    causal_chain = structured_data.get("causal_chain") or ""
    suggested_fix = structured_data.get("suggested_fix") or ""
    meta = structured_data.get("_meta") or {}

    icon, color = _failure_style(failure_type)

    _render_header(failure_type, icon, color, console)
    _render_root_cause(root_cause, console)
    _render_evidence(evidence, console)
    _render_causal_chain(causal_chain, console)
    _render_suggested_fix(suggested_fix, console)
    _render_footer(meta, console)
