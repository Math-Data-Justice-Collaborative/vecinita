"""T24.1 / UJ-014 / TC-052 / AC-E4: health aggregator polls services."""

from __future__ import annotations

import os
from typing import cast
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import json_object_get, json_str, response_json_object
from vecinita_shared_schemas.json_types import as_json_object

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")
    monkeypatch.setenv("VECINITA_ADMIN_FRONTEND_URL", "http://admin:3001")
    monkeypatch.setenv("VECINITA_CHAT_FRONTEND_URL", "http://chat-fe:3000")
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "http://modal-data:8001")
    monkeypatch.setenv("VECINITA_MODAL_EMBED_URL", "http://modal-embed:8002")
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://modal-llm:8003")
    from vecinita_internal_write_api.app import create_app

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _mock_get_ok(url: str, **kwargs: object) -> httpx.Response:
    return httpx.Response(200, json={"status": "ok"})


def _mock_get_timeout(url: str, **kwargs: object) -> httpx.Response:
    raise httpx.ConnectTimeout("timeout")


def test_health_all_returns_service_statuses(client) -> None:
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_ok):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert data["status"] in ("healthy", "degraded")
    assert "services" in data
    services = json_object_get(data, "services")
    assert "database" in services
    database = json_object_get(services, "database")
    assert json_str(database, "status") == "up"
    assert "checked_at" in data


def test_health_all_marks_down_on_timeout(client) -> None:
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_timeout):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    assert resp.status_code == 200
    data = response_json_object(resp)
    assert data["status"] == "degraded"
    services = json_object_get(data, "services")
    for svc_raw in services.values():
        svc = as_json_object(cast(object, svc_raw))
        if json_str(svc, "status") == "down":
            assert "error" in svc


def test_health_all_includes_all_configured_services(client) -> None:
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_ok):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    data = response_json_object(resp)
    expected_services = {
        "internal_write_api",
        "chat_rag_backend",
        "database",
        "modal_data_management",
        "modal_embedding",
        "modal_llm",
        "chat_rag_frontend",
        "admin_frontend",
    }
    services = json_object_get(data, "services")
    assert set(services.keys()) == expected_services
