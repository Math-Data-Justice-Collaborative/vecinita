"""F78 automations config + run history persistence (EV-027 / ADR-052 / TP3).

[Corpus: feature-list.md §F75]
[Spec: docs/api-contract.md §EV-027 Automations]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import text
from vecinita_shared_schemas.automations import (
    AutomationJobType,
    AutomationRun,
    AutomationRunCreateRequest,
    AutomationRunListResponse,
    AutomationRunStatus,
    AutomationsConfigResponse,
    is_automations_kill_switch_on,
    parse_automations_max_concurrent,
)
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_datetime,
    row_datetime_optional,
    row_str,
    row_str_optional,
    row_uuid,
    row_uuid_optional,
    scalar_int,
    sqlalchemy_scalar_one,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.engine import Engine


def _run_from_row(row: Mapping[str, object]) -> AutomationRun:
    job_type = cast("AutomationJobType", row_str(row, "job_type"))
    status = cast("AutomationRunStatus", row_str(row, "status"))
    return AutomationRun(
        id=row_uuid(row, "id"),
        job_type=job_type,
        status=status,
        started_at=row_datetime_optional(row, "started_at"),
        finished_at=row_datetime_optional(row, "finished_at"),
        error=row_str_optional(row, "error"),
        document_id=row_uuid_optional(row, "document_id"),
        revision=row_str_optional(row, "revision"),
        created_at=row_datetime(row, "created_at"),
        updated_at=row_datetime(row, "updated_at"),
    )


def get_automations_config(engine: Engine) -> AutomationsConfigResponse:
    """Return enable (DB) + kill-switch/caps (env)."""
    with engine.connect() as conn:
        enabled_raw = sqlalchemy_scalar_one(
            conn.execute(text("SELECT enabled FROM automation_settings WHERE id = 1"))
        )
    return AutomationsConfigResponse(
        enabled=bool(enabled_raw),
        kill_switch=is_automations_kill_switch_on(),
        max_concurrent=parse_automations_max_concurrent(),
    )


def set_automations_enabled(engine: Engine, *, enabled: bool) -> AutomationsConfigResponse:
    """Persist DM enable/disable and return the full config snapshot."""
    with engine.begin() as conn:
        _ = conn.execute(
            text(
                """
                UPDATE automation_settings
                SET enabled = :enabled, updated_at = now()
                WHERE id = 1
                """
            ),
            {"enabled": enabled},
        )
    return get_automations_config(engine)


def list_automation_runs(
    engine: Engine,
    *,
    page: int = 1,
    page_size: int = 20,
) -> AutomationRunListResponse:
    """Return paginated automation_runs (newest first)."""
    offset = (page - 1) * page_size
    with engine.connect() as conn:
        total = scalar_int(
            sqlalchemy_scalar_one(conn.execute(text("SELECT COUNT(*) FROM automation_runs")))
        )
        rows = (
            conn.execute(
                text(
                    """
                    SELECT
                        id, job_type, status, started_at, finished_at, error,
                        document_id, revision, created_at, updated_at
                    FROM automation_runs
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": page_size, "offset": offset},
            )
            .mappings()
            .all()
        )
    items = [_run_from_row(mapping_row(row)) for row in rows]
    return AutomationRunListResponse(
        items=items,
        page=page,
        page_size=page_size,
        total_count=total,
    )


_TERMINAL_RUN_STATUSES: frozenset[str] = frozenset({"completed", "failed", "skipped", "blocked"})


def create_automation_run(
    engine: Engine,
    body: AutomationRunCreateRequest,
) -> AutomationRun:
    """Insert one ``automation_runs`` row and return the persisted record (TC-289)."""
    now = datetime.now(UTC)
    started_at = body.started_at or now
    finished_at = body.finished_at
    if finished_at is None and body.status in _TERMINAL_RUN_STATUSES:
        finished_at = now
    with engine.begin() as conn:
        row = mapping_row(
            conn.execute(
                text(
                    """
                    INSERT INTO automation_runs (
                        job_type, status, started_at, finished_at,
                        error, document_id, revision
                    )
                    VALUES (
                        :job_type, :status, :started_at, :finished_at,
                        :error, :document_id, :revision
                    )
                    RETURNING
                        id, job_type, status, started_at, finished_at, error,
                        document_id, revision, created_at, updated_at
                    """
                ),
                {
                    "job_type": body.job_type,
                    "status": body.status,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error": body.error,
                    "document_id": body.document_id,
                    "revision": body.revision,
                },
            )
            .mappings()
            .one()
        )
    return _run_from_row(row)
