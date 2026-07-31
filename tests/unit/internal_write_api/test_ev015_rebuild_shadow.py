"""T88.4 — rebuild_runs + shadow dual-write (TP-S017-02 / TC-164).

Requires local Postgres (same as other internal_write_api unit tests).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

_EMBEDDING = [0.02] * EMBEDDING_DIMENSION


def test_create_rebuild_run_and_shadow_batch_leaves_live_chunks(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """dry_run path: rebuild_runs + shadow rows; live chunk count unchanged (TC-164)."""
    with engine.connect() as conn:
        url = row_str(
            mapping_row(
                conn.execute(
                    text("SELECT url FROM documents WHERE id = :id"),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "url",
        )
        live_before = row_int(
            mapping_row(
                conn.execute(
                    text("SELECT COUNT(*) AS c FROM chunks WHERE document_id = :id"),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "c",
        )

    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": "BAAI/bge-small-en-v1.5",
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 64,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    rebuild_run_id = UUID(json_str(as_json_object(cast("object", create.json())), "rebuild_run_id"))

    shadow = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
        json={
            "documents": [
                {
                    "url": url,
                    "rebuild_run_id": str(rebuild_run_id),
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "shadow-only chunk text",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert shadow.status_code == HTTPStatus.OK, shadow.text

    complete = write_client.patch(
        f"/internal/v1/rebuild/{rebuild_run_id}",
        json={"status": "completed"},
        headers=auth_headers(),
    )
    assert complete.status_code == HTTPStatus.OK, complete.text
    assert json_str(as_json_object(cast("object", complete.json())), "status") == "completed"

    try:
        with engine.connect() as conn:
            live_after = row_int(
                mapping_row(
                    conn.execute(
                        text("SELECT COUNT(*) AS c FROM chunks WHERE document_id = :id"),
                        {"id": seeded_document},
                    )
                    .mappings()
                    .one()
                ),
                "c",
            )
            assert live_after == live_before

            shadow_count = row_int(
                mapping_row(
                    conn.execute(
                        text(
                            """
                            SELECT COUNT(*) AS c FROM shadow_chunks
                            WHERE rebuild_run_id = :run_id AND document_id = :doc_id
                            """
                        ),
                        {"run_id": rebuild_run_id, "doc_id": seeded_document},
                    )
                    .mappings()
                    .one()
                ),
                "c",
            )
            assert shadow_count == 1

            run_status = row_str(
                mapping_row(
                    conn.execute(
                        text("SELECT status FROM rebuild_runs WHERE id = :id"),
                        {"id": rebuild_run_id},
                    )
                    .mappings()
                    .one()
                ),
                "status",
            )
            assert run_status == "completed"
    finally:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    DELETE FROM shadow_embeddings
                    WHERE shadow_chunk_id IN (
                        SELECT id FROM shadow_chunks WHERE rebuild_run_id = :id
                    )
                    """
                ),
                {"id": rebuild_run_id},
            )
            conn.execute(
                text("DELETE FROM shadow_chunks WHERE rebuild_run_id = :id"),
                {"id": rebuild_run_id},
            )
            conn.execute(text("DELETE FROM rebuild_runs WHERE id = :id"), {"id": rebuild_run_id})


def test_create_rebuild_run_rejects_unknown_mode(write_client: TestClient) -> None:
    """Unknown mode is rejected at the API validation boundary."""
    response = write_client.post(
        "/internal/v1/rebuild/runs",
        json={"mode": "reindex", "dry_run": True},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_shadow_batch_unknown_url_returns_404(write_client: TestClient) -> None:
    """Unknown document URL on shadow batch returns 404 (missing-doc branch)."""
    create = write_client.post(
        "/internal/v1/rebuild/runs",
        json={
            "mode": "rechunk",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": "BAAI/bge-small-en-v1.5",
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 64,
        },
        headers=auth_headers(),
    )
    assert create.status_code == HTTPStatus.OK, create.text
    rebuild_run_id = json_str(as_json_object(cast("object", create.json())), "rebuild_run_id")
    shadow = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
        json={
            "documents": [
                {
                    "url": "https://missing-doc-for-shadow.example.com",
                    "rebuild_run_id": rebuild_run_id,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "orphan shadow",
                            "embedding": _EMBEDDING,
                        }
                    ],
                }
            ]
        },
        headers=auth_headers(),
    )
    assert shadow.status_code == HTTPStatus.NOT_FOUND
    assert "Document not found" in shadow.text
