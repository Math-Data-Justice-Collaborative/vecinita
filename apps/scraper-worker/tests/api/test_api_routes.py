"""Tests for REST API routes and endpoints."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from vecinita_scraper.api.server import create_app
from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.models import JobStatus


@pytest.fixture
def client(monkeypatch):
    """Create FastAPI test client."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SCRAPER_DEBUG_BYPASS_AUTH", "true")
    # Submit tests mock Postgres; unset gateway persist so CI env does not skip DB create.
    monkeypatch.delenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", raising=False)
    monkeypatch.delenv("SCRAPER_API_KEYS", raising=False)
    get_config.cache_clear()
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_client(monkeypatch):
    """Create FastAPI test client with auth enforcement enabled."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SCRAPER_DEBUG_BYPASS_AUTH", "false")
    monkeypatch.delenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", raising=False)
    monkeypatch.setenv("SCRAPER_API_KEYS", "test-api-key")
    get_config.cache_clear()
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_config_cache_after_test():
    """Avoid cross-test env leakage through config cache."""
    yield
    get_config.cache_clear()


@pytest.fixture
def mock_db_for_api():
    """Mock database for API tests."""
    db = AsyncMock()
    db.create_scraping_job = AsyncMock(return_value="test-job-id-123")
    db.get_job_status = AsyncMock(
        return_value={
            "id": "test-job-id-123",
            "url": "https://example.com",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error_message": None,
            "crawl_url_count": 0,
            "chunk_count": 0,
            "embedding_count": 0,
        }
    )
    db.update_job_status = AsyncMock()
    return db


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_root_public_without_auth(self, auth_client):
        """Service root is public so the Render URL is not a bare 401 in a browser."""
        response = auth_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "vecinita-scraper"
        assert "/health" in data.values()

    def test_health_check(self, client):
        """Health check should return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "vecinita-scraper"


class TestAuthMiddleware:
    """Test auth middleware behavior."""

    def test_requires_authorization_header(self, auth_client):
        """Protected routes require a valid Authorization header."""
        response = auth_client.get("/jobs")
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing or invalid Authorization header"

    def test_rejects_invalid_api_key(self, auth_client):
        """Protected routes reject unknown API keys."""
        response = auth_client.get("/jobs", headers={"Authorization": "Bearer wrong-key"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid API key"

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_accepts_valid_api_key(self, mock_db_class, auth_client, mock_db_for_api):
        """Protected routes accept configured API keys."""
        mock_db_class.return_value = mock_db_for_api
        response = auth_client.get("/jobs", headers={"Authorization": "Bearer test-api-key"})
        assert response.status_code == 200

    def test_bypass_not_allowed_outside_dev(self, monkeypatch):
        """Bypass mode should fail config validation outside local/dev/test environments."""
        from vecinita_scraper.core.errors import ConfigError

        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("SCRAPER_DEBUG_BYPASS_AUTH", "true")
        get_config.cache_clear()

        with pytest.raises(ConfigError):
            create_app()


class TestSubmitJob:
    """Test job submission endpoint."""

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    @patch("vecinita_scraper.api.routes.scrape_jobs_queue")
    def test_submit_job_minimal(
        self, mock_queue, mock_db_class, client, mock_db_for_api, monkeypatch
    ):
        """Submit job with minimal config should succeed."""
        monkeypatch.setenv("MODAL_SCRAPER_FORCE_QUEUE_DISPATCH", "1")
        mock_db_class.return_value = mock_db_for_api
        mock_queue.put = AsyncMock()
        mock_queue.put.aio = AsyncMock()

        response = client.post(
            "/jobs",
            json={
                "url": "https://example.com",
                "user_id": "user-123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == "test-job-id-123"
        assert data["status"] == JobStatus.PENDING
        assert "created_at" in data
        assert data["url"] == "https://example.com/"

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    @patch("vecinita_scraper.api.routes.scrape_jobs_queue")
    def test_submit_job_with_configs(
        self, mock_queue, mock_db_class, client, mock_db_for_api, monkeypatch
    ):
        """Submit job with custom crawl and chunking configs."""
        monkeypatch.setenv("MODAL_SCRAPER_FORCE_QUEUE_DISPATCH", "1")
        mock_db_class.return_value = mock_db_for_api
        mock_queue.put = AsyncMock()
        mock_queue.put.aio = AsyncMock()

        response = client.post(
            "/jobs",
            json={
                "url": "https://example.com",
                "user_id": "user-123",
                "crawl_config": {
                    "max_depth": 2,
                    "timeout_seconds": 120,
                    "headless": True,
                },
                "chunking_config": {
                    "min_size_tokens": 256,
                    "max_size_tokens": 2048,
                    "overlap_ratio": 0.1,
                },
                "metadata": {"source": "api_test"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == "test-job-id-123"

        # Verify database was called with configs
        mock_db_for_api.create_scraping_job.assert_called_once()
        call_args = mock_db_for_api.create_scraping_job.call_args
        assert call_args[1]["url"] == "https://example.com/"
        assert call_args[1]["metadata"]["source"] == "api_test"

    def test_submit_job_invalid_url(self, client):
        """Submit job with invalid URL should fail."""
        response = client.post(
            "/jobs",
            json={
                "url": "not-a-url",
                "user_id": "user-123",
            },
        )

        assert response.status_code == 422

    def test_submit_job_missing_user_id(self, client):
        """Submit job without user_id should fail."""
        response = client.post(
            "/jobs",
            json={"url": "https://example.com"},
        )

        assert response.status_code == 422

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_submit_job_database_error(self, mock_db_class, client):
        """Submit job with database error should return 500."""
        from vecinita_scraper.core.errors import DatabaseError

        mock_db = AsyncMock()
        mock_db.create_scraping_job = AsyncMock(side_effect=DatabaseError("Connection failed"))
        mock_db_class.return_value = mock_db

        response = client.post(
            "/jobs",
            json={
                "url": "https://example.com",
                "user_id": "user-123",
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]


class TestPollSpawnResult:
    """``GET /jobs/spawns/{call_id}`` mirrors Modal ``FunctionCall.get(timeout=0)``."""

    def test_poll_spawn_pending_returns_202(self, client, monkeypatch):
        import modal

        fc = MagicMock()

        async def _pending(*, timeout: float = 0, **_kwargs: object) -> None:
            raise TimeoutError()

        fc.get.aio = _pending
        monkeypatch.setattr(modal.FunctionCall, "from_id", lambda _cid: fc)

        response = client.get("/jobs/spawns/fc-test123")
        assert response.status_code == 202
        assert response.content == b""

    def test_poll_spawn_completed_returns_json(self, client, monkeypatch):
        import modal

        fc = MagicMock()

        async def _done(*, timeout: float = 0, **_kwargs: object) -> dict[str, object]:
            return {"job_id": "j1", "pages_crawled": 1}

        fc.get.aio = _done
        monkeypatch.setattr(modal.FunctionCall, "from_id", lambda _cid: fc)

        response = client.get("/jobs/spawns/fc-test456")
        assert response.status_code == 200
        assert response.json() == {"job_id": "j1", "pages_crawled": 1}

    def test_poll_spawn_expired_returns_404(self, client, monkeypatch):
        import modal
        from modal.exception import OutputExpiredError

        fc = MagicMock()

        async def _expired(*, timeout: float = 0, **_kwargs: object) -> None:
            raise OutputExpiredError()

        fc.get.aio = _expired
        monkeypatch.setattr(modal.FunctionCall, "from_id", lambda _cid: fc)

        response = client.get("/jobs/spawns/fc-expired")
        assert response.status_code == 404


class TestGetJobStatus:
    """Test job status retrieval endpoint."""

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_pending(self, mock_db_class, client, mock_db_for_api):
        """Get status of pending job."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "url": "https://example.com",
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error_message": None,
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.get("/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == JobStatus.PENDING
        assert data["progress_pct"] == 5

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_crawling(self, mock_db_class, client, mock_db_for_api):
        """Get status of crawling job shows correct progress."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.CRAWLING,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.get("/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == JobStatus.CRAWLING
        assert data["progress_pct"] == 20

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_completed(self, mock_db_class, client, mock_db_for_api):
        """Get status of completed job shows 100% progress."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.COMPLETED,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.get("/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == JobStatus.COMPLETED
        assert data["progress_pct"] == 100

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_failed(self, mock_db_class, client, mock_db_for_api):
        """Get status of failed job includes error message."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.FAILED,
            "error_message": "Connection timeout",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.get("/jobs/job-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == JobStatus.FAILED
        assert data["error_message"] == "Connection timeout"

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_not_found(self, mock_db_class, client):
        """Get status of nonexistent job returns 404."""
        mock_db = AsyncMock()
        mock_db.get_job_status = AsyncMock(return_value=None)
        mock_db_class.return_value = mock_db

        response = client.get("/jobs/nonexistent-job")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_get_job_status_database_error(self, mock_db_class, client):
        """Get status with database error returns 500."""
        from vecinita_scraper.core.errors import DatabaseError

        mock_db = AsyncMock()
        mock_db.get_job_status = AsyncMock(side_effect=DatabaseError("Connection failed"))
        mock_db_class.return_value = mock_db

        response = client.get("/jobs/job-123")

        assert response.status_code == 500


class TestCancelJob:
    """Test job cancellation endpoint."""

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_cancel_pending_job(self, mock_db_class, client, mock_db_for_api):
        """Cancel a pending job should succeed."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.PENDING,
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.post("/jobs/job-123/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-123"
        assert data["previous_status"] == JobStatus.PENDING
        assert data["new_status"] == JobStatus.CANCELLED
        mock_db_for_api.update_job_status.assert_called_once_with(
            "job-123", JobStatus.CANCELLED.value
        )

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_cancel_completed_job_fails(self, mock_db_class, client, mock_db_for_api):
        """Cannot cancel already completed job."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.COMPLETED,
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.post("/jobs/job-123/cancel")

        assert response.status_code == 409
        data = response.json()
        assert "Cannot cancel" in data["detail"]

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_cancel_failed_job_fails(self, mock_db_class, client, mock_db_for_api):
        """Cannot cancel already failed job."""
        mock_db_for_api.get_job_status.return_value = {
            "id": "job-123",
            "status": JobStatus.FAILED,
        }
        mock_db_class.return_value = mock_db_for_api

        response = client.post("/jobs/job-123/cancel")

        assert response.status_code == 409

    @patch("vecinita_scraper.services.job_control.PostgresDB")
    def test_cancel_nonexistent_job(self, mock_db_class, client):
        """Cannot cancel nonexistent job."""
        mock_db = AsyncMock()
        mock_db.get_job_status = AsyncMock(return_value=None)
        mock_db_class.return_value = mock_db

        response = client.post("/jobs/nonexistent-job/cancel")

        assert response.status_code == 404
