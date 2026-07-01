"""Eval run persistence and background execution (F36, ADR-033)."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_embedding_client.client import EmbeddingClient
from vecinita_eval.runner import EvalSummary, RowResult, run_golden_eval
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_int,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.internal_write import (
    EvalMetricsSummary,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunItemDetail,
    EvalRunItemMetrics,
    EvalRunListItem,
    EvalRunListResponse,
    EvalRunStatus,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL is required for eval runs"
        raise RuntimeError(msg)
    return _normalize_database_url(url)


def _fixture_path() -> Path:
    configured = os.environ.get(
        "VECINITA_EVAL_FIXTURE_PATH",
        "data/fixtures/eval/qa_pairs.json",
    )
    path = Path(configured)
    if path.is_file():
        return path
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / configured


def _summary_to_json(summary: EvalSummary) -> dict[str, float | int | None]:
    return {
        "retrieval_relevance": summary.retrieval_relevance,
        "faithfulness": summary.faithfulness,
        "answer_relevancy": summary.answer_relevancy,
        "latency_p95_ms": summary.latency_p95_ms,
    }


def _summary_from_json(payload: object) -> EvalMetricsSummary:
    if not isinstance(payload, dict):
        return EvalMetricsSummary()
    data = cast("dict[str, object]", payload)
    return EvalMetricsSummary(
        retrieval_relevance=_optional_float(data.get("retrieval_relevance")),
        faithfulness=_optional_float(data.get("faithfulness")),
        answer_relevancy=_optional_float(data.get("answer_relevancy")),
        latency_p95_ms=_optional_int(data.get("latency_p95_ms")),
    )


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def create_eval_run(
    engine: Engine,
    *,
    corpus_profile: str,
) -> EvalRunCreateResponse:
    """Insert a pending eval run row."""
    run_id = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_runs (id, status, corpus_profile, metrics_summary)
                VALUES (:id, 'pending', :corpus_profile, '{}'::jsonb)
                """
            ),
            {"id": run_id, "corpus_profile": corpus_profile},
        )
        created_at = sqlalchemy_scalar_one(
            conn.execute(
                text("SELECT created_at FROM eval_runs WHERE id = :id"),
                {"id": run_id},
            )
        )
    if not isinstance(created_at, datetime):
        created_at = datetime.now(UTC)
    return EvalRunCreateResponse(run_id=run_id, status="pending", created_at=created_at)


def _default_embed_fn(question: str) -> list[float]:
    client = EmbeddingClient()
    return client.embed(question)


def _optional_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def execute_eval_run(
    engine: Engine,
    *,
    run_id: UUID,
    corpus_profile: str,
    embed_fn: Callable[[str], list[float]] | None = None,
    judge: JudgeClient | None = None,
) -> None:
    """Run golden eval and persist per-row results."""
    embed = embed_fn or _default_embed_fn
    database_url = _database_url()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE eval_runs
                    SET status = 'running', started_at = now()
                    WHERE id = :id
                    """
                ),
                {"id": run_id},
            )
        fixture_path = _fixture_path() if corpus_profile == "fixture" else None
        results, summary = run_golden_eval(
            embed_fn=embed,
            database_url=database_url,
            judge=judge,
            llm=None,
            fixture_path=fixture_path,
        )
        _persist_results(engine, run_id=run_id, results=results, summary=summary)
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE eval_runs
                    SET status = 'completed',
                        completed_at = now(),
                        metrics_summary = CAST(:metrics AS jsonb)
                    WHERE id = :id
                    """
                ),
                {"id": run_id, "metrics": json.dumps(_summary_to_json(summary))},
            )
    except Exception as exc:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE eval_runs
                    SET status = 'failed',
                        completed_at = now(),
                        error_message = :error
                    WHERE id = :id
                    """
                ),
                {"id": run_id, "error": str(exc)},
            )
        raise


def _persist_results(
    engine: Engine,
    *,
    run_id: UUID,
    results: list[RowResult],
    summary: EvalSummary,
) -> None:
    _ = summary
    with engine.begin() as conn:
        for result in results:
            conn.execute(
                text(
                    """
                    INSERT INTO eval_run_items (
                        run_id, case_id, locale, question, expected_doc_url,
                        retrieved_urls, answer, metrics, latency_ms
                    )
                    VALUES (
                        :run_id, :case_id, :locale, :question, :expected_doc_url,
                        CAST(:retrieved_urls AS jsonb), :answer,
                        CAST(:metrics AS jsonb), :latency_ms
                    )
                    """
                ),
                {
                    "run_id": run_id,
                    "case_id": result.row.id,
                    "locale": result.row.locale,
                    "question": result.row.question,
                    "expected_doc_url": result.row.expected_doc_url,
                    "retrieved_urls": json.dumps(result.retrieved_urls),
                    "answer": result.answer,
                    "metrics": json.dumps(
                        {
                            "retrieval_pass": result.metrics.retrieval_pass,
                            "faithfulness": result.metrics.faithfulness,
                            "answer_relevancy": result.metrics.answer_relevancy,
                            "latency_ms": result.metrics.latency_ms,
                        }
                    ),
                    "latency_ms": result.metrics.latency_ms,
                },
            )


def list_eval_runs(
    engine: Engine,
    *,
    page: int,
    page_size: int,
) -> EvalRunListResponse:
    """Return paginated eval run history."""
    offset = (page - 1) * page_size
    with engine.connect() as conn:
        total = scalar_int(
            sqlalchemy_scalar_one(conn.execute(text("SELECT COUNT(*) FROM eval_runs")))
        )
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, status, started_at, completed_at, metrics_summary
                    FROM eval_runs
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
                status=_status(row_str(mapping_row(row), "status")),
                started_at=_optional_datetime(mapping_row(row).get("started_at")),
                completed_at=_optional_datetime(mapping_row(row).get("completed_at")),
                metrics_summary=_summary_from_json(mapping_row(row).get("metrics_summary")),
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
                    SELECT id, status, metrics_summary
                    FROM eval_runs WHERE id = :id
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
            cast("dict[str, object]", metrics_raw)
            if isinstance(metrics_raw, dict)
            else {}
        )
        items.append(
            EvalRunItemDetail(
                case_id=row_str(item, "case_id"),
                locale=row_str(item, "locale"),
                question=row_str(item, "question"),
                expected_doc_url=row_str_optional(item, "expected_doc_url"),
                retrieved_urls=_url_list(item.get("retrieved_urls")),
                answer=row_str_optional(item, "answer"),
                metrics=EvalRunItemMetrics(
                    retrieval_pass=bool(metrics_obj.get("retrieval_pass")),
                    faithfulness=_optional_float(metrics_obj.get("faithfulness")),
                    answer_relevancy=_optional_float(metrics_obj.get("answer_relevancy")),
                    latency_ms=_latency_ms(dict(item), metrics_obj),
                ),
            )
        )
    return EvalRunDetailResponse(
        run_id=row_uuid(run, "id"),
        status=_status(row_str(run, "status")),
        metrics_summary=_summary_from_json(run.get("metrics_summary")),
        items=items,
    )


def _status(value: str) -> EvalRunStatus:
    if value in {"pending", "running", "completed", "failed"}:
        return cast("EvalRunStatus", value)
    msg = f"invalid eval run status: {value!r}"
    raise ValueError(msg)


def _url_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    entries = cast("list[object]", value)
    return [str(item) for item in entries]


def _latency_ms(
    item: dict[str, object],
    metrics_obj: dict[str, object],
) -> int:
    latency = metrics_obj.get("latency_ms")
    if isinstance(latency, int):
        return latency
    if isinstance(latency, float):
        return int(latency)
    raw = item.get("latency_ms")
    if isinstance(raw, int):
        return raw
    return 0
