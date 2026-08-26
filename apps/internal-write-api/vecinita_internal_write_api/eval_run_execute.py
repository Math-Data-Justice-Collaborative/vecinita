"""Eval run background execution (F36 golden + adhoc)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

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
from vecinita_shared_schemas.db_mapping import mapping_row, row_str
from vecinita_shared_schemas.eval_config import EvalConfig, eval_config_from_json

from vecinita_internal_write_api.eval_criteria_service import list_enabled_criteria
from vecinita_internal_write_api.eval_run_metrics import run_mode, summary_to_json
from vecinita_internal_write_api.eval_run_types import EvalRunNotFoundError, LoadedEvalRun

if TYPE_CHECKING:
    from collections.abc import Callable

    from llama_index.core.llms import LLM
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


def _default_fixture_relpath(*, corpus_profile: str) -> str:
    """Map corpus_profile to the golden JSON used for Admin / promote-path eval."""
    if corpus_profile == "staging":
        return "data/fixtures/eval/qa_pairs_staging.json"
    return "data/fixtures/eval/qa_pairs.json"


def _fixture_path(*, corpus_profile: str = "fixture") -> Path:
    """Resolve golden fixture path (ISS-008: staging → qa_pairs_staging.json)."""
    configured = os.environ.get(
        "VECINITA_EVAL_FIXTURE_PATH",
        _default_fixture_relpath(corpus_profile=corpus_profile),
    )
    path = Path(configured)
    if path.is_file():
        return path
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / configured


def _default_embed_fn(question: str) -> list[float]:
    client = EmbeddingClient()
    return client.embed(question)


def _load_eval_run(engine: Engine, *, run_id: UUID) -> LoadedEvalRun:
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT config_snapshot, mode, corpus_profile
                    FROM eval_runs
                    WHERE id = :id AND deleted_at IS NULL
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
        config_snapshot=eval_config_from_json(loaded.get("config_snapshot")),
        mode=run_mode(loaded.get("mode")),
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
            fixture_path = _fixture_path(corpus_profile=loaded.corpus_profile)
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
                {"id": run_id, "metrics": json.dumps(summary_to_json(summary))},
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
