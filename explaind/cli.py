import sys
import argparse

from explaind.main import run


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

    print("analyzing...", end="", file=sys.stderr, flush=True)
    result = run(content, ability=args.ability)
    print("\r            \r", end="", file=sys.stderr, flush=True)

    print(result)
