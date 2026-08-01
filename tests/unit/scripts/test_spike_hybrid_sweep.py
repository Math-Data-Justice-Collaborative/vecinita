"""Unit tests for EV-016 hybrid sweep helpers (S019-D29)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from vecinita_rag.types import RetrievedChunk

if TYPE_CHECKING:
    from types import ModuleType

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "scripts"
    / "spike_hybrid_sweep.py"
)


def _load() -> ModuleType:
    """Load the session hybrid spike script as a module."""
    name = "spike_hybrid_sweep"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _chunk(*, text: str, language: str, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text=text,
        score=score,
        title="Title",
        url="https://example.org/doc",
        language=language,
    )


def test_pack_p1_includes_title_and_url() -> None:
    """P1 packing prefixes each chunk with Source/URL headers."""
    mod = _load()
    packed = mod.pack_p1([_chunk(text="body", language="en")])
    assert "Source: Title" in packed
    assert "URL: https://example.org/doc" in packed
    assert "body" in packed


def test_pack_p3_dedupes_and_caps() -> None:
    """P3 keeps one chunk per document and respects char budget."""
    mod = _load()
    doc = uuid4()
    high = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=doc,
        text="high-score text",
        score=0.9,
        title="A",
        url="https://example.org/a",
        language="en",
    )
    low = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=doc,
        text="low-score text",
        score=0.1,
        title="A",
        url="https://example.org/a",
        language="en",
    )
    packed = mod.pack_p3([low, high], max_chars=80)
    assert "high-score" in packed
    assert "low-score" not in packed
    assert len(packed) <= 80


def test_cross_lang_share_counts_mismatches() -> None:
    """Cross-lang share is fraction of chunks whose language != query lang."""
    mod = _load()
    chunks = [
        _chunk(text="a", language="en"),
        _chunk(text="b", language="es"),
        _chunk(text="c", language="en"),
    ]
    assert mod.cross_lang_share(chunks, "en") == 1 / 3


def test_answer_lang_match_compares_detected_to_locale() -> None:
    """Answer language match is true when detected answer lang equals locale."""
    mod = _load()
    assert mod.answer_lang_match(answer="The clinic is open Monday.", locale="en") is True
    assert mod.answer_lang_match(answer="La clínica está abierta.", locale="es") is True
    assert mod.answer_lang_match(answer="The clinic is open Monday.", locale="es") is False


def test_hybrid_rewrites_spanish_locale() -> None:
    """Spanish questions get a Providence RI locale rewrite without English how→what."""
    mod = _load()
    rewrites = mod.hybrid_rewrites("¿Qué es Nuevas Voces?", locale="es")
    assert rewrites[0] == "¿Qué es Nuevas Voces?"
    assert any("Providence" in r for r in rewrites)
    assert len(rewrites) <= 3


def test_locale_breakdown_aggregates_en_and_es() -> None:
    """Locale breakdown reports separate means for en and es rows."""
    mod = _load()
    rows = [
        {
            "locale": "en",
            "retrieval_pass": True,
            "faithfulness": 1.0,
            "answer_relevancy": 0.5,
            "answer_lang_match": True,
            "cross_lang_share": 0.0,
        },
        {
            "locale": "es",
            "retrieval_pass": False,
            "faithfulness": 0.0,
            "answer_relevancy": 0.25,
            "answer_lang_match": False,
            "cross_lang_share": 0.5,
        },
    ]
    breakdown = mod.locale_breakdown(rows)
    assert breakdown["en"]["n"] == 1
    assert breakdown["es"]["n"] == 1
    assert breakdown["en"]["answer_relevancy"] == 0.5
    assert breakdown["es"]["answer_lang_match_rate"] == 0.0
    assert breakdown["es"]["mean_cross_lang_share"] == 0.5


def test_rerank_r1_prefers_title_overlap() -> None:
    """R1 boosts chunks whose title overlaps the question."""
    mod = _load()
    weak = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="unrelated",
        score=0.55,
        title="Other",
        url="https://example.org/o",
        language="en",
    )
    strong = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="clinic hours detail",
        score=0.5,
        title="Clinic hours",
        url="https://example.org/c",
        language="en",
    )
    ranked = mod.rerank_r1("What are clinic hours?", [weak, strong], top_k=1)
    assert ranked[0].title == "Clinic hours"
