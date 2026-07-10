"""Ollama tag → HuggingFace repo registry (ADR-037)."""

from __future__ import annotations

from infra.modal.llm_model_registry import normalize_ollama_tag, resolve_hf_repo


def test_registry_reexports_shared_inference() -> None:
    """Modal registry module delegates to shared-schemas inference."""
    assert resolve_hf_repo("qwen3.6:latest") == "Qwen/Qwen3.6-35B-A3B"
    assert normalize_ollama_tag("qwen2.5:3b-instruct-q4_K_M") == "qwen2.5:3b-instruct"
