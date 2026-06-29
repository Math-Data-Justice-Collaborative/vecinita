"""TC-001: POST /api/v1/ask/stream SSE integration."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import pytest
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _parse_sse(raw: str) -> list[JsonObject]:
    return [
        as_json_object(cast("object", json.loads(line.removeprefix("data: "))))
        for line in raw.splitlines()
        if line.startswith("data: ")
    ]


def test_ask_stream_emits_token_sources_done(chat_client: TestClient) -> None:
    """POST /api/v1/ask/stream emits token, sources, and done SSE events."""
    response = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "When is the food pantry open?"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(response.text)
    assert any("token" in event for event in events)
    assert any("sources" in event for event in events)
    assert events[-1].get("done") is True
