"""T129.6 — FinetuneEvalReport schema + builder (F77 / TC-261).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-261]
[Spec: docs/acceptance-criteria.md §AC-FT3 §AC-FT4]
[Spec: docs/decisions.md §RD-338]
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.finetune_eval import (
    FinetuneEvalReportResponse,
    FinetuneSideMetrics,
    build_finetune_eval_report,
)

_BASE_FAITH = 0.8
_ADAPTER_FAITH = 0.85
_QUESTIONS = 2


def test_finetune_eval_report_schema_requires_base_and_adapter() -> None:
    """TC-261 / AC-FT3: report payload includes base and adapter metric sides."""
    run_id = uuid4()
    report = FinetuneEvalReportResponse(
        run_id=run_id,
        adapter_id="adapter-abc",
        base_model_id="qwen2.5:1.5b-instruct",
        base=FinetuneSideMetrics(
            faithfulness=_BASE_FAITH,
            answer_relevancy=0.7,
            questions_scored=3,
        ),
        adapter=FinetuneSideMetrics(
            faithfulness=_ADAPTER_FAITH,
            answer_relevancy=0.75,
            questions_scored=3,
        ),
        auto_promote=False,
        summary="Human judgment required — no automated promote (RD-338)",
    )
    assert report.run_id == run_id
    assert report.adapter_id == "adapter-abc"
    assert report.base.faithfulness == _BASE_FAITH
    assert report.adapter.faithfulness == _ADAPTER_FAITH
    assert report.auto_promote is False


def test_finetune_eval_report_rejects_auto_promote_true() -> None:
    """AC-FT4 / RD-338: auto_promote must stay false (human judgment only)."""
    with pytest.raises(ValidationError):
        FinetuneEvalReportResponse(
            run_id=uuid4(),
            adapter_id="adapter-x",
            base_model_id="qwen2.5:1.5b-instruct",
            base=FinetuneSideMetrics(),
            adapter=FinetuneSideMetrics(),
            auto_promote=True,  # type: ignore[arg-type]
            summary="x",
        )


def test_build_finetune_eval_report_sets_human_judgment_summary() -> None:
    """Builder always disables auto-promote and states human judgment (RD-338)."""
    report = build_finetune_eval_report(
        run_id=uuid4(),
        adapter_id="adapter-1",
        base_model_id="qwen2.5:1.5b-instruct",
        base=FinetuneSideMetrics(
            faithfulness=0.5,
            answer_relevancy=0.4,
            questions_scored=_QUESTIONS,
        ),
        adapter=FinetuneSideMetrics(
            faithfulness=0.6,
            answer_relevancy=0.55,
            questions_scored=_QUESTIONS,
        ),
    )
    assert report.auto_promote is False
    assert "judgment" in report.summary.lower()
    assert report.base.questions_scored == _QUESTIONS
    assert report.adapter.questions_scored == _QUESTIONS
