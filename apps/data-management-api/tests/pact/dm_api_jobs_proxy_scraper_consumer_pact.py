"""Consumer Pact: DM API ``jobs_proxy`` → scraper-compatible ``/jobs`` HTTP (``ScraperClient.forward_jobs``).

Writes ``apis/data-management-api/pacts/vecinita-dm-api-vecinita-scraper-jobs-http.json`` (gitignored).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pact import Pact

pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _dm_api_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pact_output_dir() -> Path:
    return _dm_api_root() / "pacts"


def _configure_dm_app_env(mock_scraper_base: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCRAPER_SERVICE_BASE_URL", mock_scraper_base.rstrip("/"))
    monkeypatch.setenv("EMBEDDING_SERVICE_BASE_URL", "http://embedding.pact.test")
    monkeypatch.setenv("MODEL_SERVICE_BASE_URL", "http://model.pact.test")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")

    from shared_config import get_settings

    get_settings.cache_clear()


def test_dm_api_writes_jobs_proxy_scraper_consumer_pact(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("pact")
    from fastapi.testclient import TestClient

    from vecinita_dm_api.app import create_app

    pact = Pact("vecinita-dm-api", "vecinita-scraper-jobs-http").with_specification("V4")

    jobs_list = {
        "jobs": [
            {
                "id": "pact-job-1",
                "user_id": "pact-browser",
                "status": "pending",
                "created_at": "2026-01-01T00:00:00.000Z",
                "updated_at": "2026-01-01T00:00:00.000Z",
                "url": "https://example.com/pact",
            }
        ],
        "total": 1,
        "limit": 25,
        "user_id": "pact-browser",
    }

    job_get = {
        "job_id": "pact-job-1",
        "status": "pending",
        "created_at": "2026-01-01T00:00:00.000Z",
        "updated_at": "2026-01-01T00:01:00.000Z",
        "chunk_count": 0,
        "crawl_url_count": 0,
        "embedding_count": 0,
        "current_step": "pending",
        "progress_pct": 5,
        "url": "https://example.com/pact",
    }

    cancel_body = {
        "job_id": "pact-job-1",
        "previous_status": "pending",
        "new_status": "cancelled",
    }

    (
        pact.upon_receiving("DM API proxies browser GET /jobs list to scraper")
        .with_request("GET", "/jobs")
        .with_query_parameters({"user_id": "pact-browser", "limit": "25"})
        .with_header("Authorization", "Bearer pact-dm-token", part="Request")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(jobs_list, content_type="application/json", part="Response")
    )

    (
        pact.upon_receiving("DM API proxies browser GET /jobs/{job_id} to scraper")
        .with_request("GET", "/jobs/pact-job-1")
        .with_header("Authorization", "Bearer pact-dm-token", part="Request")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(job_get, content_type="application/json", part="Response")
    )

    (
        pact.upon_receiving("DM API proxies browser POST /jobs/{job_id}/cancel to scraper")
        .with_request("POST", "/jobs/pact-job-1/cancel")
        .with_header("Authorization", "Bearer pact-dm-token", part="Request")
        .will_respond_with(200)
        .with_header("Content-Type", "application/json", part="Response")
        .with_body(cancel_body, content_type="application/json", part="Response")
    )

    with pact.serve(raises=True, verbose=False) as mock_scraper:
        mock_base = str(mock_scraper.url).rstrip("/")
        _configure_dm_app_env(mock_base, monkeypatch)
        client = TestClient(create_app())

        common_headers = {"Authorization": "Bearer pact-dm-token"}

        listed = client.get(
            "/jobs",
            params={"user_id": "pact-browser", "limit": 25},
            headers=common_headers,
        )
        assert listed.status_code == 200
        assert listed.json()["total"] == 1

        detail = client.get("/jobs/pact-job-1", headers=common_headers)
        assert detail.status_code == 200
        assert detail.json()["job_id"] == "pact-job-1"

        cancelled = client.post("/jobs/pact-job-1/cancel", headers=common_headers)
        assert cancelled.status_code == 200
        assert cancelled.json()["new_status"] == "cancelled"

    pact.write_file(_pact_output_dir(), overwrite=True)
