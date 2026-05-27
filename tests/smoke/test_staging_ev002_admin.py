"""T3 live: EV-002 admin API smokes (UJ-013-UJ-021) when staging write URL + key are set."""

from __future__ import annotations

import os

import httpx
import pytest
from tests.helpers.json_response import response_json_object

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


@pytest.fixture
def write_api() -> str:
    url = _env("VECINITA_STAGING_WRITE_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    return url.rstrip("/")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    key = _env("VECINITA_STAGING_INTERNAL_API_KEY")
    if not key:
        pytest.skip("Set VECINITA_STAGING_INTERNAL_API_KEY for EV-002 admin smokes")
    return {"Authorization": f"Bearer {key}"}


def test_t3_stats_summary(write_api: str, auth_headers: dict[str, str]) -> None:
    """UJ-013: GET /internal/v1/stats/summary returns aggregate counts."""
    resp = httpx.get(
        f"{write_api}/internal/v1/stats/summary",
        headers=auth_headers,
        timeout=30.0,
    )
    assert resp.status_code == 200
    body = response_json_object(resp)
    assert "total_documents" in body
    assert "total_chunks" in body


def test_t3_health_all(write_api: str, auth_headers: dict[str, str]) -> None:
    """UJ-014: GET /internal/v1/health/all returns service map."""
    resp = httpx.get(
        f"{write_api}/internal/v1/health/all",
        headers=auth_headers,
        timeout=60.0,
    )
    assert resp.status_code == 200
    body = response_json_object(resp)
    assert body.get("status") in ("healthy", "degraded")
    services = body.get("services")
    assert isinstance(services, dict)
    assert "database" in services


def test_t3_audit_log(write_api: str, auth_headers: dict[str, str]) -> None:
    """UJ-017: GET /internal/v1/audit returns paginated items."""
    resp = httpx.get(
        f"{write_api}/internal/v1/audit",
        headers=auth_headers,
        params={"page": 1, "page_size": 10},
        timeout=30.0,
    )
    assert resp.status_code == 200
    body = response_json_object(resp)
    assert "items" in body
    assert "total_count" in body


def test_t3_top_served(write_api: str, auth_headers: dict[str, str]) -> None:
    """UJ-019: GET /internal/v1/stats/top-served returns ranked documents."""
    resp = httpx.get(
        f"{write_api}/internal/v1/stats/top-served",
        headers=auth_headers,
        params={"limit": 5},
        timeout=30.0,
    )
    assert resp.status_code == 200
    body = response_json_object(resp)
    assert "items" in body
