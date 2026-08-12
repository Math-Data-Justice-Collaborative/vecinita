"""F77 LoRA FT promote / rollback schemas (TC-262 / TC-265 / AC-FT6 / AC-FT9).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-262 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT4 §AC-FT6 §AC-FT9]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FinetunePromoteRequest(BaseModel):
    """POST /internal/v1/finetune/promote body (human promote or clear-pin rollback)."""

    model_config = ConfigDict(extra="forbid")

    adapter_id: str | None = None
    rollback: bool = False

    @field_validator("adapter_id", mode="before")
    @classmethod
    def _strip_adapter_id(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def _require_adapter_unless_rollback(self) -> Self:
        if self.rollback:
            self.adapter_id = None
            return self
        if self.adapter_id is None:
            msg = "adapter_id is required unless rollback is true"
            raise ValueError(msg)
        return self


class FinetunePromoteResponse(BaseModel):
    """POST /internal/v1/finetune/promote response (UJ-082 / TC-262 / TC-265)."""

    model_config = ConfigDict(extra="forbid")

    promoted: bool
    adapter_id: str | None = None
    base: bool
    auto_promote: Literal[False] = False


class FinetuneAdapterPinResponse(BaseModel):
    """GET /internal/v1/finetune/adapter — current prod pin (write-read parity)."""

    model_config = ConfigDict(extra="forbid")

    adapter_id: str | None = Field(default=None)
    base: bool
