"""UJ-007 / TC-030: reject identity fields in ChatRAG ask body."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.integration.chat_rag.conftest import _MockLlmClient
from tests.unit.rag.conftest import basis_vector

pytestmark = pytest.mark.e2e


@pytest.fixture
def identity_client() -> TestClient:
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
    service = ChatRagService(retriever=retriever, llm_client=_MockLlmClient())  # type: ignore[arg-type]
    app = create_app(settings=settings, chat_service=service)
    return TestClient(app)


def test_ask_rejects_email_field(identity_client: TestClient) -> None:
    response = identity_client.post(
        "/api/v1/ask",
        json={"question": "hello", "email": "user@example.com"},
    )
    assert response.status_code == 400
