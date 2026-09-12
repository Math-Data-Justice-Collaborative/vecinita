"""F75 daily catch-up schedule tick (ADR-052 / TC-289).

[Corpus: feature-list.md §F78]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-289]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from vecinita_shared_schemas.automations import (
    AutomationRunStatus,
    EmbedStatus,
    enqueue_catchup_targets,
    is_automations_enabled,
    is_automations_kill_switch_on,
    parse_automations_max_concurrent,
)

from vecinita_data_management_backend.automation_run_persist import (
    maybe_record_automation_run,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

_logger = logging.getLogger(__name__)

TICK_RESULT = "automation_catchup_tick"


class _EnqueueCatchupFn(Protocol):
    def __call__(self, document_id: UUID, *, revision: str, embed_status: str) -> UUID:
        """Enqueue one catch-up target."""
        ...


class _FunctionCatchupClient:
    def __init__(self, enqueue: _EnqueueCatchupFn) -> None:
        self._enqueue = enqueue

    def enqueue_automation_catchup(
        self,
        document_id: UUID,
        *,
        revision: str,
        embed_status: EmbedStatus,
        authorization: str | None = None,
    ) -> UUID:
        _ = authorization
        return self._enqueue(document_id, revision=revision, embed_status=embed_status)


def _record_tick(
    write_client: object,
    *,
    status: AutomationRunStatus,
    error: str | None = None,
) -> bool:
    return maybe_record_automation_run(
        write_client,
        job_type="automation_catchup",
        status=status,
        document_id=None,
        revision=None,
        error=error,
    )


def run_scheduled_catchup_tick(
    *,
    write_client: object,
    list_residuals: Callable[[], list[tuple[UUID, str, EmbedStatus]]],
    enqueue_catchup: _EnqueueCatchupFn,
    running_count: int,
    seen_keys: frozenset[str],
) -> dict[str, object]:
    """Scan residual embed states and enqueue F78 catch-up work (EV-038 / TC-341)."""
    _logger.info("daily schedule tick: job_type=automation_catchup residual scan")
    if is_automations_kill_switch_on():
        persisted = _record_tick(write_client, status="blocked")
        result: dict[str, object] = {
            "job_type": "automation_catchup",
            "enqueued": 0,
            "skipped": 0,
            "outcome": "skipped_kill_switch",
        }
        if not persisted:
            result["history_persist_failed"] = True
        return result
    if not is_automations_enabled():
        persisted = _record_tick(write_client, status="skipped")
        result = {
            "job_type": "automation_catchup",
            "enqueued": 0,
            "skipped": 0,
            "outcome": "skipped_disabled",
        }
        if not persisted:
            result["history_persist_failed"] = True
        return result

    results = enqueue_catchup_targets(
        _FunctionCatchupClient(enqueue_catchup),
        targets=list_residuals(),
        enabled=True,
        kill_switch=False,
        running_count=running_count,
        max_concurrent=parse_automations_max_concurrent(),
        seen_keys=seen_keys,
    )
    enqueued = sum(1 for decision, _job_id in results if decision == "enqueue")
    skipped = len(results) - enqueued
    persisted = _record_tick(write_client, status="completed")
    if not persisted:
        return {
            "job_type": "automation_catchup",
            "enqueued": enqueued,
            "skipped": skipped,
            "outcome": "history_persist_failed",
            "history_persist_failed": True,
        }
    return {
        "job_type": "automation_catchup",
        "enqueued": enqueued,
        "skipped": skipped,
        "outcome": "enqueued" if enqueued else "noop",
    }


def record_scheduled_catchup_tick(write_client: object) -> str:
    """Backward-compatible wrapper for historical callers."""
    _logger.info("daily schedule tick: job_type=automation_catchup (compat history-only)")
    _ = _record_tick(write_client, status="completed")
    return TICK_RESULT
