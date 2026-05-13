"""ASGI tests for ``apps/backend`` data-management FastAPI (no live Modal or scraper)."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from shared_schemas.embedding import EmbedResponse
from shared_schemas.model import PredictResponse


def _fresh_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SCRAPER_SERVICE_BASE_URL", "http://scraper.test")
    monkeypatch.setenv("EMBEDDING_SERVICE_BASE_URL", "http://embedding.test")
    monkeypatch.setenv("MODEL_SERVICE_BASE_URL", "http://model.test")
    monkeypatch.delenv("MODAL_FUNCTION_INVOCATION", raising=False)
    from shared_config import get_settings

    get_settings.cache_clear()
    from vecinita_dm_api.app import create_app

    return TestClient(create_app())


def test_health_uses_scraper_client(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeScraper:
        def __init__(self, *_a, **_k):
            pass

        async def health(self) -> dict:
            return {"status": "ok", "service": "vecinita-scraper"}

    with patch("vecinita_dm_api.routers.health.ScraperClient", _FakeScraper):
        c = _fresh_client(monkeypatch)
        r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_jobs_get_proxies(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Fake:
        def __init__(self, *_a, **_k):
            pass

        async def forward_jobs(self, method: str, subpath: str, **kw):  # noqa: ANN003
            assert method == "GET"
            assert subpath == ""
            assert "user_id=op" in (kw.get("query") or "")
            return httpx.Response(200, json={"jobs": [], "limit": 100, "total": 0, "user_id": "op"})

    with patch("vecinita_dm_api.routers.jobs_proxy.ScraperClient", _Fake):
        c = _fresh_client(monkeypatch)
        r = c.get("/jobs?user_id=op&limit=100")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["jobs"] == []


def test_embed_delegates_to_embedding_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    fake_embed = AsyncMock(
        return_value=EmbedResponse(embedding=[0.25, -0.25], model_version="v-test"),
    )

    class _FakeEmb:
        def __init__(self, *_a, **_k):
            pass

        embed = fake_embed

    with patch("vecinita_dm_api.routers.ingest.EmbeddingClient", _FakeEmb):
        c = _fresh_client(monkeypatch)
        r = c.post("/embed", json={"text": "hello", "model_version": None})
    assert r.status_code == 200
    assert r.json()["embedding"] == [0.25, -0.25]
    fake_embed.assert_awaited_once()


def test_predict_delegates_to_model_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import AsyncMock

    fake_predict = AsyncMock(
        return_value=PredictResponse(label="ok", score=0.9, model_version=None),
    )

    class _FakeModel:
        def __init__(self, *_a, **_k):
            pass

        predict = fake_predict

    with patch("vecinita_dm_api.routers.ingest.ModelClient", _FakeModel):
        c = _fresh_client(monkeypatch)
        r = c.post("/predict", json={"text": "classify me", "model_version": None})
    assert r.status_code == 200
    assert r.json()["label"] == "ok"
    fake_predict.assert_awaited_once()


def test_dm_api_requires_canonical_database_url_in_render(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/placeholder_db")
    with pytest.raises(RuntimeError, match="canonical postgres"):
        _fresh_client(monkeypatch)
