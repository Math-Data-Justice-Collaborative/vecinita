"""Operator notify after feedback insert (F68 / #214 / TC-309-311 / ADR-046)."""

from __future__ import annotations

from contextlib import nullcontext
from http import HTTPStatus
from typing import cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app
from vecinita_internal_write_api.feedback_notify import (
    FeedbackNotifyPayload,
    notify_feedback_operators,
)
from vecinita_shared_schemas.chat_rag import FeedbackCreateResponse

from tests.helpers.json_response import json_str, response_json_object

pytestmark = pytest.mark.unit

_API_KEY = "test-key"
_MESSAGE = "Search felt truncated on mobile."
_CREATED = "2026-08-04T12:00:00+00:00"


class _FakeEngine:
    def begin(self) -> object:
        return nullcontext(MagicMock())

    def connect(self) -> object:
        return nullcontext(MagicMock())

    def dispose(self) -> None:
        return


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def _payload(**overrides: object) -> FeedbackNotifyPayload:
    base: dict[str, object] = {
        "id": str(uuid4()),
        "category": "suggestion",
        "locale": "en",
        "created_at": _CREATED,
        "message": _MESSAGE,
    }
    base.update(overrides)
    return FeedbackNotifyPayload(
        id=str(base["id"]),
        category=str(base["category"]),
        locale=str(base["locale"]) if base["locale"] is not None else None,
        created_at=str(base["created_at"]),
        message=str(base["message"]),
    )


def test_notify_webhook_posts_payload_when_url_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-309: non-empty VECINITA_FEEDBACK_NOTIFY_WEBHOOK triggers POST JSON."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(HTTPStatus.OK, json={"ok": True})

    monkeypatch.setenv("VECINITA_FEEDBACK_NOTIFY_WEBHOOK", "https://hooks.example/feedback")
    monkeypatch.delenv("VECINITA_FEEDBACK_NOTIFY_EMAIL", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    payload = _payload()
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        notify_feedback_operators(payload, http_client=client)
    assert len(seen) == 1
    assert str(seen[0].url) == "https://hooks.example/feedback"
    body = seen[0].read()
    assert payload.id.encode() in body
    assert payload.message.encode() in body
    assert b'"email"' not in body


def test_notify_email_posts_resend_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-310: Resend email when To + RESEND_* are set."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(HTTPStatus.OK, json={"id": "msg_1"})

    monkeypatch.delenv("VECINITA_FEEDBACK_NOTIFY_WEBHOOK", raising=False)
    monkeypatch.setenv("VECINITA_FEEDBACK_NOTIFY_EMAIL", "ops@example.org")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_SENDER_EMAIL", "noreply@example.org")
    payload = _payload()
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        notify_feedback_operators(payload, http_client=client)
    assert len(seen) == 1
    assert seen[0].url.host == "api.resend.com"
    raw = seen[0].read().decode()
    assert "ops@example.org" in raw
    assert _MESSAGE in raw
    assert payload.category in raw


def test_notify_failure_is_fail_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-311: transport failures do not raise (store path stays successful)."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(HTTPStatus.INTERNAL_SERVER_ERROR, text="boom")

    monkeypatch.setenv("VECINITA_FEEDBACK_NOTIFY_WEBHOOK", "https://hooks.example/fail")
    monkeypatch.setenv("VECINITA_FEEDBACK_NOTIFY_EMAIL", "ops@example.org")
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("RESEND_SENDER_EMAIL", "noreply@example.org")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        notify_feedback_operators(_payload(), http_client=client)


def test_notify_noop_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing notify config does not call HTTP."""
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(HTTPStatus.OK)

    monkeypatch.delenv("VECINITA_FEEDBACK_NOTIFY_WEBHOOK", raising=False)
    monkeypatch.delenv("VECINITA_FEEDBACK_NOTIFY_EMAIL", raising=False)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        notify_feedback_operators(_payload(), http_client=client)
    assert calls == 0


def test_create_feedback_route_invokes_notify_after_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Route calls notify after successful insert (fail-open isolation)."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    feedback_id = uuid4()
    notify_mock = MagicMock()
    with (
        patch(
            "vecinita_internal_write_api.deps.create_engine",
            return_value=_FakeEngine(),
        ),
        patch(
            "vecinita_internal_write_api.routes.audit_feedback.insert_feedback",
            return_value=FeedbackCreateResponse(id=feedback_id, created_at=_CREATED),
        ),
        patch(
            "vecinita_internal_write_api.routes.audit_feedback.notify_feedback_operators",
            notify_mock,
        ),
    ):
        client = TestClient(create_app())
        resp = client.post(
            "/internal/v1/feedback",
            json={"category": "suggestion", "message": _MESSAGE, "locale": "en"},
            headers=_auth(),
        )
    assert resp.status_code == HTTPStatus.CREATED
    body = response_json_object(resp)
    assert json_str(body, "id") == str(feedback_id)
    notify_mock.assert_called_once()
    called = cast("FeedbackNotifyPayload", notify_mock.call_args.args[0])
    assert called.message == _MESSAGE
    assert called.category == "suggestion"
    assert str(called.id) == str(feedback_id)
