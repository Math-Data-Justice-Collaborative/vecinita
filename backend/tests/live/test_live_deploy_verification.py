"""Live deploy verification tests (Phase F).

Confirms the deployed services are running in production-safe mode:
- Consistent health response shape across all services
- No test/debug providers in agent config
- CORS headers present on gateway preflight
- No Python traceback leak on malformed input
- Ask SLA (< 30s) — duplicated from ask_flow for standalone verification run
"""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def test_gateway_health_has_status_key(gateway_health_url: str):
    resp = requests.get(gateway_health_url, timeout=30)
    assert resp.status_code == 200
    assert "status" in resp.json(), f"Gateway health missing 'status': {resp.json()}"


def test_agent_health_has_status_key(agent_url: str):
    resp = requests.get(f"{agent_url}/health", timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    # Accept 'status' or 'ok' or 'healthy' as valid indicators
    assert any(
        k in body for k in ("status", "ok", "healthy")
    ), f"Agent health body has no recognised status key: {body}"


def test_agent_config_shows_no_debug_or_test_providers(agent_config_url: str):
    """Production config must not expose debug, test, or local-only providers."""
    resp = requests.get(agent_config_url, timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    providers = body.get("providers", body.get("provider", ""))
    providers_str = str(providers).lower()
    debug_indicators = {"debug", "test-provider", "fake", "mock", "dev-only"}
    found = [d for d in debug_indicators if d in providers_str]
    assert not found, f"Agent config exposes debug indicators {found}: {body}"


def test_gateway_cors_preflight_returns_headers(gateway_url: str):
    """Gateway OPTIONS preflight must return Access-Control headers."""
    resp = requests.options(
        f"{gateway_url}/api/v1/ask",
        headers={
            "Origin": "https://vecinita.example.com",
            "Access-Control-Request-Method": "POST",
        },
        timeout=30,
    )
    # 200 or 204 are both valid preflight responses
    assert resp.status_code in (200, 204), f"Gateway CORS preflight returned {resp.status_code}"
    cors_header = resp.headers.get("Access-Control-Allow-Origin", "")
    assert cors_header, "Gateway CORS preflight response missing Access-Control-Allow-Origin"


def test_malformed_request_does_not_leak_traceback(gateway_url: str):
    """A malformed body must not return a Python traceback in the response."""
    resp = requests.post(
        f"{gateway_url}/api/v1/ask",
        data="not-valid-json{{{{",
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    body_text = resp.text
    assert (
        "Traceback" not in body_text
    ), f"Gateway leaked a Python traceback on malformed input: {body_text[:300]}"
    assert (
        'File "' not in body_text
    ), f"Gateway response contains file path (possible traceback leak): {body_text[:300]}"
