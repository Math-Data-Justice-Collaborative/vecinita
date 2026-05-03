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
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.setenv("SCRAPER_API_KEYS", "test-ingest-secret,other-key")
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

    def _capture(jid: str, st: str, err: str | None = None, **_: object) -> None:
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


def test_pipeline_ingest_accepts_any_listed_api_key(
    pipeline_ingest_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gateway accepts X-Scraper-Pipeline-Ingest-Token matching any SCRAPER_API_KEYS segment."""
    from src.services.ingestion import modal_scraper_pipeline_persist

    calls: list[tuple[str, str, str | None]] = []

    def _capture(jid: str, st: str, err: str | None = None, **_: object) -> None:
        calls.append((jid, st, err))

    monkeypatch.setattr(modal_scraper_pipeline_persist, "update_job_status", _capture)

    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "embedding", "error_message": None},
        headers={"X-Scraper-Pipeline-Ingest-Token": "other-key"},
    )
    assert resp.status_code == 204
    assert calls == [(jid, "embedding", None)]


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        (
            "post",
            lambda jid: f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
            lambda jid: {"status": "crawling"},
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/crawled-urls",
            lambda jid: {
                "job_id": jid,
                "url": "https://example.com/",
                "raw_content": "",
                "content_hash": "a" * 64,
                "status": "success",
            },
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/extracted-content",
            lambda jid: {
                "crawled_url_id": str(jid),
                "content_type": "text/html",
                "raw_content": "x",
            },
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/processed-documents",
            lambda jid: {
                "extracted_content_id": str(jid),
                "markdown_content": "# hi",
            },
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/chunks",
            lambda jid: {"processed_doc_id": str(jid), "chunks": []},
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/embeddings",
            lambda jid: {"job_id": str(jid), "chunk_embeddings": []},
        ),
    ],
)
def test_pipeline_ingest_all_routes_401_without_token(
    pipeline_ingest_client: TestClient,
    method: str,
    path: object,
    json_body: object,
) -> None:
    """Every pipeline ingest route rejects missing pipeline token (401)."""
    jid = str(uuid.uuid4())
    url = path(jid)  # type: ignore[misc]
    body = json_body(jid)  # type: ignore[misc]
    resp = getattr(pipeline_ingest_client, method)(url, json=body)
    assert resp.status_code == 401


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        (
            "post",
            lambda jid: f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
            lambda jid: {"status": "crawling"},
        ),
        (
            "post",
            lambda _jid: "/api/v1/internal/scraper-pipeline/crawled-urls",
            lambda jid: {
                "job_id": jid,
                "url": "https://example.com/",
                "raw_content": "",
                "content_hash": "b" * 64,
                "status": "success",
            },
        ),
    ],
)
def test_pipeline_ingest_routes_503_when_api_keys_unset(
    env_vars,
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    path: object,
    json_body: object,
) -> None:
    """Pipeline ingest returns 503 when SCRAPER_API_KEYS is unset (misconfigured gateway)."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SCRAPER_API_KEYS", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    from src.api.main import app

    client = TestClient(app)
    jid = str(uuid.uuid4())
    url = path(jid)  # type: ignore[misc]
    body = json_body(jid)  # type: ignore[misc]
    resp = getattr(client, method)(url, json=body, headers={"X-Scraper-Pipeline-Ingest-Token": "x"})
    assert resp.status_code == 503


def test_pipeline_ingest_not_configured_returns_503(
    env_vars, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SCRAPER_API_KEYS", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
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


def test_pipeline_ingest_store_crawled_url_ok(
    pipeline_ingest_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST /crawled-urls returns 200 with id (idempotent upsert is implemented in persist layer)."""
    from src.services.ingestion import modal_scraper_pipeline_persist

    fixed = str(uuid.uuid4())

    def _fake_store(
        job_id: str,
        url: str,
        raw_content: str,
        content_hash: str,
        status: str = "success",
        error_message: str | None = None,
    ) -> str:
        _ = (job_id, url, raw_content, content_hash, status, error_message)
        return fixed

    monkeypatch.setattr(modal_scraper_pipeline_persist, "store_crawled_url", _fake_store)

    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        "/api/v1/internal/scraper-pipeline/crawled-urls",
        json={
            "job_id": jid,
            "url": "https://health.ri.gov/",
            "raw_content": "",
            "content_hash": "e" * 64,
            "status": "failed",
            "error_message": "Blocked by anti-bot protection",
        },
        headers={"X-Scraper-Pipeline-Ingest-Token": "test-ingest-secret"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"crawled_url_id": fixed}


def test_pipeline_ingest_status_maps_value_error_to_400(
    pipeline_ingest_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist

    def _bad(
        job_id: str,
        status: str,
        error_message: str | None = None,
        *,
        pipeline_stage: str | None = None,
        error_category: str | None = None,
    ) -> None:
        _ = (job_id, status, error_message, pipeline_stage, error_category)
        raise ValueError("transition scraping -> embedding is not allowed")

    monkeypatch.setattr(modal_scraper_pipeline_persist, "update_job_status", _bad)

    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={"status": "embedding", "pipeline_stage": "embedding"},
        headers={"X-Scraper-Pipeline-Ingest-Token": "test-ingest-secret"},
    )
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["error"]


def test_pipeline_ingest_status_passes_pipeline_fields_to_persist(
    pipeline_ingest_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services.ingestion import modal_scraper_pipeline_persist

    captured: dict[str, object] = {}

    def _capture(
        job_id: str,
        status: str,
        error_message: str | None = None,
        *,
        pipeline_stage: str | None = None,
        error_category: str | None = None,
    ) -> None:
        captured["job_id"] = job_id
        captured["status"] = status
        captured["error_message"] = error_message
        captured["pipeline_stage"] = pipeline_stage
        captured["error_category"] = error_category

    monkeypatch.setattr(modal_scraper_pipeline_persist, "update_job_status", _capture)

    jid = str(uuid.uuid4())
    resp = pipeline_ingest_client.post(
        f"/api/v1/internal/scraper-pipeline/jobs/{jid}/status",
        json={
            "status": "chunking",
            "error_message": "x",
            "pipeline_stage": "chunking",
            "error_category": "transient",
        },
        headers={"X-Scraper-Pipeline-Ingest-Token": "test-ingest-secret"},
    )
    assert resp.status_code == 204
    assert captured == {
        "job_id": jid,
        "status": "chunking",
        "error_message": "x",
        "pipeline_stage": "chunking",
        "error_category": "transient",
    }
