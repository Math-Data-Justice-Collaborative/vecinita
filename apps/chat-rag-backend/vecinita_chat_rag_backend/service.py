"""ChatRAG orchestration: retrieve → generate (F1, F4, F5, F6, F22)."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from sqlalchemy import create_engine
from vecinita_embedding_client import EmbeddingClient
from vecinita_llm_client import LlmClient, format_instruct_prompt
from vecinita_rag.cache import (
    AnswerCache,
    CachedAnswer,
    CacheHitKind,
    CascadeRequest,
    cascade_lookup,
)
from vecinita_rag.engine import answer_from_chunks
from vecinita_rag.es_esl_supplement import (
    merge_es_esl_retrieval_for_r6,
    should_supplement_en_for_es_esl_query,
)
from vecinita_rag.language import detect_query_language, no_context_message
from vecinita_rag.multi_query import merge_multi_query_hits, multi_query_retrieve
from vecinita_rag.packing import PackerMode, pack_chunks
from vecinita_rag.query_refine import refine_queries_llm
from vecinita_rag.rerank import CrossEncoderScorer, rerank_with_scorer
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.soft_language import soft_language_retrieve
from vecinita_rag.tag_inference import TagInferFn, resolve_retrieval_tags
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_rerank_client import RerankClient
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source
from vecinita_shared_schemas.eval_config import EvalConfig, resolve_system_prompt_for_language
from vecinita_tagging.llm_client import LlmTagClient
from vecinita_tagging.vocabulary import load_seed_vocabulary, vocabulary_slugs

from vecinita_chat_rag_backend.rag_production_config import load_active_rag_config

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from vecinita_chat_rag_backend.config import ChatRagSettings

EmbedFn = Callable[[str], list[float]]
CacheHit = Literal["none", "exact", "semantic", "retrieve"]


def _cache_hit_label(kind: CacheHitKind) -> CacheHit:
    """Map package enum to OpenAPI cache_hit literal."""
    mapping: dict[CacheHitKind, CacheHit] = {
        CacheHitKind.NONE: "none",
        CacheHitKind.EXACT: "exact",
        CacheHitKind.SEMANTIC: "semantic",
        CacheHitKind.RETRIEVE: "retrieve",
    }
    return mapping[kind]


def _build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    system_prompt: str,
    packer: PackerMode = "p3",
    context_max_chars: int = 3500,
) -> str:
    """Build instruct prompt via shared HF chat-template helper (RD-167 / TC-145 / F42)."""
    context = pack_chunks(chunks, mode=packer, max_chars=context_max_chars)
    user = f"Context:\n{context}\n\nQuestion: {question}"
    return format_instruct_prompt(system=system_prompt, user=user)


def _to_ask_response(
    result: RagAnswer,
    *,
    cache_hit: CacheHit = "none",
) -> AskResponse:
    sources = [
        Source(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            url=chunk.url,
            score=chunk.score,
            source_domain=chunk.source_domain,
            source_path=chunk.source_path,
            parent_url=chunk.parent_url,
            canonical_url=chunk.canonical_url,
        )
        for chunk in result.sources
    ]
    language: Literal["en", "es"] = "es" if result.language == "es" else "en"
    return AskResponse(
        answer=result.answer,
        language=language,
        sources=sources,
        cache_hit=cache_hit,
    )


def _cached_to_rag_answer(cached: CachedAnswer) -> RagAnswer:
    return RagAnswer(
        answer=cached.answer,
        language=cached.language,
        sources=list(cached.sources),
    )


def _sources_from_chunks(chunks: Sequence[RetrievedChunk]) -> list[Source]:
    return [
        Source(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            url=chunk.url,
            score=chunk.score,
            source_domain=chunk.source_domain,
            source_path=chunk.source_path,
            parent_url=chunk.parent_url,
            canonical_url=chunk.canonical_url,
        )
        for chunk in chunks
    ]


@dataclass
class AskStreamSession:
    """SSE ingredients: sources, cache_hit, and token iterator (F43)."""

    sources: list[Source]
    cache_hit: CacheHit
    tokens: Iterator[str]


class ChatRagService:
    """Orchestrate retrieval and LLM answer generation for /ask endpoints."""

    def __init__(  # noqa: PLR0913 — wiring retriever, LLM, optional production config reader
        self,
        *,
        retriever: CorpusPgvectorRetriever,
        llm_client: LlmClient,
        chat_max_tokens: int = 256,
        tag_infer_fn: TagInferFn | None = None,
        llm_model_id: str | None = None,
        settings: ChatRagSettings | None = None,
        config_engine: Engine | None = None,
        answer_cache: AnswerCache | None = None,
        ce_scorer: CrossEncoderScorer | None = None,
    ) -> None:
        """Wire retrieval, LLM, and optional tag inference for ask flows."""
        self._retriever = retriever
        self._llm = llm_client
        self._chat_max_tokens = chat_max_tokens
        self._tag_infer_fn = tag_infer_fn
        self._llm_model_id = llm_model_id
        self._settings = settings
        self._config_engine = config_engine
        self._answer_cache = answer_cache
        self._ce_scorer = ce_scorer
        if self._answer_cache is None and settings is not None and settings.rag_cache:
            self._answer_cache = AnswerCache(
                ttl_s=settings.rag_cache_ttl_s,
                max_entries=settings.rag_cache_max_entries,
                semantic_threshold=settings.rag_cache_semantic_threshold,
            )

    @classmethod
    def from_settings(cls, settings: ChatRagSettings) -> ChatRagService:
        """Construct service clients and retriever from ChatRAG settings."""
        embed_client = EmbeddingClient(
            settings.embed_url,
            timeout=settings.request_timeout_s,
        )
        llm_client = LlmClient(
            settings.llm_url,
            timeout=settings.request_timeout_s,
            model_id=settings.llm_model_id,
            require_proxy_key=True,  # RD-165 — Modal /generate requires proxy key
        )
        tag_client = LlmTagClient(llm_client)
        vocabulary = vocabulary_slugs(load_seed_vocabulary())

        def embed_fn(text: str) -> list[float]:
            return embed_client.embed(text)

        def tag_infer_fn(question: str) -> list[str]:
            return tag_client.infer_query_tags(question=question, vocabulary=vocabulary)

        retriever = CorpusPgvectorRetriever(
            embed_fn=embed_fn,
            database_url=settings.database_url,
            top_k=settings.top_k,
            score_threshold=settings.min_retrieval_score,
        )
        config_engine = create_engine(settings.database_url)
        ce_scorer: CrossEncoderScorer | None = None
        if settings.rag_rerank_ce and settings.rerank_url:
            ce_scorer = RerankClient(
                settings.rerank_url,
                timeout=settings.request_timeout_s,
            )
        return cls(
            retriever=retriever,
            llm_client=llm_client,
            chat_max_tokens=settings.chat_max_tokens,
            tag_infer_fn=tag_infer_fn,
            llm_model_id=settings.llm_model_id,
            settings=settings,
            config_engine=config_engine,
            ce_scorer=ce_scorer,
        )

    def _effective_language(self, request: AskRequest) -> str:
        if request.language is not None:
            return request.language
        return detect_query_language(request.question)

    def _retrieval_tags(self, request: AskRequest) -> list[str] | None:
        return resolve_retrieval_tags(
            question=request.question,
            selected_tags=request.tags or None,
            infer_fn=self._tag_infer_fn,
        )

    def _production_config(self) -> EvalConfig:
        if self._settings is None or self._config_engine is None:
            return EvalConfig()
        return load_active_rag_config(self._config_engine, self._settings)

    def _rag_packing(self) -> tuple[bool, int, PackerMode, int]:
        """Return (multi_query, count, packer, max_chars) from settings or defaults."""
        if self._settings is None:
            return True, 3, "p3", 3500
        return (
            self._settings.rag_multi_query,
            self._settings.rag_multi_query_count,
            self._settings.rag_packer,
            self._settings.rag_context_max_chars,
        )

    def _cache_enabled(self) -> bool:
        return (
            self._answer_cache is not None
            and self._settings is not None
            and self._settings.rag_cache
        )

    def _query_embedding(self, question: str) -> tuple[float, ...] | None:
        """Embed query for semantic cache when F43 semantic tier is on."""
        if self._settings is None or not self._settings.rag_cache_semantic:
            return None
        embed_fn = getattr(self._retriever, "embed_fn", None)
        if not callable(embed_fn):
            return None
        return tuple(cast("EmbedFn", embed_fn)(question))

    def _retrieval_questions(self, request: AskRequest) -> list[str]:
        """F81 optional LLM refinement; always includes the raw question first."""
        language = self._effective_language(request)
        raw = request.question.strip()
        if not raw:
            return []
        if self._settings is None or not self._settings.rag_query_refine:
            return [raw]

        def _generate(prompt: str) -> str:
            return self._llm.generate(prompt, max_tokens=128)

        refined = refine_queries_llm(
            raw,
            locale=language,
            generate_fn=_generate,
            count=self._settings.rag_query_refine_count,
        )
        return refined or [raw]

    def _retrieve(
        self,
        request: AskRequest,
        *,
        top_k: int,
        min_retrieval_score: float,
    ) -> list[RetrievedChunk]:
        language = self._effective_language(request)
        tag_slugs = self._retrieval_tags(request)
        multi_query, multi_count, _, _ = self._rag_packing()
        soft_fallback = (
            self._settings.rag_soft_language_fallback if self._settings is not None else False
        )
        ce_enabled = (
            self._settings is not None
            and self._settings.rag_rerank_ce
            and self._ce_scorer is not None
        )
        retrieve_k = top_k
        if ce_enabled and self._settings is not None:
            retrieve_k = max(top_k, self._settings.rag_rerank_ce_top_n)

        def _retrieve_lang(question: str, lang: str | None) -> list[RetrievedChunk]:
            chunks = self._retriever.retrieve_chunks(
                question,
                tag_slugs=tag_slugs,
                language=lang,
                top_k=retrieve_k,
                score_threshold=min_retrieval_score,
            )
            if not chunks and tag_slugs:
                chunks = self._retriever.retrieve_chunks(
                    question,
                    tag_slugs=None,
                    language=lang,
                    top_k=retrieve_k,
                    score_threshold=min_retrieval_score,
                )
            return chunks

        def _retrieve_once(question: str) -> list[RetrievedChunk]:
            chunks = soft_language_retrieve(
                question,
                language=language,
                retrieve_fn=_retrieve_lang,
                enabled=soft_fallback,
            ).chunks
            if should_supplement_en_for_es_esl_query(
                language=language,
                question=question,
                tag_slugs=tag_slugs,
            ):
                en_chunks = _retrieve_lang(question, "en")
                chunks = merge_es_esl_retrieval_for_r6(
                    chunks,
                    en_chunks,
                    top_k=retrieve_k,
                )
            return chunks

        questions = self._retrieval_questions(request)
        groups: list[list[RetrievedChunk]] = []
        for question_text in questions:
            sub_request = request.model_copy(update={"question": question_text})
            sub_chunks = multi_query_retrieve(
                sub_request.question,
                locale=language,
                top_k=retrieve_k,
                retrieve_fn=_retrieve_once,
                enabled=multi_query,
                count=multi_count,
            )
            groups.append(sub_chunks)
        chunks = merge_multi_query_hits(groups, top_k=retrieve_k)
        if ce_enabled and self._ce_scorer is not None:
            return rerank_with_scorer(
                request.question,
                chunks,
                top_k=top_k,
                scorer=self._ce_scorer,
                score_threshold=min_retrieval_score,
            )
        return chunks

    def _synthesize(
        self,
        request: AskRequest,
        chunks: Sequence[RetrievedChunk],
        *,
        language: str,
        production: EvalConfig,
        query_embedding: Sequence[float] | None,
    ) -> CachedAnswer:
        _, _, packer, max_chars = self._rag_packing()
        if not chunks:
            return CachedAnswer(
                answer=no_context_message(language),
                language=language,
                sources=(),
                query_embedding=tuple(query_embedding) if query_embedding is not None else None,
            )
        chunk_list = list(chunks)
        prompt = _build_prompt(
            request.question,
            chunk_list,
            system_prompt=resolve_system_prompt_for_language(language, production),
            packer=packer,
            context_max_chars=max_chars,
        )
        model_id = production.model_id or self._llm_model_id
        answer_text = self._llm.generate(
            prompt,
            max_tokens=production.max_tokens,
            model_id=model_id,
        )
        result = answer_from_chunks(request.question, chunk_list, answer_text=answer_text)
        return CachedAnswer(
            answer=result.answer,
            language=language,
            sources=tuple(result.sources),
            query_embedding=tuple(query_embedding) if query_embedding is not None else None,
        )

    def ask(self, request: AskRequest) -> AskResponse:
        """Retrieve context and generate a non-streaming answer (F43 cache cascade)."""
        production = self._production_config()
        language = self._effective_language(request)
        if not self._cache_enabled():
            return self._ask_uncached(request, production=production, language=language)

        cache = self._answer_cache
        if cache is None:  # pragma: no cover — guarded by _cache_enabled
            return self._ask_uncached(request, production=production, language=language)

        chunks_holder: list[RetrievedChunk] = []
        query_embedding = self._query_embedding(request.question)

        def retrieve() -> list[RetrievedChunk]:
            chunks = self._retrieve(
                request,
                top_k=production.top_k,
                min_retrieval_score=production.min_retrieval_score,
            )
            chunks_holder.clear()
            chunks_holder.extend(chunks)
            return chunks

        def generate() -> CachedAnswer:
            return self._synthesize(
                request,
                chunks_holder,
                language=language,
                production=production,
                query_embedding=query_embedding,
            )

        hit, cached, cached_chunks = cascade_lookup(
            cache,
            CascadeRequest(
                query=request.question,
                locale=language,
                query_embedding=query_embedding,
                retrieve=retrieve,
                generate=generate,
            ),
        )
        if cached is not None:
            return _to_ask_response(
                _cached_to_rag_answer(cached),
                cache_hit=_cache_hit_label(hit),
            )
        if hit == CacheHitKind.RETRIEVE and cached_chunks is not None:
            synthesized = self._synthesize(
                request,
                cached_chunks,
                language=language,
                production=production,
                query_embedding=query_embedding,
            )
            cache.store_answer(request.question, language, synthesized)
            return _to_ask_response(
                _cached_to_rag_answer(synthesized),
                cache_hit="retrieve",
            )
        return _to_ask_response(
            RagAnswer(
                answer=no_context_message(language),
                language=language,
                sources=[],
            ),
            cache_hit="none",
        )

    def _ask_uncached(
        self,
        request: AskRequest,
        *,
        production: EvalConfig,
        language: str,
    ) -> AskResponse:
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        synthesized = self._synthesize(
            request,
            chunks,
            language=language,
            production=production,
            query_embedding=None,
        )
        return _to_ask_response(_cached_to_rag_answer(synthesized), cache_hit="none")

    def stream_ask(self, request: AskRequest) -> AskStreamSession:
        """Prepare SSE stream with sources and cache_hit (F43)."""
        production = self._production_config()
        language = self._effective_language(request)
        if not self._cache_enabled():
            return self._stream_uncached(request, production=production, language=language)

        cache = self._answer_cache
        if cache is None:  # pragma: no cover
            return self._stream_uncached(request, production=production, language=language)

        query_embedding = self._query_embedding(request.question)
        hit, cached, cached_chunks = cascade_lookup(
            cache,
            CascadeRequest(
                query=request.question,
                locale=language,
                query_embedding=query_embedding,
            ),
        )
        if cached is not None:
            return AskStreamSession(
                sources=_sources_from_chunks(cached.sources),
                cache_hit=_cache_hit_label(hit),
                tokens=iter((cached.answer,)),
            )

        chunks: list[RetrievedChunk]
        cache_hit: CacheHit = "none"
        if hit == CacheHitKind.RETRIEVE and cached_chunks is not None:
            chunks = list(cached_chunks)
            cache_hit = "retrieve"
        else:
            chunks = self._retrieve(
                request,
                top_k=production.top_k,
                min_retrieval_score=production.min_retrieval_score,
            )
            cache.store_retrieve(request.question, language, chunks)

        if not chunks:
            message = no_context_message(language)
            empty = CachedAnswer(
                answer=message,
                language=language,
                sources=(),
                query_embedding=tuple(query_embedding) if query_embedding is not None else None,
            )
            cache.store_answer(request.question, language, empty)
            return AskStreamSession(
                sources=[],
                cache_hit=cache_hit,
                tokens=iter((message,)),
            )

        _, _, packer, max_chars = self._rag_packing()
        prompt = _build_prompt(
            request.question,
            chunks,
            system_prompt=resolve_system_prompt_for_language(language, production),
            packer=packer,
            context_max_chars=max_chars,
        )
        model_id = production.model_id or self._llm_model_id
        parts: list[str] = []

        def _token_stream() -> Iterator[str]:
            for token in self._llm.generate_stream(
                prompt,
                max_tokens=production.max_tokens,
                model_id=model_id,
            ):
                parts.append(token)
                yield token
            cache.store_answer(
                request.question,
                language,
                CachedAnswer(
                    answer="".join(parts),
                    language=language,
                    sources=tuple(chunks),
                    query_embedding=(
                        tuple(query_embedding) if query_embedding is not None else None
                    ),
                ),
            )

        return AskStreamSession(
            sources=_sources_from_chunks(chunks),
            cache_hit=cache_hit,
            tokens=_token_stream(),
        )

    def _stream_uncached(
        self,
        request: AskRequest,
        *,
        production: EvalConfig,
        language: str,
    ) -> AskStreamSession:
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        if not chunks:
            return AskStreamSession(
                sources=[],
                cache_hit="none",
                tokens=iter((no_context_message(language),)),
            )
        _, _, packer, max_chars = self._rag_packing()
        prompt = _build_prompt(
            request.question,
            chunks,
            system_prompt=resolve_system_prompt_for_language(language, production),
            packer=packer,
            context_max_chars=max_chars,
        )
        model_id = production.model_id or self._llm_model_id
        return AskStreamSession(
            sources=_sources_from_chunks(chunks),
            cache_hit="none",
            tokens=self._llm.generate_stream(
                prompt,
                max_tokens=production.max_tokens,
                model_id=model_id,
            ),
        )

    def ask_stream(self, request: AskRequest) -> Iterator[str]:
        """Stream LLM tokens for a question after retrieval."""
        yield from self.stream_ask(request).tokens

    def retrieve_sources(self, request: AskRequest) -> list[Source]:
        """Return ranked source chunks without invoking the LLM."""
        production = self._production_config()
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        return _sources_from_chunks(chunks)
