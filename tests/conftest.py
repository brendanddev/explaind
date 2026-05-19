import pytest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def set_project_root(monkeypatch):
    """Run every test from the project root so relative paths (abilities/, GEMMA.md) resolve."""
    monkeypatch.chdir(_PROJECT_ROOT)
