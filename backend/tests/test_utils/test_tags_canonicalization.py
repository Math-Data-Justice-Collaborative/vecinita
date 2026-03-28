from src.utils.tags import canonicalize_tag, normalize_tag_fields, normalize_tags, parse_tags_input


def test_normalize_tags_maps_bilingual_aliases_to_canonical_values():
    tags = normalize_tags(["RI", "PVD", "Inmigración", "Vivienda", "Housing"])
    assert tags == ["rhode island", "providence", "immigration", "housing"]


def test_parse_tags_input_canonicalizes_and_deduplicates():
    tags = parse_tags_input("educación, Education, inmigracion, immigration")
    assert tags == ["education", "immigration"]


def test_canonicalize_tag_strips_accents_and_whitespace():
    assert canonicalize_tag("  Educación   Bilingüe ") == "bilingual education"


def test_normalize_tag_fields_updates_and_prunes_empty_lists():
    metadata = {
        "tags": ["RI", "Rhode Island", "Housing"],
        "location_tags": ["PVD"],
        "subject_tags": [],
        "title": "Sample",
    }
    normalized, changed = normalize_tag_fields(metadata)

    assert changed is True
    assert normalized["tags"] == ["rhode island", "housing"]
    assert normalized["location_tags"] == ["providence"]
    assert "subject_tags" not in normalized
    assert normalized["title"] == "Sample"
