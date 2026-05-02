import pytest

from src.utils.tags import build_bilingual_tag_fields, infer_tags_from_text

pytestmark = pytest.mark.unit


def test_infer_tags_from_spanish_text_returns_canonical_english_tags():
    tags = infer_tags_from_text("Necesito ayuda de inmigración y servicios legales en Providence")
    assert "immigration" in tags
    assert "legal services" in tags
    assert "providence" in tags


def test_build_bilingual_tag_fields_generates_en_and_es_lists():
    fields = build_bilingual_tag_fields(["immigration", "housing assistance"])
    assert fields["tags_en"] == ["immigration", "housing assistance"]
    assert "inmigracion" in fields["tags_es"]
    assert "asistencia de vivienda" in fields["tags_es"]
