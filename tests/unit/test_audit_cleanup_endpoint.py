"""POST /internal/v1/audit/cleanup reads VECINITA_AUDIT_RETENTION_DAYS."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app

pytestmark = pytest.mark.unit


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    return TestClient(create_app())


def test_audit_cleanup_uses_retention_env(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_AUDIT_RETENTION_DAYS", "90")
    with patch(
        "vecinita_internal_write_api.app.cleanup_audit_log",
        return_value=3,
    ) as mock_cleanup:
        resp = client.post(
            "/internal/v1/audit/cleanup",
            headers={"Authorization": "Bearer test-key"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"deleted": 3, "retention_days": 90}
    mock_cleanup.assert_called_once()
    assert mock_cleanup.call_args.kwargs["retention_days"] == 90


def test_audit_cleanup_skips_when_retention_zero(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VECINITA_AUDIT_RETENTION_DAYS", "0")
    with patch("vecinita_internal_write_api.app.cleanup_audit_log") as mock_cleanup:
        resp = client.post(
            "/internal/v1/audit/cleanup",
            headers={"Authorization": "Bearer test-key"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"deleted": 0, "retention_days": 0}
    mock_cleanup.assert_not_called()
