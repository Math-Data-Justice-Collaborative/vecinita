"""Fixtures and skip guard for live Render environment tests.

All tests in backend/tests/live/ use the ``live`` pytest marker and
are automatically skipped when neither RENDER_GATEWAY_URL nor RENDER_AGENT_URL
is set in the environment.  This keeps the suite safe for local offline runs
and CI runs that do not have live Render credentials.

Required environment variables (at least one must be set):
    RENDER_GATEWAY_URL   -- public URL of vecinita-gateway  (e.g. https://gateway.onrender.com)
    RENDER_AGENT_URL     -- public URL of vecinita-agent    (e.g. https://vecinita-agent-lx27.onrender.com)
    RENDER_FRONTEND_URL  -- public URL of vecinita-frontend (optional)
"""

from __future__ import annotations

import os

import pytest
import requests

# ---------------------------------------------------------------------------
# Skip guard — applied to all tests in this package
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(items):
    _has_gateway = bool(os.getenv("RENDER_GATEWAY_URL"))
    _has_agent = bool(os.getenv("RENDER_AGENT_URL"))
    skip_marker = pytest.mark.skip(
        reason="Neither RENDER_GATEWAY_URL nor RENDER_AGENT_URL is set — skipping live tests"
    )
    for item in items:
        if "live" in str(item.fspath):
            item.add_marker(pytest.mark.live)
            if not _has_gateway and not _has_agent:
                item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Session-scoped URL fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def gateway_url() -> str:
    url = os.environ.get("RENDER_GATEWAY_URL", "")
    if not url:
        pytest.skip("RENDER_GATEWAY_URL not set")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def gateway_health_url(gateway_url: str) -> str:
    """Gateway health endpoint with compatibility fallback (/api/v1/health -> /health)."""
    candidates = (f"{gateway_url}/api/v1/health", f"{gateway_url}/health")
    for url in candidates:
        try:
            resp = requests.get(url, timeout=15)
        except requests.RequestException:
            continue
        if resp.status_code == 200:
            return url

    # Return preferred path so downstream assertions report a concrete failure location.
    return candidates[0]


@pytest.fixture(scope="session")
def agent_url() -> str:
    """Agent service URL.

    Resolution order:
    1. ``RENDER_AGENT_URL`` env var (direct agent endpoint)
    2. ``RENDER_GATEWAY_URL`` env var (gateway used as agent proxy)
    3. Skip — neither variable is set.
    """
    url = os.environ.get("RENDER_AGENT_URL") or os.environ.get("RENDER_GATEWAY_URL", "")
    if not url:
        pytest.skip("Neither RENDER_AGENT_URL nor RENDER_GATEWAY_URL is set")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def frontend_url() -> str:
    url = os.environ.get("RENDER_FRONTEND_URL", "")
    if not url:
        pytest.skip("RENDER_FRONTEND_URL not set")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def agent_config_url(agent_url: str) -> str:
    """Resolve config endpoint for either gateway-routed or direct-agent URL."""
    candidates = (f"{agent_url}/api/v1/ask/config", f"{agent_url}/config")
    for url in candidates:
        try:
            resp = requests.get(url, timeout=15)
        except requests.RequestException:
            continue
        if resp.status_code == 200:
            return url
    return candidates[0]


@pytest.fixture(scope="session")
def ask_base_url(agent_url: str) -> str:
    """Resolve ask endpoint base path for gateway-routed or direct-agent URL."""
    candidates = (f"{agent_url}/api/v1/ask", f"{agent_url}/ask")
    for url in candidates:
        try:
            # Send minimal request to detect a live route.
            resp = requests.get(url, params={"question": "ping"}, timeout=20)
        except requests.RequestException:
            continue
        if resp.status_code != 404:
            return url
    return candidates[1]
