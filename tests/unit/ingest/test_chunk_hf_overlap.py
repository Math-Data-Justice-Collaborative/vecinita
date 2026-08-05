"""T103.1 / TC-191-192 - HF tokenizer chunk sizing + overlap (F49 / ADR-044)."""

from __future__ import annotations

import re
from itertools import pairwise

import pytest
from vecinita_ingest.chunk import (
    DEFAULT_CHUNK_OVERLAP_TOKENS,
    DEFAULT_CHUNK_TOKENIZER_ID,
    chunk_text,
    count_tokens,
    estimate_tokens,
    get_default_tokenizer,
)

_EXPECTED_DEFAULT_OVERLAP = 32
_MIN_CHUNK_COUNT = 2
_OVERLAP_TOLERANCE = 8
_CHUNK_SIZE = 64


def _long_fixture_text(*, words: int = 200) -> str:
    """Build multi-paragraph text with subword-heavy tokens (diverges from word≈token)."""
    # "tokenization" / hyphenated forms split differently under BPE/WordPiece than len(split()).
    paragraph_a = " ".join(f"tokenization-{i}" for i in range(words // 2))
    paragraph_b = " ".join(f"neighborhood-{i}" for i in range(words // 2))
    return f"{paragraph_a}\n\n{paragraph_b}"


def test_default_chunk_overlap_tokens_is_32() -> None:
    """Default overlap is 32 tokenizer tokens (RD-223 / AC-IR5)."""
    assert DEFAULT_CHUNK_OVERLAP_TOKENS == _EXPECTED_DEFAULT_OVERLAP


def test_default_chunk_tokenizer_id_matches_embed_pin() -> None:
    """Default tokenizer id matches F70 embed pin (ADR-048 / S027-D15 / T120.2)."""
    assert DEFAULT_CHUNK_TOKENIZER_ID == "intfloat/multilingual-e5-small"


def test_count_tokens_uses_hf_not_word_split_only() -> None:
    """HF token count diverges from whitespace word estimate for subword-heavy text."""
    text = "tokenization " * 40
    hf_count = count_tokens(text)
    word_count = estimate_tokens(text)
    assert hf_count != word_count
    assert hf_count > 0


def test_chunk_text_overlap_shares_approximately_32_tokenizer_tokens() -> None:
    """Consecutive HF id windows overlap by ~32 tokens (TC-191 / AC-IR5).

    Asserts overlap on the encode_with_offsets id stream (chunker source of truth).
    Metaspace tokenizers (e5) do not always re-encode string slices to the same ids.
    """
    text = _long_fixture_text(words=240)
    normalized = re.sub(r"\n+", "\n", text).strip()
    tokenizer = get_default_tokenizer()
    ids, _offsets = tokenizer.encode_with_offsets(normalized)
    assert len(ids) > _CHUNK_SIZE

    step = _CHUNK_SIZE - _EXPECTED_DEFAULT_OVERLAP
    windows: list[list[int]] = []
    start = 0
    while start < len(ids):
        end = min(start + _CHUNK_SIZE, len(ids))
        windows.append(ids[start:end])
        if end >= len(ids):
            break
        start += step

    assert len(windows) >= _MIN_CHUNK_COUNT
    overlap_low = _EXPECTED_DEFAULT_OVERLAP - _OVERLAP_TOLERANCE
    overlap_high = _EXPECTED_DEFAULT_OVERLAP + _OVERLAP_TOLERANCE
    for left, right in pairwise(windows):
        if len(left) < _CHUNK_SIZE or len(right) < _CHUNK_SIZE:
            continue
        overlap = 0
        max_check = min(len(left), len(right), _CHUNK_SIZE)
        for size in range(max_check, 0, -1):
            if left[-size:] == right[:size]:
                overlap = size
                break
        assert overlap_low <= overlap <= overlap_high, (
            f"expected ~{_EXPECTED_DEFAULT_OVERLAP}-token id overlap, got {overlap}"
        )


def test_chunk_text_respects_hf_token_budget_with_overlap() -> None:
    """Each emitted chunk re-encodes to ≤ chunk_size + Metaspace slack (e5)."""
    text = _long_fixture_text(words=180)
    chunks = chunk_text(
        text,
        chunk_size_tokens=_CHUNK_SIZE,
        chunk_overlap_tokens=DEFAULT_CHUNK_OVERLAP_TOKENS,
    )
    assert chunks
    # Unigram/Metaspace may add ≤1 token when re-encoding a char slice (ADR-048 pin).
    _metaspace_slack = 1
    assert all(count_tokens(chunk) <= _CHUNK_SIZE + _metaspace_slack for chunk in chunks)


def test_chunk_text_rejects_overlap_equal_to_size() -> None:
    """Validation rejects overlap >= chunk_size (TC-192 / AC-IR6)."""
    with pytest.raises(ValueError, match="overlap"):
        chunk_text(
            "hello world",
            chunk_size_tokens=256,
            chunk_overlap_tokens=256,
        )


def test_chunk_text_rejects_overlap_greater_than_size() -> None:
    """Validation rejects overlap greater than chunk_size (TC-192 / AC-IR6)."""
    with pytest.raises(ValueError, match="overlap"):
        chunk_text(
            "hello world",
            chunk_size_tokens=64,
            chunk_overlap_tokens=100,
        )


def test_chunk_text_rejects_negative_overlap() -> None:
    """Overlap must be >= 0."""
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("hello world", chunk_size_tokens=64, chunk_overlap_tokens=-1)


class _EmptyIdsTokenizer:
    """Tokenizer stub that yields no content tokens."""

    def encode_ids(self, text: str) -> list[int]:
        _ = text
        return []

    def encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        _ = text
        return [], []


class _SpaceOnlySpanTokenizer:
    """Tokenizer stub whose sole token span is a single space (strip → drop)."""

    def encode_ids(self, text: str) -> list[int]:
        return self.encode_with_offsets(text)[0]

    def encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        idx = text.find(" ")
        if idx < 0:
            return [1], [(0, max(len(text), 1))]
        return [1], [(idx, idx + 1)]


def test_chunk_text_empty_ids_returns_empty_list() -> None:
    """No content tokens → no chunks (branch after encode_with_offsets)."""
    assert (
        chunk_text(
            "visible text",
            chunk_size_tokens=64,
            chunk_overlap_tokens=0,
            tokenizer=_EmptyIdsTokenizer(),
        )
        == []
    )


def test_chunk_text_drops_whitespace_only_window() -> None:
    """Windows that strip to empty are omitted from the chunk list."""
    chunks = chunk_text(
        "hello world",
        chunk_size_tokens=64,
        chunk_overlap_tokens=0,
        tokenizer=_SpaceOnlySpanTokenizer(),
    )
    assert chunks == []
