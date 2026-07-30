"""T89.1 — promote copies shadow→live in one txn; counts (TC-165 / TP-S017-03).

Postgres-backed API assertions require local DATABASE_URL (same as T88.4).
The service import check runs without Docker and fails until T89.3 lands.
"""

from __future__ import annotations

import importlib
from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import text
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_int, json_str
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

_EMBEDDING = [0.03] * EMBEDDING_DIMENSION
_SHADOW_TEXT = "promoted-shadow-chunk-text"
_PROMOTE_MODULE = "vecinita_internal_write_api.rebuild_promote"


def test_promote_rebuild_run_service_is_importable() -> None:
    """Transactional promote lives in rebuild_promote.promote_rebuild_run (TP-S017-03)."""
    module = importlib.import_module(_PROMOTE_MODULE)
    promote_rebuild_run = getattr(module, "promote_rebuild_run", None)
    assert callable(promote_rebuild_run)


def test_promote_copies_shadow_to_live_and_returns_counts(
    write_client: TestClient,
    engine: Engine,
    seeded_document: UUID,
) -> None:
    """POST …/promote copies shadow→live; response includes counts (TC-165 / TP-S017-06)."""
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
        live_text_before = row_str(
            mapping_row(
                conn.execute(
                    text(
                        """
                        SELECT text FROM chunks
                        WHERE document_id = :id
                        ORDER BY chunk_index
                        LIMIT 1
                        """
                    ),
                    {"id": seeded_document},
                )
                .mappings()
                .one()
            ),
            "text",
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
                            "text": _SHADOW_TEXT,
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

    promote = write_client.post(
        f"/internal/v1/rebuild/{rebuild_run_id}/promote",
        headers=auth_headers(),
    )
    assert promote.status_code == HTTPStatus.OK, promote.text
    body = as_json_object(cast("object", promote.json()))
    assert body.get("promoted") is True
    assert json_str(body, "rebuild_run_id") == str(rebuild_run_id)
    assert json_int(body, "chunks_promoted") == 1
    assert json_int(body, "documents_promoted") == 1

    try:
        with engine.connect() as conn:
            live_text_after = row_str(
                mapping_row(
                    conn.execute(
                        text(
                            """
                            SELECT text FROM chunks
                            WHERE document_id = :id
                            ORDER BY chunk_index
                            LIMIT 1
                            """
                        ),
                        {"id": seeded_document},
                    )
                    .mappings()
                    .one()
                ),
                "text",
            )
            assert live_text_after == _SHADOW_TEXT
            assert live_text_after != live_text_before

            live_count = row_int(
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
            assert live_count == 1

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
            assert run_status == "promoted"

            revision_count = row_int(
                mapping_row(
                    conn.execute(
                        text(
                            """
                            SELECT COUNT(*) AS c FROM document_revisions
                            WHERE document_id = :doc_id AND rebuild_run_id = :run_id
                            """
                        ),
                        {"doc_id": seeded_document, "run_id": rebuild_run_id},
                    )
                    .mappings()
                    .one()
                ),
                "c",
            )
            assert revision_count >= 1
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
            conn.execute(
                text("DELETE FROM document_revisions WHERE rebuild_run_id = :id"),
                {"id": rebuild_run_id},
            )
            conn.execute(text("DELETE FROM rebuild_runs WHERE id = :id"), {"id": rebuild_run_id})
