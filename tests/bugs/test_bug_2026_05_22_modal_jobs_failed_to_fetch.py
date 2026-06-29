"""BUG-2026-05-22: Admin POST /jobs — browser preflight must reach FastAPI CORS.

Modal `requires_proxy_auth=True` returns 401 on OPTIONS before CORSMiddleware runs;
browser shows Failed to fetch. App-level Modal-Key auth must replace edge proxy auth.
"""

from __future__ import annotations

import re
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app as create_data_mgmt_app

from tests.helpers.json_response import header_str

ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"
_MODAL_APP = Path(__file__).resolve().parents[2] / "infra" / "modal" / "data_management_app.py"
_LIVE_MODAL_JOBS = "https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs"


@pytest.fixture(autouse=True)
def _cors_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"https://vecinita-chat-rag-frontend.example.com,{ADMIN_ORIGIN}",
    )


def test_modal_data_mgmt_asgi_does_not_use_edge_proxy_auth() -> None:
    """Browser CORS preflight cannot satisfy Modal requires_proxy_auth (see deploy-report H4)."""
    source = _MODAL_APP.read_text(encoding="utf-8")
    assert "requires_proxy_auth=True" not in source, (
        "data_management_app.py must not use requires_proxy_auth=True; "
        "use FastAPI Modal-Key check so OPTIONS reaches CORSMiddleware"
    )
    assert re.search(r"requires_proxy_auth\s*=\s*False", source), (
        "Explicit requires_proxy_auth=False on @modal.asgi_app for browser /jobs"
    )


def test_data_mgmt_options_preflight_without_modal_key_succeeds() -> None:
    """OPTIONS preflight does not send Modal-Key; must still return 200 + CORS headers."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/jobs",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, x-vecinita-proxy-key",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "POST" in allow_methods


@pytest.mark.live
def test_live_modal_jobs_options_preflight_succeeds() -> None:
    """Production H4: OPTIONS /jobs from admin origin must not return 401 at edge."""
    response = httpx.options(
        _LIVE_MODAL_JOBS,
        headers={
            "Origin": "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, x-vecinita-proxy-key",
        },
        timeout=60.0,
    )
    assert response.status_code == 200, (
        f"Expected 200 CORS preflight, got {response.status_code}: {response.text[:200]}"
    )
    origin = header_str(response.headers, "access-control-allow-origin")
    assert origin in (
        "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
        "*",
    ), f"Missing Allow-Origin: {origin!r}"
