"""T87.1 — Ingest batch upsert writes body_text + revision stamp (TC-163 / RD-196)."""

from __future__ import annotations

import hashlib
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str, row_str_optional

from tests.helpers.json_response import (
    find_json_object_by_str,
    json_str,
    response_document_list_items,
)
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_CHUNK_SIZE_TOKENS = 256
_EMBEDDING_MODEL_ID = "fastembed-default"
_BODY = "Normalized scrape body for document store"


def _content_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_batch_upsert_persists_body_text_and_revision_stamp(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """POST /documents/batch stores body_text and stamps a document_revisions row (TC-163)."""
    body_text = _BODY
    content_hash = _content_hash(body_text)
    doc_url = f"https://ev015-store-{uuid.uuid4().hex[:10]}.example.com/"
    response = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "Store write doc",
                    "language": "en",
                    "content_hash": content_hash,
                    "body_text": body_text,
                    "embedding_model_id": _EMBEDDING_MODEL_ID,
                    "embedding_dim": EMBEDDING_DIMENSION,
                    "chunk_size_tokens": _CHUNK_SIZE_TOKENS,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "chunk from body",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK

    listing = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100},
        headers=auth_headers(),
    )
    rows = response_document_list_items(listing)
    doc = find_json_object_by_str(rows, "url", doc_url)
    document_id = UUID(json_str(doc, "document_id"))

    try:
        with engine.connect() as conn:
            doc_row = (
                conn.execute(
                    text(
                        """
                        SELECT body_text, content_hash
                        FROM documents
                        WHERE id = :id
                        """
                    ),
                    {"id": document_id},
                )
                .mappings()
                .one()
            )
            stored = mapping_row(doc_row)
            assert row_str_optional(stored, "body_text") == body_text
            assert row_str_optional(stored, "content_hash") == content_hash

            rev_row = (
                conn.execute(
                    text(
                        """
                        SELECT body_text, content_hash, embedding_model_id,
                               embedding_dim, chunk_size_tokens
                        FROM document_revisions
                        WHERE document_id = :id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"id": document_id},
                )
                .mappings()
                .one()
            )
            revision = mapping_row(rev_row)
            assert row_str(revision, "body_text") == body_text
            assert row_str_optional(revision, "content_hash") == content_hash
            assert row_str_optional(revision, "embedding_model_id") == _EMBEDDING_MODEL_ID
            assert row_int(revision, "embedding_dim") == EMBEDDING_DIMENSION
            assert row_int(revision, "chunk_size_tokens") == _CHUNK_SIZE_TOKENS
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": document_id})
            conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": document_id},
            )
            conn.execute(
                text("DELETE FROM document_revisions WHERE document_id = :id"),
                {"id": document_id},
            )
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": document_id})
