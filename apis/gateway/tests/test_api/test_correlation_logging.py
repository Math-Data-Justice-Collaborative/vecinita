"""US3 / SC-007: correlation and request ids appear in structured gateway logs."""

from __future__ import annotations

import logging
import uuid

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def pipeline_ingest_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.setenv("SCRAPER_API_KEYS", "test-ingest-secret,other-key")
    from src.api.main import app

    return TestClient(app)


def test_modal_scraper_submit_logs_correlation_id(
    env_vars, monkeypatch, caplog: pytest.LogCaptureFixture
) -> None:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist,
        "find_completed_scrape_job_duplicate",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist,
        "create_scraping_job",
        lambda **kwargs: "new-job-id",
    )
    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda payload: {
            "ok": True,
            "data": {
                "job_id": "new-job-id",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "url": str(payload["url"]),
            },
        },
    )
    monkeypatch.setattr(router_modal_jobs, "spawn_modal_scraper_reindex", lambda *_a, **_k: None)

    from src.api.main import app

    client = TestClient(app)
    with caplog.at_level(logging.INFO, logger="src.api.router_modal_jobs"):
        resp = client.post(
            "/api/v1/modal-jobs/scraper",
            json={"url": "https://example.com/page", "user_id": "test-user"},
            headers={"X-Correlation-ID": "corr-log-test-1"},
        )
    assert resp.status_code == 200
    assert "corr-log-test-1" in caplog.text
    assert "modal_scraper_submit_gateway_modal_rpc" in caplog.text


def test_pipeline_ingest_status_logs_correlation_and_request_id(
    pipeline_ingest_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist

    monkeypatch.setattr(modal_scraper_pipeline_persist, "update_job_status", lambda *a, **k: None)

    jid = str(uuid.uuid4())
    with caplog.at_level(logging.INFO, logger="src.api.router_scraper_pipeline_ingest"):
        resp = pipeline_ingest_client.post(
            f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
            json={"status": "crawling", "pipeline_stage": "scraping"},
            headers={
                "X-Scraper-Pipeline-Ingest-Token": "test-ingest-secret",
                "X-Correlation-ID": "corr-ingest-99",
                "X-Request-Id": "req-line-aa",
            },
        )
    assert resp.status_code == 204
    assert "corr-ingest-99" in caplog.text
    assert "req-line-aa" in caplog.text
    assert "scraper_pipeline_job_status_ingest" in caplog.text
