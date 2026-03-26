"""
Test for Supabase Edge Function Embeddings Client

Run with: uv run pytest tests/test_supabase_embeddings.py -v
"""

from unittest.mock import Mock

import pytest

from src.utils.supabase_embeddings import SupabaseEmbeddings, create_embedding_model


class TestSupabaseEmbeddings:
    """Test suite for SupabaseEmbeddings client."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        mock_client = Mock()
        mock_client.functions = Mock()
        return mock_client

    @pytest.fixture
    def embeddings(self, mock_supabase):
        """Create SupabaseEmbeddings instance with mocked client."""
        return SupabaseEmbeddings(mock_supabase)

    def test_initialization(self, mock_supabase):
        """Test SupabaseEmbeddings initializes correctly."""
        embeddings = SupabaseEmbeddings(mock_supabase, function_name="test-function")

        assert embeddings.supabase == mock_supabase
        assert embeddings.function_name == "test-function"
        assert embeddings.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embeddings.dimension == 384

    def test_embed_query_success(self, embeddings, mock_supabase):
        """Test embed_query returns correct embedding vector."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "dimension": 4,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        }
        mock_supabase.functions.invoke.return_value = mock_response

        # Test
        result = embeddings.embed_query("test query")

        # Verify
        assert result == [0.1, 0.2, 0.3, 0.4]
        mock_supabase.functions.invoke.assert_called_once_with(
            "generate-embedding", invoke_options={"body": {"text": "test query"}}
        )

    def test_embed_query_failure(self, embeddings, mock_supabase):
        """Test embed_query raises error on API failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.data = "Internal Server Error"
        mock_supabase.functions.invoke.return_value = mock_response

        # Test and verify exception
        with pytest.raises(RuntimeError, match="Edge function returned status 500"):
            embeddings.embed_query("test query")

    def test_embed_query_invalid_response(self, embeddings, mock_supabase):
        """Test embed_query raises error on invalid response format."""
        # Mock response with invalid format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid input"}
        mock_supabase.functions.invoke.return_value = mock_response

        # Test and verify exception (wrapped in RuntimeError)
        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            embeddings.embed_query("test query")

    def test_embed_documents_success(self, embeddings, mock_supabase):
        """Test embed_documents returns correct embedding vectors."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],
            "count": 3,
            "dimension": 3,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        }
        mock_supabase.functions.invoke.return_value = mock_response

        # Test
        texts = ["doc 1", "doc 2", "doc 3"]
        result = embeddings.embed_documents(texts)

        # Verify
        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]
        mock_supabase.functions.invoke.assert_called_once_with(
            "generate-embedding", invoke_options={"body": {"texts": texts}}
        )

    def test_embed_documents_fallback(self, embeddings, mock_supabase):
        """Test embed_documents falls back to individual calls on batch failure."""
        # Mock batch call failure, individual calls success
        mock_batch_response = Mock()
        mock_batch_response.status_code = 500

        mock_single_response = Mock()
        mock_single_response.status_code = 200
        mock_single_response.json.return_value = {"embedding": [0.1, 0.2, 0.3], "dimension": 3}

        # First call fails (batch), subsequent calls succeed (individual)
        mock_supabase.functions.invoke.side_effect = [
            mock_batch_response,
            mock_single_response,
            mock_single_response,
        ]

        # Test
        texts = ["doc 1", "doc 2"]
        result = embeddings.embed_documents(texts)

        # Verify fallback worked
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.1, 0.2, 0.3]
        assert mock_supabase.functions.invoke.call_count == 3  # 1 batch + 2 individual

    def test_create_embedding_model(self, mock_supabase):
        """Test factory function creates SupabaseEmbeddings correctly."""
        model = create_embedding_model(mock_supabase)

        assert isinstance(model, SupabaseEmbeddings)
        assert model.supabase == mock_supabase
        assert model.function_name == "generate-embedding"

    def test_aembed_query(self, embeddings, mock_supabase):
        """Test aembed_query delegates to embed_query correctly."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": [0.1, 0.2], "dimension": 2}
        mock_supabase.functions.invoke.return_value = mock_response

        # Test (async method just delegates to sync)
        import asyncio

        result = asyncio.run(embeddings.aembed_query("test query"))

        # Verify
        assert result == [0.1, 0.2]

    def test_aembed_documents(self, embeddings, mock_supabase):
        """Test aembed_documents delegates to embed_documents correctly."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embeddings": [[0.1], [0.2]], "count": 2}
        mock_supabase.functions.invoke.return_value = mock_response

        # Test (async method just delegates to sync)
        import asyncio

        result = asyncio.run(embeddings.aembed_documents(["doc 1", "doc 2"]))

        # Verify
        assert len(result) == 2
        assert result[0] == [0.1]
        assert result[1] == [0.2]


class TestIntegration:
    """Integration tests (require actual Supabase edge function deployed)."""

    @pytest.mark.skipif(
        True,  # Change to False when testing with real edge function
        reason="Requires deployed Supabase edge function and HUGGING_FACE_TOKEN",
    )
    def test_real_edge_function(self):
        """Test with real Supabase edge function (manual test only)."""
        import os

        from supabase import create_client

        # Requires actual credentials
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            pytest.skip("SUPABASE_URL or SUPABASE_KEY not set")

        supabase = create_client(supabase_url, supabase_key)
        embeddings = create_embedding_model(supabase)

        # Test single embedding
        result = embeddings.embed_query("Hello world")
        assert len(result) == 384  # Expected dimension
        assert all(isinstance(x, float) for x in result)

        # Test batch embeddings
        results = embeddings.embed_documents(["Hello", "world"])
        assert len(results) == 2
        assert all(len(emb) == 384 for emb in results)
