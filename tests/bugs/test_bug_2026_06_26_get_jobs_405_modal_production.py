"""BUG-2026-06-26: Production GET /jobs returns 405 until Modal data-mgmt is redeployed.

PR #95 added list_jobs to create_app(); production Modal image predates that deploy.
"""

from __future__ import annotations

import os

import httpx
import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import response_json_object
from vecinita_data_management_backend.app import create_app

_LIVE_MODAL_JOBS = "https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs"
_PROXY_KEY_ENV = "VECINITA_MODAL_PROXY_KEY"


def test_create_app_registers_get_jobs_list() -> None:
    """Local contract: GET /jobs must exist (regression guard for undeployed production)."""
    client = TestClient(create_app(require_proxy_auth=False))
    response = client.get("/jobs")
    assert response.status_code == 200, response.text
    body = response_json_object(response)
    assert isinstance(body.get("jobs"), list)


@pytest.mark.live
def test_live_modal_get_jobs_list_returns_200() -> None:
    """Production H4: Jobs tab needs GET /jobs — fails with 405 until Modal redeploy."""
    proxy_key = os.environ.get(_PROXY_KEY_ENV, "").strip()
    if not proxy_key:
        pytest.skip(f"{_PROXY_KEY_ENV} not set — skip live Modal probe")

    response = httpx.get(
        _LIVE_MODAL_JOBS,
        headers={"X-Vecinita-Proxy-Key": proxy_key},
        timeout=60.0,
    )
    assert response.status_code == 200, (
        f"Expected GET /jobs 200 on production Modal, got {response.status_code}: "
        f"{response.text[:200]}"
    )
    body = response_json_object(response)
    assert isinstance(body.get("jobs"), list)
