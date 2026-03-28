import pytest

from src.utils.tags import (
    MAX_TAG_COUNT,
    MAX_TAG_LENGTH,
    _normalize_noncanonical_tag,
    build_bilingual_tag_fields,
    canonicalize_tag,
    infer_tags_from_text,
    normalize_tag_fields,
    normalize_tags,
    parse_tags_input,
)

pytestmark = pytest.mark.unit


def test_canonicalize_tag_normalizes_aliases_and_ascii():
    assert canonicalize_tag(" Inmigración ") == "immigration"
    assert canonicalize_tag("RI") == "rhode island"
    assert canonicalize_tag("") == ""


def test_normalize_tags_deduplicates_and_filters_invalid_values():
    result = normalize_tags(["Housing", "housing", "bad@tag", "", "  Vivienda  "])

    assert result == ["housing"]


def test_parse_tags_input_normalizes_comma_separated_values():
    assert parse_tags_input("ri, inmigracion, legal aid") == [
        "rhode island",
        "immigration",
        "legal aid",
    ]


def test_normalize_tag_fields_updates_and_removes_empty_fields():
    normalized, changed = normalize_tag_fields(
        {
            "tags": ["RI", "ri", "housing assistance"],
            "service_tags": [],
            "other": "keep",
        }
    )

    assert changed is True
    assert normalized["tags"] == ["rhode island", "housing assistance"]
    assert "service_tags" not in normalized
    assert normalized["other"] == "keep"


def test_normalize_tags_handles_none_long_values_and_max_count():
    long_tag = "x" * (MAX_TAG_LENGTH + 10)
    many_tags = [f"tag{index}" for index in range(MAX_TAG_COUNT + 5)]

    result = normalize_tags([None, "", long_tag, "bad@tag", *many_tags])

    assert result[0] == "x" * MAX_TAG_LENGTH
    assert len(result) == MAX_TAG_COUNT


def test_infer_tags_handles_empty_text_and_fallback_alias_search():
    assert infer_tags_from_text(None) == []
    assert infer_tags_from_text("") == []
    assert infer_tags_from_text("No labels here") == []
    assert infer_tags_from_text("Apoyo para salud publica y doctores", max_tags=2) == [
        "healthcare",
        "healthcare providers",
    ]
    assert infer_tags_from_text("immigration-related support for families", max_tags=1) == [
        "immigration"
    ]


def test_infer_tags_skips_duplicate_ngrams_and_respects_max_tags():
    assert infer_tags_from_text("legal aid legal aid translation", max_tags=2) == [
        "legal aid",
        "translation",
    ]


def test_build_bilingual_tag_fields_deduplicates_and_preserves_unknown_tags():
    result = build_bilingual_tag_fields(["legal aid", "ayuda legal", "custom service"])

    assert result == {
        "tags_en": ["legal aid", "custom service"],
        "tags_es": ["ayuda legal", "custom service"],
    }


def test_build_bilingual_tag_fields_enforces_max_count_and_normalizes_noncanonical_tags():
    long_translated_tag = "y" * (MAX_TAG_LENGTH + 10)

    assert _normalize_noncanonical_tag("") == ""
    assert _normalize_noncanonical_tag("bad@tag") == ""
    assert _normalize_noncanonical_tag(long_translated_tag) == "y" * MAX_TAG_LENGTH

    many_tags = [f"custom{i}" for i in range(MAX_TAG_COUNT + 5)]
    result = build_bilingual_tag_fields(many_tags)

    assert len(result["tags_en"]) == MAX_TAG_COUNT
    assert len(result["tags_es"]) == MAX_TAG_COUNT


def test_normalize_tag_fields_reports_unchanged_metadata_and_handles_non_lists():
    metadata = {
        "tags": ["housing"],
        "service_tags": "not-a-list",
    }

    normalized, changed = normalize_tag_fields(metadata)

    assert normalized == {"tags": ["housing"]}
    assert changed is True

    normalized_again, changed_again = normalize_tag_fields({"tags": ["housing"]})
    assert normalized_again == {"tags": ["housing"]}
    assert changed_again is False


def test_parse_tags_input_returns_empty_list_for_missing_input():
    assert parse_tags_input(None) == []
    assert parse_tags_input("") == []
