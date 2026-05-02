"""Integration: documents overview fails closed when canonical path is unavailable."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import router_documents

pytestmark = pytest.mark.integration


def test_documents_overview_returns_503_on_canonical_path_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_backend_unavailable():
        raise RuntimeError("database_url_not_configured")

    monkeypatch.setattr(router_documents, "_load_overview_via_sql", _raise_backend_unavailable)

    app = FastAPI()
    app.include_router(router_documents.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/documents/overview")
    assert response.status_code == 503
    assert "temporarily unavailable" in str(response.json().get("detail", "")).lower()
