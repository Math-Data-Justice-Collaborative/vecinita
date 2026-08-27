"""F77 LoRA FT eval report schema — base vs adapter (TC-261 / AC-FT3 / RD-338).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-261]
[Spec: docs/acceptance-criteria.md §AC-FT3 §AC-FT4]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

HUMAN_JUDGMENT_SUMMARY = (
    "Human judgment required — no automated promote (RD-338 / AC-FT4). "
    + "Promote only when the operator judges the adapter better than base."
)


class FinetuneSideMetrics(BaseModel):
    """One side of a base-vs-adapter FT eval comparison."""

    model_config = ConfigDict(extra="forbid")

    faithfulness: float | None = Field(default=None, ge=0.0, le=1.0)
    answer_relevancy: float | None = Field(default=None, ge=0.0, le=1.0)
    questions_scored: int = Field(default=0, ge=0)


class FinetuneEvalReportResponse(BaseModel):
    """GET /internal/v1/finetune/runs/{id}/eval (UJ-082 / TC-261)."""

    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    adapter_id: str = Field(min_length=1)
    base_model_id: str = Field(min_length=1)
    base: FinetuneSideMetrics
    adapter: FinetuneSideMetrics
    auto_promote: Literal[False] = False
    summary: str = Field(min_length=1)


def build_finetune_eval_report(  # noqa: PLR0913  # report fields are the public builder surface
    *,
    run_id: UUID,
    adapter_id: str,
    base_model_id: str,
    base: FinetuneSideMetrics,
    adapter: FinetuneSideMetrics,
    summary: str = HUMAN_JUDGMENT_SUMMARY,
) -> FinetuneEvalReportResponse:
    """Build an operator-facing base vs adapter report (never auto-promotes)."""
    return FinetuneEvalReportResponse(
        run_id=run_id,
        adapter_id=adapter_id,
        base_model_id=base_model_id,
        base=base,
        adapter=adapter,
        auto_promote=False,
        summary=summary,
    )
