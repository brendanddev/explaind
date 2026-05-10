from typing import Optional
import typer
import sys
from explaind.main import run

app = typer.Typer()

@app.command()
def explain(file: Optional[str] = typer.Argument(None, help="Path to log file or '-' for stdin")):

    if not file or file == "-":
        content = sys.stdin.read()
    else:
        with open(file, "r") as f:
            content = f.read()

    output = run(content)

    print("\nexplaind output:\n")
    print(output)


def main():
    app()