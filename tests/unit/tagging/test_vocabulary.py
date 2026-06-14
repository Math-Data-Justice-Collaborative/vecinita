"""Unit tests for vecinita_tagging.vocabulary (RD-030, RD-031)."""

from __future__ import annotations

import json
from pathlib import Path

import langdetect
import pytest
from vecinita_shared_schemas.internal_write import TagInput
from vecinita_tagging.vocabulary import (
    SeedTag,
    default_seed_path,
    detect_document_language,
    load_seed_vocabulary,
    tag_inputs_for_slugs,
    vocabulary_slugs,
)

_SAMPLE_VOCAB = [
    SeedTag(slug="housing", label_en="Housing", label_es="Vivienda"),
    SeedTag(slug="legal", label_en="Legal", label_es="Legal"),
]

_SAMPLE_VOCAB_WITH_DUP = [
    *_SAMPLE_VOCAB,
    SeedTag(slug="housing", label_en="Housing dup", label_es="Vivienda dup"),
]


def test_default_seed_path_uses_env_when_file_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_file = tmp_path / "custom_tags.json"
    seed_file.write_text('{"tags": []}', encoding="utf-8")
    monkeypatch.setenv("VECINITA_TAG_SEED_PATH", str(seed_file))

    assert default_seed_path() == seed_file


def test_default_seed_path_falls_back_to_repo_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VECINITA_TAG_SEED_PATH", "/nonexistent/seed_tags.json")

    path = default_seed_path()

    assert path.is_file()
    assert path.name == "seed_tags.json"


def test_load_seed_vocabulary_from_custom_path(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed_tags.json"
    seed_path.write_text(
        json.dumps(
            {
                "tags": [
                    {
                        "slug": "housing",
                        "label_en": "Housing",
                        "label_es": "Vivienda",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    tags = load_seed_vocabulary(seed_path)

    assert tags == [SeedTag(slug="housing", label_en="Housing", label_es="Vivienda")]


def test_load_seed_vocabulary_loads_repo_fixture() -> None:
    tags = load_seed_vocabulary()

    assert len(tags) >= 8
    assert tags[0].slug == "housing"


def test_load_seed_vocabulary_requires_tags_array(tmp_path: Path) -> None:
    seed_path = tmp_path / "bad.json"
    seed_path.write_text('{"tags": "not-a-list"}', encoding="utf-8")

    with pytest.raises(ValueError, match="tags"):
        load_seed_vocabulary(seed_path)


def test_vocabulary_slugs_deduplicates_in_order() -> None:
    assert vocabulary_slugs(_SAMPLE_VOCAB_WITH_DUP) == ["housing", "legal"]


def test_detect_document_language_returns_es_for_spanish() -> None:
    text = "Este documento explica los derechos de los inquilinos en español."

    assert detect_document_language(text) == "es"


def test_detect_document_language_returns_en_for_english() -> None:
    text = "This document explains tenant rights in plain English."

    assert detect_document_language(text) == "en"


def test_detect_document_language_uses_fallback_on_detection_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fail(_text: str) -> str:
        raise langdetect.LangDetectException("fail", "detection failed")

    monkeypatch.setattr(langdetect, "detect", _fail)

    assert detect_document_language("???", fallback="es") == "es"


def test_tag_inputs_for_slugs_uses_english_labels() -> None:
    inputs = tag_inputs_for_slugs(
        ["housing", "missing"],
        _SAMPLE_VOCAB,
        language="en",
    )

    assert inputs == [
        TagInput(slug="housing", label="Housing", source="llm"),
    ]


def test_tag_inputs_for_slugs_uses_spanish_labels_and_human_source() -> None:
    inputs = tag_inputs_for_slugs(
        ["legal"],
        _SAMPLE_VOCAB,
        language="es",
        source="human",
    )

    assert inputs == [TagInput(slug="legal", label="Legal", source="human")]


def test_tag_inputs_for_slugs_skips_unknown_slugs() -> None:
    inputs = tag_inputs_for_slugs(
        ["unknown"],
        _SAMPLE_VOCAB,
        language="en",
    )

    assert inputs == []
