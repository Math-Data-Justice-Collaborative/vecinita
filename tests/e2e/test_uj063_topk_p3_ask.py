"""UJ-063 / TC-195: ask uses default top_k=8 + P3 packing (F50-F51)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.packing import pack_chunks
from vecinita_rag.types import RetrievedChunk

from tests.helpers.json_response import json_list, json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_EXPECTED_TOP_K = 8
_HIT_COUNT = 10
_SOURCE_CAP = 8


class _CapturingLlm:
    """Capture generate prompts for P3 packing assertions."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        self.prompts.append(prompt)
        return "Community programs are listed on the city site."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = kwargs
        self.prompts.append(prompt)
        yield "Community programs are listed on the city site."

    def close(self) -> None:
        return


class _MultiHitRetriever:
    """Return at least eight chunks including a same-document duplicate for P3."""

    def __init__(self) -> None:
        shared_doc = uuid4()
        self._chunks: list[RetrievedChunk] = [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=shared_doc,
                text="Primary shared-doc chunk (keep for P3).",
                score=0.95,
                title="Shared Doc Keep",
                url="https://example.org/shared",
                language="en",
            ),
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=shared_doc,
                text="Duplicate shared-doc chunk (drop for P3).",
                score=0.4,
                title="Shared Doc Drop",
                url="https://example.org/shared-dup",
                language="en",
            ),
        ]
        for index in range(_HIT_COUNT - 2):
            self._chunks.append(
                RetrievedChunk(
                    chunk_id=uuid4(),
                    document_id=uuid4(),
                    text=f"Distinct corpus hit {index}.",
                    score=0.9 - (index * 0.01),
                    title=f"Doc {index}",
                    url=f"https://example.org/doc-{index}",
                    language="en",
                )
            )

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
        _ = (question, tag_slugs, language, score_threshold, rebuild_run_id)
        limit = top_k if top_k is not None else _EXPECTED_TOP_K
        return self._chunks[:limit]


@pytest.fixture
def uj063_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, _CapturingLlm, ChatRagSettings]:
    """Chat client with production defaults (top_k=8, packer=p3) and stub retrieve."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://vecinita:vecinita@localhost/db")
    monkeypatch.delenv("VECINITA_TOP_K", raising=False)
    monkeypatch.delenv("VECINITA_RAG_PACKER", raising=False)
    settings = ChatRagSettings.from_env()
    assert settings.top_k == _EXPECTED_TOP_K
    assert settings.rag_packer == "p3"
    llm = _CapturingLlm()
    service = ChatRagService(
        retriever=_MultiHitRetriever(),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
    )
    return TestClient(create_app(settings=settings, chat_service=service)), llm, settings


def test_uj063_ask_returns_at_most_eight_sources(
    uj063_client: tuple[TestClient, _CapturingLlm, ChatRagSettings],
) -> None:
    """TC-195 / AC-RQ8: default ask returns ≤8 sources with no client override."""
    client, _llm, settings = uj063_client
    response = client.post(
        "/api/v1/ask",
        json={"question": "What community programs are available?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer")
    sources = json_list(body, "sources")
    assert len(sources) <= _SOURCE_CAP
    assert len(sources) == settings.top_k


def test_uj063_ask_uses_p3_packer_by_default(
    uj063_client: tuple[TestClient, _CapturingLlm, ChatRagSettings],
) -> None:
    """TC-195 / AC-RQ9: ask packs with mode=p3 and dedupes same document_id."""
    client, llm, _settings = uj063_client
    with patch(
        "vecinita_chat_rag_backend.service.pack_chunks",
        wraps=pack_chunks,
    ) as pack_spy:
        response = client.post(
            "/api/v1/ask",
            json={"question": "What community programs are available?"},
        )
    assert response.status_code == HTTPStatus.OK
    spy = cast_magic_mock(pack_spy)
    assert spy.called
    call_kwargs = spy.call_args.kwargs
    assert call_kwargs["mode"] == "p3"
    assert llm.prompts
    prompt = llm.prompts[0]
    assert "Source: Shared Doc Keep" in prompt
    assert "Source: Shared Doc Drop" not in prompt


def cast_magic_mock(value: object) -> MagicMock:
    """Narrow patch target to MagicMock for strict typing."""
    assert isinstance(value, MagicMock)
    return value
