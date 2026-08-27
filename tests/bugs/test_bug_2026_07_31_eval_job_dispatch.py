"""BUG-2026-07-31: Modal run_job must dispatch job_type=eval (not ingest).

Admin Evaluation enqueues Modal jobs with job_type=eval and empty urls. Before the
fix, run_job fell through to run_ingest_job → BatchUpsertRequest(documents=[])
ValidationError → job failed. Eval must call the eval worker instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore

if TYPE_CHECKING:
    from vecinita_shared_schemas.internal_write import BatchUpsertRequest


class _StubEmbedClient:
    """Minimal embed stub — must not be required for eval dispatch."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [[0.0] * 384 for _ in texts]


class _CapturingWriteClient:
    """Record upsert/execute calls for eval dispatch assertions."""

    def __init__(self) -> None:
        """Initialize empty capture lists."""
        self.upsert_batches: list[object] = []
        self.executed_eval_runs: list[tuple[UUID, str | None]] = []

    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _CapturingWriteClient:
        """Return self — audit actor scoping is a no-op in unit stubs."""
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        """No-op audit emit for unit stubs."""
        _ = event

    def upsert_batch(self, body: BatchUpsertRequest | object) -> None:
        """Capture ingest upserts (eval must never call this)."""
        self.upsert_batches.append(body)

    def execute_eval_run(
        self,
        eval_run_id: UUID,
        *,
        question: str | None = None,
    ) -> None:
        """Capture Modal→DO eval execute calls."""
        self.executed_eval_runs.append((eval_run_id, question))


def test_run_job_eval_dispatches_to_execute_not_ingest() -> None:
    """job_type=eval must complete via execute_eval_run, never empty ingest upsert.

    Pre-fix: ValidationError from BatchUpsertRequest(documents=[]) / failed status.
    Post-fix: status=completed and write_client.execute_eval_run called.
    """
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id), "question": "What hours?"},
    )
    write = _CapturingWriteClient()

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=write,  # type: ignore[arg-type]
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed", (
        f"expected completed eval job, got {updated.status}: "
        + f"{updated.error_code} {updated.error_message}"
    )
    assert write.upsert_batches == [], "eval must not call upsert_batch (ingest path)"
    assert write.executed_eval_runs == [(eval_run_id, "What hours?")]


def test_run_job_eval_without_eval_run_id_fails_closed() -> None:
    """Eval jobs missing eval_run_id must fail with a clear error (not ingest)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="eval", options={})
    write = _CapturingWriteClient()

    with pytest.raises((ValueError, KeyError, RuntimeError)):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=write,  # type: ignore[arg-type]
        )

    assert write.upsert_batches == []
    assert write.executed_eval_runs == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"


def test_run_job_unknown_job_type_fails_closed_not_ingest() -> None:
    """Unknown job_type must fail closed — never fall through to ingest.

    Prevention for BUG-2026-07-31 class: catch-all else → run_ingest_job.
    """
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="not_a_real_job_type", options={})
    write = _CapturingWriteClient()

    with pytest.raises(ValueError, match="unknown job_type"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=write,  # type: ignore[arg-type]
        )

    assert write.upsert_batches == []
    assert write.executed_eval_runs == []
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "ValueError"
