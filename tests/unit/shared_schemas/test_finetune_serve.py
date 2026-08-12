"""T129.8 — F77 serve adapter pin resolution (prod promote vs playground candidate).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-262 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT6 §AC-FT9]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_ADAPTER_ID]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from vecinita_shared_schemas.finetune import (
    DEFAULT_LORA_MAX_RANK,
    decide_serve_adapter_id,
    merge_lora_engine_kwargs,
    parse_playground_finetune_adapter_id,
    resolve_finetune_adapter_dir,
)

if TYPE_CHECKING:
    import pytest


def test_prod_serve_uses_promoted_pin_never_latest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-262 / AC-FT6: prod loads only VECINITA_FINETUNE_ADAPTER_ID after promote."""
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_ID", raising=False)
    monkeypatch.setenv("VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID", "adapter-candidate")
    assert decide_serve_adapter_id(role="prod") is None

    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "adapter-promoted-1")
    assert decide_serve_adapter_id(role="prod") == "adapter-promoted-1"
    assert (
        resolve_finetune_adapter_dir(adapter_id="adapter-promoted-1")
        == "/adapters/adapter-promoted-1"
    )


def test_prod_serve_clears_to_base_after_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-265 / AC-FT9: empty promote pin → base (no adapter dir)."""
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "")
    assert decide_serve_adapter_id(role="prod") is None
    assert resolve_finetune_adapter_dir(adapter_id=None) is None


def test_playground_serve_uses_candidate_env_not_prod_pin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Playground may load pre-promote candidates via dedicated env (ADR-053)."""
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "adapter-promoted-prod")
    monkeypatch.delenv("VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID", raising=False)
    assert decide_serve_adapter_id(role="playground") is None
    assert parse_playground_finetune_adapter_id() is None

    monkeypatch.setenv(
        "VECINITA_PLAYGROUND_FINETUNE_ADAPTER_ID",
        "  adapter-candidate-9  ",
    )
    assert parse_playground_finetune_adapter_id() == "adapter-candidate-9"
    assert decide_serve_adapter_id(role="playground") == "adapter-candidate-9"


def test_merge_lora_engine_kwargs_enables_only_when_adapter_dir() -> None:
    """VLLM enable_lora is set only when an adapter dir is selected."""
    base: dict[str, object] = {"model": "Qwen/Qwen2.5-1.5B-Instruct", "dtype": "half"}
    assert merge_lora_engine_kwargs(base, adapter_dir=None) == base
    with_lora = merge_lora_engine_kwargs(base, adapter_dir="/adapters/adapter-1")
    assert with_lora["enable_lora"] is True
    assert with_lora["max_loras"] == 1
    assert with_lora["max_lora_rank"] == DEFAULT_LORA_MAX_RANK
    assert with_lora["model"] == "Qwen/Qwen2.5-1.5B-Instruct"
