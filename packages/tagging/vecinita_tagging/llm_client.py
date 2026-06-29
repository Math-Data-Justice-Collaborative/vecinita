"""LLM-backed document tagging via vecinita-llm (ADR-015 TP-014)."""

from __future__ import annotations

import json
import os
import re
from typing import Final, cast

from vecinita_llm_client import LlmClient, LlmClientError
from vecinita_shared_schemas.json_types import as_json_object

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
        """Wrap ``llm_client`` with tag-specific token limits."""
        self._llm = llm_client
        if tag_max_tokens is not None:
            self._tag_max_tokens = tag_max_tokens
        else:
            self._tag_max_tokens = int(os.environ.get(_ENV_TAG_MAX_TOKENS, _DEFAULT_TAG_MAX_TOKENS))

    def close(self) -> None:
        """Close the underlying LLM client."""
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
            msg = "max_tags must be at least 1"
            raise LlmTagClientError(msg)
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
        "<|im_start|>system\n"
        "You assign corpus tags for a community document. "
        'Respond with JSON only: {"tags": ["slug1", "slug2"]}. '
        "Use only slugs from the allowed list.\n"
        "<|im_start|>user\n"
        f"Document language: {language}\n"
        f"Allowed tag slugs (choose up to {max_tags}): {vocab_csv}\n"
        f"Title: {title}\n"
        f"Text:\n{text}\n"
        "<|im_start|>assistant\n"
    )


def _parse_tag_slugs(raw: str) -> list[str]:
    payload = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", payload, re.DOTALL)
    if fence:
        payload = fence.group(1)
    try:
        data = as_json_object(cast("object", json.loads(payload)))
    except json.JSONDecodeError as exc:
        msg = f"tag response is not valid JSON: {exc}"
        raise LlmTagClientError(msg) from exc
    tags = data.get("tags")
    if not isinstance(tags, list):
        msg = "tag response JSON must contain a 'tags' string array"
        raise LlmTagClientError(msg)
    tag_slugs: list[str] = []
    for tag in cast("list[object]", tags):
        if not isinstance(tag, str):
            msg = "tag response JSON must contain a 'tags' string array"
            raise LlmTagClientError(msg)
        tag_slugs.append(tag)
    return tag_slugs
