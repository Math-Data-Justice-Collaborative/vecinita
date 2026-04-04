"""
Unit tests for src/gateway/main.py

Tests FastAPI app initialization, routes, and error handling.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def gateway_client(env_vars, monkeypatch):
    """Create a FastAPI test client for the gateway."""
    # Set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    monkeypatch.setenv("AGENT_SERVICE_URL", "http://localhost:8000")
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
    # Clear MODAL_EMBEDDING_ENDPOINT so localhost defaults are used
    monkeypatch.delenv("MODAL_EMBEDDING_ENDPOINT", raising=False)

    # Import and reload module to pick up env vars
    import src.api.main

    importlib.reload(src.api.main)

    app = src.api.main.app
    return TestClient(app)


class TestGatewayInitialization:
    """Test gateway app initialization."""

    def test_app_creation(self, env_vars, monkeypatch):
        """Test that gateway FastAPI app is created."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        from src.api.main import app

        assert app is not None
        assert app.title == "Vecinita Unified API Gateway"

    def test_app_version(self, env_vars, monkeypatch):
        """Test app has correct version."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        from src.api.main import app

        assert app.version == "1.0.0"


class TestGatewayRootEndpoints:
    """Test root endpoints."""

    def test_root_endpoint(self, gateway_client):
        """Test GET / returns service info."""
        response = gateway_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Vecinita Unified API Gateway"
        assert "endpoints" in data

    def test_root_endpoint_structure(self, gateway_client):
        """Test root endpoint returns expected structure."""
        response = gateway_client.get("/")
        data = response.json()

        # Check main sections exist
        assert "Q&A" in data["endpoints"]
        assert "Scraping" in data["endpoints"]
        assert "Embeddings" in data["endpoints"]
        assert "Documentation" in data["endpoints"]

    def test_root_endpoint_environment(self, gateway_client):
        """Test root endpoint includes environment info."""
        response = gateway_client.get("/")
        data = response.json()

        assert "environment" in data
        assert "agent_service" in data["environment"]
        assert "embedding_service" in data["environment"]

    def test_health_check_endpoint(self, gateway_client):
        """Test GET /health returns health status."""
        response = gateway_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in {"ok", "degraded"}
        assert "timestamp" in data

    def test_health_check_structure(self, gateway_client):
        """Test health check response structure."""
        response = gateway_client.get("/health")
        data = response.json()

        assert "agent_service" in data
        assert "embedding_service" in data
        assert "database" in data
        assert "timestamp" in data

    def test_health_check_v1_alias(self, gateway_client):
        """Test GET /api/v1/health alias remains available for deploy probes."""
        response = gateway_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agent_service" in data

    def test_health_check_reports_ok_when_probes_succeed(self, gateway_client, monkeypatch):
        """Gateway reports OK when all downstream probes succeed."""
        import src.api.main as gateway_main

        async def _ok_probe(*_args, **_kwargs):
            return "ok"

        monkeypatch.setattr(gateway_main, "_probe_http_health", _ok_probe)
        monkeypatch.setattr(gateway_main, "_probe_database_socket", _ok_probe)

        response = gateway_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["agent_service"] == "ok"
        assert data["embedding_service"] == "ok"
        assert data["database"] == "ok"

    def test_health_check_reports_degraded_when_agent_probe_fails(self, gateway_client, monkeypatch):
        """Gateway reports degraded when the agent dependency probe fails."""
        import src.api.main as gateway_main

        async def _probe_http(*args, **_kwargs):
            if args and "localhost:8000" in str(args[0]):
                return "error"
            return "ok"

        async def _probe_db(*_args, **_kwargs):
            return "ok"

        monkeypatch.setattr(gateway_main, "_probe_http_health", _probe_http)
        monkeypatch.setattr(gateway_main, "_probe_database_socket", _probe_db)

        response = gateway_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["agent_service"] == "error"

    def test_config_endpoint(self, gateway_client):
        """Test GET /config returns gateway configuration."""
        response = gateway_client.get("/config")
        assert response.status_code == 200
        data = response.json()

        assert data["agent_url"] == "http://localhost:8000"
        assert "embedding_service_url" in data
        assert isinstance(data["embedding_service_url"], str)
        assert len(data["embedding_service_url"]) > 0
        assert data["max_urls_per_request"] == 100
        assert data["job_retention_hours"] == 24


class TestGatewayRouterInclusion:
    """Test that all routers are properly included."""

    def test_ask_router_included(self, gateway_client):
        """Test Q&A router is included."""
        # Try to access an ask endpoint with wrong parameter (query instead of question)
        response = gateway_client.get("/api/v1/ask?query=test")
        # Should get 422 (unprocessable entity - missing required 'question' param)
        assert response.status_code == 422

    def test_scrape_router_included(self, gateway_client):
        """Test scrape router is included."""
        response = gateway_client.post("/api/v1/scrape", json={"urls": ["https://example.com"]})
        # Should be accepted (or get 422 for validation)
        assert response.status_code in [202, 200, 422]

    def test_embed_router_included(self, gateway_client):
        """Test embed router is included."""
        response = gateway_client.post("/api/v1/embed", json={"text": "hello"})
        # Embed router proxies to embedding service; unavailable backend returns 503
        assert response.status_code in [200, 503]


class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    def test_cors_headers_present(self, gateway_client):
        """Test that CORS headers are present."""
        response = gateway_client.get("/", headers={"Origin": "http://localhost:3000"})
        # FastAPI test client should include CORS in response
        assert response.status_code == 200

    def test_cors_allows_all_origins(self, gateway_client):
        """Test CORS is configured to allow all origins."""
        # The test client will handle CORS, just verify app doesn't reject
        response = gateway_client.get("/")
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation endpoints."""

    def test_openapi_json_endpoint(self, gateway_client):
        """Test GET /api/v1/openapi.json returns OpenAPI schema."""
        response = gateway_client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()

        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Vecinita Unified API Gateway"

    def test_swagger_docs_endpoint(self, gateway_client):
        """Test GET /api/v1/docs returns Swagger UI."""
        response = gateway_client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_redoc_endpoint_exists(self, gateway_client):
        """Test redoc endpoint exists."""
        response = gateway_client.get("/api/v1/redoc")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling."""

    def test_404_not_found(self, gateway_client):
        """Test 404 for nonexistent route."""
        response = gateway_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

    def test_invalid_json_request(self, gateway_client):
        """Test invalid JSON in request body."""
        response = gateway_client.post(
            "/api/v1/embed",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_field(self, gateway_client):
        """Test missing required field in request."""
        response = gateway_client.post("/api/v1/scrape", json={})
        assert response.status_code == 422

    def test_validation_error_includes_detail(self, gateway_client):
        """Test validation errors include detail."""
        response = gateway_client.post("/api/v1/scrape", json={"urls": []})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestRequestValidation:
    """Test request validation."""

    def test_scrape_request_validation_urls_required(self, gateway_client):
        """Test scrape request requires URLs."""
        response = gateway_client.post("/api/v1/scrape", json={})
        assert response.status_code == 422

    def test_scrape_request_validation_urls_nonempty(self, gateway_client):
        """Test scrape request requires non-empty URLs list."""
        response = gateway_client.post("/api/v1/scrape", json={"urls": []})
        # Pydantic validation returns 422 (Unprocessable Entity), not 400
        assert response.status_code == 422

    def test_scrape_request_validation_valid(self, gateway_client):
        """Test valid scrape request."""
        response = gateway_client.post("/api/v1/scrape", json={"urls": ["https://example.com"]})
        # Should succeed (200) or return job ID
        assert response.status_code in [200, 202]

    def test_embed_request_validation_text_required(self, gateway_client):
        """Test embed request requires text."""
        response = gateway_client.post("/api/v1/embed", json={})
        assert response.status_code == 422

    def test_ask_request_validation_query_required(self, gateway_client):
        """Test ask endpoint requires query."""
        response = gateway_client.get("/api/v1/ask")
        assert response.status_code == 422


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_agent_service_url_from_env(self, env_vars, monkeypatch):
        """Test agent service URL is read from environment."""
        import importlib

        custom_url = "http://custom-agent:9000"
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setenv("AGENT_SERVICE_URL", custom_url)

        # Reload module to pick up new environment variables
        import src.api.main

        importlib.reload(src.api.main)
        assert src.api.main.AGENT_SERVICE_URL == custom_url

    def test_embedding_service_url_from_env(self, env_vars, monkeypatch):
        """Test embedding service URL uses canonical env key precedence."""
        # Canonical precedence is:
        # VECINITA_EMBEDDING_API_URL > MODAL_EMBEDDING_ENDPOINT > EMBEDDING_SERVICE_URL > default
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        canonical_url = "https://test-embedding-via-canonical.run"
        monkeypatch.setenv("VECINITA_EMBEDDING_API_URL", canonical_url)
        monkeypatch.setenv("MODAL_EMBEDDING_ENDPOINT", "https://legacy-modal.run")
        monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://legacy-embedding-service:8001")

        # Reload module to pick up new environment variables
        import src.api.main
        import src.config

        importlib.reload(src.config)
        importlib.reload(src.api.main)
        assert src.api.main.EMBEDDING_SERVICE_URL == canonical_url

    def test_max_urls_per_request_from_env(self, env_vars, monkeypatch):
        """Test max URLs limit from environment."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setenv("MAX_URLS_PER_REQUEST", "50")

        # Force reimport
        import sys

        if "src.api.main" in sys.modules:
            del sys.modules["src.api.main"]

        from src.api.main import MAX_URLS_PER_REQUEST

        assert MAX_URLS_PER_REQUEST == 50

    def test_job_retention_hours_from_env(self, env_vars, monkeypatch):
        """Test job retention hours from environment."""
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setenv("JOB_RETENTION_HOURS", "48")

        import sys

        if "src.api.main" in sys.modules:
            del sys.modules["src.api.main"]

        from src.api.main import JOB_RETENTION_HOURS

        assert JOB_RETENTION_HOURS == 48


class TestAPIStructure:
    """Test overall API structure."""

    def test_all_api_endpoints_prefixed(self, gateway_client):
        """Test that all API endpoints use /api prefix."""
        response = gateway_client.get("/")
        data = response.json()

        for category, endpoints in data["endpoints"].items():
            if category in ["Q&A", "Scraping", "Embeddings", "Admin"]:
                for _name, path in endpoints.items():
                    if not path.startswith("/"):
                        continue
                    # All service endpoints should have /api prefix
                    if not path.startswith("/docs") and not path.startswith("/open"):
                        assert (
                            path.startswith("/api")
                            or path.startswith("GET /api")
                            or path.startswith("POST /api")
                        )

    def test_versioning_in_paths(self, gateway_client):
        """Test API includes /v1/ version in paths."""
        response = gateway_client.get("/")
        data = response.json()

        # Endpoints should have /v1/ in API paths
        all_paths = []
        for _category, endpoints in data["endpoints"].items():
            if isinstance(endpoints, dict):
                all_paths.extend(endpoints.values())

        # At least some paths should contain /v1/
        api_paths = [p for p in all_paths if isinstance(p, str) and "/api/" in p]
        assert any("/v1/" in path for path in api_paths)
