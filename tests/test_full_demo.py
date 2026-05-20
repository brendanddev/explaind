import io
import sys
from unittest.mock import patch

import pytest

from explaind.cli import main


def _invoke(*args):
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


def test_full_demo_dry_run_exits_0():
    _, _, exit_code = _invoke("--full-demo", "--dry-run")
    assert exit_code == 0


def test_full_demo_dry_run_contains_act_1():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "Act 1 / 5" in stdout


def test_full_demo_dry_run_contains_act_2():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "Act 2 / 5" in stdout


def test_full_demo_dry_run_contains_act_3():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "Act 3 / 5" in stdout


def test_full_demo_dry_run_contains_act_4():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "Act 4 / 5" in stdout


def test_full_demo_dry_run_contains_act_5():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "Act 5 / 5" in stdout


def test_full_demo_dry_run_contains_explaind():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "explaind" in stdout


def test_full_demo_dry_run_contains_ability_names():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    for name in ("balanced", "skeptical", "causal", "compressive", "exploratory", "calibrator", "devil", "updater"):
        assert name in stdout


def test_full_demo_dry_run_contains_bias_field():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "BIAS FIELD" in stdout


def test_full_demo_dry_run_contains_skeptical_and_devil():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "skeptical" in stdout
    assert "devil" in stdout


def test_full_demo_dry_run_contains_skip_message():
    stdout, _, _ = _invoke("--full-demo", "--dry-run")
    assert "[--dry-run active: skipping live inference]" in stdout


def test_full_demo_and_demo_together_exits_1():
    _, _, exit_code = _invoke("--full-demo", "--demo")
    assert exit_code == 1


def test_full_demo_and_ability_together_exits_1():
    _, _, exit_code = _invoke("--full-demo", "--ability", "skeptical")
    assert exit_code == 1


def test_full_demo_and_compare_together_exits_1():
    _, _, exit_code = _invoke("--full-demo", "--compare", "skeptical", "causal")
    assert exit_code == 1
