"""Write-API CRUD hooks that enqueue F75 catch-up asynchronously (RD-335).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/decisions.md §RD-326 RD-335]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vecinita_shared_schemas.automations import (
    CatchupEnqueueDecision,
    CatchupEnqueueRequest,
    EmbedStatus,
    catchup_idempotency_key,
    decide_catchup_enqueue,
    is_automations_kill_switch_on,
    parse_automations_max_concurrent,
)

from vecinita_internal_write_api.automations import get_automations_config

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Engine

    from vecinita_internal_write_api.jobs_client import DataManagementJobsClient

_logger = logging.getLogger(__name__)


def maybe_enqueue_catchup_after_document_change(  # noqa: PLR0913  # CRUD hook surface
    *,
    engine: Engine,
    jobs_client: DataManagementJobsClient | None,
    document_id: UUID,
    revision: str,
    embed_status: EmbedStatus,
    authorization: str | None = None,
) -> CatchupEnqueueDecision:
    """Best-effort async catch-up enqueue after doc CRUD (never raises to caller)."""
    if jobs_client is None:
        return "skip_disabled"
    try:
        config = get_automations_config(engine)
        kill_switch = is_automations_kill_switch_on() or config.kill_switch
        decision = decide_catchup_enqueue(
            CatchupEnqueueRequest(
                enabled=config.enabled,
                kill_switch=kill_switch,
                embed_status=embed_status,
                idempotency_key=catchup_idempotency_key(
                    document_id=document_id,
                    revision=revision,
                ),
                seen_keys=frozenset(),
                running_count=0,
                max_concurrent=parse_automations_max_concurrent(),
            )
        )
        if decision != "enqueue":
            return decision
        jobs_client.enqueue_automation_catchup(
            document_id,
            revision=revision,
            embed_status=embed_status,
            authorization=authorization,
        )
    except Exception:  # noqa: BLE001  # CRUD must not fail when catch-up enqueue fails
        _logger.warning(
            "catch-up enqueue after document %s failed",
            document_id,
            exc_info=True,
        )
        return "skip_disabled"
    else:
        return "enqueue"
