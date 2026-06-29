"""T24.1 / UJ-014 / TC-052 / AC-E4: health aggregator polls services."""

from __future__ import annotations

import os
from http import HTTPStatus
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import (
    as_json_object,
)

from tests.helpers.json_response import (
    json_object_get,
    json_str,
    response_json_object,
)

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    """Return the configured database URL, falling back to the local default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide a TestClient for the internal write API with service URLs set."""
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")
    monkeypatch.setenv("VECINITA_ADMIN_FRONTEND_URL", "http://admin:3001")
    monkeypatch.setenv("VECINITA_CHAT_FRONTEND_URL", "http://chat-fe:3000")
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "http://modal-data:8001")
    monkeypatch.setenv("VECINITA_MODAL_EMBED_URL", "http://modal-embed:8002")
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://modal-llm:8003")
    # Import after env vars are set so app config reads them at startup.
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    """Return the bearer auth header for the internal API key."""
    return {"Authorization": f"Bearer {_API_KEY}"}


def _mock_get_ok(_url: str, **_kwargs: object) -> httpx.Response:
    """Return a healthy response for any polled service URL."""
    return httpx.Response(200, json={"status": "ok"})


def _mock_get_timeout(_url: str, **_kwargs: object) -> httpx.Response:
    """Raise a connect timeout for any polled service URL."""
    msg = "timeout"
    raise httpx.ConnectTimeout(msg)


def test_health_all_returns_service_statuses(client: TestClient) -> None:
    """Health-all returns per-service statuses with the database up."""
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_ok):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    assert resp.status_code == HTTPStatus.OK
    data = response_json_object(resp)
    assert data["status"] in ("healthy", "degraded")
    assert "services" in data
    services = json_object_get(data, "services")
    assert "database" in services
    database = json_object_get(services, "database")
    assert json_str(database, "status") == "up"
    assert "checked_at" in data


def test_health_all_marks_down_on_timeout(client: TestClient) -> None:
    """Health-all reports degraded with errors when services time out."""
    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get_timeout):
        resp = client.get("/internal/v1/health/all", headers=_auth())
    assert resp.status_code == HTTPStatus.OK
    data = response_json_object(resp)
    assert data["status"] == "degraded"
    services = json_object_get(data, "services")
    for svc_raw in services.values():
        svc = as_json_object(svc_raw)
        if json_str(svc, "status") == "down":
            assert "error" in svc


def test_health_all_includes_all_configured_services(client: TestClient) -> None:
    """Health-all includes every configured service in its report."""
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
