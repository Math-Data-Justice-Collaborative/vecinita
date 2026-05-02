import pytest

from src.utils.resource_metadata import infer_resource_language_metadata

pytestmark = pytest.mark.unit


def test_infer_resource_language_metadata_detects_english():
    metadata = infer_resource_language_metadata(
        ["This housing resource explains where families can find community support in Providence."]
    )

    assert metadata["language"] == "English"
    assert metadata["primary_language_code"] == "en"
    assert metadata["is_bilingual"] is False


def test_infer_resource_language_metadata_marks_bilingual_when_languages_mix():
    metadata = infer_resource_language_metadata(
        [
            "This legal aid guide explains how to apply for immigration support.",
            "Esta guia de ayuda legal explica como solicitar apoyo de inmigracion.",
        ]
    )

    assert metadata["is_bilingual"] is True
    assert "English" in metadata["available_languages"]
    assert "Spanish" in metadata["available_languages"]
