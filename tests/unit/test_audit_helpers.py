"""Unit tests for audit event emission and version snapshot creation (ADR-016, F29)."""

from __future__ import annotations

import os
import uuid
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture()
def engine():
    return create_engine(_database_url())


@pytest.fixture()
def sample_document(engine):
    """Insert a document and return its id; clean up after test."""
    url = f"https://test.example.com/audit-{uuid.uuid4().hex[:8]}"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Audit Test Doc', 'en') RETURNING id"
                ),
                {"url": url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
    yield doc_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_emit_audit_event_inserts_row(engine, sample_document) -> None:
    """emit_audit_event() creates an audit_log row with correct fields."""
    from vecinita_internal_write_api.audit import emit_audit_event

    request_id = uuid.uuid4()
    with engine.begin() as conn:
        emit_audit_event(
            conn,
            event_type="document.created",
            entity_type="document",
            entity_id=sample_document,
            request_id=request_id,
            payload={"title": "Audit Test Doc", "url": "https://test.example.com"},
        )

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT event_type, entity_type, entity_id, request_id, payload "
                    "FROM audit_log WHERE entity_id = :entity_id AND request_id = :request_id"
                ),
                {"entity_id": sample_document, "request_id": request_id},
            )
            .mappings()
            .first()
        )

    assert row is not None
    assert row["event_type"] == "document.created"
    assert row["entity_type"] == "document"
    assert row["entity_id"] == sample_document
    assert row["request_id"] == request_id
    assert row["payload"]["title"] == "Audit Test Doc"


def test_emit_audit_event_empty_payload(engine, sample_document) -> None:
    """emit_audit_event() works with empty payload."""
    from vecinita_internal_write_api.audit import emit_audit_event

    request_id = uuid.uuid4()
    with engine.begin() as conn:
        emit_audit_event(
            conn,
            event_type="document.deleted",
            entity_type="document",
            entity_id=sample_document,
            request_id=request_id,
        )

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT payload FROM audit_log "
                    "WHERE entity_id = :entity_id AND request_id = :request_id"
                ),
                {"entity_id": sample_document, "request_id": request_id},
            )
            .mappings()
            .first()
        )

    assert row is not None
    assert row["payload"] == {}


def test_create_document_version_inserts_snapshot(engine, sample_document) -> None:
    """create_document_version() creates a version row with tags snapshot."""
    from vecinita_internal_write_api.audit import create_document_version

    with engine.begin() as conn:
        create_document_version(
            conn,
            document_id=sample_document,
            title="Audit Test Doc",
            language="en",
            tags_snapshot=[{"slug": "housing", "label": "Housing", "source": "llm"}],
        )

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT version_number, title, language, tags_snapshot "
                    "FROM document_versions WHERE document_id = :doc_id "
                    "ORDER BY version_number DESC LIMIT 1"
                ),
                {"doc_id": sample_document},
            )
            .mappings()
            .first()
        )

    assert row is not None
    assert row["version_number"] == 1
    assert row["title"] == "Audit Test Doc"
    assert row["language"] == "en"
    assert len(row["tags_snapshot"]) == 1
    assert row["tags_snapshot"][0]["slug"] == "housing"


def test_create_document_version_increments_version_number(engine, sample_document) -> None:
    """Successive calls increment version_number."""
    from vecinita_internal_write_api.audit import create_document_version

    with engine.begin() as conn:
        create_document_version(
            conn,
            document_id=sample_document,
            title="v1",
            language="en",
            tags_snapshot=[],
        )
    with engine.begin() as conn:
        create_document_version(
            conn,
            document_id=sample_document,
            title="v2",
            language="en",
            tags_snapshot=[{"slug": "legal", "label": "Legal", "source": "human"}],
        )

    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT version_number, title FROM document_versions "
                    "WHERE document_id = :doc_id ORDER BY version_number"
                ),
                {"doc_id": sample_document},
            )
            .mappings()
            .all()
        )

    assert len(rows) == 2
    assert rows[0]["version_number"] == 1
    assert rows[0]["title"] == "v1"
    assert rows[1]["version_number"] == 2
    assert rows[1]["title"] == "v2"
