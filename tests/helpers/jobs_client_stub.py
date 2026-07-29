"""Shared stub for Modal jobs client in internal-write integration/e2e tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from vecinita_internal_write_api.eval_service import execute_eval_run

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


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
        question: str | None = None,
    ) -> UUID:
        """Record an eval enqueue and return a synthetic job id."""
        _ = (authorization, question)
        self.enqueued_eval.append(eval_run_id)
        return uuid4()


class LocalEvalJobsClient(StubJobsClient):
    """Enqueue eval by running ``execute_eval_run`` locally (test harness only)."""

    def __init__(
        self,
        engine: Engine,
        *,
        embed_fn: Callable[[str], list[float]],
        judge: JudgeClient,
    ) -> None:
        """Bind DB engine and eval harness deps used for local execution."""
        super().__init__()
        self._engine = engine
        self._embed_fn = embed_fn
        self._judge = judge

    def enqueue_eval(
        self,
        eval_run_id: UUID,
        *,
        authorization: str | None = None,
        question: str | None = None,
    ) -> UUID:
        """Enqueue by executing the eval harness synchronously for tests."""
        job_id = StubJobsClient.enqueue_eval(
            self,
            eval_run_id,
            authorization=authorization,
            question=question,
        )
        execute_eval_run(
            self._engine,
            run_id=eval_run_id,
            question=question,
            embed_fn=self._embed_fn,
            judge=self._judge,
        )
        return job_id
