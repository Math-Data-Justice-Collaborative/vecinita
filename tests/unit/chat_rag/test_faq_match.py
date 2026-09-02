"""TC-320-01: FAQ normalize + exact match (F85 / EV-320)."""

from __future__ import annotations

from pathlib import Path

import pytest
from vecinita_chat_rag_backend.faq.match import (
    FaqEntry,
    FaqStore,
    default_faq_store_path,
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


def test_match_faq_empty_normalized_question_misses() -> None:
    """Punctuation-only input does not match."""
    store = FaqStore(
        entries=(
            FaqEntry(
                id="what-is-vecinita",
                language="en",
                variants=("What is Vecinita?",),
                answer="ok",
            ),
        )
    )
    assert match_faq(store, "???", language="en") is None
    assert normalize_faq_question("   ") == ""


def test_load_faq_store_rejects_invalid_shapes(tmp_path: Path) -> None:
    """Loader fails closed on non-mapping root, missing entries, and bad language."""
    not_map = tmp_path / "list.yaml"
    _ = not_map.write_text("- not a mapping\n", encoding="utf-8")
    with pytest.raises(TypeError, match="mapping"):
        _ = load_faq_store(not_map)

    no_entries = tmp_path / "no_entries.yaml"
    _ = no_entries.write_text("entries: {}\n", encoding="utf-8")
    with pytest.raises(TypeError, match="entries list"):
        _ = load_faq_store(no_entries)

    bad_lang = tmp_path / "bad_lang.yaml"
    _ = bad_lang.write_text(
        "entries:\n  - id: x\n    language: fr\n    variants: [Hi]\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="must be en"):
        _ = load_faq_store(bad_lang)

    empty_variants = tmp_path / "empty_variants.yaml"
    _ = empty_variants.write_text(
        "entries:\n  - id: x\n    language: en\n    variants: []\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="variants"):
        _ = load_faq_store(empty_variants)

    not_entry_map = tmp_path / "not_entry.yaml"
    _ = not_entry_map.write_text("entries:\n  - just-a-string\n", encoding="utf-8")
    with pytest.raises(TypeError, match="FAQ entry must be a mapping"):
        _ = load_faq_store(not_entry_map)

    whitespace_variants = tmp_path / "ws_variants.yaml"
    _ = whitespace_variants.write_text(
        "entries:\n  - id: x\n    language: en\n    variants: ['  ']\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no valid string variants"):
        _ = load_faq_store(whitespace_variants)

    missing_id = tmp_path / "missing_id.yaml"
    _ = missing_id.write_text(
        "entries:\n  - language: en\n    variants: [Hi]\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="id"):
        _ = load_faq_store(missing_id)

    empty_answer = tmp_path / "empty_answer.yaml"
    _ = empty_answer.write_text(
        "entries:\n  - id: x\n    language: en\n    variants: [Hi]\n    answer: '  '\n",
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="answer"):
        _ = load_faq_store(empty_answer)

    not_list_variants = tmp_path / "not_list_variants.yaml"
    _ = not_list_variants.write_text(
        "entries:\n  - id: x\n    language: en\n    variants: Hi\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="variants"):
        _ = load_faq_store(not_list_variants)

    non_string_id = tmp_path / "non_string_id.yaml"
    _ = non_string_id.write_text(
        "entries:\n  - id: 1\n    language: en\n    variants: [Hi]\n    answer: A\n",
        encoding="utf-8",
    )
    with pytest.raises(TypeError, match="id"):
        _ = load_faq_store(non_string_id)


def test_load_faq_store_spanish_entry_and_skips_non_string_variants(
    tmp_path: Path,
) -> None:
    """Language es parses; non-string variant items are dropped (TC-320-01)."""
    path = tmp_path / "es.yaml"
    _ = path.write_text(
        "entries:\n  - id: hola\n    language: es\n    variants: [1, '¿Hola?', '  ']\n    answer: Hola\n",
        encoding="utf-8",
    )
    store = load_faq_store(path)
    assert len(store.entries) == 1
    entry = store.entries[0]
    assert entry.language == "es"
    assert entry.variants == ("¿Hola?",)
    hit = match_faq(store, "¿Hola?", language="es")
    assert hit is not None
    assert hit.answer == "Hola"


def test_default_faq_store_path_exists() -> None:
    """Packaged seed YAML is present next to the matcher."""
    path = default_faq_store_path()
    assert path.is_file()
    store = load_faq_store(path)
    assert store.entries
