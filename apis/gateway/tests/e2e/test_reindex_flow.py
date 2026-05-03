"""E2E-style coverage for scrape reindex API flow."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e


class _ReindexResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class _ReindexAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, params=None, headers=None):
        return _ReindexResponse(
            {
                "status": "queued",
                "call_id": "fc-e2e-123",
                "url": url,
                "params": params,
                "headers": headers or {},
            }
        )


@pytest.fixture
def gateway_client(env_vars, monkeypatch):
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    from src.api.main import app

    return TestClient(app)


def test_reindex_endpoint_e2e(gateway_client, monkeypatch):
    from src.api import router_scrape

    monkeypatch.setattr(router_scrape, "modal_function_invocation_enabled", lambda: False)
    monkeypatch.setattr(router_scrape, "REINDEX_SERVICE_URL", "https://reindex.e2e.test/jobs")
    monkeypatch.setattr(router_scrape, "REINDEX_TRIGGER_TOKEN", "e2e-token")
    monkeypatch.setattr(router_scrape.httpx, "AsyncClient", _ReindexAsyncClient)

    response = gateway_client.post("/api/v1/scrape/reindex?clean=false&verbose=true")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "queued"
    assert payload["call_id"] == "fc-e2e-123"
    assert payload["service_url"] == "https://reindex.e2e.test/jobs"
