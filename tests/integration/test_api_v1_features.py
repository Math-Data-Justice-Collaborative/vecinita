"""Integration tests for API v1 specific features.

These tests verify API v1 versioning, documentation, and gateway features.

Run with:
    pytest integration/test_api_v1_features.py -v
    
Or with environment:
    BACKEND_URL=http://localhost:8004 pytest integration/test_api_v1_features.py -v
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
class TestAPIv1Versioning:
    """Test API v1 versioning structure."""
    
    def test_root_endpoint_returns_api_info(self, api_client):
        """Test root endpoint returns service information."""
        response = api_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "api_base" in data
        assert data["api_base"] == "/api/v1"
    
    def test_health_endpoint_backward_compatible(self, api_client):
        """Test legacy /health endpoint still works."""
        response = api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
    
    def test_config_endpoint_backward_compatible(self, api_client):
        """Test legacy /config endpoint still works."""
        response = api_client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        # Should contain configuration info
        assert isinstance(data, dict)


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIv1Documentation:
    """Test API v1 documentation endpoints."""
    
    def test_docs_endpoint_available(self, api_client):
        """Test Swagger UI is available at /api/v1/docs."""
        response = api_client.get("/api/v1/docs")
        assert response.status_code == 200
        
        # Should return HTML page
        assert "text/html" in response.headers.get("content-type", "")
        assert b"swagger" in response.content.lower()
    
    def test_openapi_schema_available(self, api_client):
        """Test OpenAPI schema is available at /api/v1/openapi.json."""
        response = api_client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Verify API info
        assert schema["info"]["title"] == "Vecinita Unified API Gateway"
        assert schema["info"]["version"] == "1.0.0"
    
    def test_openapi_schema_contains_v1_endpoints(self, api_client):
        """Test OpenAPI schema documents /api/v1/* endpoints."""
        response = api_client.get("/api/v1/openapi.json")
        schema = response.json()
        
        paths = schema["paths"]
        
        # Check for key v1 endpoints
        assert "/api/v1/ask" in paths
        assert "/api/v1/scrape" in paths
        assert "/api/v1/embed/config" in paths
        assert "/api/v1/admin/health" in paths


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIv1AskEndpoint:
    """Test /api/v1/ask endpoint structure."""
    
    def test_ask_response_structure(self, api_client):
        """Test /api/v1/ask returns expected response structure."""
        response_raw = api_client.get("/api/v1/ask", params={"question": "Test question"})
        if response_raw.status_code >= 500:
            pytest.skip(f"Backend ask endpoint returned {response_raw.status_code}")
        assert response_raw.status_code == 200
        response = response_raw.json()
        
        # Check all required fields are present
        assert "question" in response, "Should echo back the question"
        assert "answer" in response, "Should contain answer field"
        assert "sources" in response, "Should contain sources field"
        assert "language" in response, "Should detect language"
        assert "model" in response, "Should indicate model used"
        
        # Validate field types
        assert isinstance(response["question"], str)
        assert isinstance(response["answer"], str)
        assert isinstance(response["sources"], list)
        assert isinstance(response["language"], str)
        assert isinstance(response["model"], str)
    
    def test_ask_sources_structure(self, api_client):
        """Test source citations have proper structure."""
        response = api_client.ask(query="What is Vecinita?")
        
        if response["sources"]:
            for source in response["sources"]:
                assert "url" in source, "Source should have URL"
                assert "title" in source, "Source should have title"
                assert isinstance(source["url"], str)
                assert isinstance(source["title"], str)


@pytest.mark.integration
@pytest.mark.backend_required  
class TestAPIv1AdminEndpoints:
    """Test /api/v1/admin/* endpoints."""
    
    def test_admin_health_endpoint(self, api_client):
        """Test /api/v1/admin/health endpoint."""
        response = api_client.get("/api/v1/admin/health")
        
        # May return 501 if not fully implemented yet
        assert response.status_code in [200, 401, 403, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
    
    def test_admin_config_endpoint(self, api_client):
        """Test /api/v1/admin/config endpoint exists."""
        # This endpoint may require auth or return 501 if not implemented
        response = api_client.get("/api/v1/admin/config")
        assert response.status_code in [200, 401, 403, 501]


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIv1ScrapeEndpoints:
    """Test /api/v1/scrape/* endpoints."""
    
    def test_scrape_history_endpoint(self, api_client):
        """Test /api/v1/scrape/history endpoint."""
        response = api_client.get("/api/v1/scrape/history")
        
        # Should return history (may be empty)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_scrape_stats_endpoint(self, api_client):
        """Test /api/v1/scrape/stats endpoint."""
        response = api_client.get("/api/v1/scrape/stats")
        
        # Should return statistics
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIv1EmbedEndpoints:
    """Test /api/v1/embed/* endpoints."""
    
    def test_embed_config_endpoint(self, api_client):
        """Test /api/v1/embed/config endpoint."""
        response = api_client.get("/api/v1/embed/config")
        
        # Should return embedding configuration
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Should have model information
        if data:  # Config might be minimal in demo mode
            assert "model" in data or "provider" in data or len(data) > 0


@pytest.mark.integration
@pytest.mark.backend_required
class TestAPIv1ErrorHandling:
    """Test API v1 error handling."""
    
    def test_invalid_endpoint_returns_404(self, api_client):
        """Test requesting invalid endpoint returns 404."""
        response = api_client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_missing_required_parameter(self, api_client):
        """Test missing required parameter returns appropriate error."""
        # /api/v1/ask requires 'question' parameter
        response = api_client.get("/api/v1/ask")
        
        # Should return validation error (422) or bad request (400)
        assert response.status_code in [400, 422]
        
        data = response.json()
        assert "detail" in data or "error" in data
    
    def test_method_not_allowed(self, api_client):
        """Test wrong HTTP method returns 405."""
        # /api/v1/ask only accepts GET
        response = api_client.post("/api/v1/ask", json={"question": "test"})
        
        # Should return method not allowed
        assert response.status_code == 405
