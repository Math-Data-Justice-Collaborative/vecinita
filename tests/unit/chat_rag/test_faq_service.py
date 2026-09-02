"""TC-320-02 / TC-320-03: FAQ ask-path bypass skips retrieve + LLM (F85)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService
from vecinita_shared_schemas.chat_rag import AskRequest

if TYPE_CHECKING:
    from collections.abc import Iterator

_SEED = (
    Path(__file__).resolve().parents[3]
    / "apps"
    / "chat-rag-backend"
    / "vecinita_chat_rag_backend"
    / "faq"
    / "seed_faq.yaml"
)


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


def test_ask_faq_hit_skips_retrieve_and_llm() -> None:
    """FAQ hit returns canned answer with answer_path=faq_bypass and empty sources."""
    service = ChatRagService(
        retriever=_BoomRetriever(),  # type: ignore[arg-type]
        llm_client=_BoomLlm(),  # type: ignore[arg-type]
        settings=_settings(enabled=True),
    )
    result = service.ask(AskRequest(question="What is Vecinita?", language="en"))
    assert result.answer_path == "faq_bypass"
    assert result.cache_hit == "none"
    assert result.sources == []
    assert result.language == "en"
    assert "bilingual" in result.answer.lower() or "vecinita" in result.answer.lower()


def test_ask_faq_kill_switch_forces_rag() -> None:
    """Kill-switch off never bypasses even for FAQ variants."""
    called: list[str] = []

    class _CountingRetriever:
        def retrieve_chunks(self, *args: object, **kwargs: object) -> list[object]:
            _ = (args, kwargs)
            called.append("retrieve")
            return []

    class _CountingLlm:
        def generate(self, prompt: str, **kwargs: object) -> str:
            _ = (prompt, kwargs)
            called.append("llm")
            return "fallback"

        def generate_stream(self, prompt: str, **kwargs: object) -> Iterator[str]:
            _ = (prompt, kwargs)
            called.append("llm_stream")
            yield "fallback"

        def close(self) -> None:
            return

    service = ChatRagService(
        retriever=_CountingRetriever(),  # type: ignore[arg-type]
        llm_client=_CountingLlm(),  # type: ignore[arg-type]
        settings=_settings(enabled=False),
    )
    result = service.ask(AskRequest(question="What is Vecinita?", language="en"))
    assert result.answer_path == "rag_llm"
    assert "retrieve" in called
