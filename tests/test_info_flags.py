import io
import sys
from unittest.mock import patch

from explaind.cli import main
from explaind.main import ALLOWED_ABILITIES
from explaind.presets import PRESET_MAP


def _invoke(*args):
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exit_code = 0
    with patch("sys.argv", ["explaind"] + list(args)), \
         patch("sys.stdout", stdout_buf), \
         patch("sys.stderr", stderr_buf), \
         patch("sys.stdin.isatty", return_value=True):
        try:
            main()
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


# ---------------------------------------------------------------------------
# --list-abilities
# ---------------------------------------------------------------------------


def test_list_abilities_exits_0():
    _, _, exit_code = _invoke("--list-abilities")
    assert exit_code == 0


def test_list_abilities_contains_all_8_names():
    stdout, _, _ = _invoke("--list-abilities")
    for name in ALLOWED_ABILITIES:
        assert name in stdout


def test_list_abilities_contains_skeptical():
    stdout, _, _ = _invoke("--list-abilities")
    assert "skeptical" in stdout


def test_list_abilities_contains_calibrator():
    stdout, _, _ = _invoke("--list-abilities")
    assert "calibrator" in stdout


def test_list_abilities_no_input_required():
    stdout, _, exit_code = _invoke("--list-abilities")
    assert exit_code == 0
    assert len(stdout) > 0


def test_list_abilities_output_contains_descriptions():
    stdout, _, _ = _invoke("--list-abilities")
    assert "Epistemic pressure" in stdout
    assert "Bayesian" in stdout


# ---------------------------------------------------------------------------
# --examples
# ---------------------------------------------------------------------------


def test_examples_exits_0():
    _, _, exit_code = _invoke("--examples")
    assert exit_code == 0


def test_examples_contains_compare():
    stdout, _, _ = _invoke("--examples")
    assert "--compare" in stdout


def test_examples_contains_scaffold():
    stdout, _, _ = _invoke("--examples")
    assert "--scaffold" in stdout


def test_examples_contains_consensus():
    stdout, _, _ = _invoke("--examples")
    assert "--consensus" in stdout


def test_examples_no_input_required():
    stdout, _, exit_code = _invoke("--examples")
    assert exit_code == 0
    assert len(stdout) > 0


def test_examples_contains_section_headers():
    stdout, _, _ = _invoke("--examples")
    assert "BASIC USAGE" in stdout
    assert "REASONING CHAINS" in stdout
    assert "EXPORT" in stdout


# ---------------------------------------------------------------------------
# --about
# ---------------------------------------------------------------------------


def test_about_exits_0():
    _, _, exit_code = _invoke("--about")
    assert exit_code == 0


def test_about_contains_explaind():
    stdout, _, _ = _invoke("--about")
    assert "explaind" in stdout


def test_about_contains_bias_field():
    stdout, _, _ = _invoke("--about")
    assert "BIAS FIELD" in stdout


def test_about_contains_wang_et_al():
    stdout, _, _ = _invoke("--about")
    assert "Wang et al." in stdout


def test_about_no_input_required():
    stdout, _, exit_code = _invoke("--about")
    assert exit_code == 0
    assert len(stdout) > 0


def test_about_contains_cognitive_steering():
    stdout, _, _ = _invoke("--about")
    assert "cognitive steering layer" in stdout


# ---------------------------------------------------------------------------
# Coexistence: --list-abilities and --list-presets both work together
# ---------------------------------------------------------------------------


def test_list_abilities_and_list_presets_no_conflict():
    _, _, exit_code = _invoke("--list-abilities", "--list-presets")
    assert exit_code == 0


def test_list_abilities_and_list_presets_both_output():
    stdout, _, exit_code = _invoke("--list-abilities", "--list-presets")
    assert exit_code == 0
    assert "skeptical" in stdout
    assert "philosopher" in stdout


def test_list_abilities_alone_does_not_print_presets():
    stdout, _, _ = _invoke("--list-abilities")
    for preset in PRESET_MAP:
        assert preset not in stdout
