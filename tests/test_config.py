import pytest
from pathlib import Path
from explaind.config import load_config, DEFAULTS, Config
from explaind.errors import ConfigError


# ---------------------------------------------------------------------------
# Missing file → defaults
# ---------------------------------------------------------------------------

def test_missing_config_returns_defaults(tmp_path):
    result = load_config(tmp_path / "explaind.toml")
    assert result == DEFAULTS


def test_defaults_backend_is_ollama():
    assert DEFAULTS.model_backend == "ollama"


def test_defaults_temperature_is_zero():
    assert DEFAULTS.temperature == 0.0


# ---------------------------------------------------------------------------
# Valid config
# ---------------------------------------------------------------------------

def test_valid_full_config(tmp_path):
    (tmp_path / "explaind.toml").write_text(
        'model_backend = "ollama"\n'
        'model_name = "mymodel:latest"\n'
        "max_tokens = 512\n"
        "temperature = 0.7\n"
    )
    cfg = load_config(tmp_path / "explaind.toml")
    assert cfg.model_backend == "ollama"
    assert cfg.model_name == "mymodel:latest"
    assert cfg.max_tokens == 512
    assert cfg.temperature == pytest.approx(0.7)


def test_valid_llamacpp_backend(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_backend = "llamacpp"\n')
    cfg = load_config(tmp_path / "explaind.toml")
    assert cfg.model_backend == "llamacpp"


def test_partial_config_fills_defaults(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_backend = "ollama"\n')
    cfg = load_config(tmp_path / "explaind.toml")
    assert cfg.max_tokens == DEFAULTS.max_tokens
    assert cfg.temperature == DEFAULTS.temperature


def test_temperature_zero_is_valid(tmp_path):
    (tmp_path / "explaind.toml").write_text("temperature = 0.0\n")
    cfg = load_config(tmp_path / "explaind.toml")
    assert cfg.temperature == 0.0


def test_temperature_two_is_valid(tmp_path):
    (tmp_path / "explaind.toml").write_text("temperature = 2.0\n")
    cfg = load_config(tmp_path / "explaind.toml")
    assert cfg.temperature == 2.0


def test_returns_config_dataclass(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_backend = "ollama"\n')
    cfg = load_config(tmp_path / "explaind.toml")
    assert isinstance(cfg, Config)


# ---------------------------------------------------------------------------
# Invalid TOML
# ---------------------------------------------------------------------------

def test_invalid_toml_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text("model_backend = [[[broken\n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(tmp_path / "explaind.toml")


# ---------------------------------------------------------------------------
# Invalid field values
# ---------------------------------------------------------------------------

def test_invalid_backend_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_backend = "openai"\n')
    with pytest.raises(ConfigError, match="model_backend"):
        load_config(tmp_path / "explaind.toml")


def test_empty_model_name_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_name = ""\n')
    with pytest.raises(ConfigError, match="model_name"):
        load_config(tmp_path / "explaind.toml")


def test_whitespace_model_name_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text('model_name = "   "\n')
    with pytest.raises(ConfigError, match="model_name"):
        load_config(tmp_path / "explaind.toml")


def test_zero_max_tokens_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text("max_tokens = 0\n")
    with pytest.raises(ConfigError, match="max_tokens"):
        load_config(tmp_path / "explaind.toml")


def test_negative_max_tokens_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text("max_tokens = -1\n")
    with pytest.raises(ConfigError, match="max_tokens"):
        load_config(tmp_path / "explaind.toml")


def test_temperature_below_range_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text("temperature = -0.1\n")
    with pytest.raises(ConfigError, match="temperature"):
        load_config(tmp_path / "explaind.toml")


def test_temperature_above_range_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text("temperature = 2.1\n")
    with pytest.raises(ConfigError, match="temperature"):
        load_config(tmp_path / "explaind.toml")


# ---------------------------------------------------------------------------
# Unknown keys
# ---------------------------------------------------------------------------

def test_unknown_key_raises(tmp_path):
    (tmp_path / "explaind.toml").write_text('mystery_key = "value"\n')
    with pytest.raises(ConfigError, match="unknown config keys"):
        load_config(tmp_path / "explaind.toml")
