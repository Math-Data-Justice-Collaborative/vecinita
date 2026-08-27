"""Eval run CRUD and timeseries queries (F36)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_int,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.eval_config import EvalConfig, eval_config_from_json, merge_eval_config
from vecinita_shared_schemas.internal_write import (
    EvalRunCreateRequest,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunItemDetail,
    EvalRunItemMetrics,
    EvalRunListItem,
    EvalRunListResponse,
    EvalTimeseriesPoint,
    EvalTimeseriesResponse,
)

from vecinita_internal_write_api.eval_config_presets_service import (
    EvalConfigPresetAccessError,
    get_eval_config_preset,
)
from vecinita_internal_write_api.eval_run_metrics import (
    BUILTIN_METRICS,
    custom_scores_from_json,
    eval_run_status,
    latency_ms,
    optional_datetime,
    optional_float,
    optional_uuid,
    run_mode,
    summary_from_json,
    url_list,
)
from vecinita_internal_write_api.eval_run_types import (
    CreatedEvalRun,
    EvalRunPresetAccessError,
    EvalRunPresetNotFoundError,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def resolve_eval_run_config(
    engine: Engine,
    *,
    requester_id: UUID,
    body: EvalRunCreateRequest,
) -> EvalConfig:
    """Merge defaults, optional preset, and request overrides into one snapshot."""
    base = EvalConfig()
    if body.preset_id is not None:
        try:
            preset = get_eval_config_preset(
                engine,
                preset_id=body.preset_id,
                requester_id=requester_id,
            )
        except EvalConfigPresetAccessError as exc:
            raise EvalRunPresetAccessError(str(exc)) from exc
        if preset is None:
            msg = "preset not found"
            raise EvalRunPresetNotFoundError(msg)
        base = preset.config
    resolved = merge_eval_config(base, body.config)
    return resolved.model_copy(
        update={
            "corpus_profile": body.corpus_profile,
            "rebuild_run_id": body.rebuild_run_id,
        }
    )


def create_eval_run(
    engine: Engine,
    *,
    body: EvalRunCreateRequest,
    requester_id: UUID,
) -> CreatedEvalRun:
    """Insert a pending eval run row with resolved sandbox config snapshot."""
    config_snapshot = resolve_eval_run_config(engine, requester_id=requester_id, body=body)
    run_id = uuid4()
    with engine.begin() as conn:
        _ = conn.execute(
            text(
                """
                INSERT INTO eval_runs (
                    id, status, corpus_profile, metrics_summary,
                    config_snapshot, mode, preset_id
                )
                VALUES (
                    :id, 'pending', :corpus_profile, '{}'::jsonb,
                    CAST(:config_snapshot AS jsonb), :mode, :preset_id
                )
                """
            ),
            {
                "id": run_id,
                "corpus_profile": config_snapshot.corpus_profile,
                "config_snapshot": json.dumps(config_snapshot.model_dump(mode="json")),
                "mode": body.mode,
                "preset_id": body.preset_id,
            },
        )
        created_at = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT created_at FROM eval_runs WHERE id = :id"),
                {"id": run_id},
            )
        )
    if not isinstance(created_at, datetime):
        created_at = datetime.now(UTC)
    response = EvalRunCreateResponse(run_id=run_id, status="pending", created_at=created_at)
    return CreatedEvalRun(
        response=response,
        corpus_profile=config_snapshot.corpus_profile,
        mode=body.mode,
        question=body.question,
        config_snapshot=config_snapshot,
    )


def soft_delete_eval_run(engine: Engine, *, run_id: UUID) -> bool:
    """Stamp ``deleted_at`` on an eval run; return False if missing or already deleted."""
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE eval_runs
                SET deleted_at = now()
                WHERE id = :id AND deleted_at IS NULL
                """
            ),
            {"id": run_id},
        )
    return int(result.rowcount or 0) > 0


def list_eval_runs(
    engine: Engine,
    *,
    page: int,
    page_size: int,
) -> EvalRunListResponse:
    """Return paginated eval run history (excludes soft-deleted rows)."""
    offset = (page - 1) * page_size
    with engine.connect() as conn:
        total = scalar_int(
            sqlalchemy_scalar_one(
                conn.execute(text("SELECT COUNT(*) FROM eval_runs WHERE deleted_at IS NULL"))
            )
        )
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, status, started_at, completed_at, metrics_summary, error_message
                    FROM eval_runs
                    WHERE deleted_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {"limit": page_size, "offset": offset},
            )
            .mappings()
            .all()
        )
    return EvalRunListResponse(
        items=[
            EvalRunListItem(
                run_id=row_uuid(mapping_row(row), "id"),
                status=eval_run_status(row_str(mapping_row(row), "status")),
                started_at=optional_datetime(mapping_row(row).get("started_at")),
                completed_at=optional_datetime(mapping_row(row).get("completed_at")),
                metrics_summary=summary_from_json(mapping_row(row).get("metrics_summary")),
                error_message=row_str_optional(mapping_row(row), "error_message"),
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total_count=total,
    )


def get_eval_run(engine: Engine, *, run_id: UUID) -> EvalRunDetailResponse | None:
    """Return one eval run with per-question drill-down."""
    with engine.connect() as conn:
        run_row = (
            conn.execute(
                text(
                    """
                    SELECT id, status, metrics_summary, error_message,
                           config_snapshot, mode, preset_id
                    FROM eval_runs
                    WHERE id = :id AND deleted_at IS NULL
                    """
                ),
                {"id": run_id},
            )
            .mappings()
            .first()
        )
        if run_row is None:
            return None
        run = mapping_row(run_row)
        item_rows = (
            conn.execute(
                text(
                    """
                    SELECT case_id, locale, question, expected_doc_url,
                           retrieved_urls, answer, metrics, latency_ms
                    FROM eval_run_items
                    WHERE run_id = :run_id
                    ORDER BY case_id, locale
                    """
                ),
                {"run_id": run_id},
            )
            .mappings()
            .all()
        )
    items: list[EvalRunItemDetail] = []
    for raw_item in item_rows:
        item = mapping_row(raw_item)
        metrics_raw = item.get("metrics")
        metrics_obj: dict[str, object] = (
            cast("dict[str, object]", metrics_raw) if isinstance(metrics_raw, dict) else {}
        )
        items.append(
            EvalRunItemDetail(
                case_id=row_str(item, "case_id"),
                locale=row_str(item, "locale"),
                question=row_str(item, "question"),
                expected_doc_url=row_str_optional(item, "expected_doc_url"),
                retrieved_urls=url_list(item.get("retrieved_urls")),
                answer=row_str_optional(item, "answer"),
                metrics=EvalRunItemMetrics(
                    retrieval_pass=bool(metrics_obj.get("retrieval_pass")),
                    faithfulness=optional_float(metrics_obj.get("faithfulness")),
                    answer_relevancy=optional_float(metrics_obj.get("answer_relevancy")),
                    latency_ms=latency_ms(dict(item), metrics_obj),
                    custom_scores=custom_scores_from_json(metrics_obj.get("custom_scores")),
                ),
            )
        )
    return EvalRunDetailResponse(
        run_id=row_uuid(run, "id"),
        status=eval_run_status(row_str(run, "status")),
        mode=run_mode(run.get("mode")),
        preset_id=optional_uuid(run.get("preset_id")),
        config_snapshot=eval_config_from_json(run.get("config_snapshot")),
        metrics_summary=summary_from_json(run.get("metrics_summary")),
        items=items,
        error_message=row_str_optional(run, "error_message"),
    )


def get_eval_timeseries(engine: Engine, *, limit: int = 100) -> EvalTimeseriesResponse:
    """Return completed eval runs for dashboard time-series charts."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, completed_at, metrics_summary
                    FROM eval_runs
                    WHERE status = 'completed' AND completed_at IS NOT NULL
                    ORDER BY completed_at DESC
                    LIMIT :limit
                    """
                ),
                {"limit": limit},
            )
            .mappings()
            .all()
        )
    points: list[EvalTimeseriesPoint] = []
    custom_slugs: set[str] = set()
    for raw in rows:
        row = mapping_row(raw)
        completed = row.get("completed_at")
        if not isinstance(completed, datetime):
            continue
        summary = summary_from_json(row.get("metrics_summary"))
        if summary.custom_scores:
            custom_slugs.update(summary.custom_scores)
        points.append(
            EvalTimeseriesPoint(
                run_id=row_uuid(row, "id"),
                completed_at=completed,
                metrics_summary=summary,
            )
        )
    points.reverse()
    available = list(BUILTIN_METRICS) + sorted(custom_slugs)
    return EvalTimeseriesResponse(points=points, available_metrics=available)
