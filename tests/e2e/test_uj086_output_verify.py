"""UJ-086 / TC-284-TC-288: Output verification + citations (F82)."""

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
from vecinita_rag.constants import HEDGE_DISCLAIMER_EN
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import EvalConfig

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_QUESTION = "When is the food pantry open?"
_ANSWER = "The pantry opens Monday at 9am."
_CHUNK_TEXT = "Food pantry hours: Monday 9am-12pm."


class _StubLlm:
    """Records answer vs judge prompts."""

    def __init__(self, *, judge_reply: str = "YES") -> None:
        self.judge_reply = judge_reply
        self.judge_prompts: list[str] = []
        self.answer_prompts: list[str] = []
        self.stream_calls = 0

    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = kwargs
        if "faithfulness judge" in prompt:
            self.judge_prompts.append(prompt)
            return self.judge_reply
        self.answer_prompts.append(prompt)
        return _ANSWER

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        self.stream_calls += 1
        yield _ANSWER

    def close(self) -> None:
        return


class _StubRetriever:
    def retrieve_chunks(  # noqa: PLR0913
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
                text=_CHUNK_TEXT,
                score=0.9,
                title="pantry",
                url="https://example.org/pantry",
                language="en",
            ),
        ]


def _build(
    *, verify_enabled: bool, judge_reply: str = "YES"
) -> tuple[ChatRagService, ChatRagSettings, _StubLlm]:
    llm = _StubLlm(judge_reply=judge_reply)
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://unused:unused@localhost/unused",
        top_k=3,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_output_verify=verify_enabled,
        rag_multi_query=False,
        rag_cache=False,
        rag_packer="p1",
    )
    service = ChatRagService(
        retriever=_StubRetriever(),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=settings,
    )
    return service, settings, llm


def test_uj086_ask_verify_on_adds_citations_and_judge() -> None:
    """TC-284 / TC-287: verify on → judge call + citation suffix."""
    service, settings, llm = _build(verify_enabled=True)
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer") == f"{_ANSWER} [1]"
    assert len(llm.judge_prompts) == 1
    assert _ANSWER in llm.judge_prompts[0]


def test_uj086_ask_verify_default_off_skips_judge() -> None:
    """TC-286 / AC-OV4: default verify off → no judge LLM call."""
    service, settings, llm = _build(verify_enabled=False)
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "answer") == _ANSWER
    assert llm.judge_prompts == []


def test_uj086_ask_verify_ungrounded_prepends_hedge() -> None:
    """TC-285 / AC-OV2: NO verdict → hedge + body + citations."""
    service, settings, llm = _build(verify_enabled=True, judge_reply="NO")
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        response = client.post("/api/v1/ask", json={"question": _QUESTION, "language": "en"})
    assert response.status_code == HTTPStatus.OK
    answer = json_str(response_json_object(response), "answer")
    assert answer.startswith(HEDGE_DISCLAIMER_EN)
    assert _ANSWER in answer
    assert answer.endswith("[1]")
    assert len(llm.judge_prompts) == 1


def test_uj086_stream_buffers_then_verifies() -> None:
    """TC-288 / AC-OV5: stream yields verified answer after buffer."""
    service, settings, llm = _build(verify_enabled=True)
    production = EvalConfig(top_k=3, min_retrieval_score=0.2)
    with patch.object(service, "_production_config", return_value=production):
        client = TestClient(create_app(settings=settings, chat_service=service))
        with client.stream(
            "POST",
            "/api/v1/ask/stream",
            json={"question": _QUESTION, "language": "en"},
        ) as response:
            assert response.status_code == HTTPStatus.OK
            body = "".join(response.iter_text())
    assert f'"token": "{_ANSWER} [1]"' in body
    assert llm.stream_calls == 1
    assert len(llm.judge_prompts) == 1
