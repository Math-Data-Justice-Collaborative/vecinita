"""Unit tests for tag validation and replace helpers."""

from __future__ import annotations

import uuid
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from tests.unit.internal_write_api.conftest import database_url
from vecinita_internal_write_api.tags import (
    replace_chunk_tags,
    replace_document_tags,
    validate_chunk_tag_count,
    validate_document_tag_count,
)
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.internal_write import TagInput


@pytest.fixture()
def engine() -> Engine:
    return create_engine(database_url())


@pytest.fixture()
def tagged_document(engine: Engine):
    doc_url = f"https://tag-test-{uuid.uuid4().hex[:10]}.example.com"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO documents (url, title, language) "
                    "VALUES (:url, 'Tag test', 'en') RETURNING id"
                ),
                {"url": doc_url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
        chunk_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    "INSERT INTO chunks (document_id, chunk_index, text) "
                    "VALUES (:doc_id, 0, 'chunk') RETURNING id"
                ),
                {"doc_id": doc_id},
            )
        )
        chunk_id = UUID(str(chunk_id_raw))
    yield doc_id, chunk_id
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_validate_document_tag_count_rejects_over_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("vecinita_internal_write_api.tags._MAX_TAGS_PER_DOCUMENT", 2)
    tags = [TagInput(slug=f"tag-{index}", label=f"Tag {index}", source="llm") for index in range(3)]

    with pytest.raises(HTTPException) as exc:
        validate_document_tag_count(tags)
    assert exc.value.status_code == 400


def test_validate_chunk_tag_count_rejects_over_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("vecinita_internal_write_api.tags._MAX_TAGS_PER_CHUNK", 1)
    tags = [
        TagInput(slug="a", label="A", source="llm"),
        TagInput(slug="b", label="B", source="llm"),
    ]

    with pytest.raises(HTTPException) as exc:
        validate_chunk_tag_count(tags)
    assert exc.value.status_code == 400


def test_replace_document_tags_persists_tags(engine: Engine, tagged_document) -> None:
    doc_id, _chunk_id = tagged_document
    tags = [TagInput(slug="housing", label="Housing", source="llm")]

    with engine.begin() as conn:
        replace_document_tags(conn, document_id=doc_id, tags=tags, language="en")

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT t.slug, dt.source
                FROM document_tags dt
                JOIN tags t ON t.id = dt.tag_id
                WHERE dt.document_id = :doc_id
                """
            ),
            {"doc_id": doc_id},
        ).all()

    assert len(rows) == 1
    assert rows[0][0] == "housing"
    assert rows[0][1] == "llm"


def test_replace_chunk_tags_persists_tags(engine: Engine, tagged_document) -> None:
    _doc_id, chunk_id = tagged_document
    tags = [TagInput(slug="legal", label="Legal", source="human")]

    with engine.begin() as conn:
        replace_chunk_tags(conn, chunk_id=chunk_id, tags=tags, language="en")

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT t.slug, ct.source
                FROM chunk_tags ct
                JOIN tags t ON t.id = ct.tag_id
                WHERE ct.chunk_id = :chunk_id
                """
            ),
            {"chunk_id": chunk_id},
        ).all()

    assert len(rows) == 1
    assert rows[0][0] == "legal"
    assert rows[0][1] == "human"
