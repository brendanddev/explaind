"""Tests for the --file flag."""
from __future__ import annotations

import io
import sys
from unittest.mock import patch

import pytest

from explaind.cli import main


def _invoke(*args):
    """Run main() with the given argv args, return (stdout, stderr, exit_code)."""
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


def test_file_flag_reads_content(tmp_path):
    f = tmp_path / "input.txt"
    f.write_text("hello from file flag")
    stdout, _, exit_code = _invoke("--file", str(f), "--dry-run")
    assert exit_code == 0
    assert "hello from file flag" in stdout


def test_file_flag_nonexistent_path_exits_1(tmp_path):
    _, stderr, exit_code = _invoke("--file", str(tmp_path / "ghost.txt"), "--dry-run")
    assert exit_code == 1
    assert "no such file" in stderr


def test_file_flag_empty_file_exits_1(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    _, stderr, exit_code = _invoke("--file", str(f), "--dry-run")
    assert exit_code == 1
    assert "No input provided" in stderr
