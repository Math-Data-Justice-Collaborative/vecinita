"""Contract tests: gateway routes call Modal SDK invokers when ``MODAL_FUNCTION_INVOCATION`` is on."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.contract]


@pytest.fixture
def embed_modal_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")

    from src.api.router_embed import router as embed_router

    app = FastAPI()
    app.include_router(embed_router, prefix="/api/v1")
    return TestClient(app)


@pytest.fixture
def modal_jobs_modal_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("MODAL_SCRAPER_PERSIST_VIA_GATEWAY", "0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:10000/model")
    monkeypatch.setenv("EMBEDDING_UPSTREAM_URL", "http://localhost:8001")
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    from src.api.main import app

    return TestClient(app)


def test_embed_single_calls_invoke_modal_embedding_single(embed_modal_client, monkeypatch):
    from src.api import router_embed

    called: dict[str, Any] = {}

    def capture(text: str):
        called["text"] = text
        return {"embedding": [0.1, 0.2], "model": "m", "dimension": 2}

    monkeypatch.setattr(router_embed, "invoke_modal_embedding_single", capture)

    resp = embed_modal_client.post("/api/v1/embed", json={"text": "hello"})
    assert resp.status_code == 200
    assert called["text"] == "hello"
    body = resp.json()
    assert body["embedding"] == [0.1, 0.2]
    assert body["dimension"] == 2


def test_embed_batch_calls_invoke_modal_embedding_batch(embed_modal_client, monkeypatch):
    from src.api import router_embed

    called: dict[str, Any] = {}

    def capture(texts: list[str]):
        called["texts"] = texts
        return {"embeddings": [[0.1], [0.2]], "model": "m", "dimension": 1}

    monkeypatch.setattr(router_embed, "invoke_modal_embedding_batch", capture)

    resp = embed_modal_client.post("/api/v1/embed/batch", json={"texts": ["a", "b"]})
    assert resp.status_code == 200
    assert called["texts"] == ["a", "b"]


def test_embed_similarity_calls_invoke_modal_embedding_batch(embed_modal_client, monkeypatch):
    from src.api import router_embed

    called: dict[str, Any] = {}

    def capture(texts: list[str]):
        called["texts"] = texts
        return {"embeddings": [[1.0, 0.0], [1.0, 0.0]], "model": "m", "dimension": 2}

    monkeypatch.setattr(router_embed, "invoke_modal_embedding_batch", capture)

    resp = embed_modal_client.post(
        "/api/v1/embed/similarity", json={"text1": "same", "text2": "same"}
    )
    assert resp.status_code == 200
    assert called["texts"] == ["same", "same"]
    assert resp.json()["similarity"] == pytest.approx(1.0)


def test_modal_scraper_get_calls_invoke_modal_scrape_job_get(modal_jobs_modal_client, monkeypatch):
    from src.api import router_modal_jobs

    called: dict[str, Any] = {}

    def capture(job_id: str):
        called["job_id"] = job_id
        return {
            "ok": True,
            "data": {
                "job_id": job_id,
                "status": "pending",
                "created_at": "2024-01-01T00:00:00",
                "url": "https://example.com/",
            },
        }

    monkeypatch.setattr(router_modal_jobs, "invoke_modal_scrape_job_get", capture)

    jid = uuid.uuid4()
    resp = modal_jobs_modal_client.get(f"/api/v1/modal-jobs/scraper/{jid}")
    assert resp.status_code == 200
    assert called["job_id"] == str(jid)


def test_modal_scraper_list_calls_invoke_modal_scrape_job_list(
    modal_jobs_modal_client, monkeypatch
):
    from src.api import router_modal_jobs

    called: dict[str, Any] = {}

    def capture(user_id: str | None, limit: int):
        called["user_id"] = user_id
        called["limit"] = limit
        return {"ok": True, "data": {"jobs": [], "total": 0}}

    monkeypatch.setattr(router_modal_jobs, "invoke_modal_scrape_job_list", capture)

    resp = modal_jobs_modal_client.get("/api/v1/modal-jobs/scraper?user_id=u1&limit=7")
    assert resp.status_code == 200
    assert called["user_id"] == "u1"
    assert called["limit"] == 7


def test_modal_scraper_cancel_calls_invoke_modal_scrape_job_cancel(
    modal_jobs_modal_client, monkeypatch
):
    from src.api import router_modal_jobs

    called: dict[str, Any] = {}

    def capture(job_id: str):
        called["job_id"] = job_id
        return {
            "ok": True,
            "data": {
                "job_id": job_id,
                "status": "cancelled",
                "created_at": "2024-01-01T00:00:00",
                "url": "https://example.com/",
            },
        }

    monkeypatch.setattr(router_modal_jobs, "invoke_modal_scrape_job_cancel", capture)

    jid = uuid.uuid4()
    resp = modal_jobs_modal_client.post(f"/api/v1/modal-jobs/scraper/{jid}/cancel")
    assert resp.status_code == 200
    assert called["job_id"] == str(jid)
