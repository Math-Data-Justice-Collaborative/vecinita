"""Unit tests for ``ScraperClient`` (httpx ``MockTransport``; no live network)."""

from __future__ import annotations

import httpx
import pytest

import service_clients.scraper_client as scraper_client_mod

from service_clients.scraper_client import ScraperClient, ScraperUpstreamError


@pytest.fixture
def base_url() -> str:
    return "https://scraper.test"


@pytest.mark.asyncio
async def test_scrape_success(base_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/scrape"
        return httpx.Response(
            200,
            json={
                "url": "https://example.com/page",
                "title": "T",
                "text": "body",
                "metadata": {},
            },
        )

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    result = await ScraperClient(base_url).scrape("https://example.com/page", depth=1)
    assert result.url == "https://example.com/page"
    assert result.title == "T"


@pytest.mark.asyncio
async def test_scrape_upstream_5xx_maps_to_stable_error(
    base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"detail": "upstream failure dpg-abc123xyz.internal"},
        )

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    with pytest.raises(ScraperUpstreamError) as ei:
        await ScraperClient(base_url).scrape("https://example.com/page")
    msg = str(ei.value).lower()
    assert "dpg-" not in msg
    assert ei.value.mapped_http_status == 502


@pytest.mark.asyncio
async def test_scrape_client_error_preserves_status(
    base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "bad"})

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    with pytest.raises(ScraperUpstreamError) as ei:
        await ScraperClient(base_url).scrape("https://example.com/page")
    assert ei.value.mapped_http_status == 422


@pytest.mark.asyncio
async def test_health_request_error_maps_to_503(
    base_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    with pytest.raises(ScraperUpstreamError) as ei:
        await ScraperClient(base_url).health()
    assert ei.value.mapped_http_status == 503
    assert "unreachable" in str(ei.value).lower()


@pytest.mark.asyncio
async def test_health_uses_modal_when_invocation_enabled(
    base_url: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MODAL_FUNCTION_INVOCATION", "1")
    monkeypatch.setenv("MODAL_TOKEN_ID", "test-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "test-secret")

    async def _fake_modal_health() -> dict:
        return {"status": "ok", "worker": "vecinita-scraper"}

    monkeypatch.setattr(
        scraper_client_mod.modal_invoker, "scraper_health_modal", _fake_modal_health
    )

    result = await ScraperClient(base_url).health()
    assert result["status"] == "ok"
    assert result["worker"] == "vecinita-scraper"


@pytest.mark.asyncio
async def test_forward_jobs_returns_upstream_status_without_raise(
    base_url: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url).startswith(f"{base_url}/jobs")
        assert request.url.path == "/jobs"
        return httpx.Response(200, json={"jobs": [], "limit": 50, "total": 0})

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    resp = await ScraperClient(base_url).forward_jobs("GET", "")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_forward_jobs_subpath_and_query(
    base_url: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/jobs/job-1/cancel"
        assert "dry=1" in str(request.url)
        return httpx.Response(200, json={"job_id": "job-1", "previous_status": "x", "new_status": "cancelled"})

    transport = httpx.MockTransport(handler)

    def _async_client(*, timeout: float = 60.0, **_kw: object) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=transport, timeout=timeout)

    monkeypatch.setattr(scraper_client_mod, "AsyncClient", _async_client)

    resp = await ScraperClient(base_url).forward_jobs(
        "POST",
        "job-1/cancel",
        query="dry=1",
        content=b"{}",
        headers={"Authorization": "Bearer t"},
    )
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "cancelled"
