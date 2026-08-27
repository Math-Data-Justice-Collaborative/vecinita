"""Rebuild run persistence and shadow batch writes (ADR-040 / TP-S017)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import mapping_row, row_str, row_uuid, scalar_uuid
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    CreateRebuildRunRequest,
    CreateRebuildRunResponse,
    UpdateRebuildRunRequest,
)

from vecinita_internal_write_api.deps import document_url_key

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def create_rebuild_run_record(
    *,
    engine: Engine,
    body: CreateRebuildRunRequest,
) -> CreateRebuildRunResponse:
    """Insert a rebuild_runs row for dry-run / live tracking (TP-S017-02)."""
    with engine.begin() as conn:
        run_id = scalar_uuid(
            cast(
                "object",
                conn.execute(
                    text(
                        """
                            INSERT INTO rebuild_runs (
                                mode, dry_run, force, status, job_id,
                                embedding_model_id, embedding_dim, chunk_size_tokens,
                                chunk_tokenizer_id
                            )
                            VALUES (
                                :mode, :dry_run, :force, :status, :job_id,
                                :embedding_model_id, :embedding_dim, :chunk_size_tokens,
                                :chunk_tokenizer_id
                            )
                            RETURNING id
                            """
                    ),
                    {
                        "mode": body.mode,
                        "dry_run": body.dry_run,
                        "force": body.force,
                        "status": body.status,
                        "job_id": body.job_id,
                        "embedding_model_id": body.embedding_model_id,
                        "embedding_dim": body.embedding_dim,
                        "chunk_size_tokens": body.chunk_size_tokens,
                        "chunk_tokenizer_id": body.chunk_tokenizer_id,
                    },
                ).scalar_one(),
            )
        )
    return CreateRebuildRunResponse(rebuild_run_id=run_id, status=body.status)


def update_rebuild_run_record(
    *,
    engine: Engine,
    rebuild_run_id: UUID,
    body: UpdateRebuildRunRequest,
) -> CreateRebuildRunResponse:
    """Update rebuild_runs.status lifecycle (pending/running/completed/failed)."""
    with engine.begin() as conn:
        updated = (
            conn.execute(
                text(
                    """
                        UPDATE rebuild_runs
                        SET status = :status, updated_at = now()
                        WHERE id = :id
                        RETURNING id, status
                        """
                ),
                {"id": rebuild_run_id, "status": body.status},
            )
            .mappings()
            .first()
        )
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        row = mapping_row(updated)
    return CreateRebuildRunResponse(
        rebuild_run_id=row_uuid(row, "id"),
        status=row_str(row, "status"),
    )


def upsert_shadow_batch(
    *,
    engine: Engine,
    rebuild_run_id: UUID,
    body: BatchUpsertRequest,
) -> BatchUpsertResponse:
    """Write shadow_chunks + shadow_embeddings; leave live retrieval unchanged (TC-164)."""
    with engine.begin() as conn:
        run_row = (
            conn.execute(
                text("SELECT id, dry_run FROM rebuild_runs WHERE id = :id"),
                {"id": rebuild_run_id},
            )
            .mappings()
            .first()
        )
        if run_row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        upserted = 0
        for document in body.documents:
            url_key = document_url_key(document.url)
            doc_row = (
                conn.execute(
                    text(
                        """
                            SELECT id FROM documents
                            WHERE rtrim(url, '/') = :url_key
                            """
                    ),
                    {"url_key": url_key},
                )
                .mappings()
                .first()
            )
            if doc_row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Document not found for url={document.url}",
                )
            doc_id = row_uuid(mapping_row(doc_row), "id")
            for chunk in document.chunks:
                shadow_chunk_id = scalar_uuid(
                    cast(
                        "object",
                        conn.execute(
                            text(
                                """
                                    INSERT INTO shadow_chunks (
                                        rebuild_run_id, document_id, chunk_index, text
                                    )
                                    VALUES (
                                        :rebuild_run_id, :document_id, :chunk_index, :text
                                    )
                                    ON CONFLICT (rebuild_run_id, document_id, chunk_index)
                                    DO UPDATE SET text = EXCLUDED.text
                                    RETURNING id
                                    """
                            ),
                            {
                                "rebuild_run_id": rebuild_run_id,
                                "document_id": doc_id,
                                "chunk_index": chunk.chunk_index,
                                "text": chunk.text,
                            },
                        ).scalar_one(),
                    )
                )
                vector_literal = "[" + ",".join(str(v) for v in chunk.embedding) + "]"
                _ = conn.execute(
                    text(
                        """
                            INSERT INTO shadow_embeddings (shadow_chunk_id, embedding)
                            VALUES (:shadow_chunk_id, CAST(:embedding AS vector))
                            ON CONFLICT (shadow_chunk_id)
                            DO UPDATE SET embedding = EXCLUDED.embedding
                            """
                    ),
                    {
                        "shadow_chunk_id": shadow_chunk_id,
                        "embedding": vector_literal,
                    },
                )
                upserted += 1
    return BatchUpsertResponse(upserted_chunks=upserted, documents=[])
