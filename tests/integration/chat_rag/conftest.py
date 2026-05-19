"""ChatRAG integration test fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from tests.unit.rag.conftest import attach_embeddings, basis_vector
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_database.seeds.load import load_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever

_EMBED_URL = "http://embed.test"
_LLM_URL = "http://llm.test"


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


class _MockEmbedClient:
    def embed(self, text: str) -> list[float]:
        return basis_vector(0)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [basis_vector(0) for _ in texts]

    def close(self) -> None:
        return None


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        return "The food pantry posts hours on the city website each Monday."

    def generate_stream(self, prompt: str, **kwargs: object):
        yield "The "
        yield "food "
        yield "pantry "
        yield "posts "
        yield "hours."

    def close(self) -> None:
        return None


@pytest.fixture
def seeded_corpus_db() -> str:
    url = _database_url()
    load_corpus(database_url=url)
    attach_embeddings(
        database_url=url,
        match_substrings={"Food pantry": 0, "banco de alimentos": 2},
        default_index=1,
    )
    return url


@pytest.fixture
def chat_settings(seeded_corpus_db: str, monkeypatch: pytest.MonkeyPatch) -> ChatRagSettings:
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
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=chat_settings.database_url,
        top_k=chat_settings.top_k,
    )
    return ChatRagService(retriever=retriever, llm_client=_MockLlmClient())  # type: ignore[arg-type]


@pytest.fixture
def chat_client(chat_settings: ChatRagSettings, chat_service: ChatRagService) -> TestClient:
    app = create_app(settings=chat_settings, chat_service=chat_service)
    return TestClient(app)
