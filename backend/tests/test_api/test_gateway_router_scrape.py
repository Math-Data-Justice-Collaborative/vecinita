"""
Unit tests for src/gateway/router_scrape.py

Tests async scraping endpoints and job management.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def scrape_client(env_vars, monkeypatch):
    """Create a test client with scrape router included.
    
    Mocks background_scrape_task to prevent jobs from immediately completing.
    In TestClient, background tasks run synchronously, so we need to mock them
    to test the initial 'queued' state.
    """
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Reset shared in-memory job state between tests
    from src.api.job_manager import job_manager
    job_manager.jobs.clear()

    # Mock background task to prevent immediate job completion
    # This allows us to test the 'queued' state
    with patch("src.api.router_scrape.background_scrape_task") as mock_bg_task:
        mock_bg_task.return_value = AsyncMock()
        
        from src.api.main import app
        client = TestClient(app)
        
        yield client


class TestScrapeSubmitEndpoint:
    """Test POST /scrape endpoint."""

    def test_submit_scrape_single_url(self, scrape_client):
        """Test submitting a scrape job with single URL."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] is not None
        assert data["status"] == "queued"
        assert "message" in data

    def test_submit_scrape_multiple_urls(self, scrape_client):
        """Test submitting a scrape job with multiple URLs."""
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": urls}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] is not None

    def test_submit_scrape_with_loader(self, scrape_client):
        """Test submitting scrape with specific loader."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={
                "urls": ["https://example.com"],
                "force_loader": "playwright"
            }
        )
        assert response.status_code == 200

    def test_submit_scrape_with_stream(self, scrape_client):
        """Test submitting scrape with streaming enabled."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={
                "urls": ["https://example.com"],
                "stream": True
            }
        )
        assert response.status_code == 200

    def test_submit_scrape_missing_urls(self, scrape_client):
        """Test that submitting without URLs fails."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={}
        )
        assert response.status_code == 422

    def test_submit_scrape_empty_urls(self, scrape_client):
        """Test that submitting with empty URLs list fails."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": []}
        )
        # Pydantic validation returns 422 (Unprocessable Entity), not 400
        assert response.status_code == 422

    def test_submit_scrape_invalid_url_format(self, scrape_client):
        """Test that invalid URL format is rejected."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["not-a-url"]}
        )
        # Endpoint validation returns 400 (custom business logic validation)
        assert response.status_code == 400

    def test_submit_scrape_too_many_urls(self, scrape_client):
        """Test that too many URLs are rejected."""
        # Create 101 URLs (max is 100)
        urls = [f"https://example.com/{i}" for i in range(101)]
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": urls}
        )
        # Endpoint validation returns 400 (custom business logic validation)
        assert response.status_code == 400

    def test_submit_scrape_returns_job_id(self, scrape_client):
        """Test that response includes job ID."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        data = response.json()
        # Job ID should be a non-empty string (UUID format)
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) > 0


class TestScrapeStatusEndpoint:
    """Test GET /scrape/{job_id} endpoint."""

    def test_get_scrape_status_queued(self, scrape_client):
        """Test getting status of queued job."""
        # First submit a job
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        job_id = response.json()["job_id"]

        # Get status
        response = scrape_client.get(f"/api/v1/scrape/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job"]["job_id"] == job_id
        assert data["job"]["status"] == "queued"

    def test_get_scrape_status_nonexistent(self, scrape_client):
        """Test getting status of nonexistent job."""
        response = scrape_client.get("/api/v1/scrape/nonexistent-job-id")
        assert response.status_code == 404

    def test_get_scrape_status_includes_metadata(self, scrape_client):
        """Test that job status includes metadata."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com", "https://example.org"]}
        )
        job_id = response.json()["job_id"]

        response = scrape_client.get(f"/api/v1/scrape/{job_id}")
        data = response.json()
        job = data["job"]

        assert "metadata" in job
        assert job["metadata"]["urls"] == ["https://example.com", "https://example.org"]
        assert job["metadata"]["created_at"] is not None

    def test_get_scrape_status_includes_progress(self, scrape_client):
        """Test that status includes progress percentage."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        job_id = response.json()["job_id"]

        response = scrape_client.get(f"/api/v1/scrape/{job_id}")
        data = response.json()
        job = data["job"]

        assert "progress_percent" in job
        assert 0 <= job["progress_percent"] <= 100


class TestScrapeHistoryEndpoint:
    """Test GET /scrape/history endpoint."""

    def test_get_scrape_history_empty(self, scrape_client):
        """Test getting history when no jobs exist."""
        response = scrape_client.get("/api/v1/scrape/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_get_scrape_history_multiple(self, scrape_client):
        """Test getting history with multiple jobs."""
        # Submit 3 jobs
        for i in range(3):
            scrape_client.post(
                "/api/v1/scrape",
                json={"urls": [f"https://example.com/{i}"]}
            )

        response = scrape_client.get("/api/v1/scrape/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

    def test_get_scrape_history_pagination(self, scrape_client):
        """Test history pagination."""
        # Submit 25 jobs
        for i in range(25):
            scrape_client.post(
                "/api/v1/scrape",
                json={"urls": [f"https://example.com/{i}"]}
            )

        # Request first page
        response = scrape_client.get("/api/v1/scrape/history?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 10
        assert data["total"] == 25

        # Request second page
        response = scrape_client.get("/api/v1/scrape/history?limit=10&offset=10")
        data = response.json()
        assert len(data["jobs"]) == 10

    def test_get_scrape_history_most_recent_first(self, scrape_client):
        """Test that history is ordered with most recent first."""
        job_ids = []
        for i in range(3):
            response = scrape_client.post(
                "/api/v1/scrape",
                json={"urls": [f"https://example.com/{i}"]}
            )
            job_ids.append(response.json()["job_id"])

        response = scrape_client.get("/api/v1/scrape/history")
        data = response.json()
        # Most recent should be first
        history_ids = [job["job_id"] for job in data["jobs"]]
        assert history_ids[0] == job_ids[-1]


class TestScrapeCancelEndpoint:
    """Test POST /scrape/{job_id}/cancel endpoint."""

    def test_cancel_scrape_job(self, scrape_client):
        """Test cancelling a scrape job."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        job_id = response.json()["job_id"]

        response = scrape_client.post(f"/api/v1/scrape/{job_id}/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["job"]["status"] == "cancelled"

    def test_cancel_nonexistent_job(self, scrape_client):
        """Test cancelling nonexistent job fails."""
        response = scrape_client.post("/api/v1/scrape/nonexistent-job-id/cancel")
        assert response.status_code == 400

    def test_cancel_job_sets_cancelled_timestamp(self, scrape_client):
        """Test that cancelled timestamp is set."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={"urls": ["https://example.com"]}
        )
        job_id = response.json()["job_id"]

        scrape_client.post(f"/api/v1/scrape/{job_id}/cancel")

        response = scrape_client.get(f"/api/v1/scrape/{job_id}")
        data = response.json()
        assert data["job"]["metadata"]["cancelled_at"] is not None


class TestScrapeStatsEndpoint:
    """Test GET /scrape/stats endpoint."""

    def test_get_scrape_stats(self, scrape_client):
        """Test getting scrape statistics."""
        response = scrape_client.get("/api/v1/scrape/stats")
        assert response.status_code == 200
        data = response.json()

        assert "total_jobs" in data
        assert "by_status" in data
        assert "retention_hours" in data

    def test_scrape_stats_reflects_jobs(self, scrape_client):
        """Test that stats reflect submitted jobs."""
        # Submit jobs
        for i in range(5):
            scrape_client.post(
                "/api/v1/scrape",
                json={"urls": [f"https://example.com/{i}"]}
            )

        response = scrape_client.get("/api/v1/scrape/stats")
        data = response.json()
        assert data["total_jobs"] == 5


class _FakeReindexResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("http error")

    def json(self):
        return self._payload


class _FakeReindexClient:
    def __init__(self, *args, **kwargs):
        self.captured = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, headers=None):
        return _FakeReindexResponse(
            {
                "status": "queued",
                "call_id": "fc-test-123",
                "url": url,
                "params": params,
                "headers": headers or {},
            }
        )


class TestReindexEndpoint:
    def test_reindex_requires_service_url(self, scrape_client, monkeypatch):
        from src.api import router_scrape

        monkeypatch.setattr(router_scrape, "REINDEX_SERVICE_URL", "")
        response = scrape_client.post("/api/v1/scrape/reindex")
        assert response.status_code == 503

    def test_reindex_calls_modal_service(self, scrape_client, monkeypatch):
        from src.api import router_scrape

        monkeypatch.setattr(router_scrape, "REINDEX_SERVICE_URL", "https://reindex.modal.run")
        monkeypatch.setattr(router_scrape, "REINDEX_TRIGGER_TOKEN", "token-123")
        monkeypatch.setattr(router_scrape.httpx, "AsyncClient", _FakeReindexClient)

        response = scrape_client.post("/api/v1/scrape/reindex?clean=true&verbose=true")
        assert response.status_code == 200
        payload = response.json()

        assert payload["status"] == "queued"
        assert payload["call_id"] == "fc-test-123"
        assert payload["service_url"] == "https://reindex.modal.run"
        assert payload["params"]["clean"] is True
        assert payload["headers"]["x-reindex-token"] == "token-123"


class TestScrapeCleanupEndpoint:
    """Test POST /scrape/cleanup endpoint."""

    def test_cleanup_old_jobs(self, scrape_client):
        """Test cleanup endpoint."""
        response = scrape_client.post("/api/v1/scrape/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_jobs" in data
        assert "message" in data


class TestScrapeErrorHandling:
    """Test error handling in scrape endpoints."""

    def test_invalid_loader_type(self, scrape_client):
        """Test error with invalid loader type."""
        response = scrape_client.post(
            "/api/v1/scrape",
            json={
                "urls": ["https://example.com"],
                "force_loader": "invalid_type"
            }
        )
        # Validation error
        assert response.status_code == 422

    def test_malformed_json(self, scrape_client):
        """Test error with malformed JSON."""
        response = scrape_client.post(
            "/api/v1/scrape",
            content="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
