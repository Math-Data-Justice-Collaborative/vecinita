"""POST /internal/v1/feedback/cleanup reads VECINITA_FEEDBACK_RETENTION_DAYS (F68 / TC-228)."""

from __future__ import annotations

import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app

from tests.helpers.json_response import response_json_object

pytestmark = pytest.mark.unit

_RETENTION_DAYS = 90
_EXPECTED_DELETED = 2


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Provide a TestClient for the internal write API with env configured."""
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    return TestClient(create_app())


def test_feedback_cleanup_uses_retention_env(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Feedback cleanup passes the configured retention window to the helper."""
    monkeypatch.setenv("VECINITA_FEEDBACK_RETENTION_DAYS", str(_RETENTION_DAYS))
    with patch(
        "vecinita_internal_write_api.routes.audit_feedback.cleanup_feedback",
        return_value=_EXPECTED_DELETED,
        create=True,
    ) as mock_cleanup:
        resp = client.post(
            "/internal/v1/feedback/cleanup",
            headers={"Authorization": "Bearer test-key"},
        )

    assert resp.status_code == HTTPStatus.OK
    assert response_json_object(resp) == {
        "deleted": _EXPECTED_DELETED,
        "retention_days": _RETENTION_DAYS,
    }
    mock_cleanup.assert_called_once()
    assert mock_cleanup.call_args.kwargs["retention_days"] == _RETENTION_DAYS


def test_feedback_cleanup_skips_when_retention_zero(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Feedback cleanup skips the helper when retention is zero."""
    monkeypatch.setenv("VECINITA_FEEDBACK_RETENTION_DAYS", "0")
    with patch(
        "vecinita_internal_write_api.routes.audit_feedback.cleanup_feedback",
        create=True,
    ) as mock_cleanup:
        resp = client.post(
            "/internal/v1/feedback/cleanup",
            headers={"Authorization": "Bearer test-key"},
        )

    assert resp.status_code == HTTPStatus.OK
    assert response_json_object(resp) == {"deleted": 0, "retention_days": 0}
    mock_cleanup.assert_not_called()
