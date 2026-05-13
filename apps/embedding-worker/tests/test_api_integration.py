from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.fakes import FailingEmbedder, FakeEmbedder
from vecinita.api import create_app
from vecinita.constants import DEFAULT_MODEL
from vecinita.service import EmbeddingService


@pytest.mark.integration
def test_root_returns_status_and_model(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": DEFAULT_MODEL}


@pytest.mark.integration
def test_health_returns_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
def test_embed_returns_embedding(client: TestClient) -> None:
    response = client.post("/embed", json={"query": "hello world"})

    assert response.status_code == 200
    assert response.json() == {
        "embedding": [0.1, 0.2, 0.3],
        "model": DEFAULT_MODEL,
        "dimensions": 3,
    }


@pytest.mark.integration
def test_embed_uses_requested_model(client: TestClient) -> None:
    response = client.post(
        "/embed",
        json={"query": "hello world", "model": "custom-model"},
    )

    assert response.status_code == 200
    assert response.json()["model"] == "custom-model"


@pytest.mark.integration
def test_embed_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/embed", json={"query": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Query must not be empty."


@pytest.mark.integration
def test_embed_returns_backend_failure() -> None:
    client = TestClient(create_app(EmbeddingService(FailingEmbedder())))

    response = client.post("/embed", json={"query": "hello world"})

    assert response.status_code == 500
    assert response.json()["detail"] == "Embedding failed: backend unavailable"


@pytest.mark.integration
def test_embed_batch_returns_embeddings(client: TestClient) -> None:
    response = client.post(
        "/embed/batch",
        json={"queries": ["alpha", "beta"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        "model": DEFAULT_MODEL,
        "dimensions": 3,
    }


@pytest.mark.integration
def test_embed_batch_hyphen_path_accepts_texts_body(client: TestClient) -> None:
    response = client.post(
        "/embed-batch",
        json={"texts": ["alpha", "beta"]},
    )

    assert response.status_code == 200
    assert response.json()["embeddings"] == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


@pytest.mark.integration
def test_embed_accepts_text_field_alias(client: TestClient) -> None:
    response = client.post("/embed", json={"text": "hello world"})

    assert response.status_code == 200
    assert response.json()["dimensions"] == 3


@pytest.mark.integration
def test_embed_batch_uses_requested_model(client: TestClient) -> None:
    response = client.post(
        "/embed/batch",
        json={"queries": ["alpha", "beta"], "model": "batch-model"},
    )

    assert response.status_code == 200
    assert response.json()["model"] == "batch-model"


@pytest.mark.integration
def test_embed_batch_rejects_empty_queries(client: TestClient) -> None:
    response = client.post(
        "/embed/batch",
        json={"queries": ["alpha", "   "]},
    )

    assert response.status_code == 422
    body = response.json()["detail"]
    # Schema may reject before the service layer (string message vs validation list)
    assert "empty" in str(body).lower() or "whitespace" in str(body).lower()


@pytest.mark.integration
def test_embed_batch_validates_non_empty_list(client: TestClient) -> None:
    response = client.post("/embed/batch", json={"queries": []})

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"


@pytest.mark.integration
def test_embed_batch_returns_backend_failure() -> None:
    client = TestClient(create_app(EmbeddingService(FailingEmbedder())))

    response = client.post("/embed/batch", json={"queries": ["alpha", "beta"]})

    assert response.status_code == 500
    assert response.json()["detail"] == "Embedding failed: backend unavailable"


@pytest.mark.integration
def test_embed_calls_embedder_with_original_input() -> None:
    embedder = FakeEmbedder(vectors=[[0.1, 0.2, 0.3]])
    client = TestClient(create_app(EmbeddingService(embedder)))

    response = client.post("/embed", json={"query": " hello world "})

    assert response.status_code == 200
    assert embedder.calls == [[" hello world "]]
