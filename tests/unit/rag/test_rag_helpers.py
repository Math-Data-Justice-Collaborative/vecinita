"""Pure unit tests for vecinita_rag helpers (no database)."""

from __future__ import annotations

from uuid import uuid4

import langdetect
import pytest
from llama_index.core.llms import MockLLM
from llama_index.core.schema import QueryBundle, TextNode
from vecinita_rag.engine import (
    answer_from_chunks,
    answer_without_context,
    build_query_engine,
    build_retriever,
    synthesize_with_llm,
)
from vecinita_rag.language import (
    detect_query_language,
    no_context_message,
)
from vecinita_rag.retriever import (
    CorpusPgvectorRetriever,
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
    _vector_literal,  # pyright: ignore[reportPrivateUsage]
    chunks_to_nodes,
    database_url_from_env,
)
from vecinita_rag.tag_inference import (
    resolve_retrieval_tags,
)
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def _sample_chunk(*, text: str = "Sample chunk text") -> RetrievedChunk:
    """Sample chunk."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=text,
        score=0.95,
        title="Title",
        url="fixture://doc",
        language="en",
    )


def test_detect_query_language_defaults_for_blank_question() -> None:
    """Test detect query language defaults for blank question."""
    assert detect_query_language("   ") == "en"


def test_detect_query_language_uses_fallback_on_detection_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test detect query language uses fallback on detection failure."""

    def _fail(_text: str) -> str:
        """Fail."""
        msg = "fail"
        raise langdetect.LangDetectException(msg, "detection failed")

    monkeypatch.setattr(langdetect, "detect", _fail)

    assert detect_query_language("???") == "en"


def test_no_context_message_returns_english_copy() -> None:
    """Test no context message returns english copy."""
    message = no_context_message("en")

    assert "corpus" in message.lower()


def test_normalize_database_url_rewrites_postgresql_scheme() -> None:
    """Test normalize database url rewrites postgresql scheme."""
    assert (
        _normalize_database_url("postgresql://user:pass@localhost/db")
        == "postgresql+psycopg://user:pass@localhost/db"
    )


def test_normalize_database_url_leaves_psycopg_url_unchanged() -> None:
    """Test normalize database url leaves psycopg url unchanged."""
    url = "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita"

    assert _normalize_database_url(url) == url


def test_database_url_from_env_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test database url from env raises when missing."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        database_url_from_env()


def test_database_url_from_env_normalizes_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test database url from env normalizes value."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/vecinita")

    assert database_url_from_env().startswith("postgresql+psycopg://")


def test_vector_literal_rejects_wrong_dimension() -> None:
    """Test vector literal rejects wrong dimension."""
    with pytest.raises(ValueError, match="384"):
        _vector_literal([0.1, 0.2])


def test_vector_literal_formats_embedding() -> None:
    """Test vector literal formats embedding."""
    values = [1.0] + [0.0] * 383

    assert _vector_literal(values).startswith("[1.0,")


def test_corpus_retriever_rejects_invalid_top_k() -> None:
    """Test corpus retriever rejects invalid top k."""
    with pytest.raises(ValueError, match="top_k"):
        CorpusPgvectorRetriever(embed_fn=lambda _q: [0.0] * 384, top_k=0)


def test_build_retriever_returns_pgvector_retriever() -> None:
    """Test build retriever returns pgvector retriever."""
    retriever = build_retriever(lambda _q: [0.0] * 384, database_url="postgresql+psycopg://x")

    assert isinstance(retriever, CorpusPgvectorRetriever)


def test_build_query_engine_returns_retriever_query_engine() -> None:
    """Test build query engine returns retriever query engine."""
    engine = build_query_engine(
        lambda _q: [0.0] * 384,
        MockLLM(max_tokens=32),
        database_url="postgresql+psycopg://x",
    )

    assert engine is not None


def test_answer_from_chunks_returns_no_context_when_empty() -> None:
    """Test answer from chunks returns no context when empty."""
    result = answer_from_chunks("What is this?", [])

    assert result.sources == []
    assert result.answer == answer_without_context("What is this?").answer


def test_answer_from_chunks_uses_provided_answer_text() -> None:
    """Test answer from chunks uses provided answer text."""
    chunk = _sample_chunk()

    result = answer_from_chunks(
        "food pantry hours?",
        [chunk],
        answer_text="Custom synthesized answer",
    )

    assert result.answer == "Custom synthesized answer"
    assert result.sources == [chunk]


def test_synthesize_with_llm_returns_no_context_when_empty() -> None:
    """Test synthesize with llm returns no context when empty."""
    result = synthesize_with_llm("Question?", [], MockLLM(max_tokens=32))

    assert result.sources == []
    assert "corpus" in result.answer.lower()


def test_synthesize_with_llm_uses_response_synthesizer() -> None:
    """Test synthesize with llm uses response synthesizer."""
    chunk = _sample_chunk(text="Food pantry hours are posted on Monday.")

    result = synthesize_with_llm(
        "When is the food pantry open?",
        [chunk],
        MockLLM(max_tokens=32),
    )

    assert result.sources == [chunk]
    assert result.language == "en"
    assert result.answer


def test_chunks_to_nodes_maps_metadata() -> None:
    """Test chunks to nodes maps metadata."""
    chunk = _sample_chunk()

    nodes = chunks_to_nodes([chunk])

    assert len(nodes) == 1
    node = nodes[0].node
    assert isinstance(node, TextNode)
    assert node.text == chunk.text
    assert nodes[0].score == chunk.score
    assert node.metadata["language"] == "en"


def test_retriever_retrieve_delegates_to_retrieve_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test retriever retrieve delegates to retrieve chunks."""
    chunk = _sample_chunk()
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: [0.0] * 384,
        database_url="postgresql+psycopg://x",
    )

    def _retrieve_chunks(_query: str, **_kwargs: object) -> list[RetrievedChunk]:
        return [chunk]

    monkeypatch.setattr(retriever, "retrieve_chunks", _retrieve_chunks)

    nodes = retriever._retrieve(QueryBundle(query_str="food pantry"))  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001

    assert len(nodes) == 1
    node = nodes[0].node
    assert isinstance(node, TextNode)
    assert node.text == chunk.text


def test_resolve_retrieval_tags_returns_none_without_infer_fn() -> None:
    """Test resolve retrieval tags returns none without infer fn."""
    assert (
        resolve_retrieval_tags(
            question="When is the food pantry open?",
            selected_tags=None,
            infer_fn=None,
        )
        is None
    )


def test_resolve_retrieval_tags_returns_none_when_inference_raises() -> None:
    """Test resolve retrieval tags returns none when inference raises."""

    def _fail(_question: str) -> list[str]:
        """Fail."""
        msg = "model unavailable"
        raise RuntimeError(msg)

    assert (
        resolve_retrieval_tags(
            question="When is the food pantry open?",
            selected_tags=None,
            infer_fn=_fail,
        )
        is None
    )


def test_resolve_retrieval_tags_returns_none_for_empty_inference() -> None:
    """Test resolve retrieval tags returns none for empty inference."""
    assert (
        resolve_retrieval_tags(
            question="When is the food pantry open?",
            selected_tags=None,
            infer_fn=lambda _q: [],
        )
        is None
    )
