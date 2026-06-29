"""Unit tests for audit log and health aggregator edge cases."""

from __future__ import annotations

from http import HTTPStatus
from typing import Never
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.helpers.json_response import (
    json_int,
    json_list,
    json_object_get,
    json_str,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import (
    auth_headers,
    upsert_document_via_api,
)

_MAX_AUDIT_PAGE_SIZE = 200


def test_audit_log_supports_filters(write_client: TestClient) -> None:
    """Test audit log supports filters."""
    document_id = upsert_document_via_api(write_client, with_tags=True)
    response = write_client.get(
        "/internal/v1/audit",
        params={
            "event_type": "document.created",
            "entity_type": "document",
            "entity_id": document_id,
            "page": 1,
            "page_size": 10,
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "total_count") >= 1
    items = json_list(body, "items")
    assert len(items) >= 1


def test_audit_log_clamps_page_size(write_client: TestClient) -> None:
    """Test audit log clamps page size."""
    response = write_client.get(
        "/internal/v1/audit",
        params={"page": 0, "page_size": 500},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_int(body, "page") == 1
    assert json_int(body, "page_size") == _MAX_AUDIT_PAGE_SIZE


def test_health_all_marks_non_200_dependency_down(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health all marks non 200 dependency down."""
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")

    def _mock_get(url: str, **_kwargs: object) -> httpx.Response:
        """Mock get."""
        if url.endswith("chat-rag:8000/health"):
            return httpx.Response(503, text="unavailable")
        return httpx.Response(200, json={"status": "ok"})

    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get):
        response = write_client.get("/internal/v1/health/all", headers=auth_headers())

    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    services = json_object_get(body, "services")
    chat = json_object_get(services, "chat_rag_backend")
    assert json_str(chat, "status") == "down"


def test_health_all_marks_unconfigured_service_down(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health all marks unconfigured service down."""
    monkeypatch.delenv("VECINITA_MODAL_EMBED_URL", raising=False)
    response = write_client.get("/internal/v1/health/all", headers=auth_headers())
    body = response_json_object(response)
    services = json_object_get(body, "services")
    embed = json_object_get(services, "modal_embedding")
    assert json_str(embed, "status") == "down"
    assert "not configured" in json_str(embed, "error")


def test_health_all_uses_health_suffix_url(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health all uses health suffix url."""
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000/health")
    seen: list[str] = []

    def _mock_get(url: str, **_kwargs: object) -> httpx.Response:
        """Mock get."""
        seen.append(url)
        return httpx.Response(200, json={"status": "ok"})

    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_mock_get):
        write_client.get("/internal/v1/health/all", headers=auth_headers())

    assert "http://chat-rag:8000/health" in seen


@pytest.mark.usefixtures("write_client")
def test_health_all_database_down_marks_degraded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health all database down marks degraded."""

    class _BrokenEngine:
        """BrokenEngine."""

        def connect(self) -> Never:
            """Connect."""
            msg = "db unavailable"
            raise RuntimeError(msg)

    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")
    with patch("vecinita_internal_write_api.app._engine", return_value=_BrokenEngine()):
        from vecinita_internal_write_api.app import (  # noqa: PLC0415
            create_app,
        )

        client = TestClient(create_app())
        with patch("vecinita_internal_write_api.app.httpx.get") as mock_get:
            mock_get.return_value = httpx.Response(200, json={"status": "ok"})
            response = client.get("/internal/v1/health/all", headers=auth_headers())

    body = response_json_object(response)
    assert body["status"] == "degraded"
    services = json_object_get(body, "services")
    database = json_object_get(services, "database")
    assert json_str(database, "status") == "down"
