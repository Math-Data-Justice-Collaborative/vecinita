"""F84 / TC-299-300: metrics summary and timeseries endpoints."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_metrics_summary_24h_shape(write_client: TestClient) -> None:
    """TC-299: summary returns ingest/chat/embed workloads for 24h."""
    # Seed one chat event so chat totals are non-zero when DB is fresh.
    _ = write_client.post(
        "/internal/v1/metrics/events",
        json={
            "workload": "chat",
            "outcome": "success",
            "latency_ms": 100,
            "locale": "en",
        },
        headers=auth_headers(),
    )
    response = write_client.get(
        "/internal/v1/metrics/summary?window=24h",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["window"] == "24h"
    for key in ("ingest", "chat", "embed"):
        workload = body["workloads"][key]
        assert "total" in workload
        assert "succeeded" in workload
        assert "failed" in workload
        assert "success_rate" in workload
    assert body["workloads"]["chat"]["total"] >= 1
    assert "question" not in body
    assert "answer" not in body


def test_metrics_summary_7d_ok(write_client: TestClient) -> None:
    """TC-299: 7d window accepted."""
    response = write_client.get(
        "/internal/v1/metrics/summary?window=7d",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["window"] == "7d"


def test_metrics_timeseries_ingest_success_rate(write_client: TestClient) -> None:
    """TC-300: timeseries returns ordered buckets list."""
    response = write_client.get(
        "/internal/v1/metrics/timeseries?metric=ingest_success_rate&window=7d",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["metric"] == "ingest_success_rate"
    assert body["window"] == "7d"
    assert isinstance(body["buckets"], list)


def test_metrics_summary_rejects_bad_window(write_client: TestClient) -> None:
    """Invalid window → 422."""
    response = write_client.get(
        "/internal/v1/metrics/summary?window=year",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
