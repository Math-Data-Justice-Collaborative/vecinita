"""UJ-001: bilingual ask + stream E2E (local tier, mocked Modal)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


def _parse_sse(raw: str) -> list[dict]:
    events: list[dict] = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events


def test_uj001_ask_and_stream(chat_client: TestClient) -> None:
    ask = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert ask.status_code == 200
    assert ask.json()["language"] == "en"

    stream = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "What are the food pantry hours?"},
    )
    assert stream.status_code == 200
    events = _parse_sse(stream.text)
    assert events[-1].get("done") is True
