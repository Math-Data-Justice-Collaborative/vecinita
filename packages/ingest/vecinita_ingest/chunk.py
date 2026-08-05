"""Text chunking for ingest (HF tokenizer + overlap; ADR-044 / F49)."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from functools import lru_cache
from typing import Final, Protocol, cast

import huggingface_hub
from tokenizers import Tokenizer

_HfHubDownload = Callable[..., str]
_hf_hub_download = cast("_HfHubDownload", huggingface_hub.hf_hub_download)

MIN_CHUNK_SIZE_TOKENS: Final[int] = 64
DEFAULT_CHUNK_SIZE_TOKENS: Final[int] = 256
MAX_CHUNK_SIZE_TOKENS: Final[int] = 2048
DEFAULT_CHUNK_OVERLAP_TOKENS: Final[int] = 32
DEFAULT_CHUNK_TOKENIZER_ID: Final[str] = "intfloat/multilingual-e5-small"


class ChunkTokenizer(Protocol):
    """Minimal tokenizer surface used by the ingest chunker."""

    def encode_ids(self, text: str) -> list[int]:
        """Return content token ids (no special tokens)."""
        ...

    def encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        """Return content token ids with character offsets into ``text``."""
        ...


class HfChunkTokenizer:
    """HuggingFace ``tokenizers`` wrapper for the pinned embed model."""

    def __init__(self, tokenizer_id: str) -> None:
        """Load ``tokenizer.json`` for ``tokenizer_id`` from the Hub (cached)."""
        path = _hf_hub_download(repo_id=tokenizer_id, filename="tokenizer.json")
        self._tokenizer = Tokenizer.from_file(path)
        # Chunk sizing must count content tokens only (no [CLS]/[SEP]).
        self._tokenizer.post_processor = None

    def encode_ids(self, text: str) -> list[int]:
        """Return content token ids."""
        return list(self._tokenizer.encode(text).ids)

    def encode_with_offsets(self, text: str) -> tuple[list[int], list[tuple[int, int]]]:
        """Return content token ids with character offsets."""
        encoding = self._tokenizer.encode(text)
        ids: list[int] = []
        offsets: list[tuple[int, int]] = []
        for token_id, (start, end) in zip(encoding.ids, encoding.offsets, strict=True):
            if start == end:
                continue
            ids.append(token_id)
            offsets.append((start, end))
        return ids, offsets


@lru_cache(maxsize=4)
def _cached_hf_tokenizer(tokenizer_id: str) -> HfChunkTokenizer:
    return HfChunkTokenizer(tokenizer_id)


def resolve_tokenizer_id() -> str:
    """Resolve tokenizer id from env (config-spec ``VECINITA_CHUNK_TOKENIZER_ID``)."""
    return os.environ.get("VECINITA_CHUNK_TOKENIZER_ID", DEFAULT_CHUNK_TOKENIZER_ID)


def get_default_tokenizer() -> ChunkTokenizer:
    """Return the process-cached default HF chunk tokenizer."""
    return _cached_hf_tokenizer(resolve_tokenizer_id())


def estimate_tokens(text: str) -> int:
    """Deprecated whitespace word estimate (pre-F49). Prefer :func:`count_tokens`."""
    return len(text.split())


def count_tokens(text: str, *, tokenizer: ChunkTokenizer | None = None) -> int:
    """Count tokens with the HF embed tokenizer (ADR-044)."""
    active = tokenizer if tokenizer is not None else get_default_tokenizer()
    return len(active.encode_ids(text))


def encode_token_ids(text: str, *, tokenizer: ChunkTokenizer | None = None) -> list[int]:
    """Encode ``text`` to content token ids with the default (or injected) tokenizer."""
    active = tokenizer if tokenizer is not None else get_default_tokenizer()
    return active.encode_ids(text)


def validate_chunk_options(*, chunk_size_tokens: int, chunk_overlap_tokens: int) -> None:
    """Validate size/overlap bounds (AC-IR6)."""
    if chunk_size_tokens < MIN_CHUNK_SIZE_TOKENS:
        msg = f"chunk_size_tokens must be ≥ {MIN_CHUNK_SIZE_TOKENS}"
        raise ValueError(msg)
    if chunk_size_tokens > MAX_CHUNK_SIZE_TOKENS:
        msg = f"chunk_size_tokens must be ≤ {MAX_CHUNK_SIZE_TOKENS}"
        raise ValueError(msg)
    if chunk_overlap_tokens < 0:
        msg = "chunk_overlap_tokens must be ≥ 0"
        raise ValueError(msg)
    if chunk_overlap_tokens >= chunk_size_tokens:
        msg = "chunk_overlap_tokens must be < chunk_size_tokens"
        raise ValueError(msg)


def chunk_text(
    text: str,
    *,
    chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
    chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
    tokenizer: ChunkTokenizer | None = None,
) -> list[str]:
    """Split text into overlapping HF-token windows (ADR-044 / F49)."""
    validate_chunk_options(
        chunk_size_tokens=chunk_size_tokens,
        chunk_overlap_tokens=chunk_overlap_tokens,
    )

    normalized = re.sub(r"\n+", "\n", text).strip()
    if not normalized:
        return []

    active = tokenizer if tokenizer is not None else get_default_tokenizer()
    ids, offsets = active.encode_with_offsets(normalized)
    if not ids:
        return []

    step = chunk_size_tokens - chunk_overlap_tokens
    chunks: list[str] = []
    start = 0
    while start < len(ids):
        end = min(start + chunk_size_tokens, len(ids))
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1]
        piece = normalized[char_start:char_end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(ids):
            break
        start += step
    return chunks
