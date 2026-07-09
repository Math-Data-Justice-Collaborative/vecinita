"""LLM client HTTP contract tests (ADR-009, TC-001 prep)."""

from __future__ import annotations

import json as json_lib
from typing import cast

import httpx
import pytest
from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.json_types import (
    as_json_object,
)


def test_generate_returns_text() -> None:
    """Generate posts the prompt and returns the response text."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert request.url.path == "/generate"
        assert payload["prompt"] == "Answer briefly: food pantry hours?"
        return httpx.Response(200, json={"text": "Hours are posted on Monday."})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    text = client.generate("Answer briefly: food pantry hours?")
    assert "Monday" in text
    client.close()


def test_generate_includes_model_id_and_proxy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generate forwards model_id and proxy auth for vecinita-llm (ADR-037)."""
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "llama3.2:3b"
        assert request.headers.get("X-Vecinita-Proxy-Key") == "proxy-secret"
        return httpx.Response(200, json={"text": "Routed answer."})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        model_id="llama3.2:3b",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    assert client.generate("hello") == "Routed answer."
    client.close()


def test_generate_includes_model_id_for_unified_llm_endpoint() -> None:
    """vecinita-llm accepts model_id on /generate (ADR-037)."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "qwen2.5:1.5b-instruct"
        return httpx.Response(200, json={"text": "vllm answer"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "https://vecinita--vecinita-llm-fastapi-app.modal.run",
        model_id="qwen2.5:1.5b-instruct",
        http_client=httpx.Client(
            transport=transport,
            base_url="https://vecinita--vecinita-llm-fastapi-app.modal.run",
        ),
    )
    assert client.generate("hello", model_id="qwen2.5:1.5b-instruct") == "vllm answer"
    client.close()


def test_generate_allows_per_call_model_id_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Per-call model_id overrides the client default."""
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "mistral:7b"
        return httpx.Response(200, json={"text": "override"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        model_id="llama3.2:3b",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    assert client.generate("hello", model_id="mistral:7b") == "override"
    client.close()


def test_llm_client_requires_base_url_or_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM client raises when neither base URL nor env var is set."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_OLLAMA_URL", raising=False)

    with pytest.raises(LlmClientError, match="VECINITA_MODAL_LLM_URL"):
        LlmClient(base_url=None)


def test_generate_stream_yields_tokens() -> None:
    """Generate-stream yields tokens parsed from the SSE stream."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        assert request.url.path == "/generate/stream"
        lines = [
            'data: {"token": "Hello "}\n\n',
            'data: {"token": "world"}\n\n',
            'data: {"done": true}\n\n',
        ]
        return httpx.Response(200, content="".join(lines))

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    tokens = list(client.generate_stream("hi"))
    assert tokens == ["Hello ", "world"]
    client.close()


def test_generate_raises_on_http_error() -> None:
    """Generate raises when the server responds with an HTTP error status."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(503, json={"detail": "gpu unavailable"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    with pytest.raises(LlmClientError, match="503"):
        client.generate("test")
    client.close()


def test_llm_client_context_manager_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Context manager closes the HTTP client it created itself."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"text": "ok"})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        """Client factory."""
        client = base_client(
            base_url=cast("httpx.URL | str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 120.0)),
            follow_redirects=cast("bool", kwargs.get("follow_redirects", True)),
            transport=httpx.MockTransport(handler),
        )
        original_close = client.close

        def tracked_close() -> None:
            """Tracked close."""
            closed.append(True)
            original_close()

        client.close = tracked_close  # type: ignore[method-assign]
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)

    with LlmClient("http://llm.test") as client:
        assert client.generate("hello") == "ok"

    assert closed == [True]


def test_generate_raises_when_text_field_missing() -> None:
    """Generate raises when the response is missing the text field."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"unexpected": "value"}),
    )
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    with pytest.raises(LlmClientError, match="text"):
        client.generate("test")
    client.close()


def test_generate_stream_raises_on_http_error() -> None:
    """Generate-stream raises when the server responds with an error status."""
    transport = httpx.MockTransport(lambda _request: httpx.Response(503, json={}))
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    with pytest.raises(LlmClientError, match="503"):
        list(client.generate_stream("test"))
    client.close()


def test_generate_stream_skips_blank_and_non_data_lines() -> None:
    """Generate-stream ignores blank and non-data SSE lines."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        content = '\nnot-data\ndata: {"token": "Hi"}\ndata: {"done": true}'
        return httpx.Response(200, content=content)

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    assert list(client.generate_stream("hello")) == ["Hi"]
    client.close()


def test_generate_stream_ignores_empty_and_non_string_tokens() -> None:
    """Generate-stream skips empty and non-string token values."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        content = (
            'data: {"token": ""}\n'
            'data: {"token": 123}\n'
            'data: {"token": "Done"}\n'
            'data: {"done": true}'
        )
        return httpx.Response(200, content=content)

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    assert list(client.generate_stream("hello")) == ["Done"]
    client.close()


def test_generate_stream_returns_no_tokens_when_body_empty() -> None:
    """Generate-stream yields nothing when the response body is empty."""
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, content=""))
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    assert list(client.generate_stream("hello")) == []
    client.close()


def test_llm_client_falls_back_to_legacy_ollama_url_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Legacy VECINITA_MODAL_OLLAMA_URL still resolves base URL with a deprecation warning."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)
    monkeypatch.setenv("VECINITA_MODAL_OLLAMA_URL", "http://legacy-ollama.test")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "legacy"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        http_client=httpx.Client(transport=transport, base_url="http://legacy-ollama.test"),
    )
    assert client.generate("hello") == "legacy"
    assert "VECINITA_MODAL_OLLAMA_URL is deprecated" in caplog.text
    client.close()


def test_llm_client_default_model_id_from_legacy_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VECINITA_OLLAMA_MODEL_ID is used when VECINITA_LLM_MODEL_ID is unset."""
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://llm.test")
    monkeypatch.delenv("VECINITA_LLM_MODEL_ID", raising=False)
    monkeypatch.setenv("VECINITA_OLLAMA_MODEL_ID", "llama3.2:3b")

    client = LlmClient("http://llm.test")
    assert client.default_model_id == "llama3.2:3b"
    client.close()


def test_warm_posts_model_id_when_configured() -> None:
    """warm() POSTs /warm with the client default model_id when set."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/warm"
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "qwen2.5:1.5b-instruct"
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        model_id="qwen2.5:1.5b-instruct",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client.warm()
    client.close()


def test_warm_posts_empty_body_without_default_model() -> None:
    """warm() POSTs an empty JSON body when no default model is configured."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/warm"
        assert request.content == b"{}"
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    client.warm()
    client.close()


def test_generate_without_proxy_key_omits_auth_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generate omits proxy auth when no proxy key is configured."""
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Vecinita-Proxy-Key") is None
        return httpx.Response(200, json={"text": "open"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )
    assert client.generate("hello") == "open"
    client.close()


def test_llm_client_does_not_close_injected_http_client() -> None:
    """Closing the client must not close an externally injected HTTP client."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"text": "ok"})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://llm.test")
    original_close = http.close

    def tracked_close() -> None:
        """Tracked close."""
        closed.append(True)
        original_close()

    http.close = tracked_close  # type: ignore[method-assign]
    client = LlmClient("http://llm.test", http_client=http)
    client.close()

    assert closed == []
