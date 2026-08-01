"""ChatRAG orchestration: retrieve → generate (F1, F4, F5, F6, F22)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Literal

from sqlalchemy import create_engine
from vecinita_embedding_client import EmbeddingClient
from vecinita_llm_client import LlmClient, format_instruct_prompt
from vecinita_rag.engine import answer_from_chunks
from vecinita_rag.language import detect_query_language, no_context_message
from vecinita_rag.multi_query import multi_query_retrieve
from vecinita_rag.packing import PackerMode, pack_chunks
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.tag_inference import TagInferFn, resolve_retrieval_tags
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source
from vecinita_shared_schemas.eval_config import EvalConfig
from vecinita_tagging.llm_client import LlmTagClient
from vecinita_tagging.vocabulary import load_seed_vocabulary, vocabulary_slugs

from vecinita_chat_rag_backend.rag_production_config import load_active_rag_config

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from vecinita_chat_rag_backend.config import ChatRagSettings

EmbedFn = Callable[[str], list[float]]


def _build_prompt(
    question: str,
    chunks: list[RetrievedChunk],
    *,
    system_prompt: str,
    packer: PackerMode = "p1",
    context_max_chars: int = 3500,
) -> str:
    """Build instruct prompt via shared HF chat-template helper (RD-167 / TC-145 / F42)."""
    context = pack_chunks(chunks, mode=packer, max_chars=context_max_chars)
    user = f"Context:\n{context}\n\nQuestion: {question}"
    return format_instruct_prompt(system=system_prompt, user=user)


def _to_ask_response(result: RagAnswer) -> AskResponse:
    sources = [
        Source(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            title=chunk.title,
            url=chunk.url,
            score=chunk.score,
        )
        for chunk in result.sources
    ]
    language: Literal["en", "es"] = "es" if result.language == "es" else "en"
    return AskResponse(answer=result.answer, language=language, sources=sources)


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
    ) -> None:
        """Wire retrieval, LLM, and optional tag inference for ask flows."""
        self._retriever = retriever
        self._llm = llm_client
        self._chat_max_tokens = chat_max_tokens
        self._tag_infer_fn = tag_infer_fn
        self._llm_model_id = llm_model_id
        self._settings = settings
        self._config_engine = config_engine

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
        return cls(
            retriever=retriever,
            llm_client=llm_client,
            chat_max_tokens=settings.chat_max_tokens,
            tag_infer_fn=tag_infer_fn,
            llm_model_id=settings.llm_model_id,
            settings=settings,
            config_engine=config_engine,
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
            return True, 3, "p1", 3500
        return (
            self._settings.rag_multi_query,
            self._settings.rag_multi_query_count,
            self._settings.rag_packer,
            self._settings.rag_context_max_chars,
        )

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

        def _retrieve_once(question: str) -> list[RetrievedChunk]:
            chunks = self._retriever.retrieve_chunks(
                question,
                tag_slugs=tag_slugs,
                language=language,
                top_k=top_k,
                score_threshold=min_retrieval_score,
            )
            if not chunks and tag_slugs:
                chunks = self._retriever.retrieve_chunks(
                    question,
                    tag_slugs=None,
                    language=language,
                    top_k=top_k,
                    score_threshold=min_retrieval_score,
                )
            return chunks

        return multi_query_retrieve(
            request.question,
            locale=language,
            top_k=top_k,
            retrieve_fn=_retrieve_once,
            enabled=multi_query,
            count=multi_count,
        )

    def ask(self, request: AskRequest) -> AskResponse:
        """Retrieve context and generate a non-streaming answer."""
        production = self._production_config()
        language = self._effective_language(request)
        _, _, packer, max_chars = self._rag_packing()
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        if not chunks:
            return _to_ask_response(
                RagAnswer(
                    answer=no_context_message(language),
                    language=language,
                    sources=[],
                )
            )
        prompt = _build_prompt(
            request.question,
            chunks,
            system_prompt=production.system_prompt,
            packer=packer,
            context_max_chars=max_chars,
        )
        model_id = production.model_id or self._llm_model_id
        answer_text = self._llm.generate(
            prompt,
            max_tokens=production.max_tokens,
            model_id=model_id,
        )
        result = answer_from_chunks(request.question, chunks, answer_text=answer_text)
        result = RagAnswer(
            answer=result.answer,
            language=language,
            sources=result.sources,
        )
        return _to_ask_response(result)

    def ask_stream(self, request: AskRequest) -> Iterator[str]:
        """Stream LLM tokens for a question after retrieval."""
        production = self._production_config()
        language = self._effective_language(request)
        _, _, packer, max_chars = self._rag_packing()
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        if not chunks:
            yield no_context_message(language)
            return
        prompt = _build_prompt(
            request.question,
            chunks,
            system_prompt=production.system_prompt,
            packer=packer,
            context_max_chars=max_chars,
        )
        model_id = production.model_id or self._llm_model_id
        yield from self._llm.generate_stream(
            prompt,
            max_tokens=production.max_tokens,
            model_id=model_id,
        )

    def retrieve_sources(self, request: AskRequest) -> list[Source]:
        """Return ranked source chunks without invoking the LLM."""
        production = self._production_config()
        chunks = self._retrieve(
            request,
            top_k=production.top_k,
            min_retrieval_score=production.min_retrieval_score,
        )
        return [
            Source(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                url=chunk.url,
                score=chunk.score,
            )
            for chunk in chunks
        ]
