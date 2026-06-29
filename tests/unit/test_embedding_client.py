"""Embedding client HTTP contract tests (ADR-008)."""

from __future__ import annotations

import json
from typing import cast

import httpx
import pytest
from vecinita_embedding_client import (
    EMBEDDING_DIMENSION,
    EmbeddingClient,
    EmbeddingClientError,
)
from vecinita_shared_schemas.json_types import (
    as_json_object,
)

_SAMPLE = [0.1] * EMBEDDING_DIMENSION
_EXPECTED_BATCH_COUNT = 2


def test_embed_single_returns_384_dimensions() -> None:
    """Embed returns a vector with the expected dimension for one text."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        assert request.method == "POST"
        assert request.url.path == "/embed"
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert payload == {"text": "hello world"}
        return httpx.Response(200, json={"embedding": _SAMPLE})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vector = client.embed("hello world")
    assert len(vector) == EMBEDDING_DIMENSION
    client.close()


def test_embed_batch_returns_list_of_384_vectors() -> None:
    """Embed batch returns one vector per input text."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        assert request.url.path == "/embed/batch"
        assert payload == {"texts": ["a", "b"]}
        return httpx.Response(200, json={"embeddings": [_SAMPLE, _SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vectors = client.embed_batch(["a", "b"])
    assert len(vectors) == _EXPECTED_BATCH_COUNT
    assert all(len(v) == EMBEDDING_DIMENSION for v in vectors)
    client.close()


def test_embed_raises_on_wrong_dimension() -> None:
    """Embed raises when the server returns a wrong-dimension vector."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": [0.1, 0.2]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="384"):
        client.embed("x")
    client.close()


def test_embed_raises_on_http_error() -> None:
    """Embed raises when the server responds with an HTTP error status."""

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(503, json={"detail": "unavailable"})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="503"):
        client.embed("x")
    client.close()


def test_embedding_client_requires_base_url_or_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Embedding client raises when neither base URL nor env var is set."""
    monkeypatch.delenv("VECINITA_MODAL_EMBED_URL", raising=False)

    with pytest.raises(EmbeddingClientError, match="VECINITA_MODAL_EMBED_URL"):
        EmbeddingClient(base_url=None)


def test_embedding_client_context_manager_closes_owned_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Context manager closes the HTTP client it created itself."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": _SAMPLE})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        """Client factory."""
        client = base_client(
            base_url=cast("httpx.URL | str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 30.0)),
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

    with EmbeddingClient("http://embed.test") as client:
        assert client.embed("hello") == _SAMPLE

    assert closed == [True]


def test_embed_raises_when_embedding_field_missing() -> None:
    """Embed raises when the response is missing the embedding field."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"unexpected": []}),
    )
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="embedding"):
        client.embed("x")
    client.close()


def test_embed_batch_raises_on_http_error() -> None:
    """Embed batch raises when the server responds with an HTTP error status."""
    transport = httpx.MockTransport(lambda _request: httpx.Response(502, json={}))
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="502"):
        client.embed_batch(["a"])
    client.close()


def test_embed_batch_raises_when_embeddings_field_missing() -> None:
    """Embed batch raises when the response is missing the embeddings field."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"unexpected": []}),
    )
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )

    with pytest.raises(EmbeddingClientError, match="embeddings"):
        client.embed_batch(["a"])
    client.close()


def test_embedding_client_does_not_close_injected_http_client() -> None:
    """Closing the client must not close an externally injected HTTP client."""
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        """Handler."""
        return httpx.Response(200, json={"embedding": _SAMPLE})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport, base_url="http://embed.test")
    original_close = http.close

    def tracked_close() -> None:
        """Tracked close."""
        closed.append(True)
        original_close()

    http.close = tracked_close  # type: ignore[method-assign]
    client = EmbeddingClient("http://embed.test", http_client=http)
    client.close()

    assert closed == []
