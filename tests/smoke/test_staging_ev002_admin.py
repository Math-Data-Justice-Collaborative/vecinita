"""T3 live: EV-002 admin API smokes (UJ-013-UJ-021) when staging write URL + key are set."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import cast

import httpx
import pytest
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import response_json_object

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _require_staging_operator_creds() -> tuple[str, str, str, str]:
    supabase = _env("SUPABASE_URL")
    anon = _env("SUPABASE_PUBLISHABLE_KEY") or _env("VITE_SUPABASE_PUBLISHABLE_KEY")
    email = _env("SUPABASE_ADMIN_EMAIL")
    password = _env("SUPABASE_ADMIN_PASSWORD")
    if not supabase or not anon or not email or not password:
        pytest.skip(
            "Set staging SUPABASE_URL/SUPABASE_PUBLISHABLE_KEY/"
            + "SUPABASE_ADMIN_EMAIL/SUPABASE_ADMIN_PASSWORD"
        )
    return supabase, anon, email, password


def _mint_operator_access_token() -> str:
    supabase, anon, email, password = _require_staging_operator_creds()
    token_resp = httpx.post(
        f"{supabase.rstrip('/')}/auth/v1/token?grant_type=password",
        headers={"apikey": anon, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30.0,
    )
    assert token_resp.status_code == HTTPStatus.OK, token_resp.text
    token_payload = cast("object", token_resp.json())
    access_raw = as_json_object(token_payload).get("access_token")
    assert isinstance(access_raw, str)
    assert access_raw
    return access_raw


@pytest.fixture
def write_api() -> str:
    """Return the staging write API base URL, skipping when unset."""
    url = _env("VECINITA_STAGING_WRITE_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    return url.rstrip("/")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return bearer auth headers for EV-002 admin smokes.

    Prefer the staging internal API key when available; otherwise mint a real
    staging operator JWT via password grant so live auth regressions surface in
    smoke runs too.
    """
    key = _env("VECINITA_STAGING_INTERNAL_API_KEY")
    if key:
        return {"Authorization": f"Bearer {key}"}
    return {"Authorization": f"Bearer {_mint_operator_access_token()}"}


def test_t3_stats_summary(write_api: str, auth_headers: dict[str, str]) -> None:
    """UJ-013: GET /internal/v1/stats/summary returns aggregate counts."""
    resp = httpx.get(
        f"{write_api}/internal/v1/stats/summary",
        headers=auth_headers,
        timeout=30.0,
    )
    assert resp.status_code == HTTPStatus.OK
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
    assert resp.status_code == HTTPStatus.OK
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
    assert resp.status_code == HTTPStatus.OK
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
    assert resp.status_code == HTTPStatus.OK
    body = response_json_object(resp)
    assert "items" in body


def test_t3_modal_jobs_with_operator_jwt() -> None:
    """UJ-023/UJ-026: staging Modal jobs accept a signed-in operator JWT."""
    base = _env("VECINITA_MODAL_DATA_MGMT_URL")
    proxy = _env("VECINITA_MODAL_PROXY_KEY")
    if not base or not proxy:
        pytest.skip(
            "Set VECINITA_MODAL_DATA_MGMT_URL/VECINITA_MODAL_PROXY_KEY and staging "
            + "SUPABASE_URL/SUPABASE_PUBLISHABLE_KEY/SUPABASE_ADMIN_EMAIL/SUPABASE_ADMIN_PASSWORD"
        )
    access_raw = _mint_operator_access_token()

    resp = httpx.get(
        f"{base.rstrip('/')}/jobs",
        headers={
            "X-Vecinita-Proxy-Key": proxy,
            "Authorization": f"Bearer {access_raw}",
        },
        timeout=30.0,
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    body = response_json_object(resp)
    assert "jobs" in body
