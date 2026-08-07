"""Transactional shadow → live promote for rebuild runs (TP-S017-03 / TC-165)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text
from vecinita_embedding_client.modal_pins import LEGACY_E0_EMBEDDING_MODEL_ID
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str
from vecinita_shared_schemas.internal_write import RebuildPromoteResponse

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Connection, Engine


class RebuildPromoteNotFoundError(Exception):
    """Raised when rebuild_run_id does not exist."""


class RebuildPromoteConflictError(Exception):
    """Raised when rebuild run is not in a promotable state."""


def promote_rebuild_run(engine: Engine, *, rebuild_run_id: UUID) -> RebuildPromoteResponse:
    """Copy shadow_chunks/embeddings into live tables in one transaction."""
    with engine.begin() as conn:
        return _promote_on_connection(conn, rebuild_run_id=rebuild_run_id)


def _shadow_counts(conn: Connection, *, rebuild_run_id: UUID) -> tuple[int, int]:
    chunks_promoted = row_int(
        mapping_row(
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS c FROM shadow_chunks
                    WHERE rebuild_run_id = :id
                    """
                ),
                {"id": rebuild_run_id},
            )
            .mappings()
            .one()
        ),
        "c",
    )
    documents_promoted = row_int(
        mapping_row(
            conn.execute(
                text(
                    """
                    SELECT COUNT(DISTINCT document_id) AS c FROM shadow_chunks
                    WHERE rebuild_run_id = :id
                    """
                ),
                {"id": rebuild_run_id},
            )
            .mappings()
            .one()
        ),
        "c",
    )
    return chunks_promoted, documents_promoted


def _promote_on_connection(
    conn: Connection,
    *,
    rebuild_run_id: UUID,
) -> RebuildPromoteResponse:
    run_row = (
        conn.execute(
            text(
                """
                SELECT id, status
                FROM rebuild_runs
                WHERE id = :id
                FOR UPDATE
                """
            ),
            {"id": rebuild_run_id},
        )
        .mappings()
        .first()
    )
    if run_row is None:
        msg = "rebuild run not found"
        raise RebuildPromoteNotFoundError(msg)

    run_status = row_str(mapping_row(run_row), "status")
    chunks_promoted, documents_promoted = _shadow_counts(conn, rebuild_run_id=rebuild_run_id)

    if run_status == "promoted":
        return RebuildPromoteResponse(
            promoted=True,
            rebuild_run_id=rebuild_run_id,
            chunks_promoted=chunks_promoted,
            documents_promoted=documents_promoted,
        )
    if run_status != "completed":
        msg = f"rebuild run status must be completed to promote (got {run_status})"
        raise RebuildPromoteConflictError(msg)
    if documents_promoted == 0:
        msg = "no shadow chunks to promote for rebuild run"
        raise RebuildPromoteConflictError(msg)

    conn.execute(
        text(
            """
            DELETE FROM chunks
            WHERE document_id IN (
                SELECT DISTINCT document_id FROM shadow_chunks
                WHERE rebuild_run_id = :id
            )
            """
        ),
        {"id": rebuild_run_id},
    )

    conn.execute(
        text(
            """
            INSERT INTO chunks (document_id, chunk_index, text, token_count)
            SELECT document_id, chunk_index, text, token_count
            FROM shadow_chunks
            WHERE rebuild_run_id = :id
            ORDER BY document_id, chunk_index
            """
        ),
        {"id": rebuild_run_id},
    )

    conn.execute(
        text(
            """
            INSERT INTO embeddings (chunk_id, embedding)
            SELECT c.id, se.embedding
            FROM shadow_chunks sc
            JOIN shadow_embeddings se ON se.shadow_chunk_id = sc.id
            JOIN chunks c
              ON c.document_id = sc.document_id
             AND c.chunk_index = sc.chunk_index
            WHERE sc.rebuild_run_id = :id
            """
        ),
        {"id": rebuild_run_id},
    )

    # First cutover from unstamped live: archive LEGACY_E0 so TC-239 / AC-ME9
    # retains a restorable prior pin before writing the candidate revision.
    conn.execute(
        text(
            """
            INSERT INTO document_revisions (
                document_id,
                content_hash,
                body_text,
                embedding_model_id,
                embedding_dim,
                chunk_size_tokens,
                chunk_tokenizer_id,
                rebuild_mode,
                rebuild_run_id
            )
            SELECT
                d.id,
                d.content_hash,
                d.body_text,
                :e0_pin,
                rr.embedding_dim,
                rr.chunk_size_tokens,
                :e0_pin,
                rr.mode,
                NULL
            FROM documents d
            JOIN (
                SELECT DISTINCT document_id
                FROM shadow_chunks
                WHERE rebuild_run_id = :id
            ) scoped ON scoped.document_id = d.id
            JOIN rebuild_runs rr ON rr.id = :id
            WHERE NOT EXISTS (
                SELECT 1
                FROM document_revisions dr
                WHERE dr.document_id = d.id
            )
            """
        ),
        {"id": rebuild_run_id, "e0_pin": LEGACY_E0_EMBEDDING_MODEL_ID},
    )

    conn.execute(
        text(
            """
            INSERT INTO document_revisions (
                document_id,
                content_hash,
                body_text,
                embedding_model_id,
                embedding_dim,
                chunk_size_tokens,
                chunk_tokenizer_id,
                rebuild_mode,
                rebuild_run_id
            )
            SELECT
                d.id,
                d.content_hash,
                d.body_text,
                rr.embedding_model_id,
                rr.embedding_dim,
                rr.chunk_size_tokens,
                rr.chunk_tokenizer_id,
                rr.mode,
                rr.id
            FROM documents d
            JOIN (
                SELECT DISTINCT document_id
                FROM shadow_chunks
                WHERE rebuild_run_id = :id
            ) scoped ON scoped.document_id = d.id
            JOIN rebuild_runs rr ON rr.id = :id
            """
        ),
        {"id": rebuild_run_id},
    )

    conn.execute(
        text(
            """
            UPDATE rebuild_runs
            SET status = 'promoted', updated_at = now()
            WHERE id = :id
            """
        ),
        {"id": rebuild_run_id},
    )

    return RebuildPromoteResponse(
        promoted=True,
        rebuild_run_id=rebuild_run_id,
        chunks_promoted=chunks_promoted,
        documents_promoted=documents_promoted,
    )
