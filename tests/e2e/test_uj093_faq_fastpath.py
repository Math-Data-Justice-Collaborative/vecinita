"""UJ-093 / TC-320-04: FAQ fast-path API e2e (F85 / EV-320)."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from fastapi.testclient import TestClient
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.e2e

_SEED = Path(__file__).resolve().parents[1] / "fixtures" / "faq" / "seed_faq.yaml"


class _BoomRetriever:
    def retrieve_chunks(self, *args: object, **kwargs: object) -> list[object]:
        _ = (args, kwargs)
        msg = "retriever must not run on FAQ bypass"
        raise AssertionError(msg)


class _BoomLlm:
    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        msg = "LLM must not run on FAQ bypass"
        raise AssertionError(msg)

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        msg = "LLM stream must not run on FAQ bypass"
        raise AssertionError(msg)
        yield ""  # pragma: no cover

    def close(self) -> None:
        return


class _EmptyRetriever:
    def retrieve_chunks(self, *args: object, **kwargs: object) -> list[object]:
        _ = (args, kwargs)
        return []


class _NoopLlm:
    def generate(self, prompt: str, **kwargs: object) -> str:
        _ = (prompt, kwargs)
        msg = "LLM should not be called for empty retrieval"
        raise AssertionError(msg)

    def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
        _ = (prompt, kwargs)
        msg = "LLM should not be called for empty retrieval"
        raise AssertionError(msg)
        yield ""  # pragma: no cover

    def close(self) -> None:
        return


def _settings(*, enabled: bool) -> ChatRagSettings:
    return ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=False,
        faq_fastpath_enabled=enabled,
        faq_store_path=str(_SEED),
    )


@pytest.fixture
def faq_client() -> TestClient:
    """Client with FAQ enabled and boom retriever/LLM (hit must bypass)."""
    service = ChatRagService(
        retriever=_BoomRetriever(),  # type: ignore[arg-type]
        llm_client=_BoomLlm(),  # type: ignore[arg-type]
        settings=_settings(enabled=True),
    )
    app = create_app(settings=_settings(enabled=True), chat_service=service)
    return TestClient(app)


@pytest.fixture
def miss_client() -> TestClient:
    """Client with FAQ enabled; miss falls through to empty retrieval."""
    service = ChatRagService(
        retriever=_EmptyRetriever(),  # type: ignore[arg-type]
        llm_client=_NoopLlm(),  # type: ignore[arg-type]
        settings=_settings(enabled=True),
    )
    app = create_app(settings=_settings(enabled=True), chat_service=service)
    return TestClient(app)


def test_uj093_ask_faq_hit_bypass(faq_client: TestClient) -> None:
    """POST /ask FAQ hit → faq_bypass, empty sources, canned answer."""
    response = faq_client.post(
        "/api/v1/ask",
        json={"question": "What is Vecinita?", "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["answer_path"] == "faq_bypass"
    assert body["cache_hit"] == "none"
    assert body["sources"] == []
    assert body["language"] == "en"
    assert "vecinita" in json_str(body, "answer").lower()


def test_uj093_ask_faq_miss_rag(miss_client: TestClient) -> None:
    """Non-FAQ ask uses RAG path (empty corpus → no-context)."""
    response = miss_client.post(
        "/api/v1/ask",
        json={"question": "Where is the nearest quantum flux clinic?", "language": "en"},
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert body["answer_path"] == "rag_llm"
    assert body["sources"] == []
    assert "corpus" in json_str(body, "answer").lower()


def test_uj093_stream_faq_hit(faq_client: TestClient) -> None:
    """SSE ask/stream FAQ hit emits answer + empty sources + answer_path."""
    with faq_client.stream(
        "POST",
        "/api/v1/ask/stream",
        json={"question": "Do I need immigration status?", "language": "en"},
    ) as response:
        assert response.status_code == HTTPStatus.OK
        events: list[dict[str, object]] = []
        for line in response.iter_lines():
            if not line or not line.startswith("data: "):
                continue
            events.append(as_json_object(cast("object", json.loads(line.removeprefix("data: ")))))
    tokens = [e["token"] for e in events if "token" in e]
    assert tokens
    sources_events = [e for e in events if "sources" in e]
    assert sources_events
    assert sources_events[0]["sources"] == []
    done = next(e for e in events if e.get("done") is True)
    assert done["answer_path"] == "faq_bypass"
    assert done["cache_hit"] == "none"
