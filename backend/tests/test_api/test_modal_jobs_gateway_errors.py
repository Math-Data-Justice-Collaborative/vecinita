"""Stable gateway error JSON + correlation on Modal job scrape paths (FR-014 / FR-015)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def modal_jobs_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    from src.api.main import app

    return TestClient(app)


def _assert_fr014_fr015(resp, expected_cid: str) -> None:
    assert resp.headers.get("X-Correlation-ID") == expected_cid
    data = resp.json()
    assert isinstance(data.get("error"), str)
    assert isinstance(data.get("timestamp"), str)
    assert data.get("correlation_id") == expected_cid


def test_modal_scrape_submit_503_envelope_and_correlation(modal_jobs_client: TestClient) -> None:
    cid = "gw-err-submit-503"
    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "u1"},
        headers={"X-Correlation-ID": cid},
    )
    assert resp.status_code == 503
    _assert_fr014_fr015(resp, cid)


def test_modal_scrape_get_503_envelope_and_correlation(modal_jobs_client: TestClient) -> None:
    cid = "gw-err-get-503"
    jid = str(uuid.uuid4())
    resp = modal_jobs_client.get(
        f"/api/v1/modal-jobs/scraper/{jid}",
        headers={"X-Correlation-ID": cid},
    )
    assert resp.status_code == 503
    _assert_fr014_fr015(resp, cid)
