"""Tests for Modal-native scrape job gateway routes."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def modal_jobs_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    # Root .env may set gateway-owned scraper mode for live deploys; force Modal-RPC path for these tests.
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "0")
    # Importing ``src.api.main`` loads ``src.agent.main``, which enforces Modal policy when ``*.modal.run``
    # URLs are present without invocation tokens. ``src.config`` prefers VECINITA_* over OLLAMA_* / EMBEDDING_*.
    monkeypatch.setenv("VECINITA_MODEL_API_URL", "http://localhost:10000/model")
    monkeypatch.setenv("VECINITA_EMBEDDING_API_URL", "http://localhost:8001")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("MODAL_OLLAMA_ENDPOINT", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    from src.api.main import app

    return TestClient(app)


def test_modal_scraper_submit_returns_503_when_modal_disabled(modal_jobs_client):
    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 503


def test_modal_scraper_get_returns_503_when_modal_disabled(modal_jobs_client):
    job_id = str(uuid.uuid4())
    resp = modal_jobs_client.get(f"/api/v1/modal-jobs/scraper/{job_id}")
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
    kicks: list[tuple[bool, bool, bool]] = []
    monkeypatch.setattr(
        router_modal_jobs,
        "spawn_modal_scraper_reindex",
        lambda c, s, v: kicks.append((c, s, v)) or "call-1",
    )

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "job-abc"
    assert body["status"] == "pending"
    assert kicks == [(False, True, False)]


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


def test_modal_scraper_submit_gateway_persist_injects_job_id(modal_jobs_client, monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    from src.api import router_modal_jobs

    fixed_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist,
        "create_scraping_job",
        lambda **kwargs: fixed_id,
    )

    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda payload: {
            "ok": True,
            "data": {
                "job_id": payload.get("job_id"),
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "url": str(payload["url"]),
            },
        },
    )
    kicks: list[tuple[bool, bool, bool]] = []
    monkeypatch.setattr(
        router_modal_jobs,
        "spawn_modal_scraper_reindex",
        lambda c, s, v: kicks.append((c, s, v)) or "call-1",
    )

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 200
    assert resp.json()["job_id"] == fixed_id
    assert kicks == [(False, True, False)]


def test_modal_scraper_submit_injects_correlation_id_in_metadata_and_header(
    modal_jobs_client, monkeypatch
):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    from src.api import router_modal_jobs

    captured: dict[str, object] = {}

    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist,
        "create_scraping_job",
        lambda **kwargs: "job-corr-1",
    )

    def capture_submit(payload):
        captured["payload"] = payload
        return {
            "ok": True,
            "data": {
                "job_id": payload.get("job_id"),
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "url": str(payload["url"]),
            },
        }

    monkeypatch.setattr(router_modal_jobs, "invoke_modal_scrape_job_submit", capture_submit)
    monkeypatch.setattr(router_modal_jobs, "spawn_modal_scraper_reindex", lambda *_a, **_k: None)

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={
            "url": "https://example.com/page",
            "user_id": "test-user",
            "metadata": {"source": "t"},
        },
        headers={"X-Correlation-ID": "fixed-corr-id"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("X-Correlation-ID") == "fixed-corr-id"
    payload = captured.get("payload")
    assert isinstance(payload, dict)
    meta = payload.get("metadata")
    assert isinstance(meta, dict)
    assert meta.get("correlation_id") == "fixed-corr-id"
    assert meta.get("source") == "t"


def test_modal_scraper_get_returns_404_unknown_job_gateway_persist(modal_jobs_client, monkeypatch):
    """Gateway-owned DB path: missing row → 404 (not 5xx)."""
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist, "job_status_payload", lambda _jid: None
    )

    job_id = uuid.uuid4()
    resp = modal_jobs_client.get(
        f"/api/v1/modal-jobs/scraper/{job_id}",
        headers={"X-Correlation-ID": "cid-get-404"},
    )
    assert resp.status_code == 404
    assert resp.headers.get("X-Correlation-ID") == "cid-get-404"
    body = resp.json()
    assert body.get("correlation_id") == "cid-get-404"
    assert "not found" in str(body.get("error", "")).lower()


def test_modal_scraper_cancel_returns_404_unknown_job_gateway_persist(
    modal_jobs_client, monkeypatch
):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs.modal_scraper_persist,
        "cancel_job",
        lambda _jid: (None, "not_found"),
    )

    job_id = uuid.uuid4()
    resp = modal_jobs_client.post(
        f"/api/v1/modal-jobs/scraper/{job_id}/cancel",
        headers={"X-Correlation-ID": "cid-cancel-404"},
    )
    assert resp.status_code == 404
    assert resp.headers.get("X-Correlation-ID") == "cid-cancel-404"
    body = resp.json()
    assert body.get("correlation_id") == "cid-cancel-404"


def test_modal_scraper_submit_sanitizes_modal_envelope_500_detail(modal_jobs_client, monkeypatch):
    """Modal RPC envelope 5xx: client body must not echo raw internal Postgres hostnames (FR-002)."""
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")

    from src.api import router_modal_jobs

    monkeypatch.setattr(
        router_modal_jobs,
        "invoke_modal_scrape_job_submit",
        lambda _payload: {
            "ok": False,
            "http_status": 500,
            "detail": 'could not translate host name "dpg-zzzzzzzz" to address: Name or service not known',
        },
    )

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 500
    err = str(resp.json().get("error", "")).lower()
    assert "dpg-" not in err


def test_modal_scraper_submit_gateway_persist_db_runtime_redacted(modal_jobs_client, monkeypatch):
    """If persist raises RuntimeError with internal hostname, HTTP 503 detail is redacted."""
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "1")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    from src.api import router_modal_jobs

    def bad_create(**_kwargs):
        raise RuntimeError(
            'could not translate host name "dpg-leak123" to address: Name or service not known'
        )

    monkeypatch.setattr(router_modal_jobs.modal_scraper_persist, "create_scraping_job", bad_create)

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
        headers={"X-Correlation-ID": "cid-db-503"},
    )
    assert resp.status_code == 503
    assert resp.headers.get("X-Correlation-ID") == "cid-db-503"
    body = resp.json()
    assert body.get("correlation_id") == "cid-db-503"
    assert "dpg-" not in str(body.get("error", "")).lower()


def test_modal_scraper_submit_succeeds_when_pipeline_kick_fails(modal_jobs_client, monkeypatch):
    """Enqueue must still return 200 if trigger_reindex spawn fails (job is on Modal queue)."""
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

    def boom(_c, _s, _v):
        raise RuntimeError("modal spawn failed")

    monkeypatch.setattr(router_modal_jobs, "spawn_modal_scraper_reindex", boom)

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 200
    assert resp.json()["job_id"] == "job-abc"


def test_modal_scraper_submit_skips_pipeline_kick_when_disabled(modal_jobs_client, monkeypatch):
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("MODAL_SCRAPER_SUBMIT_AUTO_KICK", "0")

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
    called: list[bool] = []

    def nope(*_a, **_k):
        called.append(True)

    monkeypatch.setattr(router_modal_jobs, "spawn_modal_scraper_reindex", nope)

    resp = modal_jobs_client.post(
        "/api/v1/modal-jobs/scraper",
        json={"url": "https://example.com/page", "user_id": "test-user"},
    )
    assert resp.status_code == 200
    assert called == []
