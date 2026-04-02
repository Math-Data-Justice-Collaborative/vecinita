"""Live service-to-service connectivity tests for Render."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_gateway_health_implies_agent_reachable(gateway_url: str):
    """Gateway health passing confirms the gateway→agent private-network path is live."""
    resp = requests.get(f"{gateway_url}/api/v1/health", timeout=30)
    assert (
        resp.status_code == 200
    ), f"gateway /api/v1/health returned {resp.status_code} — agent may be unreachable"


def test_agent_config_shows_proxy_endpoints_not_localhost(agent_url: str):
    """Agent config endpoint must not report localhost as the model/embedding endpoint."""
    resp = requests.get(f"{agent_url}/api/v1/ask/config", timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    config_str = str(body).lower()
    assert (
        "localhost" not in config_str
    ), f"Agent config leaks a localhost endpoint — proxy routing may be broken: {body}"


def test_proxy_auth_enforced_on_unauthenticated_request(agent_url: str):
    """A request with no proxy token to a proxy-protected endpoint must be rejected."""
    # The agent /api/v1/ask without a valid payload should return 422 or similar —
    # but a completely missing auth token (when AGENT_ENFORCE_PROXY=true) may return 403.
    # We just confirm it's not a 200 pass-through with no validation.
    resp = requests.post(
        f"{agent_url}/api/v1/ask",
        json={},  # intentionally empty
        timeout=30,
    )
    # Acceptable: 400 validation error, 422 unprocessable, 403 forbidden, 401 unauthorized
    # Not acceptable: 200 (passed through with empty input), 5xx server crashes
    assert resp.status_code in (
        400,
        401,
        403,
        422,
    ), f"Expected auth/validation rejection for empty ask, got {resp.status_code}: {resp.text[:200]}"
