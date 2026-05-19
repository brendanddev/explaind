import io
import sys
from unittest.mock import patch

import pytest

from explaind.cli import main


def _invoke(*args):
    """Run main() with given args (no positional input file — demo provides its own content)."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    argv = ["explaind"] + list(args)
    with patch("sys.argv", argv), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


def test_demo_dry_run_exits_0():
    _, _, exit_code = _invoke("--demo", "--dry-run")
    assert exit_code == 0


def test_demo_dry_run_contains_demo_1_header():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "Demo 1/3" in stdout


def test_demo_dry_run_contains_demo_2_header():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "Demo 2/3" in stdout


def test_demo_dry_run_contains_demo_3_header():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "Demo 3/3" in stdout


def test_demo_dry_run_contains_demo_1_question():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "2008 financial crisis" in stdout


def test_demo_dry_run_contains_demo_2_question():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "eliminate most jobs" in stdout


def test_demo_dry_run_contains_demo_3_question():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "climate change" in stdout


def test_demo_dry_run_contains_skeptical():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "skeptical" in stdout.lower()


def test_demo_dry_run_contains_calibrator():
    stdout, _, _ = _invoke("--demo", "--dry-run")
    assert "calibrator" in stdout.lower()


def test_demo_with_ability_exits_1():
    _, stderr, exit_code = _invoke("--demo", "--ability", "skeptical")
    assert exit_code == 1
    assert "--demo" in stderr


def test_demo_with_compare_exits_1():
    _, stderr, exit_code = _invoke("--demo", "--compare", "skeptical", "causal")
    assert exit_code == 1
    assert "--demo" in stderr


def test_demo_with_chain_exits_1():
    _, stderr, exit_code = _invoke("--demo", "--chain", "skeptical", "causal")
    assert exit_code == 1
    assert "--demo" in stderr


def test_demo_with_honest_exits_1():
    _, stderr, exit_code = _invoke("--demo", "--honest")
    assert exit_code == 1
    assert "--demo" in stderr
