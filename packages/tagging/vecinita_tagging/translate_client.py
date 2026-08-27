"""LLM-backed chunk translation for ingest bilingual path (F75 / #251)."""

from __future__ import annotations

import os
from typing import Final

from vecinita_llm_client import LlmClient, LlmClientError, format_instruct_prompt
from vecinita_shared_schemas.data_management import IngestLocale

TargetLocale = IngestLocale

_ENV_TRANSLATE_MAX_TOKENS: Final[str] = "VECINITA_LLM_TRANSLATE_MAX_TOKENS"
_DEFAULT_TRANSLATE_MAX_TOKENS: Final[int] = 512


class LlmTranslateClientError(RuntimeError):
    """Chunk translation request or response validation failed."""


class LlmTranslateClient:
    """Translate corpus chunks via Modal vecinita-llm (ADR-037)."""

    def __init__(
        self,
        llm_client: LlmClient,
        *,
        translate_max_tokens: int | None = None,
    ) -> None:
        """Wrap ``llm_client`` with translation-specific token limits."""
        self._llm = llm_client
        if translate_max_tokens is not None:
            self._translate_max_tokens = translate_max_tokens
        else:
            self._translate_max_tokens = int(
                os.environ.get(_ENV_TRANSLATE_MAX_TOKENS, _DEFAULT_TRANSLATE_MAX_TOKENS)
            )

    def close(self) -> None:
        """Close the underlying LLM client."""
        self._llm.close()

    def translate_chunk(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        """Return ``text`` translated to ``target_locale``."""
        if source_locale == target_locale:
            return text
        src = "es" if source_locale == "es" else "en"
        tgt = "es" if target_locale == "es" else "en"
        prompt = _build_translate_prompt(
            text=text,
            source_locale=src,
            target_locale=tgt,
        )
        try:
            translated = self._llm.generate(
                prompt,
                max_tokens=self._translate_max_tokens,
                temperature=0.1,
            )
        except LlmClientError as exc:
            raise LlmTranslateClientError(str(exc)) from exc
        cleaned = translated.strip()
        if not cleaned:
            msg = "translation response was empty"
            raise LlmTranslateClientError(msg)
        return cleaned


def _build_translate_prompt(
    *,
    text: str,
    source_locale: TargetLocale,
    target_locale: TargetLocale,
) -> str:
    target_name = "Spanish" if target_locale == "es" else "English"
    source_name = "Spanish" if source_locale == "es" else "English"
    system = (
        "You translate community resource text for a bilingual neighborhood help site. "
        + "Preserve program names, addresses, phone numbers, and URLs exactly. "
        + "Do not add personal data or invented details. "
        + f"Return only the {target_name} translation with no preamble."
    )
    user = f"Translate this {source_name} excerpt to {target_name}:\n\n{text}"
    return format_instruct_prompt(system=system, user=user)
