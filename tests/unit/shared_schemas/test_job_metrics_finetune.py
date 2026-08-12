"""T129.9 — JobMetrics round-trips F77 train adapter fields (UJ-082).

Completed ``finetune_train`` jobs store adapter_id / path / pair_count /
base_model_id on metrics; GET /jobs must serialize them for the DM FT UI.

[Corpus: feature-list.md §F77]
[Corpus: user-journeys.md §UJ-082]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from vecinita_shared_schemas.data_management import Job, JobMetrics

_PAIR_COUNT = 12


def test_job_metrics_accepts_finetune_adapter_fields() -> None:
    """Trained LoRA outcome fields are part of JobMetrics (not forbidden extras)."""
    metrics = JobMetrics.model_validate(
        {
            "finetune_outcome": "trained",
            "adapter_id": "adapter-ui-1",
            "adapter_path": "/adapters/adapter-ui-1",
            "pair_count": _PAIR_COUNT,
            "base_model_id": "qwen2.5:1.5b-instruct",
        }
    )
    assert metrics.finetune_outcome == "trained"
    assert metrics.adapter_id == "adapter-ui-1"
    assert metrics.adapter_path == "/adapters/adapter-ui-1"
    assert metrics.pair_count == _PAIR_COUNT
    assert metrics.base_model_id == "qwen2.5:1.5b-instruct"


def test_job_schema_round_trips_completed_finetune_train() -> None:
    """GET /jobs payload after train includes adapter_id for promote UI."""
    now = datetime.now(tz=UTC)
    job = Job.model_validate(
        {
            "job_id": uuid4(),
            "status": "completed",
            "job_type": "finetune_train",
            "urls": [],
            "approved": True,
            "metrics": {
                "finetune_outcome": "trained",
                "adapter_id": "adapter-ui-2",
                "adapter_path": "/adapters/adapter-ui-2",
                "pair_count": 4,
                "base_model_id": "qwen2.5:1.5b-instruct",
            },
            "created_at": now,
            "updated_at": now,
        }
    )
    assert job.job_type == "finetune_train"
    assert job.approved is True
    assert job.metrics is not None
    assert job.metrics.adapter_id == "adapter-ui-2"
