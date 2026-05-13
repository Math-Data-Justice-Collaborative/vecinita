"""Semantic chunking utilities with adaptive sizing."""

from __future__ import annotations

import re
from typing import Any

from vecinita_scraper.core.errors import ChunkingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import ChunkingConfig

logger = get_logger(__name__)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")


class SemanticChunker:
    """Split documents at paragraph and sentence boundaries with token-aware sizing."""

    def chunk(
        self,
        markdown_content: str,
        config: ChunkingConfig,
        max_tokens_override: int | None = None,
    ) -> list[dict[str, Any]]:
        """Chunk markdown into semantically meaningful segments."""
        if not markdown_content.strip():
            raise ChunkingError("Cannot chunk empty markdown content")

        max_tokens = max_tokens_override or config.max_size_tokens
        max_tokens = max(max_tokens, config.min_size_tokens)
        paragraphs = [
            part.strip() for part in _PARAGRAPH_SPLIT_RE.split(markdown_content) if part.strip()
        ]

        chunks: list[dict[str, Any]] = []
        current_parts: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph_tokens = self.count_tokens(paragraph)
            if paragraph_tokens > max_tokens:
                if current_parts:
                    chunks.append(self._build_chunk(current_parts, len(chunks)))
                    current_parts = []
                    current_tokens = 0
                chunks.extend(
                    self._split_large_paragraph(paragraph, max_tokens, start_index=len(chunks))
                )
                continue

            if current_tokens and current_tokens + paragraph_tokens > max_tokens:
                chunks.append(self._build_chunk(current_parts, len(chunks)))
                current_parts = []
                current_tokens = 0

            current_parts.append(paragraph)
            current_tokens += paragraph_tokens

        if current_parts:
            chunks.append(self._build_chunk(current_parts, len(chunks)))

        logger.info("Chunked markdown document", chunk_count=len(chunks), max_tokens=max_tokens)
        return chunks

    def count_tokens(self, text: str) -> int:
        """Count tokens with tiktoken when available, fallback to a word-based estimate."""
        try:
            import tiktoken
        except ImportError:
            return max(1, len(text.split()))

        encoder = tiktoken.get_encoding("cl100k_base")
        return max(1, len(encoder.encode(text)))

    def _split_large_paragraph(
        self,
        paragraph: str,
        max_tokens: int,
        start_index: int,
    ) -> list[dict[str, Any]]:
        """Split a large paragraph by sentence boundaries."""
        sentences = [part.strip() for part in _SENTENCE_SPLIT_RE.split(paragraph) if part.strip()]
        if not sentences:
            return [self._build_chunk([paragraph], start_index)]

        chunks: list[dict[str, Any]] = []
        current_sentences: list[str] = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            if current_tokens and current_tokens + sentence_tokens > max_tokens:
                chunks.append(self._build_chunk(current_sentences, start_index + len(chunks)))
                current_sentences = []
                current_tokens = 0

            current_sentences.append(sentence)
            current_tokens += sentence_tokens

        if current_sentences:
            chunks.append(self._build_chunk(current_sentences, start_index + len(chunks)))
        return chunks

    def _build_chunk(self, parts: list[str], position: int) -> dict[str, Any]:
        """Construct a chunk record."""
        text = "\n\n".join(parts).strip()
        return {
            "text": text,
            "position": position,
            "token_count": self.count_tokens(text),
            "semantic_boundary": True,
        }
