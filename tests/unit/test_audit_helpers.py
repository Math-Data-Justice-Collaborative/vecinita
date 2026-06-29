"""Unit tests for audit event emission and version snapshot creation (ADR-016, F29)."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from sqlalchemy import Engine, create_engine, text
from vecinita_internal_write_api.audit import create_document_version, emit_audit_event
from vecinita_shared_schemas.db_mapping import mapping_row, sqlalchemy_scalar_one
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_object_items

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.integration

_FIRST_VERSION = 1
_SECOND_VERSION = 2
_EXPECTED_TAG_COUNT = 1
_EXPECTED_VERSION_COUNT = 2


def _database_url() -> str:
    """Return the configured database URL, falling back to the local default."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def engine() -> Engine:
    """Provide a SQLAlchemy engine bound to the test database."""
    return create_engine(_database_url())


@pytest.fixture
def sample_document(engine: Engine) -> Iterator[UUID]:
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


def test_emit_audit_event_inserts_row(engine: Engine, sample_document: UUID) -> None:
    """emit_audit_event() creates an audit_log row with correct fields."""
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
    mapping = mapping_row(row)
    assert mapping["event_type"] == "document.created"
    assert mapping["entity_type"] == "document"
    assert mapping["entity_id"] == sample_document
    assert mapping["request_id"] == request_id
    assert as_json_object(mapping["payload"])["title"] == "Audit Test Doc"


def test_emit_audit_event_empty_payload(engine: Engine, sample_document: UUID) -> None:
    """emit_audit_event() works with empty payload."""
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
    assert mapping_row(row)["payload"] == {}


def test_create_document_version_inserts_snapshot(engine: Engine, sample_document: UUID) -> None:
    """create_document_version() creates a version row with tags snapshot."""
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
    mapping = mapping_row(row)
    assert mapping["version_number"] == _FIRST_VERSION
    assert mapping["title"] == "Audit Test Doc"
    assert mapping["language"] == "en"
    tags_snapshot = json_object_items(mapping["tags_snapshot"])
    assert len(tags_snapshot) == _EXPECTED_TAG_COUNT
    assert tags_snapshot[0]["slug"] == "housing"


def test_create_document_version_increments_version_number(
    engine: Engine, sample_document: UUID
) -> None:
    """Successive calls increment version_number."""
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

    assert len(rows) == _EXPECTED_VERSION_COUNT
    first = mapping_row(rows[0])
    second = mapping_row(rows[1])
    assert first["version_number"] == _FIRST_VERSION
    assert first["title"] == "v1"
    assert second["version_number"] == _SECOND_VERSION
    assert second["title"] == "v2"
