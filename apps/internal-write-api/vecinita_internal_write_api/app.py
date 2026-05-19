"""FastAPI internal write API — sole DATABASE_URL holder (ADR-007)."""

from __future__ import annotations

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentSummary,
    HealthResponse,
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


def create_app() -> FastAPI:
    app = FastAPI(title="Vecinita Internal Write API", version="0.1.0")
    engine = _engine()

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

        return BatchUpsertResponse(upserted_chunks=upserted)

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
