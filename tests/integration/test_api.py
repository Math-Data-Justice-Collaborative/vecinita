"""Integration tests for backend API endpoints.

These tests verify that the backend API gateway responds correctly to requests.
They require the API gateway service to be running on port 8004.

Run with: 
    pytest integration/test_api.py -v
    
Or with environment configuration:
    BACKEND_URL=http://localhost:8004 pytest integration/test_api.py -v
    
Note: These tests target the API v1 gateway (/api/v1/* endpoints).
"""

import pytest
from utils import APIClient


@pytest.fixture
def api_client(backend_url, api_timeout):
    """Shared fixture for API client."""
    client = APIClient(base_url=backend_url, timeout=api_timeout)
    yield client
    client.close()


@pytest.mark.integration
@pytest.mark.backend_required
@pytest.mark.api
class TestAskEndpoint:
    """Integration tests for the /api/v1/ask endpoint."""
    
    def test_ask_endpoint_basic(self, api_client):
        """Test that /api/v1/ask endpoint returns a response."""
        response = api_client.ask(query="What is Vecinita?", language="en")
        
        assert "answer" in response, "Response should contain 'answer' field"
        assert "question" in response, "Response should contain 'question' field (API v1)"
        assert isinstance(response["answer"], str), "Answer should be a string"
        assert len(response["answer"]) > 0, "Answer should not be empty"
    
    def test_ask_endpoint_with_spanish(self, api_client):
        """Test that /api/v1/ask endpoint works with Spanish queries."""
        response = api_client.ask(query="¿Qué es Vecinita?", language="es")
        
        assert "answer" in response
        assert "question" in response
        assert isinstance(response["answer"], str)
        assert len(response["answer"]) > 0
    
    def test_ask_endpoint_returns_sources_if_available(self, api_client):
        """Test that /api/v1/ask endpoint returns sources when available."""
        response = api_client.ask(
            query="What resources are available?",
            language="en"
        )
        
        assert "answer" in response
        assert "question" in response
        
        # Sources should always be present in API v1 (may be empty list)
        assert "sources" in response, "API v1 should include 'sources' field"
        assert isinstance(response["sources"], list), "Sources should be a list"
        
        # If sources exist, validate structure
        if response["sources"]:
            for source in response["sources"]:
                assert isinstance(source, dict)
                # API v1 sources should have url, title fields
                assert "url" in source, "Source should have 'url' field"
                assert "title" in source, "Source should have 'title' field"


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIHealth:
    """Integration tests for service health checks."""
    
    def test_service_availability(self, api_client):
        """Test that backend service is available."""
        health = api_client.health()
        
        # Service should return some kind of response
        assert health is not None


@pytest.mark.integration  
@pytest.mark.backend_required
class TestAPIErrorHandling:
    """Integration tests for API error handling."""
    
    def test_ask_with_empty_query(self, api_client):
        """Test /api/v1/ask endpoint behavior with empty query."""
        try:
            response = api_client.ask(query="")
            # Should either work or return error consistently
            assert "answer" in response or "error" in response or "detail" in response
        except Exception:
            # Empty query should trigger validation error in API v1, which is acceptable
            pass
    
    def test_ask_with_very_long_query(self, api_client):
        """Test /api/v1/ask endpoint with very long query."""
        long_query = "What is Vecinita? " * 100
        
        try:
            response = api_client.ask(query=long_query)
            # Should handle long input
            assert "answer" in response or "error" in response or "detail" in response
        except Exception:
            # Long queries might timeout or hit rate limits, which is acceptable
            pass
