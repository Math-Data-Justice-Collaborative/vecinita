"""Unit coverage for internal-write feedback HTTP routes (F68)."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_shared_schemas.chat_rag import FeedbackCreateResponse
from vecinita_shared_schemas.internal_write import FeedbackItem, FeedbackListResponse

from tests.helpers.json_response import json_str, response_json_object

pytestmark = pytest.mark.unit

_API_KEY = "test-key"
_MESSAGE = "Search felt truncated on mobile."


class _FakeEngine:
    def begin(self) -> object:
        return nullcontext(MagicMock())

    def connect(self) -> object:
        return nullcontext(MagicMock())

    def dispose(self) -> None:
        return


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Internal-write client with API-key auth and mocked DB engine."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    with patch(
        "vecinita_internal_write_api.app.create_engine",
        return_value=_FakeEngine(),
    ):
        return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_create_feedback_success(client: TestClient) -> None:
    """POST /internal/v1/feedback returns 201 when insert succeeds."""
    feedback_id = uuid4()
    created_at = "2026-08-04T12:00:00+00:00"
    with patch(
        "vecinita_internal_write_api.app.insert_feedback",
        return_value=FeedbackCreateResponse(id=feedback_id, created_at=created_at),
    ):
        resp = client.post(
            "/internal/v1/feedback",
            json={"category": "suggestion", "message": _MESSAGE, "locale": "en"},
            headers=_auth(),
        )
    assert resp.status_code == HTTPStatus.CREATED
    body = response_json_object(resp)
    assert json_str(body, "id") == str(feedback_id)


def test_create_feedback_rejects_invalid_json(client: TestClient) -> None:
    """Invalid JSON returns 400."""
    resp = client.post(
        "/internal/v1/feedback",
        content=b"{bad",
        headers={**_auth(), "Content-Type": "application/json"},
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_create_feedback_rejects_non_object(client: TestClient) -> None:
    """Non-object JSON returns 400."""
    resp = client.post(
        "/internal/v1/feedback",
        json=["x"],
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_create_feedback_rejects_email(client: TestClient) -> None:
    """Email field is rejected."""
    resp = client.post(
        "/internal/v1/feedback",
        json={"category": "bug", "message": _MESSAGE, "email": "a@b.co"},
        headers=_auth(),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_list_feedback_success(client: TestClient) -> None:
    """GET /internal/v1/feedback returns list payload."""
    feedback_id = uuid4()
    with patch(
        "vecinita_internal_write_api.app.list_feedback",
        return_value=FeedbackListResponse(
            items=[
                FeedbackItem(
                    id=feedback_id,
                    created_at=datetime.now(UTC),
                    category="bug",
                    message=_MESSAGE,
                    locale="en",
                )
            ],
            page=1,
            page_size=20,
            total_count=1,
        ),
    ) as mock_list:
        resp = client.get(
            "/internal/v1/feedback",
            params={"page": 1, "page_size": 20, "category": "bug"},
            headers=_auth(),
        )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["total_count"] == 1
    mock_list.assert_called_once()
    assert mock_list.call_args.kwargs["category"] == "bug"
