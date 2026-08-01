r"""Context packing helpers for ChatRAG / F36 (F42, ADR-041).

P1 (default): ``Source: {title}\nURL: {url}\n{text}`` per chunk.
P3 (config-gated): P1 + document_id dedupe + char budget.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_rag.types import RetrievedChunk

PackerMode = Literal["p1", "p3"]

DEFAULT_CONTEXT_MAX_CHARS = 3500
_UNTITLED = "(untitled)"
_NO_URL = "(no-url)"


def _header_title(title: str | None) -> str:
    cleaned = (title or "").strip()
    return cleaned or _UNTITLED


def _header_url(url: str | None) -> str:
    cleaned = (url or "").strip()
    return cleaned or _NO_URL


def pack_p1(chunks: list[RetrievedChunk]) -> str:
    """Format each chunk with Source/URL headers (P1)."""
    parts: list[str] = []
    for chunk in chunks:
        title = _header_title(chunk.title)
        url = _header_url(chunk.url)
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def dedupe_by_document(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep the highest-score chunk per ``document_id`` (stable first-seen order)."""
    best: dict[UUID, RetrievedChunk] = {}
    order: list[UUID] = []
    for chunk in chunks:
        doc_id = chunk.document_id
        if doc_id not in best:
            order.append(doc_id)
            best[doc_id] = chunk
            continue
        if chunk.score > best[doc_id].score:
            best[doc_id] = chunk
    return [best[doc_id] for doc_id in order]


def truncate_context(context: str, *, max_chars: int) -> str:
    """Prefix-cap packed context to ``max_chars`` (P3 budget)."""
    if max_chars < 1:
        msg = "max_chars must be >= 1"
        raise ValueError(msg)
    if len(context) <= max_chars:
        return context
    return context[:max_chars]


def pack_chunks(
    chunks: list[RetrievedChunk],
    *,
    mode: PackerMode = "p1",
    max_chars: int = DEFAULT_CONTEXT_MAX_CHARS,
) -> str:
    """Pack retrieved chunks for synthesis prompts (ADR-041).

    ``mode="p1"`` — Source/URL headers (prod default).
    ``mode="p3"`` — P1 after document dedupe, then char budget.
    """
    if mode == "p1":
        return pack_p1(chunks)
    if mode == "p3":
        return truncate_context(pack_p1(dedupe_by_document(chunks)), max_chars=max_chars)
    msg = f"unsupported packer mode: {mode!r}"
    raise ValueError(msg)
