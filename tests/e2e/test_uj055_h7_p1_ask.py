"""UJ-055 / TC-173: ChatRAG ask uses shared H7+P1 helpers (F42)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.multi_query import multi_query_retrieve
from vecinita_rag.types import RetrievedChunk

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


class _CapturingLlm:
    """Capture generate prompts for packing/H7 assertions."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        self.prompts.append(prompt)
        return "Food pantry hours are posted Mondays."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = kwargs
        self.prompts.append(prompt)
        yield "Food pantry hours are posted Mondays."

    def close(self) -> None:
        return


class _StubRetriever:
    """Return a titled chunk for any retrieve call."""

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
                text="Food pantry hours are posted Mondays.",
                score=0.91,
                title="Community pantry",
                url="https://example.org/pantry",
                language="en",
            )
        ]


@pytest.fixture
def uj055_client() -> tuple[TestClient, _CapturingLlm]:
    """Chat client with stub retrieve + capturing LLM (no live DB)."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_multi_query=True,
        rag_multi_query_count=3,
        rag_packer="p1",
    )
    llm = _CapturingLlm()
    service = ChatRagService(
        retriever=_StubRetriever(),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service)), llm


def test_uj055_ask_prompt_includes_source_url_headers(
    uj055_client: tuple[TestClient, _CapturingLlm],
) -> None:
    """TC-173 / AC-RQ4: ask path packs Source/URL headers via packages/rag."""
    client, llm = uj055_client
    response = client.post(
        "/api/v1/ask",
        json={"question": "What are the food pantry hours?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["answer"]
    assert body["sources"]
    assert llm.prompts
    prompt = llm.prompts[0]
    assert "Source: Community pantry" in prompt
    assert "URL: https://example.org/pantry" in prompt


def test_uj055_ask_invokes_h7_multi_query_by_default(
    uj055_client: tuple[TestClient, _CapturingLlm],
) -> None:
    """TC-173: H7 fan-out is invoked on the ask path when enabled."""
    client, _llm = uj055_client
    with patch(
        "vecinita_chat_rag_backend.service.multi_query_retrieve",
        wraps=multi_query_retrieve,
    ) as mocked:
        response = client.post(
            "/api/v1/ask",
            json={"question": "How do I find food pantry hours?"},
        )
    assert response.status_code == HTTPStatus.OK
    assert mocked.called
    assert mocked.call_args.kwargs.get("enabled") is True
