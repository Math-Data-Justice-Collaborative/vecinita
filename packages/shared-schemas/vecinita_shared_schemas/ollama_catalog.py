"""Curated Ollama model catalog for eval playground picker + download (F38 extension)."""

from __future__ import annotations

from vecinita_shared_schemas.ollama_hf_registry import normalize_ollama_tag
from vecinita_shared_schemas.ollama_models import OllamaModelSummary

# Qwen2.5 instruct family + common quantization tags on the Modal volume.
OLLAMA_PLAYGROUND_CATALOG: tuple[str, ...] = (
    "qwen2.5:0.5b-instruct",
    "qwen2.5:1.5b-instruct",
    "qwen2.5:3b-instruct",
    "qwen2.5:3b-instruct-q4_K_M",
    "qwen2.5:3b-instruct-q8_0",
    "qwen2.5:7b-instruct",
    "qwen2.5:7b-instruct-q4_K_M",
    "qwen2.5:7b-instruct-q8_0",
    "qwen2.5:14b-instruct",
    "qwen2.5:14b-instruct-q4_K_M",
    "qwen2.5:32b-instruct",
    "qwen2.5:32b-instruct-q4_K_M",
)


def merge_ollama_catalog_with_volume(
    volume_items: list[OllamaModelSummary],
) -> list[OllamaModelSummary]:
    """Return full catalog entries with volume availability; append extra volume-only tags."""
    availability = {item.model_id: item.available for item in volume_items}
    merged: list[OllamaModelSummary] = []
    seen: set[str] = set()
    for model_id in OLLAMA_PLAYGROUND_CATALOG:
        merged.append(
            OllamaModelSummary(
                model_id=model_id,
                available=availability.get(model_id, False),
            ),
        )
        seen.add(model_id)
    for item in volume_items:
        if item.model_id in seen:
            continue
        merged.append(item)
        seen.add(item.model_id)
    return merged


def build_ollama_availability_lookup(
    volume_items: list[OllamaModelSummary],
) -> dict[str, bool]:
    """Map exact and normalized Ollama tags to volume availability."""
    lookup: dict[str, bool] = {}
    for item in volume_items:
        if not item.available:
            continue
        lookup[item.model_id] = True
        lookup[normalize_ollama_tag(item.model_id)] = True
    return lookup


def ollama_catalog_tag_available(tag: str, availability: dict[str, bool]) -> bool:
    """Return whether a catalog tag is staged on the Modal volume."""
    if availability.get(tag, False):
        return True
    return availability.get(normalize_ollama_tag(tag), False)
