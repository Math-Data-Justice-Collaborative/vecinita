"""Playground model tags → HuggingFace Hub repos for vLLM (ADR-037).

Re-exports shared registry logic used by vecinita-llm and tests.
"""

from __future__ import annotations

from vecinita_shared_schemas.playground_hf_registry import (
    normalize_playground_tag,
    repo_dir_name,
    resolve_hf_repo,
)

__all__ = ["normalize_playground_tag", "repo_dir_name", "resolve_hf_repo"]
