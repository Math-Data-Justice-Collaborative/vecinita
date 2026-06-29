"""BUG-2026-05-22: Admin DELETE document — browser CORS preflight must allow DELETE.

Production OPTIONS with Access-Control-Request-Method: DELETE returned 400 and
access-control-allow-methods: GET, POST, OPTIONS only — browser shows Failed to fetch.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.app import create_app as create_write_app

from tests.helpers.json_response import header_str

ADMIN_ORIGIN = "https://vecinita-admin-frontend.example.com"


@pytest.fixture(autouse=True)
def _cors_and_db_env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setenv(
        "VECINITA_CORS_ORIGINS",
        f"https://vecinita-chat-rag-frontend.example.com,{ADMIN_ORIGIN}",
    )
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", "test-key")
    if not os.environ.get("DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")


def test_internal_write_cors_preflight_allows_delete_document() -> None:
    """Browser DELETE /internal/v1/documents/{id} requires DELETE in Allow-Methods."""
    client = TestClient(create_write_app())
    document_id = uuid4()
    response = client.options(
        f"/internal/v1/documents/{document_id}",
        headers={
            "Origin": ADMIN_ORIGIN,
            "Access-Control-Request-Method": "DELETE",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == HTTPStatus.OK, response.text
    assert response.headers.get("access-control-allow-origin") == ADMIN_ORIGIN
    allow_methods = header_str(response.headers, "access-control-allow-methods").upper()
    assert "DELETE" in allow_methods, (
        f"CORS must allow DELETE for admin document delete; got {allow_methods!r}"
    )
