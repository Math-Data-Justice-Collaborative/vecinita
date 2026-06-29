"""Shared fixtures for chat-rag-backend unit tests."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


@pytest.fixture
def chat_settings(monkeypatch: pytest.MonkeyPatch) -> ChatRagSettings:
    monkeypatch.setenv("DATABASE_URL", database_url())
    return ChatRagSettings(
        database_url=database_url(),
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=10.0,
        internal_write_url="http://write.test",
        internal_api_key="write-key",
    )


@pytest.fixture
def engine(chat_settings: ChatRagSettings) -> Engine:
    return create_engine(chat_settings.database_url)


@pytest.fixture
def browse_document(engine: Engine) -> Iterator[tuple[UUID, str]]:
    """Insert a tagged browse document; delete after test."""
    doc_url = f"https://chat-rag-browse-{uuid.uuid4().hex[:10]}.example.com/"
    with engine.begin() as conn:
        doc_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO documents (url, title, language)
                    VALUES (:url, 'Browse fixture', 'en')
                    RETURNING id
                    """
                ),
                {"url": doc_url},
            )
        )
        doc_id = UUID(str(doc_id_raw))
        tag_id_raw = sqlalchemy_scalar_one(
            conn.execute(
                text(
                    """
                    INSERT INTO tags (slug, label, language)
                    VALUES ('housing', 'Housing', 'en')
                    ON CONFLICT (slug, language) DO UPDATE SET label = EXCLUDED.label
                    RETURNING id
                    """
                )
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO document_tags (document_id, tag_id, source)
                VALUES (:doc_id, :tag_id, 'llm')
                ON CONFLICT (document_id, tag_id) DO NOTHING
                """
            ),
            {"doc_id": doc_id, "tag_id": tag_id_raw},
        )
    yield doc_id, doc_url
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM document_tags WHERE document_id = :id"), {"id": doc_id})
        conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


_CHUNK = RetrievedChunk(
    chunk_id=uuid.uuid4(),
    document_id=uuid.uuid4(),
    title="Fixture doc",
    url="https://fixture.example.com/page",
    text="Neighborhood clinic offers housing counseling on weekdays.",
    score=0.92,
    language="en",
)


class StubChatRagService:
    """In-memory ChatRagService stand-in for route tests."""

    def __init__(
        self,
        *,
        sources: list[Source] | None = None,
        stream_tokens: list[str] | None = None,
        ask_error: Exception | None = None,
        retrieve_error: Exception | None = None,
    ) -> None:
        if sources is None:
            self.sources = [
                Source(
                    chunk_id=_CHUNK.chunk_id,
                    document_id=_CHUNK.document_id,
                    title=_CHUNK.title,
                    url=_CHUNK.url,
                    score=_CHUNK.score,
                )
            ]
        else:
            self.sources = list(sources)
        self.stream_tokens = stream_tokens or ["Hello", " world"]
        self.ask_error = ask_error
        self.retrieve_error = retrieve_error

    def ask(self, request: AskRequest) -> AskResponse:
        _ = request
        if self.ask_error is not None:
            raise self.ask_error
        return AskResponse(answer="Stub answer", language="en", sources=self.sources)

    def retrieve_sources(self, request: AskRequest) -> list[Source]:
        _ = request
        if self.retrieve_error is not None:
            raise self.retrieve_error
        return list(self.sources)

    def ask_stream(self, request: AskRequest) -> Iterator[str]:
        _ = request
        yield from self.stream_tokens
