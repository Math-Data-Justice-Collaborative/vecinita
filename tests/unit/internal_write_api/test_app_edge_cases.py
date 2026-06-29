"""Unit tests for remaining branch and edge-case coverage gaps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import (
    TYPE_CHECKING,
    Never,
)
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    text,
)
from vecinita_internal_write_api.app import (
    _database_url,  # pyright: ignore[reportPrivateUsage]
    _row_datetime_optional,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_internal_write_api.audit import (
    cleanup_audit_log,
    emit_audit_event,
)
from vecinita_shared_schemas.db_mapping import (
    scalar_int,
    sqlalchemy_scalar_one,
)

from tests.helpers.json_response import (
    json_int,
    json_list,
    json_object_get,
    json_str,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import (
    auth_headers,
    database_url,
    upsert_document_via_api,
)

_HTTP_ACCEPTED = HTTPStatus.ACCEPTED

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def test_row_datetime_optional_raises_on_wrong_type() -> None:
    """Test row datetime optional raises on wrong type."""
    with pytest.raises(TypeError, match="Expected datetime"):
        _row_datetime_optional({"last_served_at": "bad"}, "last_served_at")


def test_database_url_raises_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test database url raises when env missing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _database_url()


def test_get_document_tags_404(write_client: TestClient) -> None:
    """Test get document tags 404."""
    response = write_client.get(
        f"/internal/v1/documents/{uuid4()}/tags",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_document_chunks_404(write_client: TestClient) -> None:
    """Test list document chunks 404."""
    response = write_client.get(
        f"/internal/v1/documents/{uuid4()}/chunks",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.usefixtures("internal_api_env")
def test_retag_document_503_when_jobs_client_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test retag document 503 when jobs client missing."""
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    client = TestClient(create_app())
    response = client.post(
        f"/internal/v1/documents/{uuid4()}/retag",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_bulk_tag_reports_missing_document(write_client: TestClient) -> None:
    """Test bulk tag reports missing document."""
    missing = uuid4()
    response = write_client.patch(
        "/internal/v1/documents/bulk/tags",
        json={"document_ids": [str(missing)], "remove_tags": [], "add_tags": []},
        headers=auth_headers(),
    )
    body = response_json_object(response)
    assert json_int(body, "successes") == 0
    assert len(json_list(body, "failures")) == 1


def test_bulk_metadata_reports_missing_document(write_client: TestClient) -> None:
    """Test bulk metadata reports missing document."""
    response = write_client.patch(
        "/internal/v1/documents/bulk/metadata",
        json={
            "document_ids": [str(uuid4())],
            "updates": {"title": "Missing"},
        },
        headers=auth_headers(),
    )
    body = response_json_object(response)
    assert json_int(body, "successes") == 0


def test_bulk_metadata_updates_title_only(write_client: TestClient) -> None:
    """Test bulk metadata updates title only."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        "/internal/v1/documents/bulk/metadata",
        json={"document_ids": [document_id], "updates": {"title": "Title only"}},
        headers=auth_headers(),
    )
    assert json_int(response_json_object(response), "successes") == 1


def test_bulk_metadata_updates_language_only(write_client: TestClient) -> None:
    """Test bulk metadata updates language only."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.patch(
        "/internal/v1/documents/bulk/metadata",
        json={"document_ids": [document_id], "updates": {"language": "es"}},
        headers=auth_headers(),
    )
    assert json_int(response_json_object(response), "successes") == 1


def test_bulk_retag_skips_missing_documents(
    write_client_with_jobs: tuple[TestClient, object],
) -> None:
    """Test bulk retag skips missing documents."""
    client, _jobs = write_client_with_jobs
    response = client.post(
        "/internal/v1/documents/bulk/retag",
        json={"document_ids": [str(uuid4())]},
        headers=auth_headers(),
    )
    assert response.status_code == _HTTP_ACCEPTED
    assert response_json_object(response)["job_ids"] == []


def test_audit_log_filters_since_and_until(write_client: TestClient) -> None:
    """Test audit log filters since and until."""
    since = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    until = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    response = write_client.get(
        "/internal/v1/audit",
        params={"since": since, "until": until},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("write_client")
def test_stats_served_swallows_per_document_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test stats served swallows per document errors."""

    class _BrokenEngine:
        """BrokenEngine."""

        def begin(self) -> Never:
            """Begin."""
            msg = "write failed"
            raise RuntimeError(msg)

    monkeypatch.setattr("vecinita_internal_write_api.app._engine", _BrokenEngine)
    from vecinita_internal_write_api.app import (  # noqa: PLC0415
        create_app,
    )

    client = TestClient(create_app())
    response = client.post(
        "/internal/v1/stats/served",
        json={"document_ids": [str(uuid4())]},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.ACCEPTED


def test_health_all_swallows_dependency_exceptions(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test health all swallows dependency exceptions."""
    monkeypatch.setenv("VECINITA_CHAT_RAG_URL", "http://chat-rag:8000")

    def _boom(_url: str, **_kwargs: object) -> None:
        """Boom."""
        msg = "network down"
        raise OSError(msg)

    with patch("vecinita_internal_write_api.app.httpx.get", side_effect=_boom):
        response = write_client.get("/internal/v1/health/all", headers=auth_headers())

    body = response_json_object(response)
    services = json_object_get(body, "services")
    chat = json_object_get(services, "chat_rag_backend")
    assert json_str(chat, "status") == "down"


@pytest.fixture
def engine() -> Engine:
    """Engine."""
    return create_engine(database_url())


def test_cleanup_audit_log_deletes_old_rows(engine: Engine) -> None:
    """Test cleanup audit log deletes old rows."""
    old_ts = datetime.now(UTC) - timedelta(days=400)
    request_id = uuid4()
    entity_id = uuid4()
    with engine.begin() as conn:
        emit_audit_event(
            conn,
            event_type="document.created",
            entity_type="document",
            entity_id=entity_id,
            request_id=request_id,
            payload={"test": "cleanup-unit"},
        )
        conn.execute(
            text("UPDATE audit_log SET created_at = :ts WHERE entity_id = :entity_id"),
            {"ts": old_ts, "entity_id": entity_id},
        )

    deleted = cleanup_audit_log(engine, retention_days=365)
    assert deleted >= 1

    with engine.connect() as conn:
        remaining = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(
                    text("SELECT COUNT(*) FROM audit_log WHERE entity_id = :entity_id"),
                    {"entity_id": entity_id},
                )
            )
        )
    assert remaining == 0
