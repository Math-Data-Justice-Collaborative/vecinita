"""Eval run persistence and background execution (F36, ADR-033; EV-009 T68.6)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_embedding_client.client import EmbeddingClient
from vecinita_eval.criteria import EvalCriterionDef
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import (
    ModalHttpLLM,
    eval_runtime_for_config,
    judge_llm_from_config,
    synthesis_llm_from_config,
)
from vecinita_eval.runner import EvalSummary, RowResult, run_adhoc_eval, run_golden_eval
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
    scalar_int,
    sqlalchemy_scalar_one,
)
from vecinita_shared_schemas.eval_config import EvalConfig, EvalRunMode, merge_eval_config
from vecinita_shared_schemas.internal_write import (
    EvalMetricsSummary,
    EvalRunCreateRequest,
    EvalRunCreateResponse,
    EvalRunDetailResponse,
    EvalRunItemDetail,
    EvalRunItemMetrics,
    EvalRunListItem,
    EvalRunListResponse,
    EvalRunStatus,
    EvalTimeseriesPoint,
    EvalTimeseriesResponse,
)

from vecinita_internal_write_api.eval_config_presets_service import (
    EvalConfigPresetAccessError,
    get_eval_config_preset,
)
from vecinita_internal_write_api.eval_criteria_service import list_enabled_criteria

if TYPE_CHECKING:
    from collections.abc import Callable

    from llama_index.core.llms import LLM
    from sqlalchemy.engine import Engine
    from vecinita_eval.judges import JudgeClient


class EvalRunNotFoundError(LookupError):
    """Eval run id does not exist."""


@dataclass(frozen=True)
class LoadedEvalRun:
    """Eval run row fields needed by the background runner."""

    config_snapshot: EvalConfig
    mode: EvalRunMode
    corpus_profile: str


class EvalRunPresetNotFoundError(LookupError):
    """Referenced preset_id does not exist."""


class EvalRunPresetAccessError(PermissionError):
    """Caller cannot read the referenced preset."""


@dataclass(frozen=True)
class CreatedEvalRun:
    """Persisted eval run metadata for scheduling and API responses."""

    response: EvalRunCreateResponse
    corpus_profile: str
    mode: EvalRunMode
    question: str | None
    config_snapshot: EvalConfig


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


def _summary_to_json(summary: EvalSummary) -> dict[str, float | int | None | dict[str, float]]:
    payload: dict[str, float | int | None | dict[str, float]] = {
        "retrieval_relevance": summary.retrieval_relevance,
        "faithfulness": summary.faithfulness,
        "answer_relevancy": summary.answer_relevancy,
        "latency_p95_ms": summary.latency_p95_ms,
    }
    if summary.custom_scores:
        payload["custom_scores"] = summary.custom_scores
    return payload


def _summary_from_json(payload: object) -> EvalMetricsSummary:
    if not isinstance(payload, dict):
        return EvalMetricsSummary()
    data = cast("dict[str, object]", payload)
    return EvalMetricsSummary(
        retrieval_relevance=_optional_float(data.get("retrieval_relevance")),
        faithfulness=_optional_float(data.get("faithfulness")),
        answer_relevancy=_optional_float(data.get("answer_relevancy")),
        latency_p95_ms=_optional_int(data.get("latency_p95_ms")),
        custom_scores=_custom_scores_from_json(data.get("custom_scores")),
    )


def _custom_scores_from_json(value: object) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    raw = cast("dict[str, object]", value)
    scores: dict[str, float] = {}
    for key, entry in raw.items():
        score = _optional_float(entry)
        if score is not None:
            scores[key] = score
    return scores or None


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
    return resolved.model_copy(update={"corpus_profile": body.corpus_profile})


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
        conn.execute(
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


def _default_embed_fn(question: str) -> list[float]:
    client = EmbeddingClient()
    return client.embed(question)


def _config_from_json(value: object) -> EvalConfig:
    if isinstance(value, str):
        return EvalConfig.model_validate_json(value)
    if isinstance(value, dict):
        return EvalConfig.model_validate(value)
    return EvalConfig()


def _run_mode(value: object) -> EvalRunMode:
    if value in {"golden", "adhoc"}:
        return cast("EvalRunMode", value)
    return "golden"


def _optional_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def _load_eval_run(engine: Engine, *, run_id: UUID) -> LoadedEvalRun:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT config_snapshot, mode, corpus_profile
                    FROM eval_runs
                    WHERE id = :id
                    """
                ),
                {"id": run_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        msg = f"eval run not found: {run_id}"
        raise EvalRunNotFoundError(msg)
    loaded = mapping_row(row)
    return LoadedEvalRun(
        config_snapshot=_config_from_json(loaded.get("config_snapshot")),
        mode=_run_mode(loaded.get("mode")),
        corpus_profile=row_str(loaded, "corpus_profile"),
    )


def _criteria_for_config(
    engine: Engine,
    config: EvalConfig,
) -> list[EvalCriterionDef]:
    enabled = list_enabled_criteria(engine)
    if config.criteria_ids:
        allowed = set(config.criteria_ids)
        selected = [item for item in enabled if item.criterion_id in allowed]
    else:
        selected = enabled
    return [EvalCriterionDef(slug=item.slug, rubric=item.rubric) for item in selected]


def _resolve_eval_runtime(
    config: EvalConfig,
    judge: JudgeClient | None,
    llm: LLM | None,
) -> tuple[JudgeClient | None, LLM | None]:
    if llm is not None and isinstance(llm, ModalHttpLLM):
        synthesis = synthesis_llm_from_config(llm, config)
        if judge is not None and isinstance(judge, LlamaIndexJudgeClient):
            judge_llm = judge_llm_from_config(llm, config)
            return LlamaIndexJudgeClient(llm=judge_llm), synthesis
        return judge, synthesis
    if judge is None and llm is None:
        return eval_runtime_for_config(config)
    return judge, llm


def _require_adhoc_question(question: str | None) -> str:
    if not question:
        msg = "question is required for adhoc eval runs"
        raise ValueError(msg)
    return question


def execute_eval_run(  # noqa: PLR0913
    engine: Engine,
    *,
    run_id: UUID,
    question: str | None = None,
    embed_fn: Callable[[str], list[float]] | None = None,
    judge: JudgeClient | None = None,
    llm: LLM | None = None,
) -> None:
    """Run golden or ad-hoc eval using persisted sandbox config snapshot."""
    loaded = _load_eval_run(engine, run_id=run_id)
    config = loaded.config_snapshot
    embed = embed_fn or _default_embed_fn
    resolved_judge, resolved_llm = _resolve_eval_runtime(config, judge, llm)
    database_url = _database_url()
    criteria = _criteria_for_config(engine, config)
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
        if loaded.mode == "adhoc":
            adhoc_question = _require_adhoc_question(question)
            results, summary = run_adhoc_eval(
                embed_fn=embed,
                database_url=database_url,
                question=adhoc_question,
                judge=resolved_judge,
                llm=resolved_llm,
                criteria=criteria,
                config=config,
            )
        else:
            fixture_path = _fixture_path() if loaded.corpus_profile == "fixture" else None
            results, summary = run_golden_eval(
                embed_fn=embed,
                database_url=database_url,
                judge=resolved_judge,
                llm=resolved_llm,
                fixture_path=fixture_path,
                criteria=criteria,
                config=config,
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
                            **(
                                {"custom_scores": result.metrics.custom_scores}
                                if result.metrics.custom_scores
                                else {}
                            ),
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
                    SELECT id, status, started_at, completed_at, metrics_summary, error_message
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
                error_message=row_str_optional(mapping_row(row), "error_message"),
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total_count=total,
    )


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    return None


def get_eval_run(engine: Engine, *, run_id: UUID) -> EvalRunDetailResponse | None:
    """Return one eval run with per-question drill-down."""
    with engine.connect() as conn:
        run_row = (
            conn.execute(
                text(
                    """
                    SELECT id, status, metrics_summary, error_message,
                           config_snapshot, mode, preset_id
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
            cast("dict[str, object]", metrics_raw) if isinstance(metrics_raw, dict) else {}
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
                    custom_scores=_custom_scores_from_json(metrics_obj.get("custom_scores")),
                ),
            )
        )
    return EvalRunDetailResponse(
        run_id=row_uuid(run, "id"),
        status=_status(row_str(run, "status")),
        mode=_run_mode(run.get("mode")),
        preset_id=_optional_uuid(run.get("preset_id")),
        config_snapshot=_config_from_json(run.get("config_snapshot")),
        metrics_summary=_summary_from_json(run.get("metrics_summary")),
        items=items,
        error_message=row_str_optional(run, "error_message"),
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


_BUILTIN_METRICS: tuple[str, ...] = (
    "retrieval_relevance",
    "faithfulness",
    "answer_relevancy",
    "latency_p95_ms",
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
                    ORDER BY completed_at ASC
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
        summary = _summary_from_json(row.get("metrics_summary"))
        if summary.custom_scores:
            custom_slugs.update(summary.custom_scores)
        points.append(
            EvalTimeseriesPoint(
                run_id=row_uuid(row, "id"),
                completed_at=completed,
                metrics_summary=summary,
            )
        )
    available = list(_BUILTIN_METRICS) + sorted(custom_slugs)
    return EvalTimeseriesResponse(points=points, available_metrics=available)
