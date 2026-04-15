"""
Unit tests for src/gateway/router_embed.py

Tests embedding generation and similarity computation endpoints.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def embed_client(env_vars, monkeypatch):
    """Create a test client with embed router included."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.main import app

    return TestClient(app)


class TestEmbedSingleEndpoint:
    """Test POST /embed endpoint."""

    def test_embed_single_text(self, embed_client):
        """Test embedding a single text."""
        response = embed_client.post("/api/v1/embed", json={"text": "Hello world"})
        # Endpoint proxies to embedding service; unavailable backend returns 503
        assert response.status_code in [200, 503]

    def test_embed_text_with_model_override(self, embed_client):
        """Test embedding with model override."""
        response = embed_client.post(
            "/api/v1/embed", json={"text": "Hello world", "model": "custom-model"}
        )
        assert response.status_code in [200, 503]

    def test_embed_empty_text(self, embed_client):
        """Empty text is rejected at the gateway (min_length=1)."""
        response = embed_client.post("/api/v1/embed", json={"text": ""})
        assert response.status_code == 422

    def test_embed_missing_text(self, embed_client):
        """Test that text field is required."""
        response = embed_client.post("/api/v1/embed", json={})
        assert response.status_code == 422

    def test_embed_accepts_query_field_from_service_contract(self, embed_client):
        """Canonical embedding service contract uses `query` for single requests."""
        response = embed_client.post("/api/v1/embed", json={"query": "Hello world"})
        assert response.status_code in [200, 503]

    def test_embed_long_text(self, embed_client):
        """Test embedding long text."""
        long_text = "hello " * 10000  # Very long text
        response = embed_client.post("/api/v1/embed", json={"text": long_text})
        # Upstream may reject oversized bodies with 422 depending on deployment limits.
        assert response.status_code in [200, 422, 503]


class TestEmbedBatchEndpoint:
    """Test POST /embed/batch endpoint."""

    def test_embed_batch_texts(self, embed_client):
        """Test embedding multiple texts."""
        response = embed_client.post(
            "/api/v1/embed/batch", json={"texts": ["Hello", "World", "Test"]}
        )
        assert response.status_code in [200, 503]

    def test_embed_batch_single_text(self, embed_client):
        """Test batch endpoint with single text."""
        response = embed_client.post("/api/v1/embed/batch", json={"texts": ["Hello"]})
        assert response.status_code in [200, 503]

    def test_embed_batch_with_model(self, embed_client):
        """Test batch embedding with model override."""
        response = embed_client.post(
            "/api/v1/embed/batch", json={"texts": ["Hello", "World"], "model": "custom-model"}
        )
        assert response.status_code in [200, 503]

    def test_embed_batch_empty_list(self, embed_client):
        """Test batch endpoint rejects empty text list."""
        response = embed_client.post("/api/v1/embed/batch", json={"texts": []})
        assert response.status_code == 422

    def test_embed_batch_missing_texts(self, embed_client):
        """Test batch endpoint requires texts field."""
        response = embed_client.post("/api/v1/embed/batch", json={})
        assert response.status_code == 422

    def test_embed_batch_accepts_queries_field_from_service_contract(self, embed_client):
        """Canonical embedding service contract uses `queries` for batch requests."""
        response = embed_client.post("/api/v1/embed/batch", json={"queries": ["Hello", "World"]})
        assert response.status_code in [200, 503]

    def test_embed_batch_many_texts(self, embed_client):
        """Test batch endpoint with many texts."""
        texts = [f"Text {i}" for i in range(1000)]
        response = embed_client.post("/api/v1/embed/batch", json={"texts": texts})
        # Upstream may reject oversized batches with 422 depending on deployment limits.
        assert response.status_code in [200, 422, 503]

    def test_embed_batch_rejects_empty_string_entries(self, embed_client):
        """Whitespace and empty strings are rejected before calling upstream."""
        response = embed_client.post(
            "/api/v1/embed/batch",
            json={"texts": ["", ""]},
        )
        assert response.status_code == 422

    def test_embed_batch_rejects_whitespace_only_entries(self, embed_client):
        response = embed_client.post(
            "/api/v1/embed/batch",
            json={"texts": ["  ", "\t"]},
        )
        assert response.status_code == 422

    @patch("src.api.router_embed.httpx.AsyncClient")
    def test_embed_batch_maps_upstream_422_to_422(
        self, mock_async_client, embed_client, monkeypatch
    ):
        """Upstream embedding 422 must not be surfaced as gateway 503 (Schemathesis not_a_server_error)."""
        from src.api import router_embed

        monkeypatch.setattr(
            router_embed, "_embedding_service_url", lambda: "http://127.0.0.1:18001"
        )

        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": "invalid payload"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unprocessable Entity",
            request=MagicMock(),
            response=mock_response,
        )

        mock_inner = MagicMock()
        mock_inner.post = AsyncMock(return_value=mock_response)
        mock_inner.__aenter__ = AsyncMock(return_value=mock_inner)
        mock_inner.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_inner

        response = embed_client.post(
            "/api/v1/embed/batch",
            json={"texts": ["Hello", "World"]},
        )
        assert response.status_code == 422
        payload = response.json()
        assert "error" in payload
        assert payload["error"] == {"detail": "invalid payload"}


class TestSimilarityEndpoint:
    """Test POST /embed/similarity endpoint."""

    def test_compute_similarity(self, embed_client):
        """Test computing similarity between two texts."""
        response = embed_client.post(
            "/api/v1/embed/similarity", json={"text1": "Hello world", "text2": "Hello there"}
        )
        assert response.status_code in [200, 503]

    def test_similarity_with_model(self, embed_client):
        """Test similarity with model override."""
        response = embed_client.post(
            "/api/v1/embed/similarity",
            json={"text1": "Hello", "text2": "Hello", "model": "custom-model"},
        )
        assert response.status_code in [200, 503]

    def test_similarity_identical_texts(self, embed_client):
        """Test similarity of identical texts."""
        response = embed_client.post(
            "/api/v1/embed/similarity", json={"text1": "The same text", "text2": "The same text"}
        )
        assert response.status_code in [200, 503]

    def test_similarity_different_texts(self, embed_client):
        """Test similarity of completely different texts."""
        response = embed_client.post(
            "/api/v1/embed/similarity", json={"text1": "Hello world", "text2": "xyz abc 123"}
        )
        assert response.status_code in [200, 503]

    def test_similarity_missing_text1(self, embed_client):
        """Test similarity endpoint requires both texts."""
        response = embed_client.post("/api/v1/embed/similarity", json={"text2": "Hello"})
        assert response.status_code == 422

    def test_similarity_missing_text2(self, embed_client):
        """Test similarity endpoint requires both texts."""
        response = embed_client.post("/api/v1/embed/similarity", json={"text1": "Hello"})
        assert response.status_code == 422

    def test_similarity_empty_texts(self, embed_client):
        """Empty texts are rejected at the gateway (min_length=1)."""
        response = embed_client.post("/api/v1/embed/similarity", json={"text1": "", "text2": ""})
        assert response.status_code == 422


class TestEmbedConfigEndpoint:
    """Test embedding configuration endpoints."""

    def test_get_embedding_config(self, embed_client):
        """Test getting embedding configuration."""
        response = embed_client.get("/api/v1/embed/config")
        assert response.status_code == 200
        data = response.json()

        assert data["model"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert data["provider"] == "huggingface"
        assert data["dimension"] == 384
        assert "description" in data

    def test_embedding_config_has_required_fields(self, embed_client):
        """Test config response has all required fields."""
        response = embed_client.get("/api/v1/embed/config")
        data = response.json()

        required_fields = ["model", "provider", "dimension", "description"]
        for field in required_fields:
            assert field in data

    def test_embedding_config_dimension_is_valid(self, embed_client):
        """Test dimension is a positive integer."""
        response = embed_client.get("/api/v1/embed/config")
        data = response.json()

        assert isinstance(data["dimension"], int)
        assert data["dimension"] > 0

    def test_update_embedding_config(self, embed_client):
        """Test updating embedding configuration."""
        response = embed_client.post("/api/v1/embed/config?provider=huggingface&model=test-model")
        assert response.status_code in [200, 404, 503]

    def test_update_config_missing_model(self, embed_client):
        """Test config update requires model parameter."""
        response = embed_client.post("/api/v1/embed/config")
        assert response.status_code == 422


class TestEmbedRequestValidation:
    """Test request validation for embed endpoints."""

    def test_embed_text_must_be_string(self, embed_client):
        """Test text field must be a string."""
        response = embed_client.post("/api/v1/embed", json={"text": 123})
        assert response.status_code == 422

    def test_batch_texts_must_be_list(self, embed_client):
        """Test texts field must be a list."""
        response = embed_client.post("/api/v1/embed/batch", json={"texts": "not a list"})
        assert response.status_code == 422

    def test_batch_texts_must_be_strings(self, embed_client):
        """Test batch texts must all be strings."""
        response = embed_client.post("/api/v1/embed/batch", json={"texts": ["Hello", 123, "World"]})
        assert response.status_code == 422

    def test_similarity_texts_must_be_strings(self, embed_client):
        """Test similarity text fields must be strings."""
        response = embed_client.post(
            "/api/v1/embed/similarity", json={"text1": 123, "text2": "Hello"}
        )
        assert response.status_code == 422


class TestEmbedErrorHandling:
    """Test error handling in embed endpoints."""

    def test_malformed_json_embed(self, embed_client):
        """Test malformed JSON in embed request."""
        response = embed_client.post(
            "/api/v1/embed", content="not json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_malformed_json_batch(self, embed_client):
        """Test malformed JSON in batch request."""
        response = embed_client.post(
            "/api/v1/embed/batch", content="not json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_malformed_json_similarity(self, embed_client):
        """Test malformed JSON in similarity request."""
        response = embed_client.post(
            "/api/v1/embed/similarity",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestEmbedEndpointRouting:
    """Test that embed endpoints are properly routed."""

    def test_embed_endpoint_exists(self, embed_client):
        """Test that embed endpoint is accessible."""
        response = embed_client.post("/api/v1/embed", json={"text": "test"})
        assert response.status_code in [200, 422, 503]

    def test_batch_endpoint_exists(self, embed_client):
        """Test that batch endpoint is accessible."""
        response = embed_client.post("/api/v1/embed/batch", json={"texts": ["test"]})
        assert response.status_code in [200, 422, 503]

    def test_similarity_endpoint_exists(self, embed_client):
        """Test that similarity endpoint is accessible."""
        response = embed_client.post("/api/v1/embed/similarity", json={"text1": "a", "text2": "b"})
        assert response.status_code in [200, 422, 503]

    def test_config_endpoint_exists(self, embed_client):
        """Test that config endpoint is accessible."""
        response = embed_client.get("/api/v1/embed/config")
        # Config is implemented
        assert response.status_code == 200


class TestEmbeddingUpstreamUrlResolution:
    """``_embedding_service_url`` must rewrite legacy Modal container hosts (no HTTP)."""

    def test_rewrites_legacy_vecinita_modal_host(self, monkeypatch):
        monkeypatch.delenv("RENDER", raising=False)
        monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
        monkeypatch.delenv("LOCAL_EMBEDDING_SERVICE_URL", raising=False)
        monkeypatch.setenv(
            "VECINITA_EMBEDDING_API_URL",
            "https://vecinita--vecinita-embedding-embeddingservicecontainer-api.modal.run",
        )

        from src.api import router_embed

        resolved = router_embed._embedding_service_url()
        assert resolved == "https://vecinita--vecinita-embedding-web-app.modal.run"
        assert "embedding-embedding-web-app" not in resolved
        assert "embeddingservicecontainer-api" not in resolved


class TestGatewayEmbedOpenapiResponses:
    """Regression: upstream failures are documented for Schemathesis / contract tools."""

    def test_post_embed_routes_document_503_with_error_response_schema(self, embed_client):
        spec = embed_client.app.openapi()
        for path in (
            "/api/v1/embed",
            "/api/v1/embed/batch",
            "/api/v1/embed/similarity",
        ):
            post = spec["paths"][path]["post"]
            assert "422" in post["responses"], f"missing 422 on {path}"
            assert "503" in post["responses"], f"missing 503 on {path}"
            schema = post["responses"]["503"]["content"]["application/json"]["schema"]
            ref = schema.get("$ref", "")
            assert ref.endswith("ErrorResponse"), f"unexpected 503 schema on {path}: {schema}"


class TestModalFunctionInvocation:
    def test_embed_uses_modal_function_invocation(self, embed_client, monkeypatch):
        monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
        from src.api import router_embed

        monkeypatch.setattr(
            router_embed,
            "invoke_modal_embedding_single",
            lambda _text: {
                "embedding": [0.1, 0.2],
                "model": "sentence-transformers/test",
                "dimension": 2,
            },
        )

        response = embed_client.post("/api/v1/embed", json={"text": "Hello world"})
        assert response.status_code == 200
        data = response.json()
        assert data["dimension"] == 2
        assert data["model"] == "sentence-transformers/test"

    def test_embed_batch_uses_modal_function_invocation(self, embed_client, monkeypatch):
        monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "true")
        from src.api import router_embed

        monkeypatch.setattr(
            router_embed,
            "invoke_modal_embedding_batch",
            lambda _texts: {
                "embeddings": [[0.1, 0.2], [0.3, 0.4]],
                "model": "sentence-transformers/test",
                "dimension": 2,
            },
        )

        response = embed_client.post("/api/v1/embed/batch", json={"texts": ["Hello", "World"]})
        assert response.status_code == 200
        payload = response.json()
        assert payload["dimension"] == 2
        assert payload["model"] == "sentence-transformers/test"
        assert len(payload["embeddings"]) == 2
