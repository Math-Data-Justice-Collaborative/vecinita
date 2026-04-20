"""Tests for internal scraper pipeline ingest routes."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def pipeline_ingest_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "0")
    monkeypatch.setenv("VECINITA_MODEL_API_URL", "http://localhost:10000/model")
    monkeypatch.setenv("VECINITA_EMBEDDING_API_URL", "http://localhost:8001")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.setenv("SCRAPER_PIPELINE_INGEST_TOKEN", "test-ingest-secret")
    from src.api.main import app

    return TestClient(app)


def test_pipeline_ingest_requires_token(pipeline_ingest_client: TestClient) -> None:
    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "crawling"},
    )
    assert resp.status_code == 401


def test_pipeline_ingest_rejects_wrong_token(pipeline_ingest_client: TestClient) -> None:
    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "crawling"},
        headers={"X-Scraper-Pipeline-Ingest-Token": "wrong"},
    )
    assert resp.status_code == 401


def test_pipeline_ingest_update_status_ok(
    pipeline_ingest_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist

    calls: list[tuple[str, str, str | None]] = []

    def _capture(jid: str, st: str, err: str | None = None) -> None:
        calls.append((jid, st, err))

    monkeypatch.setattr(modal_scraper_pipeline_persist, "update_job_status", _capture)

    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "crawling", "error_message": None},
        headers={"X-Scraper-Pipeline-Ingest-Token": "test-ingest-secret"},
    )
    assert resp.status_code == 204
    assert calls == [(jid, "crawling", None)]


def test_pipeline_ingest_not_configured_returns_503(
    env_vars, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SCRAPER_PIPELINE_INGEST_TOKEN", raising=False)
    monkeypatch.setenv("VECINITA_MODEL_API_URL", "http://localhost:10000/model")
    monkeypatch.setenv("VECINITA_EMBEDDING_API_URL", "http://localhost:8001")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    from src.api.main import app

    client = TestClient(app)
    jid = str(uuid.uuid4())
    resp = client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "crawling"},
        headers={"X-Scraper-Pipeline-Ingest-Token": "any"},
    )
    assert resp.status_code == 503
