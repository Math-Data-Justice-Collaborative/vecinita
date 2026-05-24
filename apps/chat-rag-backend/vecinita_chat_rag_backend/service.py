"""ChatRAG orchestration: retrieve → generate (F1, F4, F5, F6, F22)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Literal, cast

from vecinita_embedding_client import EmbeddingClient
from vecinita_llm_client import LlmClient
from vecinita_rag.engine import answer_from_chunks, answer_without_context
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.tag_inference import TagInferFn, resolve_retrieval_tags
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, Source
from vecinita_tagging.llm_client import LlmTagClient
from vecinita_tagging.vocabulary import load_seed_vocabulary, vocabulary_slugs

from vecinita_chat_rag_backend.config import ChatRagSettings

EmbedFn = Callable[[str], list[float]]


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    """Qwen2.5-Instruct chat format — plain completion prompts loop on generic filler."""
    context = "\n\n".join(chunk.text for chunk in chunks)
    return (
        "<|im_start|>system\n"
        "Answer community questions using only the context below. Be concise. "
        "If the context does not answer the question, say you do not have that information.\n"
        "\n"
        f"<|im_start|>user\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        "\n"
        "<|im_start|>assistant\n"
    )


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
    language = cast(Literal["en", "es"], "es" if result.language == "es" else "en")
    return AskResponse(answer=result.answer, language=language, sources=sources)


class ChatRagService:
    """Orchestrate retrieval and LLM answer generation for /ask endpoints."""

    def __init__(
        self,
        *,
        retriever: CorpusPgvectorRetriever,
        llm_client: LlmClient,
        chat_max_tokens: int = 256,
        tag_infer_fn: TagInferFn | None = None,
    ) -> None:
        self._retriever = retriever
        self._llm = llm_client
        self._chat_max_tokens = chat_max_tokens
        self._tag_infer_fn = tag_infer_fn

    @classmethod
    def from_settings(cls, settings: ChatRagSettings) -> ChatRagService:
        embed_client = EmbeddingClient(
            settings.embed_url,
            timeout=settings.request_timeout_s,
        )
        llm_client = LlmClient(settings.llm_url, timeout=settings.request_timeout_s)
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
        return cls(
            retriever=retriever,
            llm_client=llm_client,
            chat_max_tokens=settings.chat_max_tokens,
            tag_infer_fn=tag_infer_fn,
        )

    def _retrieval_tags(self, request: AskRequest) -> list[str] | None:
        return resolve_retrieval_tags(
            question=request.question,
            selected_tags=request.tags or None,
            infer_fn=self._tag_infer_fn,
        )

    def _retrieve(self, request: AskRequest) -> list[RetrievedChunk]:
        tag_slugs = self._retrieval_tags(request)
        return self._retriever.retrieve_chunks(request.question, tag_slugs=tag_slugs)

    def ask(self, request: AskRequest) -> AskResponse:
        chunks = self._retrieve(request)
        if not chunks:
            return _to_ask_response(answer_without_context(request.question))
        prompt = _build_prompt(request.question, chunks)
        answer_text = self._llm.generate(prompt, max_tokens=self._chat_max_tokens)
        result = answer_from_chunks(request.question, chunks, answer_text=answer_text)
        return _to_ask_response(result)

    def ask_stream(self, request: AskRequest) -> Iterator[str]:
        chunks = self._retrieve(request)
        if not chunks:
            result = answer_without_context(request.question)
            yield result.answer
            return
        prompt = _build_prompt(request.question, chunks)
        yield from self._llm.generate_stream(prompt, max_tokens=self._chat_max_tokens)

    def retrieve_sources(self, request: AskRequest) -> list[Source]:
        chunks = self._retrieve(request)
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
