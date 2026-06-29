"""TC-002: POST /api/v1/ask integration with mocked Modal clients."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from tests.helpers.json_response import json_int, json_object_list, json_str, response_json_object

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_ask_returns_answer_and_sources(chat_client: TestClient) -> None:
    """POST /api/v1/ask returns an answer and at least one scored source."""
    response = chat_client.post(
        "/api/v1/ask",
        json={"question": "When is the food pantry open?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["language"] == "en"
    answer = json_str(body, "answer")
    sources = json_object_list(body, "sources")
    assert "food pantry" in answer.lower() or "Monday" in answer
    assert len(sources) >= 1
    assert json_int(sources[0], "score") > 0
