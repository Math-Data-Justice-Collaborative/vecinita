"""Integration test defaults: TraceCov schema map for Schemathesis pytest runs.

Schemathesis + TraceCov per https://schemathesis.readthedocs.io/en/stable/guides/coverage/
requires a session ``tracecov_schema`` fixture (see ``tracecov.pytest_plugin``). Without it,
TraceCov stays dormant even when ``tracecov.schemathesis.install()`` runs (CLI-only).

We expose one OpenAPI document per pytest session. Mixed suites (more than one of gateway,
agent, data-management) disable TraceCov (``return None``); run those targets separately
(see root ``Makefile`` ``test-schemathesis``).
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from tests.integration._dm_schemathesis_auth import scraper_bearer_token


def _active_nodeids(session: pytest.Session) -> list[str]:
    """Node ids for items that are not collection-skipped (TraceCov should match executed tests)."""
    out: list[str] = []
    for item in session.items:
        if item.get_closest_marker("skip"):
            continue
        out.append(item.nodeid)
    return out


def _resolve_tracecov_target(nodeids: list[str]) -> str | None:
    gw = any("test_api_schema_schemathesis.py" in nid for nid in nodeids)
    ag = any("test_agent_api_schema_schemathesis.py" in nid for nid in nodeids)
    dm = any("test_data_management_api_schema_schemathesis.py" in nid for nid in nodeids)
    tags = [t for t, ok in (("gateway", gw), ("agent", ag), ("data-management", dm)) if ok]
    if len(tags) != 1:
        return None
    return tags[0]


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip live data-management Schemathesis when no scraper token is configured."""
    for item in items:
        if "test_data_management_api_schema_schemathesis.py" not in item.nodeid:
            continue
        if not scraper_bearer_token():
            item.add_marker(
                pytest.mark.skip(
                    reason="Live data-management Schemathesis requires SCRAPER_API_KEYS or "
                    "SCRAPER_SCHEMATHESIS_BEARER (same as run_schemathesis_live.sh)."
                )
            )


def pytest_collection_finish(session: pytest.Session) -> None:
    session.config._vecinita_tracecov_target = _resolve_tracecov_target(_active_nodeids(session))


def _fetch_dm_openapi_dict() -> dict[str, Any]:
    import httpx

    url = os.environ.get(
        "DATA_MANAGEMENT_SCHEMA_URL",
        "https://vecinita-data-management-api-v1-lx27.onrender.com/openapi.json",
    ).strip()
    r = httpx.get(url, timeout=60.0)
    r.raise_for_status()
    return r.json()


def _agent_openapi_dict() -> dict[str, Any]:
    from src.agent.main import app

    return app.openapi()


def _gateway_openapi_dict() -> dict[str, Any] | None:
    """Gateway OpenAPI for TraceCov without importlib.reload (avoids clashing with tests)."""
    saved: dict[str, str | None] = {}
    defaults = {
        "ENABLE_AUTH": "false",
        "REINDEX_SERVICE_URL": "",
        "SCRAPER_ENDPOINT": "http://127.0.0.1:1",
        "MODEL_ENDPOINT": "http://127.0.0.1:1",
    }
    try:
        for key, val in defaults.items():
            saved[key] = os.environ.get(key)
            if saved[key] is None:
                os.environ[key] = val
        from src.api.main import app

        return app.openapi()
    except Exception:
        return None
    finally:
        for key, old in saved.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


@pytest.fixture(scope="session")
def tracecov_schema(request: pytest.FixtureRequest) -> dict[str, Any] | None:
    if os.environ.get("SCHEMATHESIS_COVERAGE", "").strip().lower() in ("0", "false", "no"):
        return None
    target = getattr(request.config, "_vecinita_tracecov_target", None)
    if target is None:
        return None
    if target == "agent":
        return _agent_openapi_dict()
    if target == "gateway":
        return _gateway_openapi_dict()
    if target == "data-management":
        return _fetch_dm_openapi_dict()
    return None
