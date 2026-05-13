"""Contract: DM ``jobs_proxy`` forwards browser-shaped requests to ``ScraperClient.forward_jobs``."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient


def _fresh_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SCRAPER_SERVICE_BASE_URL", "http://scraper.test")
    monkeypatch.setenv("EMBEDDING_SERVICE_BASE_URL", "http://embedding.test")
    monkeypatch.setenv("MODEL_SERVICE_BASE_URL", "http://model.test")
    monkeypatch.delenv("MODAL_FUNCTION_INVOCATION", raising=False)

    from shared_config import get_settings

    get_settings.cache_clear()
    from vecinita_dm_api.app import create_app

    return TestClient(create_app())


@pytest.mark.unit
@pytest.mark.contract
def test_jobs_proxy_forwards_authorization_and_query(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Fake:
        def __init__(self, *_a, **_k):
            pass

        async def forward_jobs(self, method: str, subpath: str, **kw):  # noqa: ANN003
            captured["method"] = method
            captured["subpath"] = subpath
            captured["query"] = kw.get("query")
            captured["headers"] = kw.get("headers")
            return httpx.Response(200, json={"jobs": [], "limit": 10, "total": 0, "user_id": "op"})

    with patch("vecinita_dm_api.routers.jobs_proxy.ScraperClient", _Fake):
        c = _fresh_client(monkeypatch)
        r = c.get(
            "/jobs",
            params={"user_id": "op", "limit": "10"},
            headers={"Authorization": "Bearer browser-token"},
        )

    assert r.status_code == 200
    assert captured["method"] == "GET"
    assert captured["subpath"] == ""
    q = str(captured["query"])
    assert "user_id=op" in q and "limit=10" in q
    hdrs = captured["headers"]
    assert isinstance(hdrs, dict)
    assert hdrs.get("Authorization") == "Bearer browser-token"


@pytest.mark.unit
@pytest.mark.contract
def test_jobs_proxy_forwards_subpath_and_post_body(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Fake:
        def __init__(self, *_a, **_k):
            pass

        async def forward_jobs(self, method: str, subpath: str, **kw):  # noqa: ANN003
            captured["method"] = method
            captured["subpath"] = subpath
            captured["content"] = kw.get("content")
            return httpx.Response(201, json={"job_id": "new-1", "status": "pending"})

    payload = b'{"url":"https://example.com","depth":1}'
    with patch("vecinita_dm_api.routers.jobs_proxy.ScraperClient", _Fake):
        c = _fresh_client(monkeypatch)
        r = c.post(
            "/jobs",
            content=payload,
            headers={"Content-Type": "application/json"},
        )

    assert r.status_code == 201
    assert captured["method"] == "POST"
    assert captured["subpath"] == ""
    assert captured["content"] == payload
