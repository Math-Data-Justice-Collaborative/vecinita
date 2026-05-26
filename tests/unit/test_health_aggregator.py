"""T24.1 / UJ-014 / TC-052 / AC-E4: health aggregator polls services."""

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture()
def client():
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    os.environ["VECINITA_CHAT_RAG_URL"] = "http://chat-rag:8000"
    os.environ["VECINITA_ADMIN_FRONTEND_URL"] = "http://admin:3001"
    os.environ["VECINITA_CHAT_FRONTEND_URL"] = "http://chat-fe:3000"
    os.environ["VECINITA_MODAL_DATA_MGMT_URL"] = "http://modal-data:8001"
    os.environ["VECINITA_MODAL_EMBED_URL"] = "http://modal-embed:8002"
    os.environ["VECINITA_MODAL_LLM_URL"] = "http://modal-llm:8003"
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
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "services" in data
    assert "database" in data["services"]
    assert data["services"]["database"]["status"] == "up"
    assert "checked_at" in data


def test_health_all_marks_down_on_timeout(client) -> None:
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_timeout):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    for svc in data["services"].values():
        if svc["status"] == "down":
            assert svc.get("error") is not None


def test_health_all_includes_all_configured_services(client) -> None:
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_ok):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    data = resp.json()
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
    assert set(data["services"].keys()) == expected_services
