import typer
from explaind.main import run

app = typer.Typer()


@app.command()
def explain(file: str = None):
    """
    Explain logs using Gemma 4
    """
    output = run(file)

    print("\nexplaind output:\n")
    print(output)


@app.command()
def stdin():
    """
    Read from stdin
    """
    import sys
    log = sys.stdin.read()
    output = run(None)

    print("\nexplaind output:\n")
    print(output)


if __name__ == "__main__":
    app()