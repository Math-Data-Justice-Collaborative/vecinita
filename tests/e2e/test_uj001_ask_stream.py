"""UJ-001: bilingual ask + stream E2E (local tier, mocked Modal)."""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.helpers.json_response import json_object_list, json_str, response_json_object
from tests.unit.rag.conftest import attach_embeddings, basis_vector

if TYPE_CHECKING:
    from collections.abc import Iterator


pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_P95_INFORMATIVE_S = 15.0


def _parse_sse(raw: str) -> list[JsonObject]:
    return [
        as_json_object(cast("object", json.loads(line.removeprefix("data: "))))
        for line in raw.splitlines()
        if line.startswith("data: ")
    ]


def test_uj001_ask_and_stream(chat_client: TestClient) -> None:
    """Uj001 ask and stream."""
    ask = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert ask.status_code == HTTPStatus.OK
    body = response_json_object(ask)
    assert body["language"] == "en"
    assert body["answer"]
    sources = json_object_list(body, "sources")
    assert len(sources) >= 1
    assert json_str(sources[0], "chunk_id")

    stream = chat_client.post(
        "/api/v1/ask/stream",
        json={"question": "What are the food pantry hours?"},
    )
    assert stream.status_code == HTTPStatus.OK
    events = _parse_sse(stream.text)
    assert events[-1].get("done") is True


class _SpanishMockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate."""
        _ = (prompt, kwargs)
        return "El banco de alimentos publica horarios cada lunes en el sitio de la ciudad."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        """Generate stream."""
        _ = (prompt, kwargs)
        yield "El banco de alimentos publica horarios."

    def close(self) -> None:
        """Close."""
        return


@pytest.fixture
def spanish_chat_client(seeded_corpus_db: str) -> TestClient:
    """Spanish chat client."""
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
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["language"] == "es"
    assert body["answer"]
    sources = json_object_list(body, "sources")
    answer = json_str(body, "answer")
    assert len(sources) >= 1
    assert (
        any("banco de alimentos" in json_str(source, "title").lower() for source in sources)
        or "banco de alimentos" in answer.lower()
    )


def test_uj001_mocked_ask_latency_informative(chat_client: TestClient) -> None:
    """AC-C6 (local): mocked stack should be well under 15s; live p95 in staging smoke."""
    start = time.perf_counter()
    response = chat_client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    elapsed = time.perf_counter() - start
    assert response.status_code == HTTPStatus.OK
    assert elapsed < _P95_INFORMATIVE_S, (
        f"mocked ask took {elapsed:.2f}s; investigate before staging (target p95 < {_P95_INFORMATIVE_S}s)"
    )
