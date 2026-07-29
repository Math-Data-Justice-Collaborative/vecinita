"""BUG-2026-07-29: Jobs SSE preflight must allow Cache-Control and Last-Event-ID.

Admin `subscribeJobEvents` sends Cache-Control: no-cache and optional Last-Event-ID.
Without those in CORS allow_headers, OPTIONS /jobs/events returns 400 Disallowed CORS
headers and the UI falls back to “Live updates unavailable — polling every 4s.”
"""

from __future__ import annotations

import os
from http import HTTPStatus

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app as create_data_mgmt_app

from tests.helpers.json_response import header_str

ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"
_LIVE_EVENTS = "https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs/events"
# Headers the browser requests for fetch-based SSE (see jobs.ts subscribeJobEvents).
_SSE_REQUEST_HEADERS = "accept, authorization, cache-control, last-event-id, x-vecinita-proxy-key"


@pytest.fixture(autouse=True)
def _cors_env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"https://vecinita-chat-rag-frontend.example.com,{ADMIN_ORIGIN}",
    )


def test_jobs_events_cors_preflight_allows_sse_request_headers() -> None:
    """OPTIONS /jobs/events must allow Cache-Control and Last-Event-ID (BUG-2026-07-29)."""
    client = TestClient(create_data_mgmt_app(require_proxy_auth=False))
    response = client.options(
        "/jobs/events",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": _SSE_REQUEST_HEADERS,
        },
    )
    assert response.status_code == HTTPStatus.OK, response.text
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_headers = header_str(response.headers, "access-control-allow-headers").lower()
    assert "cache-control" in allow_headers, allow_headers
    assert "last-event-id" in allow_headers, allow_headers
    assert "x-vecinita-proxy-key" in allow_headers, allow_headers


@pytest.mark.live
def test_live_modal_jobs_events_options_allows_sse_headers() -> None:
    """Production H4: OPTIONS /jobs/events with SSE headers must not be 400.

    Opt-in after Modal redeploy — unset in PR CI so undeployed production does not
    fail the merge gate (set VECINITA_RUN_LIVE_CORS=1 to probe).
    """
    if os.environ.get("VECINITA_RUN_LIVE_CORS", "").strip() != "1":
        pytest.skip("Set VECINITA_RUN_LIVE_CORS=1 to probe production after Modal redeploy")

    response = httpx.options(
        _LIVE_EVENTS,
        headers={
            "Origin": "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": _SSE_REQUEST_HEADERS,
        },
        timeout=60.0,
    )
    assert response.status_code == HTTPStatus.OK, (
        f"Expected 200 CORS preflight, got {response.status_code}: {response.text[:200]}"
    )
    allow_headers = header_str(response.headers, "access-control-allow-headers").lower()
    assert "cache-control" in allow_headers, allow_headers
    assert "last-event-id" in allow_headers, allow_headers
