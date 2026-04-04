"""Fixtures and skip guard for live Render environment tests.

All tests in backend/tests/live/ use the ``live`` pytest marker and
are automatically skipped when RENDER_GATEWAY_URL is not set in the
environment.  This keeps the suite safe for local offline runs and CI
runs that do not have live Render credentials.

Required environment variables:
    RENDER_GATEWAY_URL   -- public URL of vecinita-gateway  (e.g. https://gateway.onrender.com)
    RENDER_AGENT_URL     -- public URL of vecinita-agent    (optional, gateway used as routing)
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
    skip_marker = pytest.mark.skip(reason="RENDER_GATEWAY_URL not set — skipping live tests")
    for item in items:
        if "live" in str(item.fspath):
            item.add_marker(pytest.mark.live)
            if not os.getenv("RENDER_GATEWAY_URL"):
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
def agent_url(gateway_url: str) -> str:
    """Agent URL; falls back to gateway if RENDER_AGENT_URL is not set."""
    return os.environ.get("RENDER_AGENT_URL", gateway_url).rstrip("/")


@pytest.fixture(scope="session")
def frontend_url() -> str:
    url = os.environ.get("RENDER_FRONTEND_URL", "")
    if not url:
        pytest.skip("RENDER_FRONTEND_URL not set")
    return url.rstrip("/")
