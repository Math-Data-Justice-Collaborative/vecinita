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


def test_generate_includes_model_id_and_proxy_key() -> None:
    """Generate forwards model_id and proxy auth for Modal Ollama."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "llama3.2:3b"
        assert request.headers.get("X-Vecinita-Proxy-Key") == "proxy-secret"
        return httpx.Response(200, json={"text": "Routed answer."})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://ollama.test",
        model_id="llama3.2:3b",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    assert client.generate("hello") == "Routed answer."
    client.close()


def test_generate_omits_model_id_for_vllm_endpoint() -> None:
    """vecinita-llm GenerateRequest rejects model_id (extra=forbid)."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert "model_id" not in payload
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


def test_generate_allows_per_call_model_id_override() -> None:
    """Per-call model_id overrides the client default."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json_lib.loads(request.content.decode())))
        assert payload["model_id"] == "mistral:7b"
        return httpx.Response(200, json={"text": "override"})

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://ollama.test",
        model_id="llama3.2:3b",
        proxy_key="proxy-secret",
        http_client=httpx.Client(transport=transport, base_url="http://ollama.test"),
    )
    assert client.generate("hello", model_id="mistral:7b") == "override"
    client.close()


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


def test_llm_client_requires_base_url_or_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """LLM client raises when neither base URL nor env var is set."""
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)

    with pytest.raises(LlmClientError, match="VECINITA_MODAL_OLLAMA_URL"):
        LlmClient(base_url=None)


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
