"""Unit tests for EV-016 #159 offline embed retrieval helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_embed_retrieval.py"
)


def _load_mod() -> object:
    import sys

    spec = importlib.util.spec_from_file_location("spike_embed_retrieval", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_cosine_similarity_identical_vectors_is_one() -> None:
    """Identical unit vectors have cosine 1."""
    mod = _load_mod()
    assert mod.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0  # type: ignore[attr-defined]


def test_url_match_tolerates_trailing_slash() -> None:
    """Expected URL matching ignores trailing slashes."""
    mod = _load_mod()
    assert mod.url_match("https://x.example/es/a/", ["https://x.example/es/a"])  # type: ignore[attr-defined]


def test_top_k_urls_returns_distinct_document_urls() -> None:
    """Top-k collapses duplicate URLs from multiple chunks."""
    mod = _load_mod()
    chunk_cls = mod.CorpusChunk  # type: ignore[attr-defined]
    chunks = [
        chunk_cls("1", "https://a.example/", "en", "alpha"),
        chunk_cls("2", "https://a.example/", "en", "alpha2"),
        chunk_cls("3", "https://b.example/", "es", "beta"),
    ]
    # query closer to chunk 3
    q = [0.0, 1.0]
    vecs = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]
    urls = mod.top_k_urls(q, vecs, chunks, top_k=2)  # type: ignore[attr-defined]
    assert urls == ["https://b.example/", "https://a.example/"]


def test_summarize_hits_splits_en_es() -> None:
    """Locale breakdown uses en/es hit rates."""
    mod = _load_mod()
    case_cls = mod.GoldenHitCase  # type: ignore[attr-defined]
    rows = [
        (case_cls("a", "en", "q", "https://a"), True),
        (case_cls("b", "en", "q", "https://a"), False),
        (case_cls("c", "es", "q", "https://b"), True),
    ]
    summary = mod.summarize_hits(rows)  # type: ignore[attr-defined]
    assert summary["n"] == 3
    assert summary["hit_rate"] == 2 / 3
    assert summary["en_n"] == 2
    assert summary["en_hit"] == 0.5
    assert summary["es_n"] == 1
    assert summary["es_hit"] == 1.0
