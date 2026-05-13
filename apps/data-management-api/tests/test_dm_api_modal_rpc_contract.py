"""Contract: DM API routes delegate to service-clients Modal RPC when ``MODAL_FUNCTION_INVOCATION`` is on."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient


def _client_modal_on(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "ak-test")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "as-test")
    monkeypatch.setenv("SCRAPER_SERVICE_BASE_URL", "http://scraper.test")
    monkeypatch.setenv("EMBEDDING_SERVICE_BASE_URL", "http://embedding.test")
    monkeypatch.setenv("MODEL_SERVICE_BASE_URL", "http://model.test")

    from shared_config import get_settings

    get_settings.cache_clear()
    from vecinita_dm_api.app import create_app

    return TestClient(create_app())


@pytest.mark.unit
@pytest.mark.contract
def test_post_embed_calls_embedding_embed_single_modal(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_embed(text: str, model_version: str | None) -> dict:
        assert text == "rpc hello"
        assert model_version is None
        return {"embedding": [0.25, -0.25], "model_version": "v-modal"}

    with patch(
        "service_clients.modal_invoker.embedding_embed_single_modal",
        new_callable=AsyncMock,
        side_effect=fake_embed,
    ):
        c = _client_modal_on(monkeypatch)
        r = c.post("/embed", json={"text": "rpc hello", "model_version": None})
    assert r.status_code == 200
    assert r.json() == {"embedding": [0.25, -0.25], "model_version": "v-modal"}


@pytest.mark.unit
@pytest.mark.contract
def test_post_predict_calls_model_predict_modal(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_predict(text: str, model_version: str | None) -> dict:
        assert text == "classify me"
        assert model_version == "v1"
        return {"label": "ok", "score": 0.9, "model_version": "v1"}

    with patch(
        "service_clients.modal_invoker.model_predict_modal",
        new_callable=AsyncMock,
        side_effect=fake_predict,
    ):
        c = _client_modal_on(monkeypatch)
        r = c.post("/predict", json={"text": "classify me", "model_version": "v1"})
    assert r.status_code == 200
    assert r.json()["label"] == "ok"
    assert r.json()["score"] == pytest.approx(0.9)


@pytest.mark.unit
@pytest.mark.contract
def test_get_health_calls_scraper_health_modal(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_health() -> dict:
        return {"status": "ok", "service": "vecinita-scraper", "via": "modal"}

    with patch(
        "service_clients.modal_invoker.scraper_health_modal",
        new_callable=AsyncMock,
        side_effect=fake_health,
    ):
        c = _client_modal_on(monkeypatch)
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["via"] == "modal"


@pytest.mark.unit
@pytest.mark.contract
def test_jobs_proxy_still_uses_scraper_forward_jobs_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """``forward_jobs`` is HTTP-only (Modal RPC is used for scraper *health*, not job proxy)."""

    class _Fake:
        def __init__(self, *_a, **_k):
            pass

        async def forward_jobs(self, method: str, subpath: str, **kw):  # noqa: ANN003
            assert method == "GET"
            assert subpath == ""
            return httpx.Response(200, json={"jobs": [], "limit": 50, "total": 0, "user_id": "u"})

    with patch("vecinita_dm_api.routers.jobs_proxy.ScraperClient", _Fake):
        c = _client_modal_on(monkeypatch)
        r = c.get("/jobs?user_id=u&limit=50")
    assert r.status_code == 200
    assert r.json()["total"] == 0
