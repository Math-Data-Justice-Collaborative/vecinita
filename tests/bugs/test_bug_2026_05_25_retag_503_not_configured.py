"""BUG-2026-05-25: POST /retag returns 503 — DataManagementJobsClient not configured.

create_app() called via uvicorn --factory with no args, so jobs_client defaults to None.
The retag endpoint returns 503 "Retag job client not configured" for every request.

After fix: create_app() should auto-create DataManagementJobsClient from env vars
VECINITA_MODAL_DATA_MGMT_URL and VECINITA_MODAL_PROXY_KEY.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app as create_write_app

ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"https://vecinita-chat-rag-frontend.example.com,{ADMIN_ORIGIN}",
    )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "http://modal-data-mgmt.test")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "test-proxy-key")


def test_retag_not_503_when_modal_env_vars_configured() -> None:
    """POST /retag must not return 503 'not configured' when modal env vars are set.

    Before fix: create_app() ignores env vars for jobs_client → retag_jobs=None → 503.
    After fix: create_app() auto-creates DataManagementJobsClient from env vars.
    """
    app = create_write_app()
    client = TestClient(app, raise_server_exceptions=False)
    doc_id = uuid4()

    resp = client.post(
        f"/internal/v1/documents/{doc_id}/retag",
        headers={"Authorization": "Bearer test-key"},
    )

    assert resp.status_code != 503 or "not configured" not in resp.text.lower(), (
        f"Retag should not return 503 'not configured' when "
        f"VECINITA_MODAL_DATA_MGMT_URL and VECINITA_MODAL_PROXY_KEY are set; "
        f"got {resp.status_code}: {resp.text}"
    )
