"""Soft language L1 retrieve helper (F44, #162).

Same-language first pass; when ``enabled`` and that pass is empty above the
caller's score threshold, retry without a language filter. Default off (L0-strict).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vecinita_rag.types import RetrievedChunk

LangRetrieveFn = Callable[[str, str | None], list["RetrievedChunk"]]


@dataclass(frozen=True, slots=True)
class SoftLanguageResult:
    """Chunks plus whether an unfiltered L1 fallback pass ran."""

    chunks: list[RetrievedChunk]
    language: str
    fallback_triggered: bool
    first_pass_empty: bool


def soft_language_retrieve(
    question: str,
    *,
    language: str,
    retrieve_fn: LangRetrieveFn,
    enabled: bool = False,
) -> SoftLanguageResult:
    """Retrieve with optional L1 soft language fallback.

    Parameters
    ----------
    question :
        User query text.
    language :
        Detected / effective query locale for the same-lang first pass.
    retrieve_fn :
        ``(question, language) -> chunks`` where ``language=None`` means unfiltered.
    enabled :
        When False (default), never retry without language (L0-strict).
    """
    first = retrieve_fn(question, language)
    if first:
        return SoftLanguageResult(
            chunks=first,
            language=language,
            fallback_triggered=False,
            first_pass_empty=False,
        )
    if not enabled:
        return SoftLanguageResult(
            chunks=[],
            language=language,
            fallback_triggered=False,
            first_pass_empty=True,
        )
    second = retrieve_fn(question, None)
    return SoftLanguageResult(
        chunks=second,
        language=language,
        fallback_triggered=True,
        first_pass_empty=True,
    )
