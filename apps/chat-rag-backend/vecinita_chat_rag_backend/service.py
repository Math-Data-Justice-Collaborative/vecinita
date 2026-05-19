"""ChatRAG orchestration: retrieve → generate (F1, F4, F5, F6)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Literal, cast

from vecinita_embedding_client import EmbeddingClient
from vecinita_llm_client import LlmClient
from vecinita_rag.engine import answer_from_chunks, answer_without_context
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.chat_rag import AskResponse, Source

from vecinita_chat_rag_backend.config import ChatRagSettings

EmbedFn = Callable[[str], list[float]]


def _build_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context = "\n\n".join(chunk.text for chunk in chunks)
    return (
        "Answer using only the context below. Be concise.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
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
    def __init__(
        self,
        *,
        retriever: CorpusPgvectorRetriever,
        llm_client: LlmClient,
    ) -> None:
        self._retriever = retriever
        self._llm = llm_client

    @classmethod
    def from_settings(cls, settings: ChatRagSettings) -> ChatRagService:
        embed_client = EmbeddingClient(
            settings.embed_url,
            timeout=settings.request_timeout_s,
        )
        llm_client = LlmClient(settings.llm_url, timeout=settings.request_timeout_s)

        def embed_fn(text: str) -> list[float]:
            return embed_client.embed(text)

        retriever = CorpusPgvectorRetriever(
            embed_fn=embed_fn,
            database_url=settings.database_url,
            top_k=settings.top_k,
        )
        return cls(retriever=retriever, llm_client=llm_client)

    def ask(self, question: str) -> AskResponse:
        chunks = self._retriever.retrieve_chunks(question)
        if not chunks:
            return _to_ask_response(answer_without_context(question))
        prompt = _build_prompt(question, chunks)
        answer_text = self._llm.generate(prompt)
        result = answer_from_chunks(question, chunks, answer_text=answer_text)
        return _to_ask_response(result)

    def ask_stream(self, question: str) -> Iterator[str]:
        chunks = self._retriever.retrieve_chunks(question)
        if not chunks:
            result = answer_without_context(question)
            yield result.answer
            return
        prompt = _build_prompt(question, chunks)
        yield from self._llm.generate_stream(prompt)

    def retrieve_sources(self, question: str) -> list[Source]:
        chunks = self._retriever.retrieve_chunks(question)
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
