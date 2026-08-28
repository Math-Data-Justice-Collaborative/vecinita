"""BUG-2026-06-26: Production GET /jobs returns 405 until Modal data-mgmt is redeployed.

PR #95 added list_jobs to create_app(); production Modal image predates that deploy.
Live probe requires Supabase JWT + X-Vecinita-Proxy-Key (admin FE parity; BUG-2026-08-28).
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import response_json_object

_LIVE_MODAL_JOBS = "https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs"
_PROXY_KEY_ENV = "VECINITA_MODAL_PROXY_KEY"


def test_create_app_registers_get_jobs_list() -> None:
    """Local contract: GET /jobs must exist (regression guard for undeployed production)."""
    client = TestClient(create_app(require_proxy_auth=False))
    response = client.get("/jobs")
    assert response.status_code == HTTPStatus.OK, response.text
    body = response_json_object(response)
    assert isinstance(body.get("jobs"), list)


def _supabase_access_token() -> str | None:
    supabase = os.environ.get("SUPABASE_URL", "").rstrip("/")
    anon = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    email = os.environ.get("SUPABASE_ADMIN_EMAIL", "").strip()
    password = os.environ.get("SUPABASE_ADMIN_PASSWORD", "").strip()
    if not all([supabase, anon, email, password]):
        return None
    token_resp = httpx.post(
        f"{supabase}/auth/v1/token?grant_type=password",
        headers={"apikey": anon, "Content-Type": "application/json"},
        json={"email": email, "password": password},
        timeout=30.0,
    )
    if token_resp.status_code != HTTPStatus.OK:
        return None
    token_payload = cast("object", token_resp.json())
    access = as_json_object(token_payload).get("access_token")
    return access if isinstance(access, str) and access else None


@pytest.mark.live
def test_live_modal_get_jobs_list_returns_200() -> None:
    """Production H4: Jobs tab needs GET /jobs — 200 with proxy key + Supabase JWT."""
    proxy_key = os.environ.get(_PROXY_KEY_ENV, "").strip()
    if not proxy_key:
        pytest.skip(f"{_PROXY_KEY_ENV} not set — skip live Modal probe")
    access = _supabase_access_token()
    if access is None:
        pytest.skip("Supabase admin password-grant env required for live GET /jobs")

    response = httpx.get(
        _LIVE_MODAL_JOBS,
        headers={
            "X-Vecinita-Proxy-Key": proxy_key,
            "Authorization": f"Bearer {access}",
        },
        timeout=60.0,
    )
    assert response.status_code == HTTPStatus.OK, (
        f"Expected GET /jobs 200 on production Modal, got {response.status_code}: "
        + f"{response.text[:200]}"
    )
    body = response_json_object(response)
    assert isinstance(body.get("jobs"), list)
