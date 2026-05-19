"""Embedding client HTTP contract tests (ADR-008)."""

from __future__ import annotations

import httpx
import pytest
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClient, EmbeddingClientError

_SAMPLE = [0.1] * EMBEDDING_DIMENSION


def test_embed_single_returns_384_dimensions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        import json

        assert request.method == "POST"
        assert request.url.path == "/embed"
        payload = json.loads(request.content.decode())
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
    def handler(request: httpx.Request) -> httpx.Response:
        import json

        payload = json.loads(request.content.decode())
        assert request.url.path == "/embed/batch"
        assert payload == {"texts": ["a", "b"]}
        return httpx.Response(200, json={"embeddings": [_SAMPLE, _SAMPLE]})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    vectors = client.embed_batch(["a", "b"])
    assert len(vectors) == 2
    assert all(len(v) == EMBEDDING_DIMENSION for v in vectors)
    client.close()


def test_embed_raises_on_wrong_dimension() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
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
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "unavailable"})

    transport = httpx.MockTransport(handler)
    client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    with pytest.raises(EmbeddingClientError, match="503"):
        client.embed("x")
    client.close()
