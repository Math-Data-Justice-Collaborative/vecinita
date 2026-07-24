"""Regression: Ollama catalog tags show Not downloaded after pull (BUG-2026-07-09).

ADR-037: vecinita-llm stages playground tags via HuggingFace Hub. The admin catalog
lists ollama.com tags but availability comes from the Modal volume manifest, which only
flips to ``available: true`` after ``pull_model_job`` completes. Pull requires
``resolve_hf_repo`` mapping for the tag (or a normalized variant).
"""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo

_CATALOG_PULL_CASES: tuple[tuple[str, str], ...] = (
    ("qwen3.6:latest", "Qwen/Qwen3.6-35B-A3B"),
    ("qwen3.6:27b", "Qwen/Qwen3.6-27B"),
    ("llama3.2:3b", "meta-llama/Llama-3.2-3B-Instruct"),
    ("qwen2.5:3b-instruct-q4_K_M", "Qwen/Qwen2.5-3B-Instruct"),
)


@pytest.mark.parametrize(("model_id", "expected_repo"), _CATALOG_PULL_CASES)
def test_resolve_hf_repo_maps_catalog_tags_for_playground_pull(
    model_id: str,
    expected_repo: str,
) -> None:
    """Catalog tags must resolve so pull_model_job can stage weights and update manifest."""
    assert resolve_hf_repo(model_id) == expected_repo
