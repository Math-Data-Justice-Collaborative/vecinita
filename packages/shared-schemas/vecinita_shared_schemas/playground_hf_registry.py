"""Playground model tags → HuggingFace Hub repos for vLLM (ADR-037).

Used by vecinita-llm ``pull_model_job`` and internal-write-api catalog availability.
Quantization / MLX / packaging suffixes on playground tags map to the base HF instruct repo.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Final

_QUANT_SUFFIX: Final[re.Pattern[str]] = re.compile(r"-q\d+_[a-z0-9_]+$", re.IGNORECASE)
_PACKAGE_SUFFIXES: Final[tuple[re.Pattern[str], ...]] = (
    _QUANT_SUFFIX,
    re.compile(r"-mlx(?:-.*)?$", re.IGNORECASE),
    re.compile(r"-bf16$", re.IGNORECASE),
    re.compile(r"-mxfp8$", re.IGNORECASE),
    re.compile(r"-nvfp4$", re.IGNORECASE),
    re.compile(r"-mtp-.*$", re.IGNORECASE),
    re.compile(r"-fp16$", re.IGNORECASE),
    re.compile(r"-a3b-coding-.*$", re.IGNORECASE),
)

# Tags that break family heuristics (AWQ, MoE defaults, etc.).
_HF_OVERRIDES: Final[dict[str, str]] = {
    "qwen3:8b": "Qwen/Qwen3-8B-AWQ",
}

# ``:latest`` defaults per playground library family slug.
_LATEST_DEFAULTS: Final[dict[str, str]] = {
    "qwen3.6": "Qwen/Qwen3.6-35B-A3B",
    "llama3.2": "meta-llama/Llama-3.2-3B-Instruct",
    "llama3.1": "meta-llama/Llama-3.1-8B-Instruct",
    "llama3": "meta-llama/Meta-Llama-3-8B-Instruct",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.3",
    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "gemma2": "google/gemma-2-9b-it",
    "gemma": "google/gemma-7b-it",
    "phi3": "microsoft/Phi-3-mini-4k-instruct",
    "qwen2.5": "Qwen/Qwen2.5-7B-Instruct",
    "qwen2": "Qwen/Qwen2-7B-Instruct",
    "qwen3": "Qwen/Qwen3-8B-AWQ",
}


def _cap_b_size(raw: str) -> str:
    """``3b`` → ``3B``, ``0.5b`` → ``0.5B``."""
    lowered = raw.lower()
    if lowered.endswith("b"):
        return f"{lowered[:-1]}B"
    return raw


def normalize_playground_tag(model_id: str) -> str:
    """Strip playground tag quantization and packaging suffixes for registry lookup."""
    tag = model_id.strip()
    changed = True
    while changed:
        changed = False
        for pattern in _PACKAGE_SUFFIXES:
            stripped = pattern.sub("", tag)
            if stripped != tag:
                tag = stripped
                changed = True
    return tag


def _infer_qwen25(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>[\d.]+b)-instruct", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"Qwen/Qwen2.5-{size}-Instruct"


def _infer_qwen2(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>[\d.]+b)-instruct", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"Qwen/Qwen2-{size}-Instruct"


def _infer_qwen3(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>[\d.]+b)", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"Qwen/Qwen3-{size}"


def _infer_qwen36(variant: str) -> str | None:
    if variant in {"latest", "35b"} or variant.startswith("35b"):
        return "Qwen/Qwen3.6-35B-A3B"
    if variant.startswith("27b"):
        return "Qwen/Qwen3.6-27B"
    return None


def _infer_llama32(variant: str) -> str | None:
    if variant in {"latest", "3b"}:
        return "meta-llama/Llama-3.2-3B-Instruct"
    if variant == "1b":
        return "meta-llama/Llama-3.2-1B-Instruct"
    return None


def _infer_llama31(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>\d+b)(?:-instruct)?", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"meta-llama/Llama-3.1-{size}-Instruct"


def _infer_llama3(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>\d+b)(?:-instruct)?", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"meta-llama/Meta-Llama-3-{size}-Instruct"


def _infer_llama2(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>\d+b)(?:-chat)?", variant)
    if match is None:
        return None
    size = _cap_b_size(match.group("size"))
    return f"meta-llama/Llama-2-{size}-chat-hf"


def _infer_mistral(variant: str) -> str | None:
    if variant in {"7b", "latest"}:
        return "mistralai/Mistral-7B-Instruct-v0.3"
    return None


def _infer_mixtral(variant: str) -> str | None:
    if variant in {"8x7b", "latest"}:
        return "mistralai/Mixtral-8x7B-Instruct-v0.1"
    return None


def _infer_gemma2(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>\d+b)", variant)
    if match is None:
        return None
    return f"google/gemma-2-{match.group('size')}-it"


def _infer_gemma(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>\d+b)(?:-it)?", variant)
    if match is None:
        return None
    return f"google/gemma-{match.group('size')}-it"


def _infer_phi3(variant: str) -> str | None:
    mapping = {
        "mini": "microsoft/Phi-3-mini-4k-instruct",
        "small": "microsoft/Phi-3-small-8k-instruct",
        "medium": "microsoft/Phi-3-medium-4k-instruct",
    }
    return mapping.get(variant)


def _infer_codellama(variant: str) -> str | None:
    match = re.fullmatch(r"(?P<size>[\d.]+b)(?:-instruct)?", variant)
    if match is None:
        return None
    size = match.group("size")
    return f"codellama/CodeLlama-{size}-Instruct-hf"


def _infer_deepseek_r1(variant: str) -> str | None:
    mapping = {
        "1.5b": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "7b": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "8b": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
        "14b": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        "32b": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "70b": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    }
    return mapping.get(variant)


_FAMILY_INFERERS: Final[dict[str, Callable[[str], str | None]]] = {
    "qwen2.5": _infer_qwen25,
    "qwen2": _infer_qwen2,
    "qwen3": _infer_qwen3,
    "qwen3.6": _infer_qwen36,
    "llama3.2": _infer_llama32,
    "llama3.1": _infer_llama31,
    "llama3": _infer_llama3,
    "llama2": _infer_llama2,
    "mistral": _infer_mistral,
    "mixtral": _infer_mixtral,
    "gemma2": _infer_gemma2,
    "gemma": _infer_gemma,
    "phi3": _infer_phi3,
    "codellama": _infer_codellama,
    "deepseek-r1": _infer_deepseek_r1,
}


def _infer_hf_repo(normalized: str) -> str | None:
    if ":" not in normalized:
        return None
    family, variant = normalized.split(":", 1)
    variant = variant.lower()
    if variant == "latest":
        return _LATEST_DEFAULTS.get(family)
    inferer = _FAMILY_INFERERS.get(family)
    if inferer is None:
        return None
    return inferer(variant)


def resolve_hf_repo(model_id: str) -> str:
    """Map a playground ``model_id`` tag to a HuggingFace Hub repo id."""
    base = normalize_playground_tag(model_id)
    override = _HF_OVERRIDES.get(base)
    if override is not None:
        return override
    inferred = _infer_hf_repo(base)
    if inferred is not None:
        return inferred
    msg = f"no HuggingFace mapping for model_id {model_id!r} (normalized {base!r})"
    raise ValueError(msg)


def repo_dir_name(model_id: str) -> str:
    """Filesystem-safe directory name under ``/models/repos/``."""
    return normalize_playground_tag(model_id).replace(":", "_").replace("/", "_")
