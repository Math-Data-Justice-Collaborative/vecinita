"""UJ-007 / TC-030: reject identity fields in ChatRAG ask body."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.unit.rag.conftest import basis_vector

if TYPE_CHECKING:
    from collections.abc import Iterator


pytestmark = pytest.mark.e2e


class _E2eMockLlmClient:
    def generate(self, prompt: str, **kwargs: object) -> str:
        """Generate."""
        _ = (prompt, kwargs)
        return "ok"

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        """Generate stream."""
        _ = (prompt, kwargs)
        yield "ok"

    def close(self) -> None:
        """Close."""
        return


@pytest.fixture
def identity_client() -> TestClient:
    """ChatRAG client with mocked LLM for identity-field rejection tests."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=3,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=settings.database_url,
        top_k=3,
    )
    service = ChatRagService(retriever=retriever, llm_client=_E2eMockLlmClient())  # type: ignore[arg-type]
    app = create_app(settings=settings, chat_service=service)
    return TestClient(app)


def test_ask_rejects_email_field(identity_client: TestClient) -> None:
    """Ask body with email field is rejected before LLM invocation."""
    response = identity_client.post(
        "/api/v1/ask",
        json={"question": "hello", "email": "user@example.com"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
