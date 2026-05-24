"""LLM-backed document tagging via vecinita-llm (ADR-015 TP-014)."""

from __future__ import annotations

import json
import os
import re
from typing import Final

from vecinita_llm_client import LlmClient, LlmClientError

_ENV_TAG_MAX_TOKENS: Final[str] = "VECINITA_LLM_TAG_MAX_TOKENS"
_DEFAULT_TAG_MAX_TOKENS: Final[int] = 128


class LlmTagClientError(RuntimeError):
    """Tag inference request or response validation failed."""


class LlmTagClient:
    """Infer document tags from Modal vLLM JSON completions."""

    def __init__(
        self,
        llm_client: LlmClient,
        *,
        tag_max_tokens: int | None = None,
    ) -> None:
        self._llm = llm_client
        if tag_max_tokens is not None:
            self._tag_max_tokens = tag_max_tokens
        else:
            self._tag_max_tokens = int(os.environ.get(_ENV_TAG_MAX_TOKENS, _DEFAULT_TAG_MAX_TOKENS))

    def close(self) -> None:
        self._llm.close()

    def infer_document_tags(
        self,
        *,
        title: str,
        text: str,
        language: str,
        vocabulary: list[str],
        max_tags: int = 10,
    ) -> list[str]:
        """Return tag slugs inferred for a document body."""
        if max_tags < 1:
            raise LlmTagClientError("max_tags must be at least 1")
        prompt = _build_document_tag_prompt(
            title=title,
            text=text,
            language=language,
            vocabulary=vocabulary,
            max_tags=max_tags,
        )
        try:
            raw = self._llm.generate(
                prompt,
                max_tokens=self._tag_max_tokens,
                temperature=0.0,
            )
        except LlmClientError as exc:
            raise LlmTagClientError(str(exc)) from exc

        slugs = _parse_tag_slugs(raw)
        allowed = set(vocabulary)
        filtered = [slug for slug in slugs if slug in allowed]
        return filtered[:max_tags]

    def infer_query_tags(
        self,
        *,
        question: str,
        vocabulary: list[str],
        max_tags: int = 3,
    ) -> list[str]:
        """Return tag slugs inferred from a community question."""
        return self.infer_document_tags(
            title="",
            text=question,
            language="en",
            vocabulary=vocabulary,
            max_tags=max_tags,
        )


def _build_document_tag_prompt(
    *,
    title: str,
    text: str,
    language: str,
    vocabulary: list[str],
    max_tags: int,
) -> str:
    vocab_csv = ", ".join(vocabulary)
    return (
        "You assign corpus tags for a community document.\n"
        f"Document language: {language}\n"
        f"Allowed tag slugs (choose up to {max_tags}): {vocab_csv}\n"
        f"Title: {title}\n"
        f"Text:\n{text}\n"
        'Respond with JSON only: {"tags": ["slug1", "slug2"]}\n'
        "Use only slugs from the allowed list."
    )


def _parse_tag_slugs(raw: str) -> list[str]:
    payload = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", payload, re.DOTALL)
    if fence:
        payload = fence.group(1)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise LlmTagClientError(f"tag response is not valid JSON: {exc}") from exc
    tags = data.get("tags")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise LlmTagClientError("tag response JSON must contain a 'tags' string array")
    return tags
