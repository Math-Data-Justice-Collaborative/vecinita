"""Unit tests for Modal eval job runner (BUG-2026-07-31)."""

from __future__ import annotations

from typing import Never
from uuid import UUID, uuid4

import pytest
from vecinita_data_management_backend.pipeline import run_eval_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_data_management_backend.write_client import InternalWriteClientError


class _CapturingWriteClient:
    """Capture execute_eval_run calls."""

    def __init__(self) -> None:
        """Initialize empty capture list."""
        self.executed: list[tuple[UUID, str | None]] = []
        self.fail_with: Exception | None = None

    def execute_eval_run(
        self,
        eval_run_id: UUID,
        *,
        question: str | None = None,
    ) -> None:
        """Record or raise based on fail_with."""
        if self.fail_with is not None:
            raise self.fail_with
        self.executed.append((eval_run_id, question))


def test_run_eval_job_calls_execute_and_completes() -> None:
    """Happy path: running → execute → completed."""
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id), "question": "Hours?"},
    )
    write = _CapturingWriteClient()

    run_eval_job(
        record.job_id,
        store=store,
        write_client=write,  # type: ignore[arg-type]
    )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.eval_run_id == eval_run_id
    assert write.executed == [(eval_run_id, "Hours?")]


def test_run_eval_job_requires_eval_run_id() -> None:
    """Missing eval_run_id fails closed with ValueError."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="eval", options={})
    write = _CapturingWriteClient()

    with pytest.raises(ValueError, match="eval_run_id"):
        run_eval_job(
            record.job_id,
            store=store,
            write_client=write,  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert write.executed == []


def test_run_eval_job_rejects_non_eval_type() -> None:
    """Wrong job_type raises ValueError."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com"], job_type="ingest")
    write = _CapturingWriteClient()

    with pytest.raises(ValueError, match="not an eval job"):
        run_eval_job(
            record.job_id,
            store=store,
            write_client=write,  # type: ignore[arg-type]
        )


def test_run_eval_job_missing_job_raises_key_error() -> None:
    """Unknown job_id raises KeyError."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_eval_job(
            uuid4(),
            store=store,
            write_client=_CapturingWriteClient(),  # type: ignore[arg-type]
        )


def test_run_eval_job_marks_failed_when_execute_raises() -> None:
    """Write-api execute failure marks Modal job failed and re-raises."""
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id)},
    )
    write = _CapturingWriteClient()
    write.fail_with = InternalWriteClientError("execute_eval_run failed: 500 boom")

    with pytest.raises(InternalWriteClientError, match="execute_eval_run"):
        run_eval_job(
            record.job_id,
            store=store,
            write_client=write,  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_code == "InternalWriteClientError"


def test_run_eval_job_raises_when_execute_never_returns() -> None:
    """Never-returning stub still hits failure path when exception escapes."""
    store = InMemoryJobStore()
    eval_run_id = uuid4()
    record = store.create_job(
        urls=[],
        job_type="eval",
        options={"eval_run_id": str(eval_run_id)},
    )

    class _Boom:
        def execute_eval_run(
            self,
            _eval_run_id: UUID,
            *,
            question: str | None = None,
        ) -> Never:
            _ = question
            msg = "downstream"
            raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="downstream"):
        run_eval_job(
            record.job_id,
            store=store,
            write_client=_Boom(),  # type: ignore[arg-type]
        )

    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
