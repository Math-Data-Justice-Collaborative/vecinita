"""UJ-012 tag-filtered ask E2E (TC-044)."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from tests.unit.rag.conftest import attach_embeddings, basis_vector
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_database.seeds.tags import load_seed_tags, load_tagged_corpus
from vecinita_rag.retriever import CorpusPgvectorRetriever

pytestmark = pytest.mark.e2e


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


class _MockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        return "Tenant rights information is available from community resources."

    def generate_stream(self, prompt: str, **kwargs: object):
        yield "Tenant rights information is available."

    def close(self) -> None:
        return None


@pytest.fixture
def tag_ask_client() -> TestClient:
    url = _database_url()
    load_seed_tags(database_url=url)
    load_tagged_corpus(database_url=url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM embeddings"))
    attach_embeddings(
        database_url=url,
        match_substrings={"Housing Rights": 0, "Legal Aid": 1},
        default_index=1,
    )

    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=url,
        top_k=5,
    )
    service = ChatRagService(
        retriever=retriever,
        llm_client=_MockLlmClient(),  # type: ignore[arg-type]
        tag_infer_fn=lambda _q: ["housing"],
    )
    settings = ChatRagSettings(
        database_url=url,
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    return TestClient(create_app(settings=settings, chat_service=service))


def test_uj012_tag_filtered_ask_returns_matching_sources(tag_ask_client: TestClient) -> None:
    """Ask with tags[] limits retrieval to matching corpus documents."""
    response = tag_ask_client.post(
        "/api/v1/ask",
        json={"question": "What are my tenant rights?", "tags": ["housing"]},
    )
    assert response.status_code == 200
    sources = response.json()["sources"]
    assert sources
    assert all("corpus/tagged" in (source.get("url") or "") for source in sources)
