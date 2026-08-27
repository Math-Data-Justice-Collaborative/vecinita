"""Batch document upsert for ingest and rebuild writes."""

from __future__ import annotations

import uuid as _uuid
from typing import TYPE_CHECKING, cast
from uuid import UUID

from sqlalchemy import text
from vecinita_ingest.nested_source import derive_nested_source
from vecinita_shared_schemas.automations import EmbedStatus
from vecinita_shared_schemas.db_mapping import scalar_uuid
from vecinita_shared_schemas.internal_write import (
    BatchUpsertDocumentResult,
    BatchUpsertRequest,
    BatchUpsertResponse,
)

from vecinita_internal_write_api.audit import create_document_version, emit_audit_event
from vecinita_internal_write_api.catchup_crud import maybe_enqueue_catchup_after_document_change
from vecinita_internal_write_api.jobs_client import DataManagementJobsClient
from vecinita_internal_write_api.tags import replace_document_tags

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def batch_upsert_documents(
    *,
    engine: Engine,
    jobs_client: DataManagementJobsClient | None,
    body: BatchUpsertRequest,
    actor_id: UUID | None,
    actor_role: str | None,
) -> BatchUpsertResponse:
    """Upsert documents, chunks, embeddings, and tags; enqueue F75 catch-up when needed."""
    upserted = 0
    written_documents: list[BatchUpsertDocumentResult] = []
    request_id = _uuid.uuid4()
    pending_catchups: list[tuple[_uuid.UUID, str, EmbedStatus]] = []
    with engine.begin() as conn:
        for document in body.documents:
            nested = derive_nested_source(
                str(document.url),
                parent_url=document.parent_url,
                source_domain=document.source_domain,
                source_path=document.source_path,
                canonical_url=document.canonical_url,
            )
            doc_id = scalar_uuid(
                cast(
                    "object",
                    conn.execute(
                        text(
                            """
                        INSERT INTO documents (
                            url, title, content_hash, language, body_text,
                            source_domain, source_path, parent_url, canonical_url,
                            paired_document_id, publish_status
                        )
                        VALUES (
                            :url, :title, :content_hash, :language, :body_text,
                            :source_domain, :source_path, :parent_url, :canonical_url,
                            :paired_document_id, :publish_status
                        )
                        ON CONFLICT (url, language) DO UPDATE
                        SET title = EXCLUDED.title,
                            content_hash = EXCLUDED.content_hash,
                            language = EXCLUDED.language,
                            body_text = COALESCE(EXCLUDED.body_text, documents.body_text),
                            source_domain = EXCLUDED.source_domain,
                            source_path = EXCLUDED.source_path,
                            parent_url = EXCLUDED.parent_url,
                            canonical_url = EXCLUDED.canonical_url,
                            paired_document_id = COALESCE(
                                EXCLUDED.paired_document_id, documents.paired_document_id
                            ),
                            publish_status = COALESCE(
                                EXCLUDED.publish_status, documents.publish_status
                            ),
                            updated_at = now()
                        RETURNING id
                        """
                        ),
                        {
                            "url": str(document.url),
                            "title": document.title,
                            "content_hash": document.content_hash,
                            "language": document.language,
                            "body_text": document.body_text,
                            "source_domain": nested.source_domain,
                            "source_path": nested.source_path,
                            "parent_url": nested.parent_url,
                            "canonical_url": nested.canonical_url,
                            "paired_document_id": document.paired_document_id,
                            "publish_status": document.publish_status,
                        },
                    ).scalar_one(),
                )
            )
            written_documents.append(
                BatchUpsertDocumentResult(
                    document_id=doc_id,
                    url=str(document.url),
                    language=document.language,
                )
            )

            if document.body_text is not None:
                _ = conn.execute(
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
                                rebuild_run_id
                            )
                            VALUES (
                                :document_id,
                                :content_hash,
                                :body_text,
                                :embedding_model_id,
                                :embedding_dim,
                                :chunk_size_tokens,
                                :chunk_tokenizer_id,
                                :rebuild_run_id
                            )
                            """
                    ),
                    {
                        "document_id": doc_id,
                        "content_hash": document.content_hash,
                        "body_text": document.body_text,
                        "embedding_model_id": document.embedding_model_id,
                        "embedding_dim": document.embedding_dim,
                        "chunk_size_tokens": document.chunk_size_tokens,
                        "chunk_tokenizer_id": document.chunk_tokenizer_id,
                        "rebuild_run_id": document.rebuild_run_id,
                    },
                )

            if document.chunks:
                _ = conn.execute(
                    text("DELETE FROM chunks WHERE document_id = :document_id"),
                    {"document_id": doc_id},
                )

                for chunk in document.chunks:
                    chunk_id = scalar_uuid(
                        cast(
                            "object",
                            conn.execute(
                                text(
                                    """
                            INSERT INTO chunks (document_id, chunk_index, text)
                            VALUES (:document_id, :chunk_index, :text)
                            RETURNING id
                            """
                                ),
                                {
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
                            INSERT INTO embeddings (chunk_id, embedding)
                            VALUES (:chunk_id, CAST(:embedding AS vector))
                            ON CONFLICT (chunk_id) DO UPDATE
                            SET embedding = EXCLUDED.embedding
                            """
                        ),
                        {
                            "chunk_id": chunk_id,
                            "embedding": vector_literal,
                        },
                    )
                    upserted += 1

            tag_slugs: list[dict[str, object]] = []
            if document.tags is not None:
                replace_document_tags(
                    conn,
                    document_id=doc_id,
                    tags=document.tags,
                    language=document.language or "en",
                )
                tag_slugs = [
                    {"slug": t.slug, "label": t.label, "source": t.source or "llm"}
                    for t in document.tags
                ]

            emit_audit_event(
                conn,
                event_type="document.created",
                entity_type="document",
                entity_id=doc_id,
                request_id=request_id,
                payload={
                    "url": str(document.url),
                    "title": document.title,
                    "language": document.language,
                },
                actor_id=actor_id,
                actor_role=actor_role,
            )
            _ = create_document_version(
                conn,
                document_id=doc_id,
                title=document.title,
                language=document.language,
                tags_snapshot=tag_slugs,
            )
            pending_catchups.append(
                (
                    doc_id,
                    document.content_hash or "0",
                    "complete" if document.chunks else "missing",
                )
            )

    for doc_id, revision, embed_status in pending_catchups:
        _ = maybe_enqueue_catchup_after_document_change(
            engine=engine,
            jobs_client=jobs_client,
            document_id=doc_id,
            revision=revision,
            embed_status=embed_status,
        )

    return BatchUpsertResponse(upserted_chunks=upserted, documents=written_documents)
