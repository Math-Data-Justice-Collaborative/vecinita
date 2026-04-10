"""Live health checks for all three Render services."""

from __future__ import annotations

import pytest
import requests

pytestmark = pytest.mark.live


def _get(url: str, *, timeout: int = 30, allow_statuses: tuple[int, ...] = ()) -> int:
    resp = requests.get(url, timeout=timeout)
    if allow_statuses and resp.status_code in allow_statuses:
        return resp.status_code
    resp.raise_for_status()
    return resp.status_code


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


def test_frontend_index_returns_200(frontend_url: str):
    status = _get(f"{frontend_url}/", allow_statuses=(200, 301, 302))
    assert status < 400, f"Frontend index returned {status}"


# ---------------------------------------------------------------------------
# Gateway
# ---------------------------------------------------------------------------


def test_gateway_health_returns_200(gateway_health_url: str):
    resp = requests.get(gateway_health_url, timeout=30)
    assert resp.status_code == 200, f"Gateway health endpoint returned {resp.status_code}"
    body = resp.json()
    assert "status" in body, f"Gateway health body missing 'status': {body}"


def test_gateway_integrations_status_returns_200(gateway_url: str):
    resp = requests.get(f"{gateway_url}/api/v1/integrations/status", timeout=30)
    assert resp.status_code == 200, f"Gateway integrations status returned {resp.status_code}"
    body = resp.json()
    assert "status" in body, f"Gateway integrations body missing 'status': {body}"
    assert "components" in body, f"Gateway integrations body missing 'components': {body}"
    assert "gateway" in body, f"Gateway integrations body missing 'gateway': {body}"


def test_gateway_documents_overview_not_broken(gateway_url: str):
    resp = requests.get(f"{gateway_url}/api/v1/documents/overview", timeout=30)
    assert resp.status_code not in (
        404,
        500,
        502,
        503,
    ), f"Gateway /api/v1/documents/overview returned {resp.status_code}"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


def test_agent_health_returns_200(agent_url: str):
    resp = requests.get(f"{agent_url}/health", timeout=30)
    assert resp.status_code == 200, f"Agent /health returned {resp.status_code}"


def test_agent_config_endpoint_returns_providers(agent_config_url: str):
    resp = requests.get(agent_config_url, timeout=30)
    assert resp.status_code == 200, f"Agent config endpoint returned {resp.status_code}"
    body = resp.json()
    assert (
        "providers" in body or "provider" in body
    ), f"Agent config missing 'providers' key: {body}"
