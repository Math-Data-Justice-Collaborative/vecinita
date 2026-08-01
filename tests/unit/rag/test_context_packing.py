"""Unit tests for F42 P1/P3 context packing (TC-170, AC-RQ1, ADR-041)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_rag.packing import pack_chunks
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def _chunk(
    *,
    text: str = "chunk body",
    title: str | None = "Doc Title",
    url: str | None = "https://example.org/doc",
    score: float = 0.9,
    document_id: UUID | None = None,
) -> RetrievedChunk:
    """Build a RetrievedChunk fixture."""
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=document_id if document_id is not None else uuid4(),
        text=text,
        score=score,
        title=title,
        url=url,
        language="en",
    )


def test_pack_chunks_p1_emits_source_and_url_headers() -> None:
    """TC-170: P1 packer formats each chunk as Source/URL/text (AC-RQ1)."""
    packed = pack_chunks([_chunk(text="body text")], mode="p1")

    assert "Source: Doc Title" in packed
    assert "URL: https://example.org/doc" in packed
    assert "body text" in packed
    assert packed.startswith("Source:")
    # Not bare text concat
    assert packed != "body text"


def test_pack_chunks_p1_missing_title_uses_untitled_placeholder() -> None:
    """TC-170 edge: missing title still emits Source: line."""
    packed = pack_chunks([_chunk(title=None, url="https://example.org/x")], mode="p1")

    assert "Source: (untitled)" in packed
    assert "URL: https://example.org/x" in packed


def test_pack_chunks_p1_missing_url_uses_no_url_placeholder() -> None:
    """TC-170 edge: missing url still emits URL: line."""
    packed = pack_chunks([_chunk(title="T", url=None)], mode="p1")

    assert "Source: T" in packed
    assert "URL: (no-url)" in packed


def test_pack_chunks_p1_joins_multiple_chunks() -> None:
    """TC-170: multiple chunks keep Source/URL headers per chunk."""
    packed = pack_chunks(
        [
            _chunk(text="first", title="A", url="https://a.example"),
            _chunk(text="second", title="B", url="https://b.example"),
        ],
        mode="p1",
    )

    assert "Source: A" in packed
    assert "Source: B" in packed
    assert "first" in packed
    assert "second" in packed


def test_pack_chunks_p3_dedupes_by_document_and_caps_chars() -> None:
    """P3 (config-gated): one chunk per document_id + char budget."""
    doc = uuid4()
    high = _chunk(
        text="high-score text " * 20,
        title="Keep",
        url="https://example.org/a",
        score=0.95,
        document_id=doc,
    )
    low = _chunk(
        text="low-score text",
        title="Drop",
        url="https://example.org/b",
        score=0.1,
        document_id=doc,
    )
    max_chars = 80
    packed = pack_chunks([low, high], mode="p3", max_chars=max_chars)

    assert "Source: Keep" in packed
    assert "Source: Drop" not in packed
    assert len(packed) <= max_chars
