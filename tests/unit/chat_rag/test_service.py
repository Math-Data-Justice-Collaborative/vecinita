"""Unit tests for ChatRagService orchestration."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch
from uuid import uuid4

from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import ChatRagService, _build_prompt, _to_ask_response
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest


def _chunk(*, language: str = "en") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        title="Community guide",
        url="https://example.com/guide",
        text="The clinic is open Monday through Friday.",
        score=0.88,
        language=language,
    )


class StubRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.calls: list[tuple[str, list[str] | None, str]] = []

    def retrieve_chunks(
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str = "en",
    ) -> list[RetrievedChunk]:
        self.calls.append((question, tag_slugs, language))
        if tag_slugs and not self.chunks:
            return []
        return self.chunks


class StubLlm:
    def __init__(self, *, answer: str = "Generated answer") -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def generate(self, prompt: str, *, max_tokens: int = 256) -> str:
        _ = max_tokens
        self.prompts.append(prompt)
        return self.answer

    def generate_stream(self, prompt: str, *, max_tokens: int = 256) -> Iterator[str]:
        _ = max_tokens
        self.prompts.append(prompt)
        yield "Stream"
        yield "ed"


def _service(
    *,
    chunks: list[RetrievedChunk],
    tag_infer: list[str] | None = None,
) -> ChatRagService:
    infer_fn = (lambda _question: tag_infer) if tag_infer is not None else None
    return ChatRagService(
        retriever=StubRetriever(chunks),  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        chat_max_tokens=64,
        tag_infer_fn=infer_fn,
    )


def test_build_prompt_includes_question_and_context() -> None:
    chunk = _chunk()
    prompt = _build_prompt("When is the clinic open?", [chunk])
    assert "When is the clinic open?" in prompt
    assert chunk.text in prompt
    assert "<|im_start|>assistant" in prompt


def test_to_ask_response_maps_spanish_language() -> None:
    response = _to_ask_response(
        RagAnswer(answer="Respuesta", language="es", sources=[_chunk(language="es")])
    )
    assert response.language == "es"
    assert response.sources[0].title == "Community guide"


def test_ask_returns_no_context_message_when_empty() -> None:
    service = _service(chunks=[])
    response = service.ask(AskRequest(question="Where is the clinic?"))
    assert "context" in response.answer.lower()
    assert response.sources == []


def test_ask_generates_answer_from_retrieved_chunks() -> None:
    service = _service(chunks=[_chunk()])
    response = service.ask(AskRequest(question="clinic hours"))
    assert response.answer
    assert len(response.sources) == 1


def test_ask_uses_explicit_language() -> None:
    service = _service(chunks=[])
    response = service.ask(
        AskRequest(question="¿Dónde está la clínica?", language="es"),
    )
    assert response.language == "es"


def test_ask_retries_without_tags_when_tag_filter_empty() -> None:
    class TagThenOpenRetriever(StubRetriever):
        def retrieve_chunks(
            self,
            question: str,
            *,
            tag_slugs: list[str] | None = None,
            language: str = "en",
        ) -> list[RetrievedChunk]:
            self.calls.append((question, tag_slugs, language))
            if tag_slugs:
                return []
            return [_chunk()]

    retriever = TagThenOpenRetriever([])
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        tag_infer_fn=lambda _q: ["housing"],
    )
    response = service.ask(AskRequest(question="housing help"))
    assert response.sources
    assert len(retriever.calls) == 2


def test_ask_stream_yields_no_context_when_empty() -> None:
    service = _service(chunks=[])
    tokens = list(service.ask_stream(AskRequest(question="unknown topic")))
    assert len(tokens) == 1


def test_ask_stream_yields_llm_tokens() -> None:
    service = _service(chunks=[_chunk()])
    tokens = list(service.ask_stream(AskRequest(question="clinic hours")))
    assert tokens == ["Stream", "ed"]


def test_retrieve_sources_maps_chunks() -> None:
    service = _service(chunks=[_chunk()])
    sources = service.retrieve_sources(AskRequest(question="clinic"))
    assert len(sources) == 1
    assert sources[0].score == 0.88


def test_from_settings_embed_and_tag_infer_fns() -> None:
    captured: dict[str, object] = {}

    class _EmbedClient:
        def __init__(self, url: str | None, *, timeout: float) -> None:
            captured["embed_url"] = url

        def embed(self, text: str) -> list[float]:
            captured["embed_text"] = text
            return [0.01] * 384

    class _LlmClient:
        def __init__(self, url: str | None, *, timeout: float) -> None:
            captured["llm_url"] = url

        def generate(self, prompt: str, *, max_tokens: int = 256) -> str:
            _ = (prompt, max_tokens)
            return "Generated"

        def generate_stream(self, prompt: str, *, max_tokens: int = 256):
            _ = (prompt, max_tokens)
            yield "Generated"

    class _TagClient:
        def __init__(self, _llm: object) -> None:
            pass

        def infer_query_tags(self, *, question: str, vocabulary: list[str]) -> list[str]:
            captured["tag_question"] = question
            return ["housing"]

    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=4,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
    )

    with (
        patch("vecinita_chat_rag_backend.service.EmbeddingClient", _EmbedClient),
        patch("vecinita_chat_rag_backend.service.LlmClient", _LlmClient),
        patch("vecinita_chat_rag_backend.service.LlmTagClient", _TagClient),
        patch("vecinita_chat_rag_backend.service.load_seed_vocabulary", return_value=[]),
        patch("vecinita_chat_rag_backend.service.vocabulary_slugs", return_value=["housing"]),
        patch("vecinita_chat_rag_backend.service.CorpusPgvectorRetriever") as mock_retriever,
    ):
        embed_fn_holder: dict[str, object] = {}

        def _capture_retriever(**kwargs: object) -> StubRetriever:
            embed_fn_holder["fn"] = kwargs.get("embed_fn")
            return StubRetriever([_chunk()])

        mock_retriever.side_effect = _capture_retriever
        service = ChatRagService.from_settings(settings)
        service.ask(AskRequest(question="housing help"))

    embed_fn = embed_fn_holder.get("fn")
    assert callable(embed_fn)
    assert embed_fn("housing help") == [0.01] * 384  # type: ignore[operator]
    assert captured["tag_question"] == "housing help"
