"""Tests for Modal-native scrape job gateway routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def modal_jobs_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    from src.api.main import app

    return TestClient(app)


def test_modal_scraper_submit_returns_503_when_modal_disabled(modal_jobs_client):
    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 503


def test_modal_scraper_submit_ok_when_modal_enabled(modal_jobs_client, monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda payload: {
            "ok": True,
            "data": {
                "job_id": "job-abc",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "url": str(payload["url"]),
            },
        },
    )

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "job-abc"
    assert body["status"] == "pending"


def test_modal_scraper_submit_maps_modal_error_envelope(modal_jobs_client, monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda _payload: {
            "ok": False,
            "code": "validation_error",
            "detail": "bad",
            "http_status": 422,
        },
    )

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 422
