"""Playground catalog merge (F38 extension)."""

from __future__ import annotations

from vecinita_shared_schemas.playground_catalog import (
    build_playground_availability_lookup,
    merge_playground_catalog_with_volume,
    playground_catalog_tag_available,
)
from vecinita_shared_schemas.playground_models import PlaygroundModelSummary


def test_merge_catalog_marks_undownloaded_models_unavailable() -> None:
    """Catalog entries without a volume manifest entry are marked unavailable."""
    merged = merge_playground_catalog_with_volume(
        [PlaygroundModelSummary(model_id="qwen2.5:1.5b-instruct", available=True)],
    )
    ids = [item.model_id for item in merged]
    assert "qwen2.5:1.5b-instruct" in ids
    assert "qwen2.5:3b-instruct" in ids
    default = next(item for item in merged if item.model_id == "qwen2.5:1.5b-instruct")
    missing = next(item for item in merged if item.model_id == "qwen2.5:3b-instruct")
    assert default.available is True
    assert missing.available is False


def test_merge_catalog_includes_volume_only_custom_tag() -> None:
    """Custom pulled tags outside the catalog are appended to the merged list."""
    custom_id = "custom:7b-instruct"
    merged = merge_playground_catalog_with_volume(
        [
            PlaygroundModelSummary(model_id="qwen2.5:1.5b-instruct", available=True),
            PlaygroundModelSummary(model_id=custom_id, available=True),
        ],
    )
    assert any(item.model_id == custom_id for item in merged)


def test_catalog_tag_available_matches_normalized_volume_tag() -> None:
    """Quantized catalog tags show downloaded when base tag is on the volume."""
    lookup = build_playground_availability_lookup(
        [PlaygroundModelSummary(model_id="qwen2.5:3b-instruct", available=True)],
    )
    assert playground_catalog_tag_available("qwen2.5:3b-instruct-q4_K_M", lookup) is True
    assert playground_catalog_tag_available("qwen2.5:7b-instruct", lookup) is False
