"""BUG-2026-07-25: Manage Tags LLM retag returns opaque Internal Server Error.

Root cause: DataManagementJobsClient.enqueue_retag sends only X-Vecinita-Proxy-Key.
Modal POST /jobs requires proxy key + admin JWT (F34 write_auth_dep). Modal returns
401; write API leaves DataManagementJobsClientError uncaught → FastAPI 500.

Expected after fix:
- Authorization from the write request is forwarded to Modal
- Enqueue failures map to 502 with a clear detail (not opaque 500)
"""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_internal_write_api.jobs_client import DataManagementJobsClientError
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

_API_KEY = "test-internal-key-retag-500"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    reset_auth_config_for_tests()
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "true")


@pytest.fixture
def engine() -> Engine:
    """SQLAlchemy engine for seeding a document."""
    return create_engine(_database_url())


@pytest.fixture
def seeded_document_id(engine: Engine) -> Iterator[UUID]:
    """Insert one document and yield its id."""
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, :title, 'en') RETURNING id"
                ),
                {
                    "url": f"https://retag-500-{uuid4().hex[:8]}.example.com",
                    "title": "Retag 500 repro",
                },
            )
        )
        doc_id = UUID(str(doc_id_raw))
    yield doc_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


class _RaisingJobsClient:
    """Simulate Modal 401 on enqueue."""

    def enqueue_retag(
        self,
        document_id: UUID,
        *,
        authorization: str | None = None,
    ) -> UUID:
        """Raise the same error class jobs_client raises on Modal 401."""
        _ = (document_id, authorization)
        msg = 'enqueue_retag failed: 401 {"detail":"Unauthorized"}'
        raise DataManagementJobsClientError(msg)


class _CapturingJobsClient:
    """Record authorization forwarded into enqueue_retag."""

    def __init__(self) -> None:
        """Initialize capture lists."""
        self.authorizations: list[str | None] = []
        self.enqueued: list[UUID] = []

    def enqueue_retag(
        self,
        document_id: UUID,
        *,
        authorization: str | None = None,
    ) -> UUID:
        """Record args and return a synthetic job id."""
        self.enqueued.append(document_id)
        self.authorizations.append(authorization)
        return uuid4()


def test_retag_modal_401_must_not_be_opaque_500(seeded_document_id: UUID) -> None:
    """Modal enqueue 401 must surface as 502 (or other clear error), never opaque 500."""
    app = create_write_app(jobs_client=_RaisingJobsClient())  # type: ignore[arg-type]
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post(
        f"/internal/v1/documents/{seeded_document_id}/retag",
        headers=_auth(),
    )

    assert resp.status_code != HTTPStatus.INTERNAL_SERVER_ERROR, (
        "Retag must not return opaque 500 when Modal enqueue fails; "
        f"got {resp.status_code}: {resp.text}"
    )
    assert resp.status_code == HTTPStatus.BAD_GATEWAY
    assert "401" in resp.text or "enqueue" in resp.text.lower()


def test_retag_forwards_authorization_to_jobs_client(seeded_document_id: UUID) -> None:
    """Operator Authorization bearer must be forwarded to Modal enqueue (F34)."""
    jobs = _CapturingJobsClient()
    app = create_write_app(jobs_client=jobs)  # type: ignore[arg-type]
    client = TestClient(app)

    resp = client.post(
        f"/internal/v1/documents/{seeded_document_id}/retag",
        headers=_auth(),
    )

    assert resp.status_code == HTTPStatus.OK, resp.text
    assert jobs.authorizations == [_auth()["Authorization"]]
    assert jobs.enqueued == [seeded_document_id]
