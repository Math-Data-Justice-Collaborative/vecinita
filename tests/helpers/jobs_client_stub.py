"""Shared stub for Modal jobs client in internal-write integration tests."""

from __future__ import annotations

from uuid import UUID, uuid4


class StubJobsClient:
    """Record enqueue calls without hitting Modal (EV-012 TP-S013-06)."""

    def __init__(self) -> None:
        """Initialize empty enqueue logs."""
        self.enqueued_retag: list[UUID] = []
        self.enqueued_eval: list[UUID] = []

    def enqueue_retag(
        self,
        document_id: UUID,
        *,
        authorization: str | None = None,
    ) -> UUID:
        """Record a retag enqueue and return a synthetic job id."""
        _ = authorization
        self.enqueued_retag.append(document_id)
        return uuid4()

    def enqueue_eval(
        self,
        eval_run_id: UUID,
        *,
        authorization: str | None = None,
    ) -> UUID:
        """Record an eval enqueue and return a synthetic job id."""
        _ = authorization
        self.enqueued_eval.append(eval_run_id)
        return uuid4()
