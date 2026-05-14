import pytest
from unittest.mock import patch
from explaind.main import load_ability, ALLOWED_ABILITIES


def test_invalid_ability_raises():
    with pytest.raises(ValueError, match="unknown ability"):
        load_ability("nonexistent")


def test_invalid_ability_error_lists_allowed():
    with pytest.raises(ValueError, match="allowed:"):
        load_ability("nonexistent")


def test_missing_file_raises(tmp_path):
    valid = next(iter(sorted(ALLOWED_ABILITIES)))
    with patch("explaind.main.ABILITIES_DIR", tmp_path):
        with pytest.raises(ValueError, match="ability file missing"):
            load_ability(valid)


def test_all_allowed_abilities_load():
    for ability in ALLOWED_ABILITIES:
        content = load_ability(ability)
        assert isinstance(content, str)
        assert len(content) > 0


def test_allowed_abilities_set_contains_eight():
    assert len(ALLOWED_ABILITIES) == 8


def test_allowed_abilities_set_contents():
    assert ALLOWED_ABILITIES == {
        "balanced", "skeptical", "causal", "compressive", "exploratory",
        "calibrator", "devil", "updater",
    }


def test_empty_string_is_not_a_valid_ability():
    with pytest.raises(ValueError, match="unknown ability"):
        load_ability("")
