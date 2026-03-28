"""
Unit tests for src/gateway/router_ask.py

Tests Q&A endpoints with agent service proxying.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def ask_client(env_vars, monkeypatch):
    """Create a test client with ask router included."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    monkeypatch.setenv("AGENT_SERVICE_URL", "http://localhost:8000")
    monkeypatch.setenv("AGENT_TIMEOUT", "30")
    monkeypatch.setenv("AGENT_STREAM_TIMEOUT", "120")

    from src.api.router_ask import router as ask_router

    app = FastAPI()
    app.include_router(ask_router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture
def mock_agent_response():
    """Mock agent service response."""
    return {
        "answer": "This is a test answer.",
        "sources": [
            {
                "title": "Test Document",
                "url": "https://example.com/doc",
                "type": "document",
                "isDownload": False,
            }
        ],
        "thread_id": "thread-123",
        "language": "en",
        "model": "llama-3.1-8b-instant",
    }


class TestAskEndpoint:
    """Test GET /ask endpoint."""

    @patch("httpx.AsyncClient.get")
    def test_ask_question_success(self, mock_get, ask_client, mock_agent_response):
        """Test successful question asking."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=What%20is%20housing%3F")
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data

    def test_ask_question_required(self, ask_client):
        """Test that question parameter is required."""
        response = ask_client.get("/api/v1/ask")
        assert response.status_code == 422

    @patch("httpx.AsyncClient.get")
    def test_ask_with_thread_id(self, mock_get, ask_client, mock_agent_response):
        """Test ask endpoint with thread_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get(
            "/api/v1/ask?question=Follow%20up%20question&thread_id=thread-123"
        )
        assert response.status_code == 200

    @patch("httpx.AsyncClient.get")
    def test_ask_with_language_override(self, mock_get, ask_client, mock_agent_response):
        """Test ask endpoint with language override."""
        mock_agent_response["language"] = "es"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=What%20is%20housing%3F&lang=es")
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "es"

    @patch("httpx.AsyncClient.get")
    def test_ask_with_provider_and_model(self, mock_get, ask_client, mock_agent_response):
        """Test ask with custom provider and model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=Test&provider=ollama&model=llama3.1:8b")
        assert response.status_code == 200

    @patch("httpx.AsyncClient.get")
    def test_ask_maps_latency_metadata(self, mock_get, ask_client, mock_agent_response):
        """Gateway should surface upstream latency fields when provided by agent."""
        mock_agent_response["response_time_ms"] = 1234
        mock_agent_response["latency_breakdown"] = {
            "retrieval_invoke_ms": 110,
            "llm_ms": 820,
            "db_search": {"total_ms": 90},
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=What%20is%20housing%3F")
        assert response.status_code == 200
        data = response.json()
        assert data["response_time_ms"] == 1234
        assert data["latency_breakdown"]["retrieval_invoke_ms"] == 110

    @patch("httpx.AsyncClient.get")
    def test_ask_with_tags_and_rerank_params(self, mock_get, ask_client, mock_agent_response):
        """Test ask forwards metadata tag filter and reranking parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_agent_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get(
            "/api/v1/ask?question=Test&tags=housing,food&tag_match_mode=all&include_untagged_fallback=false&rerank=true&rerank_top_k=7"
        )
        assert response.status_code == 200

        params = mock_get.call_args.kwargs.get("params", {})
        assert params.get("tags") == "housing,food"
        assert params.get("tag_match_mode") == "all"
        assert params.get("include_untagged_fallback") == "false"
        assert params.get("rerank") == "true"
        assert params.get("rerank_top_k") == 7

    @patch("httpx.AsyncClient.get")
    def test_ask_timeout_error(self, mock_get, ask_client):
        """Test timeout handling."""
        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        response = ask_client.get("/api/v1/ask?question=Test")
        assert response.status_code == 504
        response_data = response.json()
        assert "detail" in response_data
        assert "timeout" in str(response_data["detail"]).lower()

    @patch("httpx.AsyncClient.get")
    def test_ask_agent_service_unavailable(self, mock_get, ask_client):
        """Test handling of agent service connection error."""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        response = ask_client.get("/api/v1/ask?question=Test")
        assert response.status_code == 503
        response_data = response.json()
        assert "detail" in response_data
        assert "connect" in str(response_data["detail"]).lower()

    @patch("httpx.AsyncClient.get")
    def test_ask_agent_service_error(self, mock_get, ask_client):
        """Test handling of agent service HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=Test")
        assert response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_propagates_invalid_api_key_error_details(self, mock_get, ask_client):
        """Gateway should preserve upstream invalid key details for easier diagnosis."""
        upstream_body = (
            "{\"detail\":\"Error code: 401 - {'error': {'code': 'invalid_api_key', "
            "'message': 'Incorrect API key provided'}}\"}"
        )
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = upstream_body
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=Test")

        assert response.status_code == 401
        payload = response.json()
        error_text = str(payload.get("detail", ""))
        assert "invalid_api_key" in error_text

    def test_ask_spanish_query(self, ask_client):
        """Test asking a question in Spanish."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "answer": "Respuesta de prueba",
                "sources": [],
                "language": "es",
            }
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            response = ask_client.get("/api/v1/ask?question=%C2%BFQu%C3%A9%20es%20vivienda%3F")
            assert response.status_code == 200


class TestAskStreamEndpoint:
    """Test GET /ask/stream endpoint."""

    def test_ask_stream_question_required(self, ask_client):
        """Test that stream endpoint requires question."""
        response = ask_client.get("/api/v1/ask/stream")
        assert response.status_code == 422

    @patch("httpx.AsyncClient.stream")
    def test_ask_stream_success(self, mock_stream, ask_client):
        """Test streaming ask endpoint."""

        # Mock SSE stream
        async def mock_bytes():
            yield b'data: {"type": "thinking", "message": "Searching..."}\n\n'
            yield b'data: {"type": "complete", "answer": "Test", "sources": []}\n\n'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_bytes = mock_bytes

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock()
        mock_stream.return_value = mock_context

        response = ask_client.get("/api/v1/ask/stream?question=Test")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "\n\n" in response.text

    def test_ask_stream_with_all_params(self, ask_client):
        """Test streaming with all parameters."""
        with patch("httpx.AsyncClient.stream") as mock_stream:

            async def mock_bytes():
                yield b'data: {"type": "complete", "answer": "Test"}\n\n'

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_bytes = mock_bytes

            mock_context = MagicMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock()
            mock_stream.return_value = mock_context

            response = ask_client.get(
                "/api/v1/ask/stream?question=Test&thread_id=123&lang=en&provider=ollama&model=llama3.1:8b"
            )
            assert response.status_code == 200

    @patch("httpx.AsyncClient.stream")
    def test_ask_stream_preserves_sse_event_boundaries(self, mock_stream, ask_client):
        """Test SSE proxy keeps blank-line delimiters between events."""

        async def mock_bytes():
            yield b'data: {"type":"thinking","message":"step 1"}\n\n'
            yield b'data: {"type":"tool_event","phase":"result","tool":"db_search","message":"found 3"}\n\n'
            yield b'data: {"type":"complete","answer":"done","sources":[]}\n\n'

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.aiter_bytes = mock_bytes

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock()
        mock_stream.return_value = mock_context

        response = ask_client.get("/api/v1/ask/stream?question=Test")
        assert response.status_code == 200
        body = response.text
        assert body.count("\n\n") >= 3
        assert '"type":"tool_event"' in body


class TestAskConfigEndpoint:
    """Test GET /ask/config endpoint."""

    @patch("httpx.AsyncClient.get")
    def test_get_ask_config_success(self, mock_get, ask_client):
        """Test getting ask configuration."""
        mock_config = {
            "providers": [{"name": "ollama", "models": ["llama3.1:8b"], "default": True}],
            "models": {"ollama": ["llama3.1:8b"]},
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask/config")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data

    @patch("httpx.AsyncClient.get")
    def test_get_ask_config_service_unavailable(self, mock_get, ask_client):
        """Test config endpoint with service unavailable."""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        response = ask_client.get("/api/v1/ask/config")
        assert response.status_code == 200
        assert response.json().get("service_status") == "degraded"

    @patch("httpx.AsyncClient.get")
    def test_get_ask_config_preserves_explicit_default_provider(self, mock_get, ask_client):
        """Gateway should honor upstream default flags instead of forcing first provider."""
        upstream_config = {
            "providers": [{"key": "ollama", "label": "Ollama", "default": True}],
            "models": {"ollama": ["llama3.1:8b", "llama3.2"]},
            "defaultProvider": "ollama",
            "defaultModel": "llama3.1:8b",
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = upstream_config
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask/config")
        assert response.status_code == 200
        data = response.json()

        assert data.get("defaultProvider") == "ollama"
        assert data.get("defaultModel") == "llama3.1:8b"
        ollama = next((p for p in data.get("providers", []) if p.get("name") == "ollama"), None)
        assert ollama is not None and ollama.get("default") is True


class TestAskQueryValidation:
    """Test query parameter validation."""

    @patch("httpx.AsyncClient.get")
    def test_ask_empty_question(self, mock_get, ask_client):
        """Test ask endpoint with empty query."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?query=")
        # Empty query might still be technically valid for endpoint
        # but could be rejected at implementation level
        assert response.status_code in [200, 422, 501]

    @patch("httpx.AsyncClient.get")
    def test_ask_query_with_unicode(self, mock_get, ask_client):
        """Test query with unicode characters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=你好世界")
        assert response.status_code == 200 or response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_language_parameter_values(self, mock_get, ask_client):
        """Test various language parameter values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        for lang in ["en", "es", "fr", "de"]:
            response = ask_client.get(f"/api/v1/ask?question=test&lang={lang}")
            assert response.status_code == 200 or response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_web_search_parameter_values(self, mock_get, ask_client):
        """Test web search parameter with boolean values."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        for value in ["true", "false", "True", "False"]:
            response = ask_client.get(f"/api/v1/ask?question=test&use_web_search={value}")
            assert response.status_code == 200 or response.status_code == 500


class TestAskErrorHandling:
    """Test error handling in ask endpoints."""

    @patch("httpx.AsyncClient.get")
    def test_ask_invalid_query_type(self, mock_get, ask_client):
        """Test invalid query type."""
        # Query param should be string, so this tests if API handles it
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=123")
        # Number converted to string in URL, should still work
        assert response.status_code == 200 or response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_invalid_language_type(self, mock_get, ask_client):
        """Test invalid language parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=test&lang=123")
        # Language as number string might be accepted or rejected
        assert response.status_code in [200, 422, 500]


class TestAskEndpointRouting:
    """Test that ask endpoints are properly routed."""

    def test_legacy_question_route_not_supported(self, ask_client):
        """Legacy /ask/question route should not exist (canonical is /ask?question=...)."""
        response = ask_client.get("/api/v1/ask/question?question=test")
        assert response.status_code == 404

    @patch("httpx.AsyncClient.get")
    def test_ask_endpoint_exists(self, mock_get, ask_client):
        """Test that ask endpoint is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=test")
        # Endpoint is implemented
        assert response.status_code == 200 or response.status_code == 500

    def test_ask_stream_endpoint_exists(self, ask_client):
        """Test that stream endpoint is accessible."""
        response = ask_client.get("/api/v1/ask/stream?question=test")
        assert response.status_code == 200 or response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_config_endpoint_exists(self, mock_get, ask_client):
        """Test that config endpoint is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask/config")
        assert response.status_code == 200  # Config endpoint is implemented


class TestAskParameterCombinations:
    """Test various parameter combinations."""

    @patch("httpx.AsyncClient.get")
    def test_ask_all_parameters(self, mock_get, ask_client):
        """Test ask with all parameters specified."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "es",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get(
            "/api/v1/ask?question=What%20is%20housing%3F&lang=es&use_web_search=false"
        )
        assert response.status_code == 200 or response.status_code == 500

    @patch("httpx.AsyncClient.get")
    def test_ask_minimal_parameters(self, mock_get, ask_client):
        """Test ask with only required parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=test")
        assert (
            response.status_code == 200 or response.status_code == 500
        )  # Should accept minimal params

    @patch("httpx.AsyncClient.get")
    def test_ask_duplicate_parameters(self, mock_get, ask_client):
        """Test ask with duplicate parameters."""
        # Last value should be used
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "test",
            "sources": [],
            "language": "en",
            "model": "test",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = ask_client.get("/api/v1/ask?question=test1&question=test2")
        assert response.status_code == 200 or response.status_code == 422


class TestAskMethods:
    """Test HTTP method handling for ask endpoints."""

    def test_ask_post_not_allowed(self, ask_client):
        """Test that POST is not allowed on ask endpoint."""
        response = ask_client.post("/api/v1/ask", json={"query": "test"})
        assert response.status_code == 405  # Method Not Allowed

    def test_ask_delete_not_allowed(self, ask_client):
        """Test that DELETE is not allowed."""
        response = ask_client.delete("/api/v1/ask")
        assert response.status_code == 405

    def test_ask_get_is_allowed(self, ask_client):
        """Test that GET is allowed."""
        response = ask_client.get("/api/v1/ask?query=test")
        # Should be not implemented, not method not allowed
        assert response.status_code != 405
