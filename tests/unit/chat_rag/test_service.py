"""Unit tests for ChatRagService orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch
from uuid import uuid4

from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_chat_rag_backend.service import (
    ChatRagService,
    _build_prompt,  # pyright: ignore[reportPrivateUsage]
    _to_ask_response,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_rag.cache import AnswerCache, CachedAnswer
from vecinita_rag.rerank import CallableCrossEncoderScorer
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest
from vecinita_shared_schemas.eval_config import EvalConfig

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

_EXPECTED_RETRIEVER_CALLS = 2
_CHUNK_SCORE = 0.88
_CE_TOP_K = 2


def _chunk(
    *,
    language: str = "en",
    text: str = "The clinic is open Monday through Friday.",
    title: str = "Community guide",
) -> RetrievedChunk:
    """Chunk."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        title=title,
        url="https://example.com/guide",
        text=text,
        score=0.88,
        language=language,
    )


class StubRetriever:
    """StubRetriever."""

    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        """Init  ."""
        self.chunks = chunks
        self.calls: list[tuple[str, list[str] | None, str | None]] = []

    def retrieve_chunks(
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve chunks."""
        _ = (top_k, score_threshold)
        self.calls.append((question, tag_slugs, language))
        if tag_slugs and not self.chunks:
            return []
        return self.chunks


class EmptySameLangStubRetriever:
    """Return empty for same-lang filter; cross-lang chunk when unfiltered."""

    def __init__(self, *, fallback: RetrievedChunk) -> None:
        """Init with the unfiltered fallback chunk."""
        self.fallback = fallback
        self.languages: list[str | None] = []

    def retrieve_chunks(
        self,
        question: str,
        *,
        tag_slugs: list[str] | None = None,
        language: str | None = "en",
        top_k: int | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve chunks with language-aware empty-hit behavior."""
        _ = (question, tag_slugs, top_k, score_threshold)
        self.languages.append(language)
        if language is None:
            return [self.fallback]
        return []


class StubLlm:
    """StubLlm."""

    def __init__(self, *, answer: str = "Generated answer") -> None:
        """Init  ."""
        self.answer = answer
        self.prompts: list[str] = []
        self.model_ids: list[str | None] = []

    def generate(
        self,
        prompt: str,
        *,
        max_tokens: int = 256,
        model_id: str | None = None,
    ) -> str:
        """Generate."""
        _ = max_tokens
        self.prompts.append(prompt)
        self.model_ids.append(model_id)
        return self.answer

    def generate_stream(
        self,
        prompt: str,
        *,
        max_tokens: int = 256,
        model_id: str | None = None,
    ) -> Iterator[str]:
        """Generate stream."""
        _ = (max_tokens, model_id)
        self.prompts.append(prompt)
        yield "Stream"
        yield "ed"


def _service(
    *,
    chunks: list[RetrievedChunk],
    tag_infer: list[str] | None = None,
    llm_model_id: str | None = "qwen2.5:1.5b-instruct",
) -> ChatRagService:
    """Service."""
    tag_infer_fn: Callable[[str], list[str]] | None = None
    if tag_infer is not None:
        inferred = tag_infer

        def _infer_tags(_question: str) -> list[str]:
            return inferred

        tag_infer_fn = _infer_tags
    return ChatRagService(
        retriever=StubRetriever(chunks),  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        chat_max_tokens=64,
        tag_infer_fn=tag_infer_fn,
        llm_model_id=llm_model_id,
    )


def test_build_prompt_includes_question_and_context() -> None:
    """Test build prompt includes question and P1 Source/URL packed context (F42)."""
    chunk = _chunk()
    prompt = _build_prompt(
        "When is the clinic open?",
        [chunk],
        system_prompt="Use only the context below.",
    )
    assert "When is the clinic open?" in prompt
    assert chunk.text in prompt
    assert "Source: Community guide" in prompt
    assert "URL: https://example.com/guide" in prompt
    assert "<|im_start|>assistant" in prompt


def test_to_ask_response_maps_spanish_language() -> None:
    """Test to ask response maps spanish language."""
    response = _to_ask_response(
        RagAnswer(answer="Respuesta", language="es", sources=[_chunk(language="es")])
    )
    assert response.language == "es"
    assert response.sources[0].title == "Community guide"


def test_ask_returns_no_context_message_when_empty() -> None:
    """Test ask returns no context message when empty."""
    service = _service(chunks=[])
    response = service.ask(AskRequest(question="Where is the clinic?"))
    assert "context" in response.answer.lower()
    assert response.sources == []


def test_ask_generates_answer_from_retrieved_chunks() -> None:
    """Test ask generates answer from retrieved chunks and forwards model_id."""
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([_chunk()]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        chat_max_tokens=64,
        llm_model_id="llama3.2:3b",
    )
    response = service.ask(AskRequest(question="clinic hours"))
    assert response.answer
    assert len(response.sources) == 1
    assert llm.model_ids == ["qwen2.5:1.5b-instruct"]


def test_ask_uses_explicit_language() -> None:
    """Test ask uses explicit language."""
    service = _service(chunks=[])
    response = service.ask(
        AskRequest(question="¿Dónde está la clínica?", language="es"),
    )
    assert response.language == "es"


def test_ask_retries_without_tags_when_tag_filter_empty() -> None:
    """Test ask retries without tags when tag filter empty."""

    class TagThenOpenRetriever(StubRetriever):
        """TagThenOpenRetriever."""

        def retrieve_chunks(
            self,
            question: str,
            *,
            tag_slugs: list[str] | None = None,
            language: str | None = "en",
            top_k: int | None = None,
            score_threshold: float | None = None,
        ) -> list[RetrievedChunk]:
            """Retrieve chunks."""
            _ = (top_k, score_threshold)
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
    assert len(retriever.calls) == _EXPECTED_RETRIEVER_CALLS


def test_ask_stream_yields_no_context_when_empty() -> None:
    """Test ask stream yields no context when empty."""
    service = _service(chunks=[])
    tokens = list(service.ask_stream(AskRequest(question="unknown topic")))
    assert len(tokens) == 1


def test_ask_stream_yields_llm_tokens() -> None:
    """Test ask stream yields llm tokens."""
    service = _service(chunks=[_chunk()])
    tokens = list(service.ask_stream(AskRequest(question="clinic hours")))
    assert tokens == ["Stream", "ed"]


def test_retrieve_sources_maps_chunks() -> None:
    """Test retrieve sources maps chunks."""
    service = _service(chunks=[_chunk()])
    sources = service.retrieve_sources(AskRequest(question="clinic"))
    assert len(sources) == 1
    assert sources[0].score == _CHUNK_SCORE


def test_retrieve_soft_language_fallback_when_flag_on() -> None:
    """T96.3: flag on + empty same-lang first pass retries unfiltered (AC-BB5)."""
    fallback = _chunk(language="es")
    retriever = EmptySameLangStubRetriever(fallback=fallback)
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_soft_language_fallback=True,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        settings=settings,
    )
    sources = service.retrieve_sources(
        AskRequest(question="When does the food pantry open?", language="en"),
    )
    assert len(sources) == 1
    assert "en" in retriever.languages
    assert None in retriever.languages


def test_retrieve_soft_language_default_off_skips_unfiltered_retry() -> None:
    """T96.3 / TC-181: default flag off keeps L0-strict (no language=None pass)."""
    fallback = _chunk(language="es")
    retriever = EmptySameLangStubRetriever(fallback=fallback)
    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_soft_language_fallback=False,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=retriever,  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        settings=settings,
    )
    sources = service.retrieve_sources(
        AskRequest(question="When does the food pantry open?", language="en"),
    )
    assert sources == []
    assert None not in retriever.languages
    assert retriever.languages == ["en"]


def test_retrieve_ce_flag_off_skips_scorer() -> None:
    """T97.3 / TC-183: default CE flag off never calls the mockable scorer."""
    calls: list[str] = []

    def _score(query: str, passages: Sequence[str]) -> list[float]:
        calls.append(query)
        return [0.9 for _ in passages]

    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=_CE_TOP_K,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_rerank_ce=False,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=StubRetriever(  # type: ignore[arg-type]
            [
                _chunk(text="a", title="a"),
                _chunk(text="b", title="b"),
                _chunk(text="c", title="c"),
            ]
        ),
        llm_client=StubLlm(),  # type: ignore[arg-type]
        settings=settings,
        ce_scorer=CallableCrossEncoderScorer(_score),
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=_CE_TOP_K)):
        sources = service.retrieve_sources(AskRequest(question="clinic hours", language="en"))
    assert len(sources) == _CE_TOP_K
    assert calls == []


def test_retrieve_ce_flag_on_reranks_with_scorer() -> None:
    """T97.3 / TC-182: flag on + mock scorer keeps ≤ top_k by CE score."""
    low = _chunk(text="low", title="low")
    high = _chunk(text="high", title="high")
    mid = _chunk(text="mid", title="mid")

    def _score(_query: str, passages: Sequence[str]) -> list[float]:
        weights = {"high": 0.95, "mid": 0.5, "low": 0.1}
        return [weights.get(text, 0.0) for text in passages]

    settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=_CE_TOP_K,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_rerank_ce=True,
        rag_rerank_ce_top_n=3,
        rag_multi_query=False,
        rag_cache=False,
    )
    service = ChatRagService(
        retriever=StubRetriever([low, mid, high]),  # type: ignore[arg-type]
        llm_client=StubLlm(),  # type: ignore[arg-type]
        settings=settings,
        ce_scorer=CallableCrossEncoderScorer(_score),
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=_CE_TOP_K)):
        sources = service.retrieve_sources(AskRequest(question="clinic hours", language="en"))
    assert len(sources) == _CE_TOP_K
    assert [source.title for source in sources] == ["high", "mid"]


def _cache_settings(*, semantic: bool = False) -> ChatRagSettings:
    """ChatRAG settings with F43 cache on and H7 off for focused cache tests."""
    return ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        rag_cache=True,
        rag_cache_semantic=semantic,
        rag_multi_query=False,
    )


def test_ask_cache_exact_hit_skips_llm() -> None:
    """F43 ask: exact cache hit returns cached answer without calling LLM."""
    cache = AnswerCache()
    chunk = _chunk()
    cache.store_answer(
        "clinic hours",
        "en",
        CachedAnswer(
            answer="Cached clinic hours",
            language="en",
            sources=(chunk,),
            query_embedding=None,
        ),
    )
    llm = StubLlm(answer="should-not-run")
    service = ChatRagService(
        retriever=StubRetriever([chunk]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        response = service.ask(AskRequest(question="clinic hours", language="en"))
    assert response.answer == "Cached clinic hours"
    assert response.cache_hit == "exact"
    assert llm.prompts == []


def test_ask_cache_retrieve_tier_synthesizes_and_stores_answer() -> None:
    """F43 ask: retrieve-tier hit synthesizes from cached chunks then stores answer."""
    cache = AnswerCache()
    chunk = _chunk(text="cached retrieve body")
    cache.store_retrieve("clinic hours", "en", (chunk,))
    llm = StubLlm(answer="Synthesized from retrieve cache")
    service = ChatRagService(
        retriever=StubRetriever([]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        response = service.ask(AskRequest(question="clinic hours", language="en"))
    assert response.answer == "Synthesized from retrieve cache"
    assert response.cache_hit == "retrieve"
    assert llm.prompts  # generate was called
    # Warm exact hit on second ask
    llm.prompts.clear()
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        warm = service.ask(AskRequest(question="clinic hours", language="en"))
    assert warm.cache_hit == "exact"
    assert llm.prompts == []


def test_stream_ask_cache_exact_hit_yields_cached_tokens() -> None:
    """F43 stream_ask: exact hit returns single-token iterator without LLM stream."""
    cache = AnswerCache()
    chunk = _chunk()
    cache.store_answer(
        "clinic hours",
        "en",
        CachedAnswer(
            answer="Stream cached",
            language="en",
            sources=(chunk,),
        ),
    )
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([chunk]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        session = service.stream_ask(AskRequest(question="clinic hours", language="en"))
    assert session.cache_hit == "exact"
    assert list(session.tokens) == ["Stream cached"]
    assert llm.prompts == []


def test_stream_ask_cache_miss_stores_after_token_stream() -> None:
    """F43 stream_ask: miss retrieves, streams tokens, then stores answer."""
    cache = AnswerCache()
    chunk = _chunk()
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([chunk]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        session = service.stream_ask(AskRequest(question="clinic hours", language="en"))
    assert session.cache_hit == "none"
    assert "".join(session.tokens) == "Streamed"
    assert llm.prompts
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        warm = service.stream_ask(AskRequest(question="clinic hours", language="en"))
    assert warm.cache_hit == "exact"


def test_stream_ask_cache_empty_retrieve_returns_no_context() -> None:
    """F43 stream_ask: empty retrieve stores no-context message and yields it."""
    cache = AnswerCache()
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        session = service.stream_ask(AskRequest(question="no hits here", language="en"))
    tokens = list(session.tokens)
    assert len(tokens) == 1
    assert "context" in tokens[0].lower()
    assert llm.prompts == []


def test_stream_ask_retrieve_tier_hit_streams_from_cached_chunks() -> None:
    """F43 stream_ask: retrieve-tier hit uses cached chunks (cache_hit=retrieve)."""
    cache = AnswerCache()
    chunk = _chunk(text="stream retrieve body")
    cache.store_retrieve("clinic hours", "en", (chunk,))
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        session = service.stream_ask(AskRequest(question="clinic hours", language="en"))
    assert session.cache_hit == "retrieve"
    assert "".join(session.tokens) == "Streamed"
    assert llm.prompts


def test_ask_cache_miss_empty_retrieve_returns_no_context_none_hit() -> None:
    """F43 ask: cache enabled + empty retrieve yields no-context with cache_hit=none."""
    cache = AnswerCache()
    llm = StubLlm()
    service = ChatRagService(
        retriever=StubRetriever([]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        response = service.ask(AskRequest(question="no hits here", language="en"))
    assert "context" in response.answer.lower()
    assert response.cache_hit == "none"
    assert llm.prompts == []


def test_ask_with_semantic_cache_uses_retriever_embed_fn() -> None:
    """F43: semantic-on ask embeds via retriever.embed_fn for cascade lookup."""

    class _EmbedRetriever(StubRetriever):
        def embed_fn(self, question: str) -> list[float]:
            return [1.0, 0.0] if question else [0.0, 0.0]

    cache = AnswerCache(semantic_threshold=0.5)
    chunk = _chunk()
    cache.store_answer(
        "warm clinic",
        "en",
        CachedAnswer(
            answer="Semantic cached",
            language="en",
            sources=(chunk,),
            query_embedding=(1.0, 0.0),
        ),
    )
    llm = StubLlm(answer="should-not-run")
    service = ChatRagService(
        retriever=_EmbedRetriever([chunk]),  # type: ignore[arg-type]
        llm_client=llm,  # type: ignore[arg-type]
        settings=_cache_settings(semantic=True),
        answer_cache=cache,
    )
    with patch.object(service, "_production_config", return_value=EvalConfig(top_k=5)):
        response = service.ask(AskRequest(question="near clinic", language="en"))
    assert response.cache_hit == "semantic"
    assert response.answer == "Semantic cached"
    assert llm.prompts == []


def test_from_settings_embed_and_tag_infer_fns() -> None:
    """Test from settings embed and tag infer fns."""
    captured: dict[str, object] = {}

    class _EmbedClient:
        """EmbedClient."""

        def __init__(self, url: str | None, *, timeout: float) -> None:
            """Init  ."""
            _ = timeout
            captured["embed_url"] = url

        def embed(self, text: str) -> list[float]:
            """Embed."""
            captured["embed_text"] = text
            return [0.01] * 384

    class _LlmClient:
        """LlmClient."""

        def __init__(
            self,
            url: str | None,
            *,
            timeout: float,
            model_id: str | None = None,
            require_proxy_key: bool = False,
        ) -> None:
            """Init  ."""
            _ = (timeout, model_id, require_proxy_key)
            captured["llm_url"] = url
            captured["require_proxy_key"] = require_proxy_key

        def generate(
            self,
            prompt: str,
            *,
            max_tokens: int = 256,
            model_id: str | None = None,
        ) -> str:
            """Generate."""
            _ = (prompt, max_tokens, model_id)
            return "Generated"

        def generate_stream(
            self,
            prompt: str,
            *,
            max_tokens: int = 256,
            model_id: str | None = None,
        ) -> Iterator[str]:
            """Generate stream."""
            _ = (prompt, max_tokens, model_id)
            yield "Generated"

    class _TagClient:
        """TagClient."""

        def __init__(self, _llm: object) -> None:
            """Init  ."""

        def infer_query_tags(self, *, question: str, vocabulary: list[str]) -> list[str]:
            """Infer query tags."""
            _ = vocabulary
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
        patch("vecinita_chat_rag_backend.service.create_engine"),
        patch(
            "vecinita_chat_rag_backend.service.load_active_rag_config",
            return_value=EvalConfig(),
        ),
        patch("vecinita_chat_rag_backend.service.CorpusPgvectorRetriever") as mock_retriever,
    ):
        embed_fn_holder: dict[str, object] = {}

        def _capture_retriever(**kwargs: object) -> StubRetriever:
            """Capture retriever."""
            embed_fn_holder["fn"] = kwargs.get("embed_fn")
            return StubRetriever([_chunk()])

        mock_retriever.side_effect = _capture_retriever
        service = ChatRagService.from_settings(settings)
        service.ask(AskRequest(question="housing help"))

    embed_fn = embed_fn_holder.get("fn")
    assert callable(embed_fn)
    assert embed_fn("housing help") == [0.01] * 384  # type: ignore[operator]
    assert captured["tag_question"] == "housing help"
    assert captured["require_proxy_key"] is True
