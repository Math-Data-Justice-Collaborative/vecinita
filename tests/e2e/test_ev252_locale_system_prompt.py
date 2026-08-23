"""EV-252 / TC-257: locale-specific system prompt on ask (e2e layer)."""

from __future__ import annotations

from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_SYSTEM_PROMPT,
    DEFAULT_EVAL_SYSTEM_PROMPT_ES,
    EvalConfig,
)

from tests.helpers.json_response import response_json_object

pytestmark = [pytest.mark.e2e]

_EN_PROMPT = "Promoted English system prompt for TC-257."
_ES_MARKER = "únicamente el contexto siguiente"
_EN_MARKER = "Promoted English system prompt"


class _StubRetriever:
    def retrieve_chunks(
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        _ = (question, tag_slugs, language, top_k, score_threshold)
        return [
            RetrievedChunk(
                chunk_id=uuid4(),
                document_id=uuid4(),
                title="Community guide",
                url="https://example.com/guide",
                text="The clinic is open Monday through Friday.",
                score=0.88,
                language="en",
            )
        ]


class _CapturingMockLlmClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        self.prompts.append(prompt)
        return "Answer from mock LLM."

    def close(self) -> None:
        return


@pytest.fixture
def locale_prompt_chat_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, _CapturingMockLlmClient]:
    """Chat client with LLM prompt capture and custom EN production prompt."""
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=False,
    )
    llm = _CapturingMockLlmClient()
    production = EvalConfig(system_prompt=_EN_PROMPT)
    service = ChatRagService(
        retriever=_StubRetriever(),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
    )
    monkeypatch.setattr(service, "_production_config", lambda: production)
    client = TestClient(create_app(settings=settings, chat_service=service))
    return client, llm


def test_ev252_spanish_ask_uses_spanish_system_prompt(
    locale_prompt_chat_client: tuple[TestClient, _CapturingMockLlmClient],
) -> None:
    """TC-257: language=es uses DEFAULT_EVAL_SYSTEM_PROMPT_ES in LLM prompt."""
    client, llm = locale_prompt_chat_client
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What are the food pantry hours?",
            "language": "es",
        },
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["language"] == "es"
    assert llm.prompts, "expected LLM generate call"
    prompt = llm.prompts[-1]
    assert _ES_MARKER in prompt
    assert DEFAULT_EVAL_SYSTEM_PROMPT_ES.split()[0] in prompt
    assert _EN_MARKER not in prompt
    assert DEFAULT_EVAL_SYSTEM_PROMPT.split()[0] not in prompt


def test_ev252_english_ask_uses_production_system_prompt(
    locale_prompt_chat_client: tuple[TestClient, _CapturingMockLlmClient],
) -> None:
    """TC-257: language=en uses production.system_prompt in LLM prompt."""
    client, llm = locale_prompt_chat_client
    response = client.post(
        "/api/v1/ask",
        json={
            "question": "What are the food pantry hours?",
            "language": "en",
        },
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["language"] == "en"
    assert llm.prompts, "expected LLM generate call"
    prompt = llm.prompts[-1]
    assert _EN_MARKER in prompt
    assert _ES_MARKER not in prompt
