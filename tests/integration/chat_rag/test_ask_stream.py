"""TC-001: POST /api/v1/ask/stream SSE integration."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def _parse_sse(raw: str) -> list[dict]:
    events: list[dict] = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events


def test_ask_stream_emits_token_sources_done(chat_client: TestClient) -> None:
    response = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "When is the food pantry open?"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(response.text)
    assert any("token" in event for event in events)
    assert any("sources" in event for event in events)
    assert events[-1].get("done") is True
