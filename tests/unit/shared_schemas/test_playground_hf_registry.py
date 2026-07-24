"""Playground tag → HuggingFace registry inference (ADR-037)."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.playground_hf_registry import (
    _cap_b_size,  # pyright: ignore[reportPrivateUsage]  # branch coverage for size helper
    normalize_playground_tag,
    repo_dir_name,
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
def test_resolve_hf_repo_maps_common_playground_catalog_tags(
    model_id: str,
    expected_repo: str,
) -> None:
    """Common ollama.com library tags resolve to vLLM-loadable HF repos."""
    assert resolve_hf_repo(model_id) == expected_repo


def test_normalize_playground_tag_strips_quant_and_mlx_suffixes() -> None:
    """Packaging suffixes strip before registry lookup."""
    assert normalize_playground_tag("qwen2.5:3b-instruct-q4_K_M") == "qwen2.5:3b-instruct"
    assert normalize_playground_tag("qwen3.6:27b-mlx") == "qwen3.6:27b"


def test_resolve_hf_repo_unknown_tag_raises() -> None:
    """Unmapped families raise a clear error (Ollama-only GGUF tags)."""
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("unknown-custom:7b")


def test_resolve_hf_repo_maps_additional_family_variants() -> None:
    """Cover alternate sizes / families for branch coverage of infer helpers."""
    cases = (
        ("qwen2:7b-instruct", "Qwen/Qwen2-7B-Instruct"),
        ("llama3.1:70b-instruct", "meta-llama/Llama-3.1-70B-Instruct"),
        ("llama3:70b", "meta-llama/Meta-Llama-3-70B-Instruct"),
        ("llama2:7b-chat", "meta-llama/Llama-2-7B-chat-hf"),
        ("mistral:latest", "mistralai/Mistral-7B-Instruct-v0.3"),
        ("mixtral:latest", "mistralai/Mixtral-8x7B-Instruct-v0.1"),
        ("gemma:2b", "google/gemma-2b-it"),
        ("gemma:7b-it", "google/gemma-7b-it"),
        ("phi3:small", "microsoft/Phi-3-small-8k-instruct"),
        ("phi3:medium", "microsoft/Phi-3-medium-4k-instruct"),
        ("deepseek-r1:1.5b", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"),
        ("deepseek-r1:8b", "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"),
        ("codellama:13b", "codellama/CodeLlama-13b-Instruct-hf"),
    )
    for model_id, expected in cases:
        assert resolve_hf_repo(model_id) == expected, model_id


def test_resolve_hf_repo_known_family_unmapped_variant_raises() -> None:
    """Known family with unmapped variant still raises (inferer returns None)."""
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("mistral:13b")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("llama3.2:70b")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("qwen2.5:7b")  # missing -instruct
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("qwen3.6:1b")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("qwen2:7b")  # missing -instruct
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("qwen3:latest-extra")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("llama3.1:chat")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("llama3:chat")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("llama2:chat")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("mixtral:7b")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("gemma2:2b-it")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("gemma:tiny")
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("codellama:code")


def test_resolve_hf_repo_latest_defaults_and_no_colon() -> None:
    """``:latest`` uses family defaults; tags without ``:`` are unmapped."""
    assert resolve_hf_repo("gemma:latest") == "google/gemma-7b-it"
    assert resolve_hf_repo("phi3:latest") == "microsoft/Phi-3-mini-4k-instruct"
    with pytest.raises(ValueError, match="no HuggingFace mapping"):
        resolve_hf_repo("notagfamily")


def test_cap_b_size_passthrough_without_b_suffix() -> None:
    """Sizes that do not end in ``b`` are returned unchanged."""
    assert _cap_b_size("7") == "7"
    assert _cap_b_size("3b") == "3B"


def test_repo_dir_name_sanitizes_colon() -> None:
    """Repo directory names replace ``:`` for filesystem safety."""
    assert repo_dir_name("qwen2.5:1.5b-instruct") == "qwen2.5_1.5b-instruct"
