"""FastAPI internal write API — sole DATABASE_URL holder (ADR-007)."""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from vecinita_shared_schemas.cors import configure_cors
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    ChunkDetail,
    DocumentDetail,
    DocumentSummary,
    HealthResponse,
    RetagJobResponse,
    TagInput,
    TagPatchRequest,
    TagPatchResponse,
)

from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)
from vecinita_internal_write_api.tags import (
    replace_chunk_tags,
    replace_document_tags,
    validate_chunk_tag_count,
    validate_document_tag_count,
)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required for internal write API")
    return _normalize_database_url(url)


def _engine() -> Engine:
    return create_engine(_database_url())


def _require_internal_key(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected = os.environ.get("VECINITA_INTERNAL_API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API key not configured",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def _default_jobs_client() -> DataManagementJobsClient | None:
    """Auto-create a DataManagementJobsClient from env vars when available."""
    try:
        return DataManagementJobsClient()
    except DataManagementJobsClientError:
        return None


def create_app(*, jobs_client: DataManagementJobsClient | None = None) -> FastAPI:
    """Build the internal write API (sole holder of DATABASE_URL)."""
    app = FastAPI(title="Vecinita Internal Write API", version="0.1.0")
    configure_cors(app, extra_allow_headers=["Authorization"])
    engine = _engine()
    retag_jobs = jobs_client if jobs_client is not None else _default_jobs_client()

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post(
        "/internal/v1/documents/batch",
        response_model=BatchUpsertResponse,
        dependencies=[Depends(_require_internal_key)],
    )
    def batch_upsert(body: BatchUpsertRequest) -> BatchUpsertResponse:
        upserted = 0
        with engine.begin() as conn:
            for document in body.documents:
                doc_id = conn.execute(
                    text(
                        """
                        INSERT INTO documents (url, title, content_hash, language)
                        VALUES (:url, :title, :content_hash, :language)
                        ON CONFLICT (url) DO UPDATE
                        SET title = EXCLUDED.title,
                            content_hash = EXCLUDED.content_hash,
                            language = EXCLUDED.language,
                            updated_at = now()
                        RETURNING id
                        """
                    ),
                    {
                        "url": str(document.url),
                        "title": document.title,
                        "content_hash": document.content_hash,
                        "language": document.language,
                    },
                ).scalar_one()

                conn.execute(
                    text("DELETE FROM chunks WHERE document_id = :document_id"),
                    {"document_id": doc_id},
                )

                for chunk in document.chunks:
                    chunk_id = conn.execute(
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
                    ).scalar_one()
                    vector_literal = "[" + ",".join(str(v) for v in chunk.embedding) + "]"
                    conn.execute(
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

                if document.tags is not None:
                    replace_document_tags(
                        conn,
                        document_id=doc_id,
                        tags=document.tags,
                        language=document.language or "en",
                    )

        return BatchUpsertResponse(upserted_chunks=upserted)

    @app.get(
        "/internal/v1/documents/{document_id}",
        response_model=DocumentDetail,
        dependencies=[Depends(_require_internal_key)],
    )
    def get_document_detail(document_id: UUID) -> DocumentDetail:
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT id, url, title, language
                        FROM documents
                        WHERE id = :document_id
                        """
                    ),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            chunks = (
                conn.execute(
                    text(
                        """
                    SELECT text
                    FROM chunks
                    WHERE document_id = :document_id
                    ORDER BY chunk_index ASC
                    """
                    ),
                    {"document_id": document_id},
                )
                .scalars()
                .all()
            )
        return DocumentDetail(
            document_id=row["id"],
            url=row["url"],
            title=row["title"],
            language=row["language"],
            text="\n\n".join(chunks),
        )

    @app.get(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
        dependencies=[Depends(_require_internal_key)],
    )
    def get_document_tags(document_id: UUID) -> TagPatchResponse:
        with engine.connect() as conn:
            doc = (
                conn.execute(
                    text("SELECT id, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if doc is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Not found"
                )
            language = doc["language"] or "en"
            tag_rows = (
                conn.execute(
                    text(
                        """
                        SELECT t.slug, t.label, dt.source
                        FROM document_tags dt
                        JOIN tags t ON t.id = dt.tag_id
                        WHERE dt.document_id = :document_id
                          AND t.language = :language
                        ORDER BY t.slug
                        """
                    ),
                    {"document_id": document_id, "language": language},
                )
                .mappings()
                .all()
            )
        return TagPatchResponse(
            tags=[
                TagInput(slug=row["slug"], label=row["label"], source=row["source"])
                for row in tag_rows
            ]
        )

    @app.patch(
        "/internal/v1/documents/{document_id}/tags",
        response_model=TagPatchResponse,
        dependencies=[Depends(_require_internal_key)],
    )
    def patch_document_tags(document_id: UUID, body: TagPatchRequest) -> TagPatchResponse:
        validate_document_tag_count(body.tags)
        with engine.begin() as conn:
            row = (
                conn.execute(
                    text("SELECT id, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            tags = [
                tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags
            ]
            replace_document_tags(
                conn,
                document_id=document_id,
                tags=tags,
                language=row["language"] or "en",
            )
        return TagPatchResponse(tags=tags)

    @app.get(
        "/internal/v1/documents/{document_id}/chunks",
        response_model=list[ChunkDetail],
        dependencies=[Depends(_require_internal_key)],
    )
    def list_document_chunks(document_id: UUID) -> list[ChunkDetail]:
        with engine.connect() as conn:
            doc = (
                conn.execute(
                    text("SELECT id, language FROM documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
                .mappings()
                .first()
            )
            if doc is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            language = doc["language"] or "en"
            rows = (
                conn.execute(
                    text(
                        """
                        SELECT c.id, c.chunk_index, c.text, c.token_count
                        FROM chunks c
                        WHERE c.document_id = :document_id
                        ORDER BY c.chunk_index ASC
                        """
                    ),
                    {"document_id": document_id},
                )
                .mappings()
                .all()
            )
            details: list[ChunkDetail] = []
            for row in rows:
                tag_rows = (
                    conn.execute(
                        text(
                            """
                            SELECT t.slug, t.label, ct.source
                            FROM chunk_tags ct
                            JOIN tags t ON t.id = ct.tag_id
                            WHERE ct.chunk_id = :chunk_id
                              AND t.language = :language
                            ORDER BY t.slug
                            """
                        ),
                        {"chunk_id": row["id"], "language": language},
                    )
                    .mappings()
                    .all()
                )
                details.append(
                    ChunkDetail(
                        chunk_id=row["id"],
                        chunk_index=row["chunk_index"],
                        text=row["text"],
                        token_count=row["token_count"],
                        tags=[
                            TagInput(slug=tag["slug"], label=tag["label"], source=tag["source"])
                            for tag in tag_rows
                        ],
                    )
                )
        return details

    @app.patch(
        "/internal/v1/chunks/{chunk_id}/tags",
        response_model=TagPatchResponse,
        dependencies=[Depends(_require_internal_key)],
    )
    def patch_chunk_tags(chunk_id: UUID, body: TagPatchRequest) -> TagPatchResponse:
        validate_chunk_tag_count(body.tags)
        with engine.begin() as conn:
            row = (
                conn.execute(
                    text(
                        """
                        SELECT c.id, d.language
                        FROM chunks c
                        JOIN documents d ON d.id = c.document_id
                        WHERE c.id = :chunk_id
                        """
                    ),
                    {"chunk_id": chunk_id},
                )
                .mappings()
                .first()
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            tags = [
                tag.model_copy(update={"source": tag.source or body.source}) for tag in body.tags
            ]
            replace_chunk_tags(
                conn,
                chunk_id=chunk_id,
                tags=tags,
                language=row["language"] or "en",
            )
        return TagPatchResponse(tags=tags)

    @app.post(
        "/internal/v1/documents/{document_id}/retag",
        response_model=RetagJobResponse,
        dependencies=[Depends(_require_internal_key)],
    )
    def retag_document(document_id: UUID) -> RetagJobResponse:
        if retag_jobs is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Retag job client not configured",
            )
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT id FROM documents WHERE id = :document_id"),
                {"document_id": document_id},
            ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        job_id = retag_jobs.enqueue_retag(document_id)
        return RetagJobResponse(job_id=job_id)

    @app.get(
        "/internal/v1/documents",
        response_model=list[DocumentSummary],
        dependencies=[Depends(_require_internal_key)],
    )
    def list_documents() -> list[DocumentSummary]:
        with engine.connect() as conn:
            rows = (
                conn.execute(
                    text(
                        """
                    SELECT id, url, title, language
                    FROM documents
                    ORDER BY created_at DESC
                    """
                    )
                )
                .mappings()
                .all()
            )
        return [
            DocumentSummary(
                document_id=row["id"],
                url=row["url"],
                title=row["title"],
                language=row["language"],
            )
            for row in rows
        ]

    @app.delete(
        "/internal/v1/documents/{document_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(_require_internal_key)],
    )
    def delete_document(document_id: UUID) -> None:
        with engine.begin() as conn:
            deleted = conn.execute(
                text("DELETE FROM documents WHERE id = :document_id RETURNING id"),
                {"document_id": document_id},
            ).scalar_one_or_none()
        if deleted is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return app
