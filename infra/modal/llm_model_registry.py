"""Ollama-style playground tags → HuggingFace Hub repos for vLLM (ADR-037)."""

from __future__ import annotations

import re
from typing import Final

# Playground / eval model_id tags (Ollama naming) mapped to HF instruct repos.
_OLLAMA_TAG_TO_HF: Final[dict[str, str]] = {
    "qwen2.5:0.5b-instruct": "Qwen/Qwen2.5-0.5B-Instruct",
    "qwen2.5:1.5b-instruct": "Qwen/Qwen2.5-1.5B-Instruct",
    "qwen2.5:3b-instruct": "Qwen/Qwen2.5-3B-Instruct",
    "qwen2.5:7b-instruct": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2.5:14b-instruct": "Qwen/Qwen2.5-14B-Instruct",
    "qwen2.5:32b-instruct": "Qwen/Qwen2.5-32B-Instruct",
    "qwen3:0.6b": "Qwen/Qwen3-0.6B",
    "qwen3:1.7b": "Qwen/Qwen3-1.7B",
    "qwen3:4b": "Qwen/Qwen3-4B",
    "qwen3:8b": "Qwen/Qwen3-8B-AWQ",
    "qwen3:14b": "Qwen/Qwen3-14B",
    "qwen3:32b": "Qwen/Qwen3-32B",
}

_QUANT_SUFFIX = re.compile(r"-q\d+_[a-z0-9_]+$", re.IGNORECASE)


def normalize_ollama_tag(model_id: str) -> str:
    """Strip Ollama quantization suffixes (e.g. ``-q4_K_M``) for registry lookup."""
    return _QUANT_SUFFIX.sub("", model_id.strip())


def resolve_hf_repo(model_id: str) -> str:
    """Map a playground ``model_id`` tag to a HuggingFace Hub repo id."""
    base = normalize_ollama_tag(model_id)
    repo = _OLLAMA_TAG_TO_HF.get(base)
    if repo is None:
        msg = f"no HuggingFace mapping for model_id {model_id!r} (normalized {base!r})"
        raise ValueError(msg)
    return repo


def repo_dir_name(model_id: str) -> str:
    """Filesystem-safe directory name under ``/models/repos/``."""
    return normalize_ollama_tag(model_id).replace(":", "_").replace("/", "_")
