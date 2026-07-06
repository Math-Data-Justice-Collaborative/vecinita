"""Ollama playground catalog merge (F38 extension)."""

from __future__ import annotations

from vecinita_shared_schemas.ollama_catalog import merge_ollama_catalog_with_volume
from vecinita_shared_schemas.ollama_models import OllamaModelSummary


def test_merge_catalog_marks_undownloaded_models_unavailable() -> None:
    """Catalog entries without a volume manifest entry are marked unavailable."""
    merged = merge_ollama_catalog_with_volume(
        [OllamaModelSummary(model_id="qwen2.5:1.5b-instruct", available=True)],
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
    merged = merge_ollama_catalog_with_volume(
        [
            OllamaModelSummary(model_id="qwen2.5:1.5b-instruct", available=True),
            OllamaModelSummary(model_id=custom_id, available=True),
        ],
    )
    assert any(item.model_id == custom_id for item in merged)
