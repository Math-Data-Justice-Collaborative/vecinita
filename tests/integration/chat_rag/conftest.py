"""ChatRAG integration test fixtures."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.unit.rag.conftest import basis_vector, seed_corpus_with_embeddings

if TYPE_CHECKING:
    from collections.abc import Iterator

_EMBED_URL = "http://embed.test"
_LLM_URL = "http://llm.test"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        return "The food pantry posts hours on the city website each Monday."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        yield "The "
        yield "food "
        yield "pantry "
        yield "posts "
        yield "hours."

    def close(self) -> None:
        return None


@pytest.fixture
def seeded_corpus_db() -> str:
    """Seed the corpus with embeddings and return the database URL."""
    url = _database_url()
    seed_corpus_with_embeddings(
        database_url=url,
        match_substrings={"Food pantry": 0, "banco de alimentos": 2},
        default_index=1,
    )
    return url


@pytest.fixture
def chat_settings(seeded_corpus_db: str, monkeypatch: pytest.MonkeyPatch) -> ChatRagSettings:
    """Build ChatRagSettings pointed at the seeded corpus DB."""
    monkeypatch.setenv("DATABASE_URL", seeded_corpus_db)
    return ChatRagSettings(
        database_url=seeded_corpus_db,
        top_k=5,
        embed_url=_EMBED_URL,
        llm_url=_LLM_URL,
        request_timeout_s=30.0,
    )


@pytest.fixture
def chat_service(chat_settings: ChatRagSettings) -> ChatRagService:
    """Construct a ChatRagService backed by the seeded corpus and mock LLM."""
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=chat_settings.database_url,
        top_k=chat_settings.top_k,
    )
    return ChatRagService(retriever=retriever, llm_client=_MockLlmClient())  # type: ignore[arg-type]


@pytest.fixture
def chat_client(chat_settings: ChatRagSettings, chat_service: ChatRagService) -> TestClient:
    """Return a TestClient for the chat-RAG app with the seeded service."""
    app = create_app(settings=chat_settings, chat_service=chat_service)
    return TestClient(app)
