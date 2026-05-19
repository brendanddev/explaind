import json
import pytest
from unittest.mock import MagicMock, patch
from explaind.config import Config, DEFAULTS
from explaind.errors import ConfigError, ModelInvocationError
from explaind.invoker import OllamaInvoker, LlamaCppInvoker, build_invoker


# ---------------------------------------------------------------------------
# build_invoker factory
# ---------------------------------------------------------------------------

def _cfg(**overrides) -> Config:
    fields = {
        "model_backend": DEFAULTS.model_backend,
        "model_name": DEFAULTS.model_name,
        "max_tokens": DEFAULTS.max_tokens,
        "temperature": DEFAULTS.temperature,
    }
    fields.update(overrides)
    return Config(**fields)


def test_build_invoker_ollama_returns_ollama_invoker():
    cfg = _cfg(model_backend="ollama")
    assert isinstance(build_invoker(cfg), OllamaInvoker)


def test_build_invoker_llamacpp_raises_config_error():
    cfg = _cfg(model_backend="llamacpp")
    with pytest.raises(ConfigError, match="not yet implemented"):
        build_invoker(cfg)


def test_build_invoker_unknown_backend_raises():
    cfg = _cfg(model_backend="unknown")
    with pytest.raises(ConfigError, match="unknown model_backend"):
        build_invoker(cfg)


# ---------------------------------------------------------------------------
# OllamaInvoker
# ---------------------------------------------------------------------------

def _mock_response(text: str):
    body = json.dumps({"response": text}).encode()
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = body
    return mock


def test_ollama_invoker_returns_response_text():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("hello world")
        result = invoker.invoke("some prompt")
    assert result == "hello world"


def test_ollama_invoker_sends_correct_payload():
    invoker = OllamaInvoker(model="mymodel", temperature=0.5, max_tokens=256)
    captured = {}

    def fake_open(req):
        captured["payload"] = json.loads(req.data)
        return _mock_response("ok")

    with patch("explaind.invoker.urllib.request.urlopen", side_effect=fake_open):
        invoker.invoke("test prompt")

    assert captured["payload"]["model"] == "mymodel"
    assert captured["payload"]["prompt"] == "test prompt"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["raw"] is True
    assert captured["payload"]["options"]["temperature"] == 0.5
    assert captured["payload"]["options"]["num_predict"] == 256


def test_ollama_invoker_url_error_raises_model_invocation_error():
    import urllib.error
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen",
               side_effect=urllib.error.URLError("connection refused")):
        with pytest.raises(ModelInvocationError, match="Ollama unreachable"):
            invoker.invoke("prompt")


def test_ollama_invoker_missing_response_key_raises():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    body = json.dumps({"other_field": "value"}).encode()
    mock = MagicMock()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = body
    with patch("explaind.invoker.urllib.request.urlopen", return_value=mock):
        with pytest.raises(ModelInvocationError, match="missing 'response' field"):
            invoker.invoke("prompt")


# ---------------------------------------------------------------------------
# OllamaInvoker — Gemma 4 special-token stripping
# ---------------------------------------------------------------------------

def test_ollama_invoker_strips_eos_token():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("hello<eos> world")
        result = invoker.invoke("prompt")
    assert "<eos>" not in result
    assert "hello" in result
    assert "world" in result


def test_ollama_invoker_strips_end_of_turn_token():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("hello</start_of_turn> world")
        result = invoker.invoke("prompt")
    assert "</start_of_turn>" not in result


def test_ollama_invoker_strips_tool_response_token():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("answer<|tool_response>garbage")
        result = invoker.invoke("prompt")
    assert "<|tool_response>" not in result


def test_ollama_invoker_strip_thinking_false_preserves_content():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128, strip_thinking=False)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("before<|channel>thoughtinner content<channel|>after")
        result = invoker.invoke("prompt")
    assert "inner content" in result
    assert "<|channel>thought" not in result
    assert "<channel|>" not in result


def test_ollama_invoker_strip_thinking_true_removes_trace():
    invoker = OllamaInvoker(model="test-model", temperature=0.0, max_tokens=128)
    with patch("explaind.invoker.urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_response("before<|channel>thoughtinner content<channel|>after")
        result = invoker.invoke("prompt")
    assert "inner content" not in result
    assert "<|channel>thought" not in result
    assert "<channel|>" not in result


# ---------------------------------------------------------------------------
# LlamaCppInvoker
# ---------------------------------------------------------------------------

def test_llamacpp_invoker_raises_config_error_at_construction():
    with pytest.raises(ConfigError, match="not yet implemented"):
        LlamaCppInvoker(model="test", temperature=0.0, max_tokens=128)
