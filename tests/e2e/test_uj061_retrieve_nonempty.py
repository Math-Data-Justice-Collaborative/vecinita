"""UJ-061 / TC-185-186: non-empty staging retrieve pools and ask sources (F46)."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_database.seeds.load import load_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk

from tests.helpers.corpus_db_guard import is_local_corpus_database
from tests.helpers.json_response import json_list, response_json_object
from tests.unit.rag.conftest import attach_embeddings, basis_vector, clear_embeddings

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate a fixed answer for e2e."""
        _ = (prompt, kwargs)
        return "Housing rights information is available from community resources."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        """Stream a fixed answer for e2e."""
        _ = (prompt, kwargs)
        yield "Housing rights information is available."

    def close(self) -> None:
        """Close the mock client."""
        return


class _HitRetriever:
    """Retriever that always returns one in-corpus chunk (cold-path fixture)."""

    def retrieve_chunks(  # noqa: PLR0913 — mirrors CorpusPgvectorRetriever.retrieve_chunks
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
        rebuild_run_id: object | None = None,
    ) -> list[RetrievedChunk]:
        _ = (question, tag_slugs, language, top_k, score_threshold, rebuild_run_id)
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                text="Tenant rights include notice before eviction in many jurisdictions.",
                score=0.88,
                title="Housing Rights Guide",
                url="https://example.org/housing-rights",
                language="en",
            )
        ]


def _postgres_reachable(url: str) -> bool:
    """Return True when local/CI Postgres accepts connections."""
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            _ = conn.execute(text("SELECT 1"))
    except (OperationalError, OSError):
        return False
    finally:
        engine.dispose()
    return True


@pytest.fixture
def seeded_retriever() -> CorpusPgvectorRetriever:
    """Seed corpus + embeddings so a matching query has pool > 0 (TC-185)."""
    url = _database_url()
    if not is_local_corpus_database(url):
        pytest.skip(
            "TC-185 seeds local Postgres only — unset staging DATABASE_URL (BUG-2026-08-02 guard)"
        )
    if not _postgres_reachable(url):
        pytest.skip("Postgres unavailable for fixture-backed TC-185 (start compose postgres)")
    _ = load_corpus(database_url=url)
    clear_embeddings(database_url=url)
    _ = attach_embeddings(
        database_url=url,
        match_substrings={"Housing": 0, "housing": 0},
        default_index=1,
    )
    return CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=url,
        top_k=5,
        score_threshold=0.0,
    )


@pytest.fixture
def cold_ask_client() -> TestClient:
    """ChatRAG client with hit stub + cache enabled (cold miss path)."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=True,
    )
    service = ChatRagService(
        retriever=_HitRetriever(),  # type: ignore[arg-type]
        llm_client=_MockLlmClient(),  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service))


def test_tc185_seeded_retrieve_pool_nonempty(
    seeded_retriever: CorpusPgvectorRetriever,
) -> None:
    """TC-185 / AC-FO1: representative in-corpus retrieve returns pool > 0."""
    chunks = seeded_retriever.retrieve_chunks(
        "What are my housing rights?",
        language="en",
        top_k=5,
        score_threshold=0.0,
    )
    assert len(chunks) > 0, "expected non-empty retrieve pool for seeded housing query"


def test_tc186_cold_ask_returns_sources_when_corpus_matches(
    cold_ask_client: TestClient,
) -> None:
    """TC-186 / AC-FO2: cold ask exposes non-empty sources[] when retrieve has hits."""
    response = cold_ask_client.post(
        "/api/v1/ask",
        json={"question": "What are my housing tenant rights under local law?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    sources = json_list(body, "sources")
    assert len(sources) >= 1
    if "cache_hit" in body:
        assert body["cache_hit"] in {"none", "exact", "semantic", "retrieve"}
