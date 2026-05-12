import pytest
from explaind.errors import InputError
from explaind.loader import load_input

# ---------------------------------------------------------------------------
# No input
# ---------------------------------------------------------------------------

def test_no_file_no_stdin_raises():
    with pytest.raises(InputError, match="No input provided"):
        load_input()


def test_none_file_none_stdin_raises():
    with pytest.raises(InputError, match="No input provided"):
        load_input(file_path=None, stdin_text=None)


# ---------------------------------------------------------------------------
# Empty / whitespace-only content
# ---------------------------------------------------------------------------

def test_empty_stdin_raises():
    with pytest.raises(InputError, match="No input provided"):
        load_input(stdin_text="")


def test_whitespace_stdin_raises():
    with pytest.raises(InputError, match="No input provided"):
        load_input(stdin_text="   \n\t  ")


def test_empty_file_raises(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    with pytest.raises(InputError, match="No input provided"):
        load_input(file_path=str(f))


def test_whitespace_file_raises(tmp_path):
    f = tmp_path / "ws.txt"
    f.write_text("   \n\n   ")
    with pytest.raises(InputError, match="No input provided"):
        load_input(file_path=str(f))


# ---------------------------------------------------------------------------
# File errors
# ---------------------------------------------------------------------------

def test_missing_file_raises(tmp_path):
    missing = str(tmp_path / "ghost.txt")
    with pytest.raises(InputError, match="no such file"):
        load_input(file_path=missing)


def test_missing_file_message_contains_path(tmp_path):
    missing = str(tmp_path / "ghost.txt")
    with pytest.raises(InputError) as exc:
        load_input(file_path=missing)
    assert "ghost.txt" in str(exc.value)


def test_unreadable_file_raises(tmp_path):
    f = tmp_path / "locked.txt"
    f.write_text("content")
    f.chmod(0o000)
    try:
        with pytest.raises(InputError, match="permission denied"):
            load_input(file_path=str(f))
    finally:
        f.chmod(0o644)


# ---------------------------------------------------------------------------
# Valid input
# ---------------------------------------------------------------------------

def test_valid_stdin_returns_stripped():
    result = load_input(stdin_text="  hello world  ")
    assert result == "hello world"


def test_valid_file_returns_stripped(tmp_path):
    f = tmp_path / "input.txt"
    f.write_text("  some log line  \n")
    result = load_input(file_path=str(f))
    assert result == "some log line"


def test_internal_formatting_preserved(tmp_path):
    f = tmp_path / "multiline.txt"
    f.write_text("line one\n  indented\nline three")
    result = load_input(file_path=str(f))
    assert result == "line one\n  indented\nline three"


# ---------------------------------------------------------------------------
# File takes precedence over stdin
# ---------------------------------------------------------------------------

def test_file_takes_precedence_over_stdin(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("from file")
    result = load_input(file_path=str(f), stdin_text="from stdin")
    assert result == "from file"


def test_file_takes_precedence_even_when_stdin_nonempty(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("file wins")
    result = load_input(file_path=str(f), stdin_text="stdin loses")
    assert result != "stdin loses"
    assert result == "file wins"
