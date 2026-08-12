"""Write-API helpers to enqueue F76 freshness_refresh (Refresh now).

[Corpus: feature-list.md §F76]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/decisions.md §RD-337]
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import text
from vecinita_shared_schemas.automations import is_automations_kill_switch_on
from vecinita_shared_schemas.db_mapping import mapping_row
from vecinita_shared_schemas.freshness import (
    FreshnessEnqueueRequest,
    decide_freshness_enqueue,
    is_document_stale,
    is_freshness_enabled,
    parse_freshness_stale_days,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Connection, Engine

    from vecinita_internal_write_api.jobs_client import DataManagementJobsClient

_logger = logging.getLogger(__name__)

FreshnessRefreshOutcome = Literal[
    "enqueue",
    "skip_disabled",
    "skip_kill_switch",
    "skip_refresh_disabled",
    "skip_not_stale",
    "not_found",
]


def document_is_stale_now(last_checked_at: datetime | None) -> bool:
    """Compute stale using current UTC and configured threshold (AC-FR1)."""
    return is_document_stale(
        last_checked_at,
        now=datetime.now(tz=UTC),
        stale_days=parse_freshness_stale_days(),
    )


def enqueue_document_refresh(
    *,
    engine: Engine,
    jobs_client: DataManagementJobsClient | None,
    document_id: UUID,
    force: bool = True,
    authorization: str | None = None,
) -> tuple[FreshnessRefreshOutcome, UUID | None]:
    """Enqueue ``freshness_refresh`` for one document (Refresh now uses force=True)."""
    if jobs_client is None:
        return "skip_disabled", None
    with engine.connect() as conn:
        doc = _load_freshness_row(conn, document_id)
    if doc is None:
        return "not_found", None
    refresh_enabled, last_checked_at = doc
    decision = decide_freshness_enqueue(
        FreshnessEnqueueRequest(
            freshness_enabled=is_freshness_enabled(),
            kill_switch=is_automations_kill_switch_on(),
            refresh_enabled=refresh_enabled,
            is_stale=document_is_stale_now(last_checked_at),
            force=force,
            document_id=document_id,
        )
    )
    if decision != "enqueue":
        return decision, None
    try:
        job_id = jobs_client.enqueue_freshness_refresh(
            document_id,
            force=force,
            authorization=authorization,
        )
    except Exception:  # noqa: BLE001  # Refresh now must surface skip, not 500
        _logger.warning(
            "freshness_refresh enqueue for document %s failed",
            document_id,
            exc_info=True,
        )
        return "skip_disabled", None
    return "enqueue", job_id


def _load_freshness_row(
    conn: Connection,
    document_id: UUID,
) -> tuple[bool, datetime | None] | None:
    row = (
        conn.execute(
            text(
                """
                SELECT refresh_enabled, last_checked_at
                FROM documents
                WHERE id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    mapped = mapping_row(row)
    raw_enabled = mapped["refresh_enabled"]
    refresh_enabled = raw_enabled if isinstance(raw_enabled, bool) else bool(raw_enabled)
    raw_checked = mapped.get("last_checked_at")
    last_checked = raw_checked if isinstance(raw_checked, datetime) else None
    return refresh_enabled, last_checked
