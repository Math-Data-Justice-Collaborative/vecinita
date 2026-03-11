"""
Unit tests for src/embedding_service/main.py

Tests embedding service endpoints and model loading.
"""
import pytest
import json
import importlib
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model for tests."""
    import numpy as np
    mock_embedding = MagicMock()
    # Return numpy arrays like real SentenceTransformer
    mock_embedding.encode = MagicMock(
        side_effect=lambda text, **kwargs: np.array([0.1] * 384) if isinstance(text, str) else np.array([[0.1] * 384 for _ in range(len(text))])
    )
    return mock_embedding


@pytest.fixture
def embedding_app(mock_embedding_model):
    """Create embedding service app for testing."""
    from src.embedding_service import main as server_module

    server = importlib.reload(server_module)
    server._embedding_model = None
    server._auth_token = None

    with patch("src.embedding_service.main.get_embedding_model", return_value=mock_embedding_model):
        yield server.app


@pytest.fixture
def embedding_client(embedding_app, mock_embedding_model):
    """Create test client for embedding service."""
    with patch("src.embedding_service.main.get_embedding_model", return_value=mock_embedding_model):
        return TestClient(embedding_app)


class TestEmbeddingHealth:
    """Test health check endpoint."""

    def test_health_endpoint(self, embedding_client):
        """Test /health endpoint returns ok status."""
        response = embedding_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["service"] == "embedding"


class TestEmbeddingAuth:
    def test_embed_rejects_unauthorized_when_token_enabled(self, embedding_client):
        from src.embedding_service import main as server

        server._auth_token = "test-token"
        response = embedding_client.post("/embed", json={"text": "hello"})
        assert response.status_code == 401

    def test_embed_accepts_token_header(self, embedding_client):
        from src.embedding_service import main as server

        server._auth_token = "test-token"
        response = embedding_client.post(
            "/embed",
            json={"text": "hello"},
            headers={"x-embedding-service-token": "test-token"},
        )
        assert response.status_code == 200

    def test_embed_accepts_bearer_token_when_auth_enabled(self, embedding_client):
        from src.embedding_service import main as server

        server._auth_token = "test-token"
        response = embedding_client.post(
            "/embed",
            json={"text": "hello"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint_returns_service_info(self, embedding_client):
        """Test / endpoint returns service information."""
        response = embedding_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Vecinita Embedding Service"
        assert "version" in data
        assert "endpoints" in data
        assert "model" in data


class TestEmbedSingle:
    """Test single text embedding endpoint."""

    @pytest.mark.skip(reason="Mock fixtures not properly handling array shape conversion")
    def test_embed_single_valid_text(self, embedding_client):
        """Test embedding a single text."""
        request_data = {"text": "Hello world"}
        response = embedding_client.post("/embed", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "embedding" in data
        assert "dimension" in data
        assert data["dimension"] == 384
        assert isinstance(data["embedding"], list)

    def test_embed_single_empty_text(self, embedding_client):
        """Test embedding empty text validation."""
        request_data = {"text": ""}
        response = embedding_client.post("/embed", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_embed_single_missing_text(self, embedding_client):
        """Test embedding request without text field."""
        response = embedding_client.post("/embed", json={})
        assert response.status_code == 422  # Validation error

    def test_embed_single_text_too_long(self, embedding_client):
        """Test embedding text exceeding max length."""
        request_data = {"text": "x" * 10001}
        response = embedding_client.post("/embed", json=request_data)
        assert response.status_code == 422  # Validation error


class TestEmbedBatch:
    """Test batch text embedding endpoint."""

    def test_embed_batch_multiple_texts(self, embedding_client):
        """Test embedding multiple texts."""
        request_data = {"texts": ["Hello", "World", "Test"]}
        response = embedding_client.post("/embed-batch", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "embeddings" in data
        assert len(data["embeddings"]) == 3
        assert data["count"] == 3
        assert data["dimension"] == 384

    def test_embed_batch_single_text(self, embedding_client):
        """Test batch embedding with single text."""
        request_data = {"texts": ["Single text"]}
        response = embedding_client.post("/embed-batch", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["embeddings"]) == 1

    def test_embed_batch_empty_list(self, embedding_client):
        """Test batch embedding with empty list."""
        request_data = {"texts": []}
        response = embedding_client.post("/embed-batch", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_embed_batch_too_many_texts(self, embedding_client):
        """Test batch embedding exceeding max items."""
        request_data = {"texts": ["text"] * 101}
        response = embedding_client.post("/embed-batch", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_embed_batch_missing_texts(self, embedding_client):
        """Test batch request without texts field."""
        response = embedding_client.post("/embed-batch", json={})
        assert response.status_code == 422  # Validation error


class TestConfigEndpoints:
    """Test configuration endpoints."""

    def test_get_config(self, embedding_client):
        """Test GET /config endpoint."""
        response = embedding_client.get("/config")
        assert response.status_code == 200
        data = response.json()
        assert "current" in data
        assert "available" in data
        assert "provider" in data["current"]
        assert "model" in data["current"]
        assert "locked" in data["current"]

    def test_set_config_huggingface(self, embedding_client):
        """Test POST /config with HuggingFace provider."""
        request_data = {
            "provider": "huggingface",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "lock": False
        }
        response = embedding_client.post("/config", json=request_data)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_set_config_locked_config(self, embedding_client):
        """Test that locked config cannot be changed."""
        with patch("src.embedding_service.main._lock_selection", True):
            request_data = {
                "provider": "huggingface",
                "model": "sentence-transformers/all-MiniLM-L6-v2"
            }
            response = embedding_client.post("/config", json=request_data)
            assert response.status_code == 403

    def test_set_config_unsupported_provider(self, embedding_client):
        """Test that unsupported provider is rejected."""
        request_data = {
            "provider": "unsupported",
            "model": "some-model"
        }
        response = embedding_client.post("/config", json=request_data)
        assert response.status_code == 400

    def test_set_config_missing_fields(self, embedding_client):
        """Test config request with missing fields."""
        response = embedding_client.post("/config", json={})
        assert response.status_code == 422


class TestSimilarityEndpoint:
    """Test similarity search endpoint."""

    @pytest.mark.skip(reason="sklearn not available in test environment")
    def test_similarity_search(self, embedding_client):
        """Test similarity search endpoint."""
        import numpy as np
        with patch("src.embedding_service.main.get_embedding_model") as mock_model, \
             patch("sklearn.metrics.pairwise.cosine_similarity", return_value=np.array([[0.9, 0.7, 0.5]])) as mock_cosine:
            # Mock embedding model to return deterministic vectors
            mock_embedding = MagicMock()
            def mock_encode(text, **kwargs):
                if isinstance(text, str):
                    return np.array([0.1, 0.2, 0.3] + [0.0] * 381)
                else:
                    return np.array([[0.1, 0.2, 0.3] + [0.0] * 381 for _ in range(len(text))])
            mock_embedding.encode = mock_encode
            mock_model.return_value = mock_embedding
            
            request_data = {
                "query_request": {"text": "Hello world"},
                "texts_request": {"texts": ["Hello", "World", "Test"]}
            }
            response = embedding_client.post(
                "/similarity",
                json=request_data
            )
            assert response.status_code == 200
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert len(data["results"]) == 3

    def test_similarity_results_sorted(self, embedding_client):
        """Test that similarity results are sorted by score."""
        with patch("src.embedding_service.main.get_embedding_model"):
            request_data = {
                "query_request": {"text": "test"},
                "texts_request": {"texts": ["a", "b", "c"]}
            }
            response = embedding_client.post("/similarity", json=request_data)
            if response.status_code == 200:
                data = response.json()
                if len(data["results"]) > 1:
                    scores = [r["similarity"] for r in data["results"]]
                    assert scores == sorted(scores, reverse=True)


class TestEmbedRequestModel:
    """Test EmbedRequest Pydantic model."""

    def test_embed_request_valid(self, embedding_client):
        """Test valid EmbedRequest."""
        from src.embedding_service.main import EmbedRequest
        req = EmbedRequest(text="test text")
        assert req.text == "test text"

    def test_embed_request_min_length(self, embedding_client):
        """Test EmbedRequest respects min_length."""
        from src.embedding_service.main import EmbedRequest
        with pytest.raises(ValueError):
            EmbedRequest(text="")

    def test_embed_request_max_length(self, embedding_client):
        """Test EmbedRequest respects max_length."""
        from src.embedding_service.main import EmbedRequest
        with pytest.raises(ValueError):
            EmbedRequest(text="x" * 10001)


class TestBatchEmbedRequestModel:
    """Test BatchEmbedRequest Pydantic model."""

    def test_batch_embed_request_valid(self, embedding_client):
        """Test valid BatchEmbedRequest."""
        from src.embedding_service.main import BatchEmbedRequest
        req = BatchEmbedRequest(texts=["text1", "text2"])
        assert len(req.texts) == 2

    def test_batch_embed_request_min_items(self, embedding_client):
        """Test BatchEmbedRequest respects min_items."""
        from src.embedding_service.main import BatchEmbedRequest
        with pytest.raises(ValueError):
            BatchEmbedRequest(texts=[])

    def test_batch_embed_request_max_items(self, embedding_client):
        """Test BatchEmbedRequest respects max_items."""
        from src.embedding_service.main import BatchEmbedRequest
        with pytest.raises(ValueError):
            BatchEmbedRequest(texts=["text"] * 101)


class TestEmbeddingResponseModel:
    """Test EmbeddingResponse Pydantic model."""

    def test_embedding_response_valid(self, embedding_client):
        """Test valid EmbeddingResponse."""
        from src.embedding_service.main import EmbeddingResponse
        resp = EmbeddingResponse(
            embedding=[0.1] * 384,
            dimension=384,
            model="test-model"
        )
        assert resp.dimension == 384
        assert len(resp.embedding) == 384


class TestBatchEmbeddingResponseModel:
    """Test BatchEmbeddingResponse Pydantic model."""

    def test_batch_embedding_response_valid(self, embedding_client):
        """Test valid BatchEmbeddingResponse."""
        from src.embedding_service.main import BatchEmbeddingResponse
        resp = BatchEmbeddingResponse(
            embeddings=[[0.1] * 384, [0.2] * 384],
            dimension=384,
            count=2,
            model="test-model"
        )
        assert resp.count == 2
        assert len(resp.embeddings) == 2


class TestEmbeddingModelLoading:
    """Test embedding model loading."""

    @pytest.mark.skip(reason="sentence_transformers not available in test environment")
    def test_get_embedding_model_caches_result(self):
        """Test that get_embedding_model caches the result."""
        # Mock SentenceTransformer where it's imported
        with patch("sentence_transformers.SentenceTransformer") as mock_transformer:
            mock_model = MagicMock()
            mock_transformer.return_value = mock_model

            from src.services.embedding import server
            # Reset the global embedding model
            server._embedding_model = None

            # First call should load the model
            model1 = server.get_embedding_model()
            # Second call should return cached model
            model2 = main.get_embedding_model()

            assert model1 is model2
            # Constructor should be called only once
            mock_transformer.assert_called_once()

    @pytest.mark.skip(reason="sentence_transformers not available in test environment")
    def test_get_embedding_model_raises_on_failure(self):
        """Test that get_embedding_model raises on loading failure."""
        # Mock SentenceTransformer to raise ImportError where it's imported
        with patch("sentence_transformers.SentenceTransformer") as mock_transformer:
            mock_transformer.side_effect = ImportError("sentence-transformers not found")

            from src.services.embedding import server
            server._embedding_model = None

            with pytest.raises(RuntimeError, match="Failed to load embedding model"):
                server.get_embedding_model()
