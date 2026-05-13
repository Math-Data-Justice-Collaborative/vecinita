from __future__ import annotations

import pytest
from pydantic import ValidationError

from vecinita.schemas import (
    BatchEmbeddingResponse,
    BatchQueryRequest,
    EmbeddingResponse,
    QueryRequest,
)


def test_query_request_accepts_optional_model() -> None:
    request = QueryRequest(query="hello", model="custom-model")

    assert request.query == "hello"
    assert request.model == "custom-model"


def test_query_request_defaults_model_to_none() -> None:
    request = QueryRequest(query="hello")

    assert request.model is None


def test_batch_query_request_requires_at_least_one_query() -> None:
    with pytest.raises(ValidationError):
        BatchQueryRequest(queries=[])


def test_embedding_response_serializes_dimensions() -> None:
    response = EmbeddingResponse(
        embedding=[0.1, 0.2, 0.3],
        model="demo",
        dimensions=3,
    )

    assert response.model_dump() == {
        "embedding": [0.1, 0.2, 0.3],
        "model": "demo",
        "dimensions": 3,
    }


def test_batch_embedding_response_serializes_multiple_vectors() -> None:
    response = BatchEmbeddingResponse(
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        model="demo",
        dimensions=2,
    )

    assert response.embeddings[1] == [0.3, 0.4]
    assert response.dimensions == 2
