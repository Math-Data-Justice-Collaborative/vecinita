"""TC-060 / AC-E10: CORS preflight on all EV-002 endpoints from admin origin."""

from __future__ import annotations

import os
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import (
    create_app as create_write_app,
)

pytestmark = pytest.mark.unit

ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"


@pytest.fixture(autouse=True)
def cors_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the allowed CORS origin to the admin frontend for every test."""
    monkeypatch.setenv("VECINITA_CORS_ORIGINS", ADMIN_ORIGIN)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide a TestClient for the internal write API with env configured."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    return TestClient(create_write_app())


def _preflight(client: TestClient, path: str, method: str) -> dict[str, str]:
    """Send a CORS preflight and assert it is allowed for the admin origin."""
    resp = client.options(
        path,
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert resp.status_code == HTTPStatus.OK, f"Preflight failed for {method} {path}"
    assert resp.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    return dict(resp.headers)


def test_cors_bulk_delete(client: TestClient) -> None:
    """Bulk delete endpoint allows DELETE via CORS preflight."""
    hdrs = _preflight(client, "/internal/v1/documents/bulk", "DELETE")
    assert "DELETE" in hdrs.get("access-control-allow-methods", "").upper()


def test_cors_bulk_tags(client: TestClient) -> None:
    """Bulk tags endpoint allows PATCH via CORS preflight."""
    hdrs = _preflight(client, "/internal/v1/documents/bulk/tags", "PATCH")
    assert "PATCH" in hdrs.get("access-control-allow-methods", "").upper()


def test_cors_bulk_retag(client: TestClient) -> None:
    """Bulk retag endpoint allows POST via CORS preflight."""
    _preflight(client, "/internal/v1/documents/bulk/retag", "POST")


def test_cors_bulk_metadata(client: TestClient) -> None:
    """Bulk metadata endpoint allows PATCH via CORS preflight."""
    hdrs = _preflight(client, "/internal/v1/documents/bulk/metadata", "PATCH")
    assert "PATCH" in hdrs.get("access-control-allow-methods", "").upper()


def test_cors_health_all(client: TestClient) -> None:
    """Health-all endpoint allows GET via CORS preflight."""
    _preflight(client, "/internal/v1/health/all", "GET")


def test_cors_stats_summary(client: TestClient) -> None:
    """Stats summary endpoint allows GET via CORS preflight."""
    _preflight(client, "/internal/v1/stats/summary", "GET")


def test_cors_stats_served(client: TestClient) -> None:
    """Stats served endpoint allows POST via CORS preflight."""
    _preflight(client, "/internal/v1/stats/served", "POST")


def test_cors_stats_top_served(client: TestClient) -> None:
    """Top-served stats endpoint allows GET via CORS preflight."""
    _preflight(client, "/internal/v1/stats/top-served", "GET")


def test_cors_audit_log(client: TestClient) -> None:
    """Audit log endpoint allows GET via CORS preflight."""
    _preflight(client, "/internal/v1/audit", "GET")


def test_cors_audit_cleanup(client: TestClient) -> None:
    """Audit cleanup endpoint allows POST via CORS preflight."""
    _preflight(client, "/internal/v1/audit/cleanup", "POST")
