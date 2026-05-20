"""UJ-001: bilingual ask + stream E2E (local tier, mocked Modal)."""

from __future__ import annotations

import json
import time

import pytest
from fastapi.testclient import TestClient
from tests.unit.rag.conftest import attach_embeddings, basis_vector
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_P95_INFORMATIVE_S = 15.0


def _parse_sse(raw: str) -> list[dict]:
    events: list[dict] = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line.removeprefix("data: ")))
    return events


def test_uj001_ask_and_stream(chat_client: TestClient) -> None:
    ask = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert ask.status_code == 200
    body = ask.json()
    assert body["language"] == "en"
    assert body["answer"]
    assert len(body["sources"]) >= 1
    assert body["sources"][0]["chunk_id"]

    stream = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "What are the food pantry hours?"},
    )
    assert stream.status_code == 200
    events = _parse_sse(stream.text)
    assert events[-1].get("done") is True


class _SpanishMockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        return "El banco de alimentos publica horarios cada lunes en el sitio de la ciudad."

    def generate_stream(self, prompt: str, **kwargs: object):
        yield "El banco de alimentos publica horarios."

    def close(self) -> None:
        return None


@pytest.fixture
def spanish_chat_client(seeded_corpus_db: str) -> TestClient:
    attach_embeddings(
        database_url=seeded_corpus_db,
        match_substrings={"Food pantry": 0, "banco de alimentos": 2},
        default_index=1,
    )
    settings = ChatRagSettings(
        database_url=seeded_corpus_db,
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(2),
        database_url=settings.database_url,
        top_k=settings.top_k,
    )
    service = ChatRagService(
        retriever=retriever,
        llm_client=_SpanishMockLlmClient(),  # type: ignore[arg-type]
    )
    return TestClient(create_app(settings=settings, chat_service=service))


def test_uj001_spanish_ask_returns_spanish_answer(spanish_chat_client: TestClient) -> None:
    """TC-011 / AC-C1: Spanish question → Spanish answer with corpus-backed sources."""
    response = spanish_chat_client.post(
        "/api/v1/ask",
        json={"question": "¿Cuándo publica horarios el banco de alimentos?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "es"
    assert body["answer"]
    assert len(body["sources"]) >= 1
    assert (
        any("banco de alimentos" in (s.get("title") or "").lower() for s in body["sources"])
        or "banco de alimentos" in body["answer"].lower()
    )


def test_uj001_mocked_ask_latency_informative(chat_client: TestClient) -> None:
    """AC-C6 (local): mocked stack should be well under 15s; live p95 in staging smoke."""
    start = time.perf_counter()
    response = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    elapsed = time.perf_counter() - start
    assert response.status_code == 200
    assert elapsed < _P95_INFORMATIVE_S, (
        f"mocked ask took {elapsed:.2f}s; investigate before staging (target p95 < {_P95_INFORMATIVE_S}s)"
    )
