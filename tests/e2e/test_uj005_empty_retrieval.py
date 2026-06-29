"""UJ-005 / TC-003: empty retrieval returns explicit no-context message."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator


pytestmark = pytest.mark.e2e


class _EmptyRetriever:
    def retrieve_chunks(
        self,
        query: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = None,
    ) -> list[object]:
        """Retrieve chunks."""
        _ = (query, tag_slugs, language)
        return []


class _NoopLlm:
    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate."""
        _ = (prompt, kwargs)
        msg = "LLM should not be called for empty retrieval"
        raise AssertionError(msg)

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        """Generate stream."""
        _ = (prompt, kwargs)
        msg = "LLM should not be called for empty retrieval"
        raise AssertionError(msg)
        yield ""  # pragma: no cover

    def close(self) -> None:
        """Close."""
        return


@pytest.fixture
def empty_client() -> TestClient:
    """ChatRAG client whose retriever always returns no chunks."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    service = ChatRagService(
        retriever=_EmptyRetriever(),  # type: ignore[arg-type]
        llm_client=_NoopLlm(),  # type: ignore[arg-type]
    )
    app = create_app(settings=settings, chat_service=service)
    return TestClient(app)


def test_uj005_empty_retrieval_message(empty_client: TestClient) -> None:
    """Empty retrieval returns a corpus-aware no-context answer without calling the LLM."""
    response = empty_client.post(
        "/api/v1/ask",
        json={"question": "What is the quantum flux capacitor rating?"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["sources"] == []
    assert "corpus" in json_str(body, "answer").lower()
