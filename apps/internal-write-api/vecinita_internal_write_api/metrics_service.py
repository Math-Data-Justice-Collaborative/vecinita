"""F84 operational metrics event persistence (ADR-055)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_datetime,
    row_int,
    row_str,
    row_str_optional,
    scalar_uuid,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.internal_write import (
    MetricsEventAccepted,
    MetricsEventRecord,
    MetricsEventRequest,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.engine import Engine

_Workload = Literal["chat", "embed"]
_Outcome = Literal["success", "failure", "no_context"]


def record_metric_event(*, engine: Engine, body: MetricsEventRequest) -> MetricsEventAccepted:
    """Insert one allow-listed operational metric event."""
    with engine.begin() as conn:
        event_id = scalar_uuid(
            sqlalchemy_scalar_one(
                conn.execute(
                    text(
                        """
                        INSERT INTO operation_metrics
                            (workload, outcome, latency_ms, error_code, locale, job_id)
                        VALUES
                            (:workload, :outcome, :latency_ms, :error_code, :locale, :job_id)
                        RETURNING id
                        """
                    ),
                    {
                        "workload": body.workload,
                        "outcome": body.outcome,
                        "latency_ms": body.latency_ms,
                        "error_code": body.error_code,
                        "locale": body.locale,
                        "job_id": body.job_id,
                    },
                )
            )
        )
    return MetricsEventAccepted(acknowledged=True, event_id=event_id)


def fetch_metric_event(*, engine: Engine, event_id: UUID) -> MetricsEventRecord:
    """Return one metric event by id (404 if missing)."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT id, workload, outcome, latency_ms, error_code, locale, job_id, created_at
                FROM operation_metrics
                WHERE id = :event_id
                """
                ),
                {"event_id": event_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event_not_found")
    mapped = mapping_row(row)
    workload_raw = row_str(mapped, "workload")
    outcome_raw = row_str(mapped, "outcome")
    if workload_raw not in {"chat", "embed"}:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="bad_row")
    if outcome_raw not in {"success", "failure", "no_context"}:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="bad_row")
    return MetricsEventRecord(
        event_id=scalar_uuid(mapped["id"]),
        workload=cast("_Workload", workload_raw),
        outcome=cast("_Outcome", outcome_raw),
        latency_ms=row_int(mapped, "latency_ms"),
        error_code=row_str_optional(mapped, "error_code"),
        locale=row_str_optional(mapped, "locale"),
        job_id=row_str_optional(mapped, "job_id"),
        created_at=row_datetime(mapped, "created_at"),
    )
