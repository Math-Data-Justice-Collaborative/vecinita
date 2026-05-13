from __future__ import annotations

import pytest

from tests.fakes import FailingEmbedder, FakeEmbedder
from vecinita.constants import DEFAULT_MODEL
from vecinita.service import EmbeddingExecutionError, EmbeddingService, EmptyQueryError


def test_embed_query_returns_embedding_response() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1, 2, 3]]))

    response = service.embed_query("hello world")

    assert response.embedding == [1.0, 2.0, 3.0]
    assert response.model == DEFAULT_MODEL
    assert response.dimensions == 3


def test_embed_query_uses_requested_model_name() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1, 2]]))

    response = service.embed_query("hello world", model="custom-model")

    assert response.model == "custom-model"


def test_embed_query_rejects_empty_text() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1, 2]]))

    with pytest.raises(EmptyQueryError, match="Query must not be empty"):
        service.embed_query("   ")


def test_embed_query_wraps_backend_failures() -> None:
    service = EmbeddingService(FailingEmbedder())

    with pytest.raises(EmbeddingExecutionError, match="backend unavailable"):
        service.embed_query("hello world")


def test_embed_batch_returns_response() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1, 2], [3, 4]]))

    response = service.embed_batch(["alpha", "beta"])

    assert response.embeddings == [[1.0, 2.0], [3.0, 4.0]]
    assert response.dimensions == 2
    assert response.model == DEFAULT_MODEL


def test_embed_batch_uses_requested_model_name() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1], [2]]))

    response = service.embed_batch(["alpha", "beta"], model="batch-model")

    assert response.model == "batch-model"


def test_embed_batch_rejects_empty_indices() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[[1], [2]]))

    with pytest.raises(EmptyQueryError, match=r"\[1\]"):
        service.embed_batch(["alpha", "  "])


def test_embed_batch_wraps_backend_failures() -> None:
    service = EmbeddingService(FailingEmbedder())

    with pytest.raises(EmbeddingExecutionError, match="backend unavailable"):
        service.embed_batch(["alpha", "beta"])


def test_embed_batch_handles_empty_result_set() -> None:
    service = EmbeddingService(FakeEmbedder(vectors=[]))

    response = service.embed_batch([])

    assert response.embeddings == []
    assert response.dimensions == 0
