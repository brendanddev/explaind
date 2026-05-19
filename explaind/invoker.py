from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from explaind.config import Config
from explaind.errors import ConfigError, ModelInvocationError

_OLLAMA_URL = "http://localhost:11434/api/generate"

# More-specific tokens must come before their prefixes to avoid partial matches.
_GEMMA_SPECIAL_TOKENS = [
    "<start_of_turn>user",
    "<start_of_turn>model",
    "<start_of_turn>",
    "</start_of_turn>",
    "<end_of_turn>",
    "</end_of_turn>",
    "<|channel>thought",
    "<channel|>",
    "<|tool_response>",
    "<eos>",
]


def _strip_gemma_output(text: str, strip_thinking: bool = True) -> str:
    if strip_thinking:
        text = re.sub(r"<\|channel>thought.*?<channel\|>", "", text, flags=re.DOTALL)
    for token in _GEMMA_SPECIAL_TOKENS:
        text = text.replace(token, "")
    text = re.sub(r"(?m)^model\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class ModelInvoker:
    def invoke(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaInvoker(ModelInvoker):
    def __init__(self, model: str, temperature: float, max_tokens: int, strip_thinking: bool = True) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._strip_thinking = strip_thinking

    def invoke(self, prompt: str) -> str:
        payload = json.dumps({
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "raw": True,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
            },
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
            raw = body["response"]
        except (KeyError, TypeError):
            raise ModelInvocationError("Ollama response missing 'response' field")

        return _strip_gemma_output(raw, strip_thinking=self._strip_thinking)


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
