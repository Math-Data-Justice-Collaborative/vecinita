"""TC-320-01: FAQ normalize + exact match (F85 / EV-320)."""

from __future__ import annotations

from pathlib import Path

from vecinita_chat_rag_backend.faq.match import (
    FaqEntry,
    FaqStore,
    load_faq_store,
    match_faq,
    normalize_faq_question,
)

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "faq" / "seed_faq.yaml"
_MIN_SEED_ENTRIES = 4


def test_normalize_faq_question_collapses_case_whitespace_and_punct() -> None:
    """Normalization is conservative: casefold, collapse space, strip trailing ?/punct."""
    assert normalize_faq_question("  What IS Vecinita?! ") == "what is vecinita"
    assert normalize_faq_question("¿Qué es Vecinita?") == "qué es vecinita"


def test_match_faq_exact_and_normalized_same_language() -> None:
    """Same-language exact/normalized variants hit; paraphrase and cross-lang miss."""
    store = FaqStore(
        entries=(
            FaqEntry(
                id="what-is-vecinita",
                language="en",
                variants=("What is Vecinita?", "What is VECINA?"),
                answer="Vecinita is a bilingual community Q&A assistant.",
            ),
            FaqEntry(
                id="what-is-vecinita-es",
                language="es",
                variants=("¿Qué es Vecinita?",),
                answer="Vecinita es un asistente bilingüe de preguntas frecuentes.",
            ),
        )
    )
    hit = match_faq(store, "what is  vecinita?", language="en")
    assert hit is not None
    assert hit.id == "what-is-vecinita"
    assert "bilingual" in hit.answer.lower()

    assert match_faq(store, "Tell me about Vecinita please", language="en") is None
    assert match_faq(store, "What is Vecinita?", language="es") is None

    es_hit = match_faq(store, "¿Qué es Vecinita?", language="es")
    assert es_hit is not None
    assert es_hit.id == "what-is-vecinita-es"


def test_load_faq_store_from_yaml_fixture() -> None:
    """Seed YAML loads bilingual reviewed entries (RD-320-10)."""
    store = load_faq_store(_FIXTURE)
    assert len(store.entries) >= _MIN_SEED_ENTRIES
    hit = match_faq(store, "Do I need immigration status?", language="en")
    assert hit is not None
    assert hit.id == "immigration-status"


def test_match_faq_empty_store_misses() -> None:
    """Empty store never matches."""
    assert match_faq(FaqStore(entries=()), "What is Vecinita?", language="en") is None
