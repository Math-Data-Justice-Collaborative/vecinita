"""T119.1 tests - e5 prefixes, embed runtime enum, dim=384 (TC-233-234 / AC-ME1-ME2).

[Corpus: feature-list.md §F70]
[Spec: docs/test-plan.md §TC-233, §TC-234]
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]
[Spec: docs/config-spec.md §VECINITA_EMBED_RUNTIME, §VECINITA_EMBED_E5_PREFIXES]
"""

from __future__ import annotations

import pytest
from vecinita_embedding_client import (
    EMBEDDING_DIMENSION,
    EmbeddingClientError,
    apply_embed_prefix,
    assert_embedding_dimension,
    e5_prefixes_enabled,
    is_e5_family_model,
    resolve_embed_runtime,
)

_E1 = "intfloat/multilingual-e5-small"
_E0 = "BAAI/bge-small-en-v1.5"
_QUERY_TEXT = "¿Qué es la justicia?"
_PASSAGE_TEXT = "La justicia restaurativa prioriza la reparación del daño."


def test_is_e5_family_model_detects_multilingual_e5() -> None:
    """E1 pin is treated as e5-family for prefix rules (TC-233)."""
    assert is_e5_family_model(_E1) is True
    assert is_e5_family_model(_E0) is False
    assert (
        is_e5_family_model("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2") is False
    )


def test_e5_prefixes_enabled_auto_on_for_e5_pin() -> None:
    """``auto`` enables prefixes for e5 pins and disables for non-e5 (TC-233)."""
    assert e5_prefixes_enabled(model_id=_E1, setting="auto") is True
    assert e5_prefixes_enabled(model_id=_E0, setting="auto") is False
    assert e5_prefixes_enabled(model_id=_E1, setting="on") is True
    assert e5_prefixes_enabled(model_id=_E0, setting="on") is True
    assert e5_prefixes_enabled(model_id=_E1, setting="off") is False


def test_apply_embed_prefix_query_and_passage_for_e5() -> None:
    """Ask path gets ``query:``; ingest/re-embed gets ``passage:`` (AC-ME2 / TC-233)."""
    assert apply_embed_prefix(_QUERY_TEXT, mode="query", model_id=_E1) == (f"query: {_QUERY_TEXT}")
    assert apply_embed_prefix(_PASSAGE_TEXT, mode="passage", model_id=_E1) == (
        f"passage: {_PASSAGE_TEXT}"
    )


def test_apply_embed_prefix_idempotent_when_already_prefixed() -> None:
    """Does not double-prefix texts that already start with the mode prefix."""
    already = f"query: {_QUERY_TEXT}"
    assert apply_embed_prefix(already, mode="query", model_id=_E1) == already
    already_p = f"passage: {_PASSAGE_TEXT}"
    assert apply_embed_prefix(already_p, mode="passage", model_id=_E1) == already_p


def test_apply_embed_prefix_noop_for_non_e5_under_auto() -> None:
    """Non-e5 pins under ``auto`` leave text unchanged (TC-233)."""
    assert apply_embed_prefix(_QUERY_TEXT, mode="query", model_id=_E0) == _QUERY_TEXT
    assert apply_embed_prefix(_PASSAGE_TEXT, mode="passage", model_id=_E0) == _PASSAGE_TEXT


def test_resolve_embed_runtime_accepts_allowed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``VECINITA_EMBED_RUNTIME`` accepts the three Modal host values (TC-234)."""
    for value in ("fastembed", "sentence_transformers", "onnx"):
        monkeypatch.setenv("VECINITA_EMBED_RUNTIME", value)
        assert resolve_embed_runtime() == value


def test_resolve_embed_runtime_default_fastembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unset runtime defaults to ``fastembed`` (config-spec / TC-234)."""
    monkeypatch.delenv("VECINITA_EMBED_RUNTIME", raising=False)
    assert resolve_embed_runtime() == "fastembed"


def test_resolve_embed_runtime_rejects_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown runtime values raise EmbeddingClientError (TC-234)."""
    monkeypatch.setenv("VECINITA_EMBED_RUNTIME", "openai")
    with pytest.raises(EmbeddingClientError, match="VECINITA_EMBED_RUNTIME"):
        resolve_embed_runtime()


def test_assert_embedding_dimension_accepts_384() -> None:
    """384-d vectors pass dimension hard-fail (AC-ME1 / TC-234)."""
    vector = [0.01] * EMBEDDING_DIMENSION
    assert assert_embedding_dimension(vector) == vector


def test_assert_embedding_dimension_rejects_wrong_len() -> None:
    """Non-384 vectors raise EmbeddingClientError mentioning 384 (AC-ME1)."""
    with pytest.raises(EmbeddingClientError, match="384"):
        assert_embedding_dimension([0.1, 0.2, 0.3])
