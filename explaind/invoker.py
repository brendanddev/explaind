from __future__ import annotations

import json
import urllib.error
import urllib.request

from explaind.config import Config
from explaind.errors import ConfigError, ModelInvocationError

_OLLAMA_URL = "http://localhost:11434/api/generate"


class ModelInvoker:
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaInvoker(ModelInvoker):
    def __init__(self, model: str, temperature: float, max_tokens: int) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def invoke(self, prompt: str) -> str:
        payload = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "temperature": self._temperature,
            "num_predict": self._max_tokens,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            _OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise ModelInvocationError(f"Ollama unreachable: {exc.reason}")
        except Exception as exc:
            raise ModelInvocationError(f"Ollama request failed: {exc}")

        try:
            return body["response"]
        except (KeyError, TypeError):
            raise ModelInvocationError("Ollama response missing 'response' field")


class LlamaCppInvoker(ModelInvoker):
    def __init__(self, model: str, temperature: float, max_tokens: int) -> None:
        raise ConfigError(
            "llama.cpp backend is not yet implemented. "
            "Set model_backend = 'ollama' in explaind.toml."
        )

    def invoke(self, prompt: str) -> str:
        raise ModelInvocationError("llama.cpp backend not yet implemented")


def build_invoker(config: Config) -> ModelInvoker:
    if config.model_backend == "ollama":
        return OllamaInvoker(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    if config.model_backend == "llamacpp":
        return LlamaCppInvoker(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    raise ConfigError(f"unknown model_backend: {config.model_backend!r}")
