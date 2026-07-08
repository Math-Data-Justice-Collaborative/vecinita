"""Ollama tag → HuggingFace repo registry (ADR-037)."""

from __future__ import annotations

import pytest
from infra.modal.llm_model_registry import normalize_ollama_tag, resolve_hf_repo


def test_normalize_ollama_tag_strips_quant_suffix() -> None:
    assert normalize_ollama_tag("qwen2.5:3b-instruct-q4_K_M") == "qwen2.5:3b-instruct"


def test_resolve_hf_repo_maps_playground_tags() -> None:
    assert resolve_hf_repo("qwen2.5:1.5b-instruct") == "Qwen/Qwen2.5-1.5B-Instruct"
    assert resolve_hf_repo("qwen3:8b") == "Qwen/Qwen3-8B"


def test_resolve_hf_repo_unknown_tag_raises() -> None:
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("unknown:model")
