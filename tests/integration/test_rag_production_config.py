"""TC-133: ChatRAG reads active production config after promote."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.eval_config import EvalConfig

from tests.unit.rag.conftest import basis_vector, seed_corpus_with_embeddings

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.integration

_PROMOTED_PROMPT = "Integration promoted prompt for TC-133."


class _CapturingLlmClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        self.prompts.append(prompt)
        return "Promoted-config answer."

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = kwargs
        self.prompts.append(prompt)
        yield "Promoted-config answer."

    def close(self) -> None:
        return


@pytest.fixture
def promoted_config_chat_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, _CapturingLlmClient, str]:
    """Seed corpus + active production config; return chat client and prompt capture."""
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )
    seed_corpus_with_embeddings(
        database_url=database_url,
        match_substrings={"Food pantry": 0, "banco de alimentos": 2},
        default_index=1,
    )
    engine = create_engine(database_url)
    config = EvalConfig(
        top_k=3,
        min_retrieval_score=0.2,
        system_prompt=_PROMOTED_PROMPT,
        max_tokens=128,
        temperature=0.2,
        corpus_profile="fixture",
        model_id="qwen2.5:1.5b-instruct",
    ).model_dump(mode="json")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM rag_production_config"))
        conn.execute(
            text(
                """
                INSERT INTO rag_production_config (
                    id, config, config_version, is_active, promoted_at, promoted_by
                )
                VALUES (
                    :id,
                    CAST(:config AS jsonb),
                    1,
                    true,
                    NOW(),
                    :promoted_by
                )
                """
            ),
            {
                "id": uuid4(),
                "config": json.dumps(config),
                "promoted_by": uuid4(),
            },
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = ChatRagSettings(
        database_url=database_url,
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )
    llm = _CapturingLlmClient()
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: basis_vector(0),
        database_url=database_url,
        top_k=settings.top_k,
    )
    service = ChatRagService(
        retriever=retriever,
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
        config_engine=engine,
    )
    app = create_app(settings=settings, chat_service=service)
    return TestClient(app), llm, database_url


def test_tc133_chat_rag_uses_promoted_system_prompt(
    promoted_config_chat_client: tuple[TestClient, _CapturingLlmClient, str],
) -> None:
    """After DB promote, ask assembly uses promoted system_prompt."""
    client, llm, _database_url = promoted_config_chat_client
    response = client.post(
        "/api/v1/ask",
        json={"question": "When is the food pantry open?"},
    )
    assert response.status_code == HTTPStatus.OK
    assert llm.prompts, "expected LLM to receive a prompt"
    assert _PROMOTED_PROMPT in llm.prompts[0]
