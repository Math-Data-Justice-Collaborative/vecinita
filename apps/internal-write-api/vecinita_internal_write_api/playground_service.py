"""Playground model list helpers for admin eval picker (ADR-037)."""

from __future__ import annotations

from typing import Protocol

from vecinita_llm_client import LlmClientError
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID
from vecinita_shared_schemas.playground_catalog import (
    build_playground_availability_lookup,
    merge_playground_catalog_with_volume,
)
from vecinita_shared_schemas.playground_models import (
    PlaygroundModelListResponse,
    PlaygroundModelPullResponse,
    PlaygroundModelSummary,
)


class LlmModelsClientProtocol(Protocol):
    """List/pull playground models on Modal (mockable in tests; T77.4)."""

    def list_models(self) -> PlaygroundModelListResponse:
        """Return models visible on the playground volume."""
        ...

    def start_pull(self, model_id: str) -> PlaygroundModelPullResponse:
        """Start async model pull onto playground volume."""
        ...

    def close(self) -> None:
        """Release HTTP resources when owned by the client."""
        ...


def vllm_fallback_model_list() -> PlaygroundModelListResponse:
    """Default model picker entries when Modal playground LLM is not wired (vLLM-only eval)."""
    return PlaygroundModelListResponse(
        items=merge_playground_catalog_with_volume(
            [
                PlaygroundModelSummary(
                    model_id=DEFAULT_EVAL_MODEL_ID,
                    available=True,
                ),
            ],
        ),
    )


def merge_playground_model_list(
    response: PlaygroundModelListResponse,
) -> PlaygroundModelListResponse:
    """Overlay volume manifest onto the curated playground catalog."""
    return PlaygroundModelListResponse(
        items=merge_playground_catalog_with_volume(list(response.items)),
    )


def playground_volume_availability(
    playground_models: LlmModelsClientProtocol | None,
) -> dict[str, bool]:
    """Map model_id to volume availability for catalog tag overlays."""
    if playground_models is None:
        return {}
    try:
        response = merge_playground_model_list(playground_models.list_models())
    except LlmClientError:
        return {}
    return build_playground_availability_lookup(list(response.items))
