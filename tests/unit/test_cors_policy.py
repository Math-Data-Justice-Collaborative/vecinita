"""H0c: browser CORS policy on FastAPI apps (connectivity-gates.md)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app as create_chat_app
from vecinita_data_management_backend.app import create_app as create_data_mgmt_app
from vecinita_internal_write_api.app import create_app as create_write_app

CHAT_ORIGIN = "https://vecinita-chat-rag-frontend.example.com"
ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"


@pytest.fixture(autouse=True)
def _cors_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"{CHAT_ORIGIN},{ADMIN_ORIGIN}",
    )


def test_chat_rag_cors_preflight_on_ask_stream() -> None:
    client = TestClient(create_chat_app())
    response = client.options(
        "/api/v1/ask/stream",
        headers={
            "Origin": CHAT_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == CHAT_ORIGIN


def test_internal_write_cors_preflight_on_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/documents",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN


def test_internal_write_cors_preflight_allows_delete_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for internal write app import")
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    client = TestClient(create_write_app())
    response = client.options(
        "/internal/v1/documents/00000000-0000-0000-0000-000000000001",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = response.headers.get("access-control-allow-methods", "").upper()
    assert "DELETE" in allow_methods


def test_data_management_cors_preflight_on_jobs() -> None:
    client = TestClient(
        create_data_mgmt_app(require_proxy_auth=False),
    )
    response = client.options(
        "/jobs",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, modal-key",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN


def test_no_cors_middleware_when_origins_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VECINITA_CORS_ORIGINS", raising=False)
    client = TestClient(create_chat_app())
    response = client.options(
        "/health",
        headers={"Origin": CHAT_ORIGIN, "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers
