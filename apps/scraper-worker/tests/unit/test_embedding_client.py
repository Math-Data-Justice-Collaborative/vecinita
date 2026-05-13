"""Unit tests for embedding client behavior."""

from __future__ import annotations

import pytest

from vecinita_scraper.clients.embedding_client import EmbeddingClient


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_embedding_model_config_caches_service_metadata(monkeypatch) -> None:
    """Model metadata should be fetched once and then served from cache."""
    client = EmbeddingClient(base_url="https://embedding.example")
    calls: list[tuple[str, str]] = []

    async def fake_request(method: str, path: str, json=None):
        calls.append((method, path))
        return {"model": "test-model", "dimensions": 384, "max_tokens": 2048, "batch_size": 100}

    monkeypatch.setattr(client, "_request", fake_request)

    first = await client.fetch_embedding_model_config()
    second = await client.fetch_embedding_model_config()

    assert first.model_name == "test-model"
    assert second.max_tokens == 2048
    assert calls == [("GET", "/")]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_embed_reduces_batch_size_when_latency_is_high(monkeypatch) -> None:
    """High embedding latency should reduce future batch sizes adaptively."""
    client = EmbeddingClient(base_url="https://embedding.example")

    async def fake_fetch_config(force_refresh: bool = False):
        from vecinita_scraper.core.models import EmbeddingModelConfig

        return EmbeddingModelConfig(
            model_name="test-model", dimensions=384, max_tokens=2048, batch_size=100
        )

    async def fake_request(method: str, path: str, json=None):
        return {
            "embeddings": [[0.1] * len(json["queries"])],
            "model": "test-model",
            "dimensions": 384,
        }

    monkeypatch.setattr(client, "fetch_embedding_model_config", fake_fetch_config)
    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr("vecinita_scraper.clients.embedding_client.monotonic", lambda: 10.0)
    client._cache_time = 0.0
    client._current_batch_size = 100

    times = iter([0.0, 6.5])
    monkeypatch.setattr("vecinita_scraper.clients.embedding_client.monotonic", lambda: next(times))

    response = await client.batch_embed(["a", "b", "c"])

    assert len(response["embeddings"]) == 1
    assert client._current_batch_size == 50
