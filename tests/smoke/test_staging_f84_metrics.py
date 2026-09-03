"""F84 / UJ-088 — staging write-api must expose metrics routes (TC-299, TC-300).

Guards against deploy drift: staging write-api image predating F84 returned 404 on
/internal/v1/metrics/* while stats routes worked (BUG-2026-09-03).
"""

from __future__ import annotations

import os
from http import HTTPStatus

import httpx
import pytest

from tests.helpers.json_response import json_list, json_object_get, response_json_object

pytestmark = [pytest.mark.e2e, pytest.mark.live]


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


@pytest.fixture
def write_api() -> str:
    """Return the staging write API base URL, skipping when unset."""
    url = _env("VECINITA_STAGING_WRITE_URL")
    if not url:
        pytest.skip("Set VECINITA_STAGING_WRITE_URL")
    return url.rstrip("/")


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Bearer auth for staging write API (internal key or operator JWT)."""
    key = _env("VECINITA_STAGING_INTERNAL_API_KEY")
    if not key:
        pytest.skip("Set VECINITA_STAGING_INTERNAL_API_KEY")
    return {"Authorization": f"Bearer {key}"}


def test_f84_metrics_routes_registered_in_openapi(write_api: str) -> None:
    """OpenAPI must list F84 metrics summary + timeseries (not stats-only drift)."""
    resp = httpx.get(f"{write_api}/openapi.json", timeout=30.0)
    assert resp.status_code == HTTPStatus.OK
    paths = response_json_object(resp).get("paths")
    assert isinstance(paths, dict)
    assert "/internal/v1/metrics/summary" in paths
    assert "/internal/v1/metrics/timeseries" in paths


def test_f84_metrics_summary_live(write_api: str, auth_headers: dict[str, str]) -> None:
    """TC-299: GET /internal/v1/metrics/summary returns workload aggregates."""
    resp = httpx.get(
        f"{write_api}/internal/v1/metrics/summary",
        headers=auth_headers,
        params={"window": "24h"},
        timeout=30.0,
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    body = response_json_object(resp)
    assert body["window"] == "24h"
    workloads = json_object_get(body, "workloads")
    for key in ("ingest", "chat", "embed"):
        workload = json_object_get(workloads, key)
        assert "success_rate" in workload


def test_f84_metrics_timeseries_live(write_api: str, auth_headers: dict[str, str]) -> None:
    """TC-300: GET /internal/v1/metrics/timeseries returns bucket list."""
    resp = httpx.get(
        f"{write_api}/internal/v1/metrics/timeseries",
        headers=auth_headers,
        params={"metric": "ingest_success_rate", "window": "7d"},
        timeout=30.0,
    )
    assert resp.status_code == HTTPStatus.OK, resp.text
    body = response_json_object(resp)
    assert body["metric"] == "ingest_success_rate"
    assert body["window"] == "7d"
    assert isinstance(json_list(body, "buckets"), list)
