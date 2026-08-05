"""Embed pin helpers — e5 prefixes + runtime resolution (ADR-048 / F70).

[Corpus: feature-list.md §F70]
[Spec: docs/config-spec.md §VECINITA_EMBED_RUNTIME, §VECINITA_EMBED_E5_PREFIXES]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
"""

from __future__ import annotations

import os
from typing import Final, Literal, cast

from vecinita_embedding_client.client import EMBEDDING_DIMENSION, EmbeddingClientError

EmbedTextMode = Literal["query", "passage"]
EmbedRuntime = Literal["fastembed", "sentence_transformers", "onnx"]
E5PrefixSetting = Literal["auto", "on", "off"]

_ENV_MODEL_ID: Final[str] = "VECINITA_EMBEDDING_MODEL_ID"
_ENV_RUNTIME: Final[str] = "VECINITA_EMBED_RUNTIME"
_ENV_E5_PREFIXES: Final[str] = "VECINITA_EMBED_E5_PREFIXES"
_DEFAULT_RUNTIME: Final[EmbedRuntime] = "fastembed"
_DEFAULT_E5_PREFIXES: Final[E5PrefixSetting] = "auto"
_ALLOWED_RUNTIMES: Final[frozenset[str]] = frozenset(
    {"fastembed", "sentence_transformers", "onnx"},
)
_ALLOWED_E5_SETTINGS: Final[frozenset[str]] = frozenset({"auto", "on", "off"})
_E5_NEEDLE: Final[str] = "e5"


def is_e5_family_model(model_id: str) -> bool:
    """Return True when ``model_id`` is an e5-family HuggingFace id."""
    return _E5_NEEDLE in model_id.casefold()


def _resolve_model_id(model_id: str | None) -> str:
    if model_id is not None and model_id != "":
        return model_id
    return os.environ.get(_ENV_MODEL_ID, "")


def _resolve_e5_setting(setting: str | None) -> E5PrefixSetting:
    raw = setting if setting is not None else os.environ.get(_ENV_E5_PREFIXES)
    if raw is None or raw == "":
        return _DEFAULT_E5_PREFIXES
    if raw not in _ALLOWED_E5_SETTINGS:
        msg = f"{_ENV_E5_PREFIXES} must be one of {sorted(_ALLOWED_E5_SETTINGS)}, got {raw!r}"
        raise EmbeddingClientError(msg)
    return cast("E5PrefixSetting", raw)


def e5_prefixes_enabled(*, model_id: str, setting: str | None = None) -> bool:
    """Whether query/passage prefixes should be applied for this pin."""
    resolved = _resolve_e5_setting(setting)
    if resolved == "off":
        return False
    if resolved == "on":
        return True
    return is_e5_family_model(model_id)


def apply_embed_prefix(
    text: str,
    *,
    mode: EmbedTextMode,
    model_id: str | None = None,
    prefixes: str | None = None,
) -> str:
    r"""Apply e5 ``query:`` / ``passage:`` prefixes when enabled for the pin.

    Ask path uses ``mode="query"``; ingest and re-embed use ``mode="passage"``.
    """
    resolved_model = _resolve_model_id(model_id)
    if not e5_prefixes_enabled(model_id=resolved_model, setting=prefixes):
        return text
    prefix = f"{mode}: "
    if text.startswith(prefix):
        return text
    return f"{prefix}{text}"


def resolve_embed_runtime(raw: str | None = None) -> EmbedRuntime:
    """Resolve ``VECINITA_EMBED_RUNTIME`` to an allowed Modal host value."""
    value = raw if raw is not None else os.environ.get(_ENV_RUNTIME)
    if value is None or value == "":
        return _DEFAULT_RUNTIME
    if value not in _ALLOWED_RUNTIMES:
        msg = f"{_ENV_RUNTIME} must be one of {sorted(_ALLOWED_RUNTIMES)}, got {value!r}"
        raise EmbeddingClientError(msg)
    return cast("EmbedRuntime", value)


def assert_embedding_dimension(vector: list[float]) -> list[float]:
    """Hard-fail unless ``vector`` length is ``EMBEDDING_DIMENSION`` (384)."""
    if len(vector) != EMBEDDING_DIMENSION:
        msg = f"expected {EMBEDDING_DIMENSION}-dim embedding, got {len(vector)}"
        raise EmbeddingClientError(msg)
    return vector
