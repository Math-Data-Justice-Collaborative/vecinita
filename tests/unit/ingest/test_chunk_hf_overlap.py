"""T103.1 / TC-191-192 - HF tokenizer chunk sizing + overlap (F49 / ADR-044)."""

from __future__ import annotations

from itertools import pairwise

import pytest
from vecinita_ingest.chunk import (
    DEFAULT_CHUNK_OVERLAP_TOKENS,
    DEFAULT_CHUNK_TOKENIZER_ID,
    chunk_text,
    count_tokens,
    encode_token_ids,
    estimate_tokens,
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


def test_default_chunk_tokenizer_id_is_bge_small() -> None:
    """Default tokenizer id matches pinned embed model (ADR-044 / RD-224)."""
    assert DEFAULT_CHUNK_TOKENIZER_ID == "BAAI/bge-small-en-v1.5"


def test_count_tokens_uses_hf_not_word_split_only() -> None:
    """HF token count diverges from whitespace word estimate for subword-heavy text."""
    text = "tokenization " * 40
    hf_count = count_tokens(text)
    word_count = estimate_tokens(text)
    assert hf_count != word_count
    assert hf_count > 0


def test_chunk_text_overlap_shares_approximately_32_tokenizer_tokens() -> None:
    """Consecutive chunks overlap by ~32 HF tokens (TC-191 / AC-IR5)."""
    text = _long_fixture_text(words=240)
    chunks = chunk_text(
        text,
        chunk_size_tokens=_CHUNK_SIZE,
        chunk_overlap_tokens=_EXPECTED_DEFAULT_OVERLAP,
    )
    assert len(chunks) >= _MIN_CHUNK_COUNT

    overlap_low = _EXPECTED_DEFAULT_OVERLAP - _OVERLAP_TOLERANCE
    overlap_high = _EXPECTED_DEFAULT_OVERLAP + _OVERLAP_TOLERANCE
    for left, right in pairwise(chunks):
        left_ids = encode_token_ids(left)
        right_ids = encode_token_ids(right)
        assert left_ids
        assert right_ids
        # Longest suffix of left that is a prefix of right (token overlap).
        max_check = min(len(left_ids), len(right_ids), _CHUNK_SIZE)
        overlap = 0
        for size in range(max_check, 0, -1):
            if left_ids[-size:] == right_ids[:size]:
                overlap = size
                break
        assert overlap_low <= overlap <= overlap_high, (
            f"expected ~{_EXPECTED_DEFAULT_OVERLAP}-token overlap, got {overlap}"
        )


def test_chunk_text_respects_hf_token_budget_with_overlap() -> None:
    """Each chunk is within chunk_size when counted with the HF tokenizer."""
    text = _long_fixture_text(words=180)
    chunks = chunk_text(
        text,
        chunk_size_tokens=_CHUNK_SIZE,
        chunk_overlap_tokens=DEFAULT_CHUNK_OVERLAP_TOKENS,
    )
    assert chunks
    assert all(count_tokens(chunk) <= _CHUNK_SIZE for chunk in chunks)


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
