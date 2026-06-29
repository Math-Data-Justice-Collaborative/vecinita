"""Unit tests for vecinita_tagging.vocabulary (RD-030, RD-031)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from pathlib import Path

_MIN_SEED_TAG_COUNT = 8

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
    """Test default seed path uses env when file exists."""
    seed_file = tmp_path / "custom_tags.json"
    seed_file.write_text('{"tags": []}', encoding="utf-8")
    monkeypatch.setenv("VECINITA_TAG_SEED_PATH", str(seed_file))

    assert default_seed_path() == seed_file


def test_default_seed_path_falls_back_to_repo_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test default seed path falls back to repo fixture."""
    monkeypatch.setenv("VECINITA_TAG_SEED_PATH", "/nonexistent/seed_tags.json")

    path = default_seed_path()

    assert path.is_file()
    assert path.name == "seed_tags.json"


def test_load_seed_vocabulary_from_custom_path(tmp_path: Path) -> None:
    """Test load seed vocabulary from custom path."""
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
    """Test load seed vocabulary loads repo fixture."""
    tags = load_seed_vocabulary()

    assert len(tags) >= _MIN_SEED_TAG_COUNT
    assert tags[0].slug == "housing"


def test_load_seed_vocabulary_requires_tags_array(tmp_path: Path) -> None:
    """Test load seed vocabulary requires tags array."""
    seed_path = tmp_path / "bad.json"
    seed_path.write_text('{"tags": "not-a-list"}', encoding="utf-8")

    with pytest.raises(TypeError, match="tags"):
        load_seed_vocabulary(seed_path)


def test_vocabulary_slugs_deduplicates_in_order() -> None:
    """Test vocabulary slugs deduplicates in order."""
    assert vocabulary_slugs(_SAMPLE_VOCAB_WITH_DUP) == ["housing", "legal"]


def test_detect_document_language_returns_es_for_spanish() -> None:
    """Test detect document language returns es for spanish."""
    text = "Este documento explica los derechos de los inquilinos en español."

    assert detect_document_language(text) == "es"


def test_detect_document_language_returns_en_for_english() -> None:
    """Test detect document language returns en for english."""
    text = "This document explains tenant rights in plain English."

    assert detect_document_language(text) == "en"


def test_detect_document_language_uses_fallback_on_detection_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test detect document language uses fallback on detection failure."""

    def _fail(_text: str) -> str:
        """Fail."""
        msg = "fail"
        raise langdetect.LangDetectException(msg, "detection failed")

    monkeypatch.setattr(langdetect, "detect", _fail)

    assert detect_document_language("???", fallback="es") == "es"


def test_tag_inputs_for_slugs_uses_english_labels() -> None:
    """Test tag inputs for slugs uses english labels."""
    inputs = tag_inputs_for_slugs(
        ["housing", "missing"],
        _SAMPLE_VOCAB,
        language="en",
    )

    assert inputs == [
        TagInput(slug="housing", label="Housing", source="llm"),
    ]


def test_tag_inputs_for_slugs_uses_spanish_labels_and_human_source() -> None:
    """Test tag inputs for slugs uses spanish labels and human source."""
    inputs = tag_inputs_for_slugs(
        ["legal"],
        _SAMPLE_VOCAB,
        language="es",
        source="human",
    )

    assert inputs == [TagInput(slug="legal", label="Legal", source="human")]


def test_tag_inputs_for_slugs_skips_unknown_slugs() -> None:
    """Test tag inputs for slugs skips unknown slugs."""
    inputs = tag_inputs_for_slugs(
        ["unknown"],
        _SAMPLE_VOCAB,
        language="en",
    )

    assert inputs == []
