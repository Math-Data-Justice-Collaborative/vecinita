"""LLM client HTTP contract tests (ADR-009, TC-001 prep)."""

from __future__ import annotations

from typing import cast

import httpx
import pytest
from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.json_types import as_json_object


def test_generate_returns_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        import json as json_lib

        payload = as_json_object(cast(object, json_lib.loads(request.content.decode())))
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


def test_generate_stream_yields_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
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
    def handler(request: httpx.Request) -> httpx.Response:
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
    monkeypatch.delenv("VECINITA_MODAL_LLM_URL", raising=False)

    with pytest.raises(LlmClientError, match="VECINITA_MODAL_LLM_URL"):
        LlmClient(base_url=None)


def test_llm_client_context_manager_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[bool] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "ok"})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        client = base_client(
            base_url=cast(httpx.URL | str, kwargs.get("base_url", "")),
            timeout=cast(float, kwargs.get("timeout", 120.0)),
            follow_redirects=cast(bool, kwargs.get("follow_redirects", True)),
            transport=httpx.MockTransport(handler),
        )
        original_close = client.close

        def tracked_close() -> None:
            closed.append(True)
            original_close()

        client.close = tracked_close  # type: ignore[method-assign]
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)

    with LlmClient("http://llm.test") as client:
        assert client.generate("hello") == "ok"

    assert closed == [True]


def test_generate_raises_when_text_field_missing() -> None:
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
    transport = httpx.MockTransport(lambda _request: httpx.Response(503, json={}))
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    with pytest.raises(LlmClientError, match="503"):
        list(client.generate_stream("test"))
    client.close()


def test_generate_stream_skips_blank_and_non_data_lines() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        content = "\n".join(
            [
                "",
                "not-data",
                'data: {"token": "Hi"}',
                'data: {"done": true}',
            ]
        )
        return httpx.Response(200, content=content)

    transport = httpx.MockTransport(handler)
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    assert list(client.generate_stream("hello")) == ["Hi"]
    client.close()


def test_generate_stream_ignores_empty_and_non_string_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        content = "\n".join(
            [
                'data: {"token": ""}',
                'data: {"token": 123}',
                'data: {"token": "Done"}',
                'data: {"done": true}',
            ]
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
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, content=""))
    client = LlmClient(
        "http://llm.test",
        http_client=httpx.Client(transport=transport, base_url="http://llm.test"),
    )

    assert list(client.generate_stream("hello")) == []
    client.close()


def test_llm_client_does_not_close_injected_http_client() -> None:
    closed: list[bool] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"text": "ok"})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://llm.test")
    original_close = http.close

    def tracked_close() -> None:
        closed.append(True)
        original_close()

    http.close = tracked_close  # type: ignore[method-assign]
    client = LlmClient("http://llm.test", http_client=http)
    client.close()

    assert closed == []
