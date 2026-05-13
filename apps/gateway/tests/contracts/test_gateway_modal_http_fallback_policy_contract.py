"""Contracts: gateway HTTP embedding/reindex when Modal RPC is off; block raw HTTP to ``*.modal.run``."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.unit, pytest.mark.contract]


@pytest.fixture
def scrape_client(env_vars, monkeypatch):
    """Minimal gateway client with scrape routes (same pattern as ``test_gateway_router_scrape``)."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.job_manager import job_manager

    job_manager.jobs.clear()

    with patch("src.api.router_scrape.background_scrape_task") as mock_bg_task:
        mock_bg_task.return_value = AsyncMock()
        from src.api.main import app

        yield TestClient(app)


def test_embed_returns_503_when_resolved_upstream_is_modal_and_modal_rpc_off(monkeypatch):
    """Per-request guard: no httpx to Modal hosts unless function invocation is enabled."""
    monkeypatch.delenv("LOCAL_EMBEDDING_SERVICE_URL", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv(
        "EMBEDDING_UPSTREAM_URL",
        "https://vecinita--vecinita-embedding-web-app.modal.run",
    )
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")

    import src.api.router_embed as router_embed
    import src.config as cfg
    import src.service_endpoints as ep

    importlib.reload(cfg)
    importlib.reload(ep)
    importlib.reload(router_embed)

    app = FastAPI()
    app.include_router(router_embed.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/embed", json={"text": "policy check"})
    assert response.status_code == 503
    detail = str(response.json().get("detail", ""))
    assert "modal" in detail.lower()
    assert "MODAL_FUNCTION_INVOCATION" in detail


def test_embed_http_fallback_targets_local_base_when_modal_rpc_off(monkeypatch):
    """HTTP fallback: ``LOCAL_EMBEDDING_SERVICE_URL`` bypasses Modal and issues POST to upstream."""
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.setenv("LOCAL_EMBEDDING_SERVICE_URL", "http://127.0.0.1:19999")

    captured: dict[str, str] = {}

    class _Resp:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "embedding": [0.1, 0.2, 0.3, 0.4],
                "model": "contract-model",
                "dimension": 4,
            }

    class _AsyncClient:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        async def __aenter__(self) -> _AsyncClient:
            return self

        async def __aexit__(self, *a: object) -> None:
            return None

        async def post(
            self, url: str, json: dict | None = None, headers: dict | None = None
        ) -> _Resp:
            captured["url"] = url
            return _Resp()

    from src.api import router_embed as re

    monkeypatch.setattr(re.httpx, "AsyncClient", _AsyncClient)

    app = FastAPI()
    app.include_router(re.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/embed", json={"text": "via local http"})
    assert response.status_code == 200
    assert captured["url"] == "http://127.0.0.1:19999/embed"
    body = response.json()
    assert body["dimension"] == 4
    assert body["embedding"] == [0.1, 0.2, 0.3, 0.4]


def test_reindex_returns_503_when_reindex_url_targets_modal_and_modal_rpc_off(
    scrape_client, monkeypatch
):
    from src.api import router_scrape

    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "0")
    monkeypatch.setattr(
        router_scrape,
        "REINDEX_SERVICE_URL",
        "https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs",
    )

    response = scrape_client.post("/api/v1/scrape/reindex")
    assert response.status_code == 503
    body = response.json()
    message = str(body.get("error") or body.get("detail") or "")
    assert "modal" in message.lower()
    assert "MODAL_FUNCTION_INVOCATION" in message
