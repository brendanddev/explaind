import sys
import json
import argparse

from rich.console import Console

from explaind.main import run
from explaind.render import render_result


def main():
    parser = argparse.ArgumentParser(
        prog="explaind",
        description="Debug log analyzer powered by Gemma 4",
        usage="%(prog)s [file]\n       cat file | %(prog)s\n       %(prog)s < file",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="path to log file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output raw JSON (machine-readable mode)",
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

    err = Console(stderr=True)
    out = Console()

    with err.status("[dim]analyzing…[/dim]", spinner="dots"):
        result = run(content)

    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "_meta"}, indent=2))
    else:
        render_result(result, out)
