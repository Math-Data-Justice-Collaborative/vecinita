"""TC-002: POST /api/v1/ask integration with mocked Modal clients."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_ask_returns_answer_and_sources(chat_client: TestClient) -> None:
    response = chat_client.post(
        "/api/v1/ask",
        json={"question": "When is the food pantry open?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en"
    assert "food pantry" in body["answer"].lower() or "Monday" in body["answer"]
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["score"] > 0
