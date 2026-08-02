"""Unit tests for EV-016 #159 offline embed retrieval helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_embed_retrieval.py"
)
_SUMMARY_N = 3
_SUMMARY_EN_N = 2
_SUMMARY_EN_HIT = 0.5


class _CorpusChunk(Protocol):
    url: str


class _GoldenHitCase(Protocol):
    locale: str


class _CorpusChunkCtor(Protocol):
    def __call__(
        self,
        chunk_id: str,
        url: str,
        language: str,
        text: str,
    ) -> _CorpusChunk: ...


class _GoldenHitCaseCtor(Protocol):
    def __call__(
        self,
        case_id: str,
        locale: str,
        question: str,
        expected_doc_url: str,
    ) -> _GoldenHitCase: ...


class _SpikeEmbedRetrievalMod(Protocol):
    CorpusChunk: _CorpusChunkCtor
    GoldenHitCase: _GoldenHitCaseCtor

    def cosine_similarity(self, a: list[float], b: list[float]) -> float: ...

    def url_match(self, expected: str, retrieved: list[str]) -> bool: ...

    def top_k_urls(
        self,
        query_vec: list[float],
        chunk_vecs: list[list[float]],
        chunks: list[_CorpusChunk],
        *,
        top_k: int,
    ) -> list[str]: ...

    def summarize_hits(
        self,
        rows: list[tuple[_GoldenHitCase, bool]],
    ) -> dict[str, float | int]: ...


def _load_mod() -> _SpikeEmbedRetrievalMod:
    name = "spike_embed_retrieval"
    existing = sys.modules.get(name)
    if existing is not None:
        return cast("_SpikeEmbedRetrievalMod", existing)
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return cast("_SpikeEmbedRetrievalMod", mod)


def test_cosine_similarity_identical_vectors_is_one() -> None:
    """Identical unit vectors have cosine 1."""
    mod = _load_mod()
    assert mod.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_url_match_tolerates_trailing_slash() -> None:
    """Expected URL matching ignores trailing slashes."""
    mod = _load_mod()
    assert mod.url_match("https://x.example/es/a/", ["https://x.example/es/a"])


def test_top_k_urls_returns_distinct_document_urls() -> None:
    """Top-k collapses duplicate URLs from multiple chunks."""
    mod = _load_mod()
    chunks: list[_CorpusChunk] = [
        mod.CorpusChunk("1", "https://a.example/", "en", "alpha"),
        mod.CorpusChunk("2", "https://a.example/", "en", "alpha2"),
        mod.CorpusChunk("3", "https://b.example/", "es", "beta"),
    ]
    # query closer to chunk 3
    q = [0.0, 1.0]
    vecs = [[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]]
    urls = mod.top_k_urls(q, vecs, chunks, top_k=2)
    assert urls == ["https://b.example/", "https://a.example/"]


def test_summarize_hits_splits_en_es() -> None:
    """Locale breakdown uses en/es hit rates."""
    mod = _load_mod()
    rows: list[tuple[_GoldenHitCase, bool]] = [
        (mod.GoldenHitCase("a", "en", "q", "https://a"), True),
        (mod.GoldenHitCase("b", "en", "q", "https://a"), False),
        (mod.GoldenHitCase("c", "es", "q", "https://b"), True),
    ]
    summary = mod.summarize_hits(rows)
    assert summary["n"] == _SUMMARY_N
    assert summary["hit_rate"] == _SUMMARY_EN_N / _SUMMARY_N
    assert summary["en_n"] == _SUMMARY_EN_N
    assert summary["en_hit"] == _SUMMARY_EN_HIT
    assert summary["es_n"] == 1
    assert summary["es_hit"] == 1.0
