"""F84 metrics summary and timeseries queries (ADR-055)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal, cast

from fastapi import HTTPException, status
from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import mapping_row, row_int, row_str
from vecinita_shared_schemas.internal_write import (
    MetricsLatencyPercentiles,
    MetricsSummaryResponse,
    MetricsTimeseriesBucket,
    MetricsTimeseriesResponse,
    MetricsTopError,
    MetricsWorkloadStats,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

MetricsWindow = Literal["1h", "24h", "7d", "30d"]
MetricsMetric = Literal[
    "ingest_success_rate",
    "chat_success_rate",
    "embed_success_rate",
    "ingest_volume",
    "chat_volume",
    "embed_volume",
]

_WINDOW_DELTAS: dict[MetricsWindow, timedelta] = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def parse_metrics_window(raw: str) -> MetricsWindow:
    """Validate window query param."""
    if raw == "1h":
        return "1h"
    if raw == "24h":
        return "24h"
    if raw == "7d":
        return "7d"
    if raw == "30d":
        return "30d"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="invalid_window",
    )


def parse_metrics_metric(raw: str) -> MetricsMetric:
    """Validate timeseries metric query param."""
    if raw == "ingest_success_rate":
        return "ingest_success_rate"
    if raw == "chat_success_rate":
        return "chat_success_rate"
    if raw == "embed_success_rate":
        return "embed_success_rate"
    if raw == "ingest_volume":
        return "ingest_volume"
    if raw == "chat_volume":
        return "chat_volume"
    if raw == "embed_volume":
        return "embed_volume"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="invalid_metric",
    )


def _window_start(window: MetricsWindow) -> datetime:
    return datetime.now(tz=UTC) - _WINDOW_DELTAS[window]


def _success_rate(succeeded: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(succeeded / total, 6)


def _ingest_stats(*, engine: Engine, since: datetime) -> MetricsWorkloadStats:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT status, COUNT(*)::int AS n
                FROM jobs
                WHERE created_at >= :since
                  AND COALESCE(job_type, 'ingest') IN ('ingest', 'retag')
                GROUP BY status
                """
            ),
            {"since": since},
        ).mappings()
    counts = {row_str(mapping_row(row), "status"): row_int(mapping_row(row), "n") for row in rows}
    succeeded = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    total = sum(counts.values())
    return MetricsWorkloadStats(
        total=total,
        succeeded=succeeded,
        failed=failed,
        success_rate=_success_rate(succeeded, total),
    )


def _event_workload_stats(
    *,
    engine: Engine,
    since: datetime,
    workload: Literal["chat", "embed"],
) -> MetricsWorkloadStats:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT
                      COUNT(*)::int AS total,
                      COUNT(*) FILTER (WHERE outcome = 'success')::int AS succeeded,
                      COUNT(*) FILTER (WHERE outcome = 'failure')::int AS failed,
                      COUNT(*) FILTER (WHERE outcome = 'no_context')::int AS no_context
                    FROM operation_metrics
                    WHERE created_at >= :since AND workload = :workload
                    """
                ),
                {"since": since, "workload": workload},
            )
            .mappings()
            .one()
        )
    mapped = mapping_row(row)
    total = row_int(mapped, "total")
    succeeded = row_int(mapped, "succeeded")
    failed = row_int(mapped, "failed")
    no_context = row_int(mapped, "no_context")
    stats = MetricsWorkloadStats(
        total=total,
        succeeded=succeeded,
        failed=failed,
        success_rate=_success_rate(succeeded, total),
    )
    if workload == "chat":
        return stats.model_copy(update={"no_context": no_context})
    return stats


def _latency_for(
    *,
    engine: Engine,
    since: datetime,
    workload: Literal["chat", "embed"],
) -> MetricsLatencyPercentiles | None:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT
                      percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) AS p50,
                      percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95
                    FROM operation_metrics
                    WHERE created_at >= :since AND workload = :workload
                    """
                ),
                {"since": since, "workload": workload},
            )
            .mappings()
            .one()
        )
    p50 = mapping_row(row)["p50"]
    p95 = mapping_row(row)["p95"]
    if p50 is None or p95 is None:
        return None
    return MetricsLatencyPercentiles(p50=int(float(str(p50))), p95=int(float(str(p95))))


def _top_errors(*, engine: Engine, since: datetime) -> list[MetricsTopError]:
    out: list[MetricsTopError] = []
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT workload, error_code, COUNT(*)::int AS n
                FROM operation_metrics
                WHERE created_at >= :since
                  AND error_code IS NOT NULL
                  AND outcome = 'failure'
                GROUP BY workload, error_code
                ORDER BY n DESC
                LIMIT 20
                """
            ),
            {"since": since},
        ).mappings()
    for row in rows:
        mapped = mapping_row(row)
        workload = row_str(mapped, "workload")
        if workload not in {"chat", "embed"}:
            continue  # pragma: no cover — defensive; CHECK constraint prevents
        out.append(
            MetricsTopError(
                workload=cast("Literal['chat', 'embed']", workload),
                error_code=row_str(mapped, "error_code"),
                count=row_int(mapped, "n"),
            )
        )
    with engine.connect() as conn:
        job_rows = conn.execute(
            text(
                """
                SELECT error_code, COUNT(*)::int AS n
                FROM jobs
                WHERE created_at >= :since
                  AND status = 'failed'
                  AND error_code IS NOT NULL
                  AND COALESCE(job_type, 'ingest') IN ('ingest', 'retag')
                GROUP BY error_code
                ORDER BY n DESC
                LIMIT 10
                """
            ),
            {"since": since},
        ).mappings()
    out.extend(
        [
            MetricsTopError(
                workload="ingest",
                error_code=row_str(mapping_row(row), "error_code"),
                count=row_int(mapping_row(row), "n"),
            )
            for row in job_rows
        ]
    )
    out.sort(key=lambda item: item.count, reverse=True)
    return out[:20]


def fetch_metrics_summary(*, engine: Engine, window: MetricsWindow) -> MetricsSummaryResponse:
    """Aggregate ingest (jobs) + chat/embed (operation_metrics) for a window."""
    since = _window_start(window)
    chat = _event_workload_stats(engine=engine, since=since, workload="chat")
    embed = _event_workload_stats(engine=engine, since=since, workload="embed")
    ingest = _ingest_stats(engine=engine, since=since)
    latency: dict[str, MetricsLatencyPercentiles] = {}
    chat_lat = _latency_for(engine=engine, since=since, workload="chat")
    embed_lat = _latency_for(engine=engine, since=since, workload="embed")
    if chat_lat is not None:
        latency["chat"] = chat_lat
    if embed_lat is not None:
        latency["embed"] = embed_lat
    return MetricsSummaryResponse(
        window=window,
        workloads={"ingest": ingest, "chat": chat, "embed": embed},
        latency_ms=latency,
        top_error_codes=_top_errors(engine=engine, since=since),
    )


def _ingest_timeseries(
    *,
    engine: Engine,
    since: datetime,
    window: MetricsWindow,
) -> list[MetricsTimeseriesBucket]:
    if window == "1h":
        sql = """
            SELECT date_trunc('minute', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE status = 'completed')::int AS succeeded,
                   COUNT(*) FILTER (WHERE status = 'failed')::int AS failed
            FROM jobs
            WHERE created_at >= :since
              AND COALESCE(job_type, 'ingest') IN ('ingest', 'retag')
            GROUP BY 1 ORDER BY 1
            """
    elif window == "24h":
        sql = """
            SELECT date_trunc('hour', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE status = 'completed')::int AS succeeded,
                   COUNT(*) FILTER (WHERE status = 'failed')::int AS failed
            FROM jobs
            WHERE created_at >= :since
              AND COALESCE(job_type, 'ingest') IN ('ingest', 'retag')
            GROUP BY 1 ORDER BY 1
            """
    else:
        sql = """
            SELECT date_trunc('day', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE status = 'completed')::int AS succeeded,
                   COUNT(*) FILTER (WHERE status = 'failed')::int AS failed
            FROM jobs
            WHERE created_at >= :since
              AND COALESCE(job_type, 'ingest') IN ('ingest', 'retag')
            GROUP BY 1 ORDER BY 1
            """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"since": since}).mappings()
    buckets: list[MetricsTimeseriesBucket] = []
    for row in rows:
        mapped = mapping_row(row)
        total = row_int(mapped, "total")
        succeeded = row_int(mapped, "succeeded")
        failed = row_int(mapped, "failed")
        bucket_t = mapped["bucket"]
        if not isinstance(bucket_t, datetime):  # pragma: no cover
            continue
        buckets.append(
            MetricsTimeseriesBucket(
                t=bucket_t,
                success_rate=_success_rate(succeeded, total),
                total=total,
                failed=failed,
            )
        )
    return buckets


def _event_timeseries(
    *,
    engine: Engine,
    since: datetime,
    window: MetricsWindow,
    workload: Literal["chat", "embed"],
) -> list[MetricsTimeseriesBucket]:
    if window == "1h":
        sql = """
            SELECT date_trunc('minute', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE outcome = 'success')::int AS succeeded,
                   COUNT(*) FILTER (WHERE outcome = 'failure')::int AS failed
            FROM operation_metrics
            WHERE created_at >= :since AND workload = :workload
            GROUP BY 1 ORDER BY 1
            """
    elif window == "24h":
        sql = """
            SELECT date_trunc('hour', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE outcome = 'success')::int AS succeeded,
                   COUNT(*) FILTER (WHERE outcome = 'failure')::int AS failed
            FROM operation_metrics
            WHERE created_at >= :since AND workload = :workload
            GROUP BY 1 ORDER BY 1
            """
    else:
        sql = """
            SELECT date_trunc('day', created_at) AS bucket,
                   COUNT(*)::int AS total,
                   COUNT(*) FILTER (WHERE outcome = 'success')::int AS succeeded,
                   COUNT(*) FILTER (WHERE outcome = 'failure')::int AS failed
            FROM operation_metrics
            WHERE created_at >= :since AND workload = :workload
            GROUP BY 1 ORDER BY 1
            """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"since": since, "workload": workload}).mappings()
    buckets: list[MetricsTimeseriesBucket] = []
    for row in rows:
        mapped = mapping_row(row)
        total = row_int(mapped, "total")
        succeeded = row_int(mapped, "succeeded")
        failed = row_int(mapped, "failed")
        bucket_t = mapped["bucket"]
        if not isinstance(bucket_t, datetime):  # pragma: no cover
            continue
        buckets.append(
            MetricsTimeseriesBucket(
                t=bucket_t,
                success_rate=_success_rate(succeeded, total),
                total=total,
                failed=failed,
            )
        )
    return buckets


def fetch_metrics_timeseries(
    *,
    engine: Engine,
    metric: MetricsMetric,
    window: MetricsWindow,
) -> MetricsTimeseriesResponse:
    """Return ordered buckets for success rate or volume."""
    since = _window_start(window)

    if metric.startswith("ingest_"):
        buckets = _ingest_timeseries(engine=engine, since=since, window=window)
    elif metric.startswith("chat_"):
        buckets = _event_timeseries(engine=engine, since=since, window=window, workload="chat")
    else:
        buckets = _event_timeseries(engine=engine, since=since, window=window, workload="embed")

    return MetricsTimeseriesResponse(metric=metric, window=window, buckets=buckets)
