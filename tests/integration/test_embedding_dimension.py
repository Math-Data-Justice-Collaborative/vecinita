"""Verify embedding client enforces 384-dim vectors (data-management-plan §Verification)."""

from __future__ import annotations

import httpx
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClient

_SAMPLE_VALUE = 0.05
_SAMPLE = [_SAMPLE_VALUE] * EMBEDDING_DIMENSION


def test_embedding_client_integration_mocked_http() -> None:
    """EmbeddingClient returns 384-dim vectors from mocked HTTP responses."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Handler."""
        if request.url.path == "/embed":
            return httpx.Response(200, json={"embedding": _SAMPLE})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    with EmbeddingClient(
        "http://vecinita-embedding.test",
        http_client=httpx.Client(transport=transport, base_url="http://vecinita-embedding.test"),
    ) as client:
        vector = client.embed("community pantry hours")
    assert len(vector) == EMBEDDING_DIMENSION
    assert vector[0] == _SAMPLE_VALUE
