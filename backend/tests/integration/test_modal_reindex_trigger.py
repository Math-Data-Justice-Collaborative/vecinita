"""Integration tests for Modal reindex trigger endpoint."""

from __future__ import annotations

import importlib
from typing import Any

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class _Resp:
    def __init__(self, payload: dict[str, Any], status_code: int = 200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _AsyncClientStub:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, params=None, headers=None):
        return _Resp(
            {
                "status": "queued",
                "call_id": "fc-integration-001",
                "url": url,
                "params": params,
                "headers": headers,
            }
        )


@pytest.fixture
def client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    monkeypatch.setenv("ENABLE_AUTH", "false")
    monkeypatch.setenv("AUTH_FAIL_CLOSED", "false")

    import src.api.main as main_module
    import src.api.middleware as middleware_module
    import src.api.router_scrape as router_scrape_module

    importlib.reload(middleware_module)
    importlib.reload(router_scrape_module)
    importlib.reload(main_module)

    return TestClient(main_module.app)


def test_modal_reindex_endpoint_returns_queued(client, monkeypatch):
    from src.api import router_scrape

    monkeypatch.setattr(router_scrape, "modal_function_invocation_enabled", lambda: False)
    monkeypatch.setattr(
        router_scrape, "REINDEX_SERVICE_URL", "https://reindex.integration.test/jobs"
    )
    monkeypatch.setattr(router_scrape, "REINDEX_TRIGGER_TOKEN", "integration-token")
    monkeypatch.setattr(router_scrape.httpx, "AsyncClient", _AsyncClientStub)

    response = client.post("/api/v1/scrape/reindex")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "queued"
    assert body["call_id"] == "fc-integration-001"
    assert body["service_url"] == "https://reindex.integration.test/jobs"
