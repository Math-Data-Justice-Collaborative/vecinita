"""Text chunking for ingest (config-spec: chunk_size_tokens ≥ 64)."""

from __future__ import annotations

import re
from typing import Final

MIN_CHUNK_SIZE_TOKENS: Final[int] = 64
DEFAULT_CHUNK_SIZE_TOKENS: Final[int] = 256
MAX_CHUNK_SIZE_TOKENS: Final[int] = 2048


def estimate_tokens(text: str) -> int:
    """Approximate token count without a tokenizer (v1)."""
    return len(text.split())


def chunk_text(text: str, *, chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS) -> list[str]:
    """Split plain text into paragraph-aware chunks bounded by token estimate."""
    if chunk_size_tokens < MIN_CHUNK_SIZE_TOKENS:
        msg = f"chunk_size_tokens must be ≥ {MIN_CHUNK_SIZE_TOKENS}"
        raise ValueError(msg)
    if chunk_size_tokens > MAX_CHUNK_SIZE_TOKENS:
        msg = f"chunk_size_tokens must be ≤ {MAX_CHUNK_SIZE_TOKENS}"
        raise ValueError(msg)

    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = f"{buffer} {paragraph}".strip() if buffer else paragraph
        if estimate_tokens(candidate) <= chunk_size_tokens:
            buffer = candidate
            continue
        if buffer:
            chunks.append(buffer)
        if estimate_tokens(paragraph) <= chunk_size_tokens:
            buffer = paragraph
        else:
            words = paragraph.split()
            start = 0
            while start < len(words):
                end = start
                while end < len(words) and len(words[start:end]) <= chunk_size_tokens:
                    end += 1
                if end == start:
                    end = start + 1
                chunks.append(" ".join(words[start:end]))
                start = end
            buffer = ""
    if buffer:
        chunks.append(buffer)
    return chunks
