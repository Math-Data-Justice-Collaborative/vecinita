"""UJ-070 / TC-218–219: ask + stream include energy_estimate (F65 / AC-UX3)."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import cast

import pytest
from fastapi.testclient import TestClient
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import response_json_object

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


def _parse_sse(raw: str) -> list[JsonObject]:
    return [
        as_json_object(cast("object", json.loads(line.removeprefix("data: "))))
        for line in raw.splitlines()
        if line.startswith("data: ")
    ]


def _assert_energy_estimate(payload: object) -> None:
    assert isinstance(payload, dict)
    estimate = as_json_object(cast("object", payload))
    for key in (
        "wh",
        "g_co2e",
        "method",
        "advisory",
        "car_km_equiv",
        "car_m_equiv",
    ):
        assert key in estimate, f"missing energy_estimate.{key}"
    assert estimate["method"] == "tdp_util_walltime_v1"
    assert isinstance(estimate["wh"], (int, float))
    assert isinstance(estimate["g_co2e"], (int, float))
    assert isinstance(estimate["car_km_equiv"], (int, float))
    assert isinstance(estimate["car_m_equiv"], (int, float))
    assert float(estimate["wh"]) >= 0.0
    assert float(estimate["g_co2e"]) >= 0.0
    assert float(estimate["car_m_equiv"]) == pytest.approx(
        float(estimate["car_km_equiv"]) * 1000.0,
        rel=1e-6,
        abs=1e-9,
    )
    advisory = estimate["advisory"]
    assert isinstance(advisory, str) and advisory.strip()


def test_uj070_ask_includes_energy_estimate(chat_client: TestClient) -> None:
    """TC-218: POST /api/v1/ask returns energy_estimate with car_* fields."""
    response = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert "energy_estimate" in body
    _assert_energy_estimate(body["energy_estimate"])


def test_uj070_stream_done_includes_energy_estimate(chat_client: TestClient) -> None:
    """TC-219: stream done event includes energy_estimate."""
    stream = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "What are the food pantry hours?"},
    )
    assert stream.status_code == HTTPStatus.OK
    events = _parse_sse(stream.text)
    assert events, "expected SSE events"
    done = events[-1]
    assert done.get("done") is True
    assert "energy_estimate" in done
    _assert_energy_estimate(done["energy_estimate"])
