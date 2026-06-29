"""BUG-2026-05-27: health aggregator must not double /health on embed URL."""

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.helpers.json_response import json_object_get, json_str, response_json_object

pytestmark = pytest.mark.unit

_API_KEY = "test-internal-key"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")
    monkeypatch.setenv("VECINITA_ADMIN_FRONTEND_URL", "http://admin:3001")
    monkeypatch.setenv("VECINITA_CHAT_FRONTEND_URL", "http://chat-fe:3000")
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "http://modal-data:8001")
    monkeypatch.setenv(
        "VECINITA_MODAL_EMBED_URL",
        "http://modal-embed:8002/health",
    )
    monkeypatch.setenv("VECINITA_MODAL_LLM_URL", "http://modal-llm:8003")
    from vecinita_internal_write_api.app import create_app

    return TestClient(create_app())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_health_all_modal_embedding_url_must_not_double_health_suffix(
    client: TestClient,
) -> None:
    """When VECINITA_MODAL_EMBED_URL ends with /health, probe that URL once (not /health/health)."""
    probed: list[str] = []

    def mock_get(url: str, **kwargs: object) -> httpx.Response:
        probed.append(url)
        return httpx.Response(200, json={"status": "ok"})

    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=mock_get):
        resp = client.get("/internal/v1/health/all", headers=_auth())

    assert resp.status_code == 200
    data = response_json_object(resp)
    services = json_object_get(data, "services")
    embedding = json_object_get(services, "modal_embedding")
    assert json_str(embedding, "status") == "up", embedding
    assert "http://modal-embed:8002/health" in probed
    assert "http://modal-embed:8002/health/health" not in probed
