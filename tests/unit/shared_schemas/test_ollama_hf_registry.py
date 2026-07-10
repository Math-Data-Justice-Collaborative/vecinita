"""Ollama tag → HuggingFace registry inference (ADR-037)."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.ollama_hf_registry import (
    normalize_ollama_tag,
    resolve_hf_repo,
)

_CATALOG_TAG_CASES: tuple[tuple[str, str], ...] = (
    ("qwen2.5:1.5b-instruct", "Qwen/Qwen2.5-1.5B-Instruct"),
    ("qwen2.5:3b-instruct-q4_K_M", "Qwen/Qwen2.5-3B-Instruct"),
    ("qwen3:8b", "Qwen/Qwen3-8B-AWQ"),
    ("qwen3:4b", "Qwen/Qwen3-4B"),
    ("qwen3.6:latest", "Qwen/Qwen3.6-35B-A3B"),
    ("qwen3.6:27b-mlx", "Qwen/Qwen3.6-27B"),
    ("qwen3.6:35b-a3b-q4_K_M", "Qwen/Qwen3.6-35B-A3B"),
    ("llama3.2:3b", "meta-llama/Llama-3.2-3B-Instruct"),
    ("llama3.2:latest", "meta-llama/Llama-3.2-3B-Instruct"),
    ("llama3.2:1b", "meta-llama/Llama-3.2-1B-Instruct"),
    ("llama3.1:8b", "meta-llama/Llama-3.1-8B-Instruct"),
    ("llama3:8b", "meta-llama/Meta-Llama-3-8B-Instruct"),
    ("mistral:7b", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("mixtral:8x7b", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
    ("gemma2:2b", "google/gemma-2-2b-it"),
    ("gemma2:9b", "google/gemma-2-9b-it"),
    ("phi3:mini", "microsoft/Phi-3-mini-4k-instruct"),
    ("codellama:7b-instruct", "codellama/CodeLlama-7b-Instruct-hf"),
    ("deepseek-r1:7b", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"),
)


@pytest.mark.parametrize(("model_id", "expected_repo"), _CATALOG_TAG_CASES)
def test_resolve_hf_repo_maps_common_ollama_catalog_tags(
    model_id: str,
    expected_repo: str,
) -> None:
    """Common ollama.com library tags resolve to vLLM-loadable HF repos."""
    assert resolve_hf_repo(model_id) == expected_repo


def test_normalize_ollama_tag_strips_quant_and_mlx_suffixes() -> None:
    """Packaging suffixes strip before registry lookup."""
    assert normalize_ollama_tag("qwen2.5:3b-instruct-q4_K_M") == "qwen2.5:3b-instruct"
    assert normalize_ollama_tag("qwen3.6:27b-mlx") == "qwen3.6:27b"


def test_resolve_hf_repo_unknown_tag_raises() -> None:
    """Unmapped families raise a clear error (Ollama-only GGUF tags)."""
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("unknown-custom:7b")
