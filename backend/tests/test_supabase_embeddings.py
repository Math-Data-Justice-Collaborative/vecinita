"""Tests for Supabase Edge Function Embeddings client."""

from unittest.mock import Mock

import pytest

from src.utils.supabase_embeddings import SupabaseEmbeddings, create_embedding_model

pytestmark = pytest.mark.unit


class TestSupabaseEmbeddings:
    """Test suite for SupabaseEmbeddings client."""

    @pytest.fixture
    def mock_supabase(self):
        mock_client = Mock()
        mock_client.functions = Mock()
        return mock_client

    @pytest.fixture
    def embeddings(self, mock_supabase):
        return SupabaseEmbeddings(mock_supabase)

    def test_initialization(self, mock_supabase):
        embeddings = SupabaseEmbeddings(mock_supabase, function_name="test-function")

        assert embeddings.supabase == mock_supabase
        assert embeddings.function_name == "test-function"
        assert embeddings.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert embeddings.dimension == 384

    def test_embed_query_success(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "dimension": 4,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        }
        mock_supabase.functions.invoke.return_value = mock_response

        result = embeddings.embed_query("test query")

        assert result == [0.1, 0.2, 0.3, 0.4]
        mock_supabase.functions.invoke.assert_called_once_with(
            "generate-embedding", invoke_options={"body": {"text": "test query"}}
        )

    def test_embed_query_failure(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.data = "Internal Server Error"
        mock_supabase.functions.invoke.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            embeddings.embed_query("test query")

    def test_embed_query_invalid_response(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid input"}
        mock_supabase.functions.invoke.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            embeddings.embed_query("test query")

    def test_embed_query_supports_data_attribute_only_responses(self, embeddings, mock_supabase):
        mock_response = Mock()
        del mock_response.json
        mock_response.status_code = 200
        mock_response.data = {"embedding": [0.5, 0.6]}
        mock_supabase.functions.invoke.return_value = mock_response

        assert embeddings.embed_query("test query") == [0.5, 0.6]

    def test_embed_query_rejects_unknown_response_shapes(self, embeddings, mock_supabase):
        mock_response = Mock()
        del mock_response.json
        del mock_response.data
        mock_response.status_code = 200
        mock_supabase.functions.invoke.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to generate embedding"):
            embeddings.embed_query("test query")

    def test_embed_documents_success(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [
                [0.1, 0.2, 0.3],
                [0.4, 0.5, 0.6],
                [0.7, 0.8, 0.9],
            ],
            "count": 3,
            "dimension": 3,
            "model": "sentence-transformers/all-MiniLM-L6-v2",
        }
        mock_supabase.functions.invoke.return_value = mock_response

        texts = ["doc 1", "doc 2", "doc 3"]
        result = embeddings.embed_documents(texts)

        assert len(result) == 3
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        assert result[2] == [0.7, 0.8, 0.9]
        mock_supabase.functions.invoke.assert_called_once_with(
            "generate-embedding", invoke_options={"body": {"texts": texts}}
        )

    def test_embed_documents_fallback(self, embeddings, mock_supabase):
        mock_batch_response = Mock()
        mock_batch_response.status_code = 500
        mock_batch_response.data = "Batch failed"

        mock_single_response = Mock()
        mock_single_response.status_code = 200
        mock_single_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3],
            "dimension": 3,
        }

        mock_supabase.functions.invoke.side_effect = [
            mock_batch_response,
            mock_single_response,
            mock_single_response,
        ]

        texts = ["doc 1", "doc 2"]
        result = embeddings.embed_documents(texts)

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.1, 0.2, 0.3]
        assert mock_supabase.functions.invoke.call_count == 3

    def test_embed_documents_supports_data_attribute_only_responses(
        self, embeddings, mock_supabase
    ):
        mock_response = Mock()
        del mock_response.json
        mock_response.status_code = 200
        mock_response.data = {"embeddings": [[0.3], [0.4]]}
        mock_supabase.functions.invoke.return_value = mock_response

        assert embeddings.embed_documents(["doc 1", "doc 2"]) == [[0.3], [0.4]]

    def test_embed_documents_falls_back_on_unknown_response_shape(self, embeddings, mock_supabase):
        mock_response = Mock()
        del mock_response.json
        del mock_response.data
        mock_response.status_code = 200
        mock_supabase.functions.invoke.return_value = mock_response
        embeddings.embed_query = Mock(side_effect=[[0.1], [0.2]])

        assert embeddings.embed_documents(["doc 1", "doc 2"]) == [[0.1], [0.2]]
        assert embeddings.embed_query.call_count == 2

    def test_embed_documents_invalid_payload_falls_back_to_individual_calls(
        self, embeddings, mock_supabase
    ):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embeddings": "not-a-list"}
        mock_supabase.functions.invoke.return_value = mock_response
        embeddings.embed_query = Mock(side_effect=[[0.7], [0.8]])

        assert embeddings.embed_documents(["doc 1", "doc 2"]) == [[0.7], [0.8]]
        assert embeddings.embed_query.call_count == 2

    def test_create_embedding_model(self, mock_supabase):
        model = create_embedding_model(mock_supabase)

        assert isinstance(model, SupabaseEmbeddings)
        assert model.supabase == mock_supabase
        assert model.function_name == "generate-embedding"

    @pytest.mark.anyio
    async def test_async_embed_query(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2],
            "dimension": 2,
        }
        mock_supabase.functions.invoke.return_value = mock_response

        result = await embeddings.aembed_query("test query")

        assert result == [0.1, 0.2]

    @pytest.mark.anyio
    async def test_async_embed_documents(self, embeddings, mock_supabase):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1], [0.2]],
            "count": 2,
        }
        mock_supabase.functions.invoke.return_value = mock_response

        result = await embeddings.aembed_documents(["doc 1", "doc 2"])

        assert len(result) == 2
        assert result[0] == [0.1]
        assert result[1] == [0.2]
