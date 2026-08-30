"""F84 / TC-301: POST /internal/v1/metrics/events privacy-safe operational events."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from tests.helpers.json_response import json_str, response_json_object
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

# Accepted chat success event (api-contract F84 / ADR-055).
_CHAT_OK = {
    "workload": "chat",
    "outcome": "success",
    "latency_ms": 1820,
    "error_code": None,
    "locale": "en",
}


def test_metrics_events_accepts_chat_outcome(write_client: TestClient) -> None:
    """TC-301 happy path: allow-listed chat event returns 202 with event_id."""
    response = write_client.post(
        "/internal/v1/metrics/events",
        json=_CHAT_OK,
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert body["acknowledged"] is True
    event_id = json_str(body, "event_id")

    get_resp = write_client.get(
        f"/internal/v1/metrics/events/{event_id}",
        headers=auth_headers(),
    )
    assert get_resp.status_code == HTTPStatus.OK
    got = response_json_object(get_resp)
    assert got["event_id"] == event_id
    assert got["workload"] == "chat"
    assert got["outcome"] == "success"
    assert got["latency_ms"] == _CHAT_OK["latency_ms"]
    assert got["locale"] == _CHAT_OK["locale"]
    assert "question" not in got
    assert "answer" not in got


def test_metrics_events_accepts_embed_with_job_id(write_client: TestClient) -> None:
    """Embed stage event may correlate to ingest job_id."""
    job_id = str(uuid4())
    response = write_client.post(
        "/internal/v1/metrics/events",
        json={
            "workload": "embed",
            "outcome": "failure",
            "latency_ms": 900,
            "error_code": "EmbedClientError",
            "job_id": job_id,
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.ACCEPTED
    body = response_json_object(response)
    assert body["acknowledged"] is True

    got = response_json_object(
        write_client.get(
            f"/internal/v1/metrics/events/{json_str(body, 'event_id')}",
            headers=auth_headers(),
        ),
    )
    assert got["workload"] == "embed"
    assert got["outcome"] == "failure"
    assert got["error_code"] == "EmbedClientError"
    assert got["job_id"] == job_id


@pytest.mark.parametrize(
    "forbidden_field",
    ["question", "answer", "prompt", "message"],
)
def test_metrics_events_rejects_chat_content_fields(
    write_client: TestClient,
    forbidden_field: str,
) -> None:
    """TC-301: bodies with chat content fields are rejected (extra=forbid)."""
    payload = {**_CHAT_OK, forbidden_field: "should never persist"}
    response = write_client.post(
        "/internal/v1/metrics/events",
        json=payload,
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_metrics_events_get_unknown_404(write_client: TestClient) -> None:
    """Unknown event_id returns 404."""
    response = write_client.get(
        f"/internal/v1/metrics/events/{uuid4()}",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
