"""BUG-2026-08-05 — E1 pin must not die under default FastEmbed runtime.

[Corpus: feature-list.md §F70]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
[Spec: docs/decisions/evolve-decisions.md §S027-D12]
[Spec: docs/bug-reports/BUG-2026-08-05-embed-e1-unsupported-fastembed.md]
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Protocol, cast

from vecinita_embedding_client.modal_pins import DEFAULT_EMBEDDING_MODEL_ID

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from _pytest.monkeypatch import MonkeyPatch


class _NamedBackend(Protocol):
    name: str


class _FakeFastEmbed:
    def __init__(self, model_id: str, cache_dir: str) -> None:
        del cache_dir
        if model_id == DEFAULT_EMBEDDING_MODEL_ID:
            msg = (
                f"Model {model_id} is not supported in TextEmbedding. "
                "Please check the supported models using "
                "`TextEmbedding.list_supported_models()`"
            )
            raise ValueError(msg)
        self.name = "fastembed"


class _FakeST:
    def __init__(self, model_id: str, cache_dir: str) -> None:
        del model_id, cache_dir
        self.name = "sentence_transformers"


def _embedding_app() -> ModuleType:
    return importlib.import_module("infra.modal.embedding_app")


def _load_backend_fn(emb: ModuleType) -> Callable[[str], _NamedBackend]:
    return cast("Callable[[str], _NamedBackend]", emb._load_backend)  # noqa: SLF001


def test_load_backend_falls_back_to_st_when_fastembed_rejects_e1(
    monkeypatch: MonkeyPatch,
) -> None:
    """S027-D12: unloadable FastEmbed pin → sentence_transformers (H3 hang root cause)."""
    emb = _embedding_app()
    monkeypatch.setenv("VECINITA_EMBED_RUNTIME", "fastembed")
    monkeypatch.setenv("VECINITA_EMBEDDING_MODEL_ID", DEFAULT_EMBEDDING_MODEL_ID)
    monkeypatch.setattr(emb, "_FastEmbedBackend", _FakeFastEmbed)
    monkeypatch.setattr(emb, "_SentenceTransformersBackend", _FakeST)

    backend = _load_backend_fn(emb)("/models")
    assert backend.name == "sentence_transformers"


def test_load_backend_keeps_fastembed_when_model_supported(
    monkeypatch: MonkeyPatch,
) -> None:
    """Supported FastEmbed pins must not force an ST fallback."""
    emb = _embedding_app()
    monkeypatch.setenv("VECINITA_EMBED_RUNTIME", "fastembed")
    monkeypatch.setenv("VECINITA_EMBEDDING_MODEL_ID", "BAAI/bge-small-en-v1.5")
    monkeypatch.setattr(emb, "_FastEmbedBackend", _FakeFastEmbed)
    monkeypatch.setattr(emb, "_SentenceTransformersBackend", _FakeST)

    backend = _load_backend_fn(emb)("/models")
    assert backend.name == "fastembed"
