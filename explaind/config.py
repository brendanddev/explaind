from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from explaind.errors import ConfigError

_CONFIG_FILE = "explaind.toml"
_VALID_BACKENDS = frozenset({"ollama", "llamacpp"})
_KNOWN_KEYS = frozenset({"model_backend", "model_name", "max_tokens", "temperature"})


@dataclass(frozen=True)
class Config:
    model_backend: str
    model_name: str
    max_tokens: int
    temperature: float


DEFAULTS = Config(
    model_backend="ollama",
    model_name="gemma4-e2b_q4_k_m:latest",
    max_tokens=2048,
    temperature=0.0,
)


def load_config(path: Path = Path(_CONFIG_FILE)) -> Config:
    """Return a Config, loading from path if it exists.

    Missing file → DEFAULTS.  Present file → strict validation, ConfigError on any problem.
    """
    if not path.exists():
        return DEFAULTS

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}")

    unknown = set(raw.keys()) - _KNOWN_KEYS
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")

    backend = raw.get("model_backend", DEFAULTS.model_backend)
    if backend not in _VALID_BACKENDS:
        raise ConfigError(
            f"model_backend must be one of {sorted(_VALID_BACKENDS)}, got {backend!r}"
        )

    model_name = raw.get("model_name", DEFAULTS.model_name)
    if not isinstance(model_name, str) or not model_name.strip():
        raise ConfigError("model_name must be a non-empty string")

    max_tokens = raw.get("max_tokens", DEFAULTS.max_tokens)
    if not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0:
        raise ConfigError("max_tokens must be a positive integer")

    temperature = raw.get("temperature", DEFAULTS.temperature)
    if not isinstance(temperature, (int, float)) or isinstance(temperature, bool):
        raise ConfigError("temperature must be a number")
    temperature = float(temperature)
    if not (0.0 <= temperature <= 2.0):
        raise ConfigError("temperature must be between 0.0 and 2.0")

    return Config(
        model_backend=backend,
        model_name=model_name.strip(),
        max_tokens=max_tokens,
        temperature=temperature,
    )
