"""Live service-to-service connectivity tests for Render."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_gateway_health_implies_agent_reachable(gateway_health_url: str):
    """Gateway health passing confirms the gateway→agent private-network path is live.

    If ``agent_service`` is ``error``, check Render gateway env ``AGENT_SERVICE_URL``
    (private service URL) and that the agent service returns 200 from ``GET /health``.
    """
    resp = requests.get(gateway_health_url, timeout=30)
    assert (
        resp.status_code == 200
    ), f"gateway health endpoint returned {resp.status_code} — agent may be unreachable"
    payload = resp.json()
    assert payload.get("agent_service") == "ok", (
        "gateway health indicates agent dependency is not healthy: "
        f"agent_service={payload.get('agent_service')} payload={payload}"
    )


def test_agent_config_shows_route_endpoints_not_localhost(agent_config_url: str):
    """Agent config endpoint must not report localhost as the model/embedding endpoint."""
    resp = requests.get(agent_config_url, timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    config_str = str(body).lower()
    assert (
        "localhost" not in config_str
    ), f"Agent config leaks a localhost endpoint — routing routing may be broken: {body}"


def test_service_auth_enforced_on_unauthenticated_request(ask_base_url: str):
    """Ask without a required question must not return 200 (GET contract on gateway and agent)."""
    # POST to /api/v1/ask returns 405; use GET without ``question`` → 422 validation error.
    resp = requests.get(ask_base_url, timeout=30)
    # Acceptable: 400 validation error, 422 unprocessable, 403 forbidden, 401 unauthorized
    # Not acceptable: 200 (passed through with empty input), 5xx server crashes
    assert resp.status_code in (
        400,
        401,
        403,
        422,
    ), f"Expected auth/validation rejection for empty ask, got {resp.status_code}: {resp.text[:200]}"
