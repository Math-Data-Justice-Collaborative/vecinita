"""Unit tests for F42 P1/P3 context packing (TC-170, AC-RQ1, ADR-041)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_rag.packing import pack_chunks, truncate_context
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit

_LARGE_BUDGET = 5000


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
    """TC-194 / P3: one chunk per document_id + char budget (AC-RQ9)."""
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


def test_tc194_p3_default_budget_matches_context_max_chars() -> None:
    """TC-194: P3 packing with default CONTEXT_MAX_CHARS budget still dedupes."""
    from vecinita_rag.packing import DEFAULT_CONTEXT_MAX_CHARS  # noqa: PLC0415

    doc = uuid4()
    long_text = "x" * (DEFAULT_CONTEXT_MAX_CHARS + 200)
    chunks = [
        _chunk(text=long_text, title="A", score=0.9, document_id=doc),
        _chunk(text="other", title="B", score=0.5, document_id=doc),
    ]
    packed = pack_chunks(chunks, mode="p3", max_chars=DEFAULT_CONTEXT_MAX_CHARS)
    assert "Source: A" in packed
    assert "Source: B" not in packed
    assert len(packed) <= DEFAULT_CONTEXT_MAX_CHARS


def test_pack_chunks_p3_keeps_first_when_later_score_not_higher() -> None:
    """Dedupe keeps the first chunk when a later same-doc score is not higher."""
    doc = uuid4()
    first = _chunk(text="first", title="First", score=0.9, document_id=doc)
    second = _chunk(text="second", title="Second", score=0.5, document_id=doc)
    packed = pack_chunks([first, second], mode="p3", max_chars=500)
    assert "Source: First" in packed
    assert "Source: Second" not in packed


def test_pack_chunks_p1_blank_title_and_url_use_placeholders() -> None:
    """Whitespace-only title/url collapse to placeholders."""
    packed = pack_chunks([_chunk(title="  ", url="  ")], mode="p1")
    assert "Source: (untitled)" in packed
    assert "URL: (no-url)" in packed


def test_pack_chunks_p3_short_context_skips_truncate() -> None:
    """Under-budget P3 context is returned unchanged."""
    packed = pack_chunks([_chunk(text="short")], mode="p3", max_chars=_LARGE_BUDGET)
    assert "short" in packed
    assert len(packed) < _LARGE_BUDGET


def test_truncate_context_rejects_non_positive_max_chars() -> None:
    """max_chars < 1 raises ValueError."""
    with pytest.raises(ValueError, match="max_chars"):
        truncate_context("abc", max_chars=0)


def test_pack_chunks_rejects_unsupported_mode() -> None:
    """Unknown packer mode raises ValueError."""
    with pytest.raises(ValueError, match="unsupported packer mode"):
        pack_chunks([_chunk()], mode="p2")  # type: ignore[arg-type]
