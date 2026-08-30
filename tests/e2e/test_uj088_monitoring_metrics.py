"""UJ-088 / TC-299-301: Monitoring metrics API e2e (F84 / ADR-055)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_uj088_metrics_summary_and_timeseries(write_client: TestClient) -> None:
    """TC-299/300: summary + timeseries after a privacy-safe event."""
    create = write_client.post(
        "/internal/v1/metrics/events",
        json={
            "workload": "chat",
            "outcome": "success",
            "latency_ms": 250,
            "locale": "en",
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    event_id = create.json()["event_id"]
    assert isinstance(event_id, str)

    summary = write_client.get(
        "/internal/v1/metrics/summary?window=24h",
        headers=auth_headers(),
    )
    assert summary.status_code == HTTPStatus.OK
    body = summary.json()
    assert body["window"] == "24h"
    assert body["workloads"]["chat"]["total"] >= 1
    assert "question" not in body
    assert "answer" not in body

    series = write_client.get(
        "/internal/v1/metrics/timeseries?metric=chat_success_rate&window=24h",
        headers=auth_headers(),
    )
    assert series.status_code == HTTPStatus.OK
    assert series.json()["metric"] == "chat_success_rate"
    assert isinstance(series.json()["buckets"], list)

    got = write_client.get(
        f"/internal/v1/metrics/events/{event_id}",
        headers=auth_headers(),
    )
    assert got.status_code == HTTPStatus.OK
    record = got.json()
    assert record["workload"] == "chat"
    assert record["outcome"] == "success"
    assert "question" not in record
    assert "answer" not in record


def test_uj088_metrics_events_reject_chat_content(write_client: TestClient) -> None:
    """TC-301: forbidden content fields are rejected."""
    response = write_client.post(
        "/internal/v1/metrics/events",
        json={
            "workload": "chat",
            "outcome": "success",
            "latency_ms": 10,
            "question": "should not be stored",
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_uj088_metrics_events_embed_with_job_id(write_client: TestClient) -> None:
    """Embed failure event accepts job_id correlation (ADR-055)."""
    job_id = str(uuid4())
    response = write_client.post(
        "/internal/v1/metrics/events",
        json={
            "workload": "embed",
            "outcome": "failure",
            "latency_ms": 900,
            "error_code": "EmbeddingClientError",
            "job_id": job_id,
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    event_id = response.json()["event_id"]
    got = write_client.get(
        f"/internal/v1/metrics/events/{event_id}",
        headers=auth_headers(),
    )
    assert got.status_code == HTTPStatus.OK
    assert got.json()["job_id"] == job_id
    assert got.json()["workload"] == "embed"
