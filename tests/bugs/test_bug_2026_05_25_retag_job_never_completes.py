"""BUG-2026-05-25: Retag job stays "pending" when tag_client is None.

Root cause: run_job() raises RuntimeError before run_retag_job's try/except can
mark the job as "failed". The exception escapes the FastAPI background task runner
and the job stays in a non-terminal "pending" state indefinitely.

The fix must ensure that ANY exception during job execution results in the job
reaching a terminal state ("failed" with an error message).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore

if TYPE_CHECKING:
    from uuid import UUID


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.01] * 384 for _ in texts]

    def close(self) -> None:
        return None


class _MockWriteClient:
    def get_document_detail(self, document_id: UUID) -> object:
        msg = "should not be called when tag_client is None"
        raise AssertionError(msg)

    def patch_document_tags(self, document_id: UUID, tags: list) -> object:
        msg = "should not be called when tag_client is None"
        raise AssertionError(msg)

    def upsert_batch(self, body: object) -> object:
        msg = "should not be called for retag jobs"
        raise AssertionError(msg)

    def close(self) -> None:
        return None


@pytest.fixture
def store_with_retag_job() -> tuple[InMemoryJobStore, UUID]:
    """Create a store with a pending retag job."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        options={"document_id": "b39cd779-0275-46fa-997e-485ffa9b6938"},
        job_type="retag",
    )
    assert record.status == "pending"
    return store, record.job_id


def test_retag_job_reaches_terminal_state_when_tag_client_none(
    store_with_retag_job: tuple[InMemoryJobStore, UUID],
) -> None:
    """A retag job with tag_client=None must be marked 'failed', not stay 'pending'.

    This is the core bug: run_job raises RuntimeError("tag_client is required...")
    but no handler updates the job status. The frontend polls forever.
    """
    store, job_id = store_with_retag_job

    with pytest.raises(RuntimeError, match="tag_client is required"):
        run_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=_MockWriteClient(),  # type: ignore[arg-type]
            tag_client=None,
        )

    record = store.get_job(job_id)
    assert record is not None
    # BUG: job stays "pending" — should be "failed"
    assert record.status == "failed", (
        f"Expected job status 'failed' but got '{record.status}'. "
        "The job must reach a terminal state so the frontend stops polling."
    )
    assert record.error_message is not None
    assert "tag_client" in record.error_message.lower()


def test_retag_job_reaches_terminal_state_on_any_pre_execution_error(
    store_with_retag_job: tuple[InMemoryJobStore, UUID],
) -> None:
    """Any error before run_retag_job's own handler must still mark job 'failed'."""
    store, job_id = store_with_retag_job

    # Corrupt the job options so document_id validation fails inside run_retag_job
    record = store.get_job(job_id)
    assert record is not None
    record.options = {}  # missing document_id

    class _TagClient:
        def infer_document_tags(self, **kwargs: object) -> list[str]:
            return []

    with pytest.raises((RuntimeError, ValueError, KeyError)):
        run_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=_MockWriteClient(),  # type: ignore[arg-type]
            tag_client=_TagClient(),  # type: ignore[arg-type]
        )

    record = store.get_job(job_id)
    assert record is not None
    assert record.status == "failed", (
        f"Expected job status 'failed' but got '{record.status}'. "
        "Pre-execution errors must still mark the job as failed."
    )
