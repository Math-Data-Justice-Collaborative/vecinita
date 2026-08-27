"""Cartesian grid helpers for golden-set model/parameter sweeps (F36 sample tooling)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_MODEL_ID, EvalConfig
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from vecinita_shared_schemas.json_types import JsonObject

    from vecinita_eval.criteria import EvalCriterionDef
    from vecinita_eval.golden import GoldenRow
    from vecinita_eval.runner import RowResult


@dataclass(frozen=True, slots=True)
class SweepCell:
    """One point in the model/parameter grid."""

    label: str
    config: EvalConfig
    prompt_name: str = "default"


@dataclass(frozen=True, slots=True)
class SweepRunRecord:
    """Scores and wall time for one eval pass of a sweep cell."""

    run_index: int
    wall_time_s: float
    retrieval_relevance: float
    faithfulness: float | None
    answer_relevancy: float | None
    latency_p95_ms: float
    custom_scores: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class PromptVariant:
    """Named system prompt used as a sweep dimension."""

    name: str
    text: str


def parse_csv_strs(raw: str) -> list[str]:
    """Split a comma-separated string into stripped non-empty tokens."""
    if not raw.strip():
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_csv_floats(raw: str) -> list[float]:
    """Parse comma-separated floats."""
    return [float(token) for token in parse_csv_strs(raw)]


def parse_csv_ints(raw: str) -> list[int]:
    """Parse comma-separated integers."""
    return [int(token) for token in parse_csv_strs(raw)]


def load_prompt_variants(
    *,
    paths: Sequence[Path] | None = None,
    prompt_dir: Path | None = None,
    inline: str | None = None,
    default_text: str,
) -> list[PromptVariant]:
    """Load named system prompts from files, a directory, or a single inline string."""
    variants: list[PromptVariant] = []
    if inline and inline.strip():
        variants.append(PromptVariant(name="inline", text=inline.strip()))
    for path in paths or ():
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            msg = f"empty system prompt file: {path}"
            raise ValueError(msg)
        variants.append(PromptVariant(name=path.stem, text=text))
    if prompt_dir is not None:
        if not prompt_dir.is_dir():
            msg = f"prompt dir not found: {prompt_dir}"
            raise ValueError(msg)
        for path in sorted(prompt_dir.glob("*.txt")):
            text = path.read_text(encoding="utf-8").strip()
            if text:
                variants.append(PromptVariant(name=path.stem, text=text))
    if not variants:
        variants.append(PromptVariant(name="default", text=default_text))
    return variants


def build_config_grid(  # noqa: PLR0913
    *,
    models: Sequence[str],
    temperatures: Sequence[float],
    top_ks: Sequence[int],
    max_tokens_list: Sequence[int],
    min_retrieval_scores: Sequence[float],
    judge_temperatures: Sequence[float],
    prompts: Sequence[PromptVariant],
    base: EvalConfig,
) -> list[SweepCell]:
    """Build the cartesian product of sandbox overrides onto ``base``."""
    model_ids = list(models) or [base.model_id or DEFAULT_EVAL_MODEL_ID]
    prompt_list = list(prompts) or [PromptVariant(name="default", text=base.system_prompt)]
    cells: list[SweepCell] = []
    for prompt in prompt_list:
        for model_id in model_ids:
            for temperature in temperatures:
                for top_k in top_ks:
                    for max_tokens in max_tokens_list:
                        for min_score in min_retrieval_scores:
                            for judge_temperature in judge_temperatures:
                                config = base.model_copy(
                                    update={
                                        "model_id": model_id,
                                        "temperature": temperature,
                                        "top_k": top_k,
                                        "max_tokens": max_tokens,
                                        "min_retrieval_score": min_score,
                                        "judge_temperature": judge_temperature,
                                        "system_prompt": prompt.text,
                                    }
                                )
                                label = (
                                    f"{model_id}|p={prompt.name}|t={temperature}|k={top_k}|" +
                                    f"mt={max_tokens}|mrs={min_score}|jt={judge_temperature}"
                                )
                                cells.append(
                                    SweepCell(
                                        label=label,
                                        config=config,
                                        prompt_name=prompt.name,
                                    )
                                )
    return cells


def filter_golden_rows(
    rows: Sequence[GoldenRow],
    *,
    ids: set[str] | None,
    domains: set[str] | None,
    locales: set[str] | None,
    limit: int | None,
) -> list[GoldenRow]:
    """Filter golden rows by id/domain/locale and optionally cap count."""
    filtered: list[GoldenRow] = []
    for row in rows:
        if ids is not None and row.id not in ids:
            continue
        if domains is not None and row.domain not in domains:
            continue
        if locales is not None and row.locale not in locales:
            continue
        filtered.append(row)
    if limit is not None and limit > 0:
        return filtered[:limit]
    return filtered


def resolve_model_type(model_id: str) -> str:
    """Map a playground ``model_id`` to its HuggingFace repo id (or ``unknown``)."""
    try:
        return resolve_hf_repo(model_id)
    except ValueError:
        return "unknown"


def config_snapshot(
    config: EvalConfig,
    *,
    criteria: Sequence[EvalCriterionDef] | None = None,
    prompt_name: str = "default",
) -> JsonObject:
    """Serialize sandbox parameters, model type, system prompt, and rubric rules."""
    rules: list[JsonObject] = [
        {"slug": criterion.slug, "rubric": criterion.rubric} for criterion in criteria or ()
    ]
    return {
        "model_id": config.model_id,
        "model_type": resolve_model_type(config.model_id),
        "prompt_name": prompt_name,
        "temperature": config.temperature,
        "top_k": config.top_k,
        "max_tokens": config.max_tokens,
        "min_retrieval_score": config.min_retrieval_score,
        "judge_temperature": config.judge_temperature,
        "corpus_profile": config.corpus_profile,
        "system_prompt": config.system_prompt,
        "criteria_ids": [str(cid) for cid in config.criteria_ids],
        "rules": rules,
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _mean_optional(values: Sequence[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return _mean(present)


def average_run_records(runs: Sequence[SweepRunRecord]) -> JsonObject:
    """Average wall time and scores across repeated runs of one cell."""
    if not runs:
        return {
            "run_count": 0,
            "wall_time_s": 0.0,
            "retrieval_relevance": 0.0,
            "faithfulness": None,
            "answer_relevancy": None,
            "latency_p95_ms": 0.0,
            "custom_scores": {},
        }
    custom_keys = {key for run in runs if run.custom_scores for key in run.custom_scores}
    custom_avg: dict[str, float] = {}
    for key in sorted(custom_keys):
        values = [
            run.custom_scores[key]
            for run in runs
            if run.custom_scores is not None and key in run.custom_scores
        ]
        if values:
            custom_avg[key] = _mean(values)
    return {
        "run_count": len(runs),
        "wall_time_s": _mean([run.wall_time_s for run in runs]),
        "retrieval_relevance": _mean([run.retrieval_relevance for run in runs]),
        "faithfulness": _mean_optional([run.faithfulness for run in runs]),
        "answer_relevancy": _mean_optional([run.answer_relevancy for run in runs]),
        "latency_p95_ms": _mean([run.latency_p95_ms for run in runs]),
        "custom_scores": custom_avg,
    }


def summarize_cell(
    *,
    cell: SweepCell,
    spawn_wall_time_s: float,
    runs: Sequence[SweepRunRecord],
    last_run_rows: Sequence[RowResult] | None = None,
    criteria: Sequence[EvalCriterionDef] | None = None,
) -> JsonObject:
    """Serialize one sweep cell with config, spawn timing, runs, and averages."""
    row_payloads: list[JsonObject] = [
        {
            "id": result.row.id,
            "locale": result.row.locale,
            "domain": result.row.domain,
            "retrieval_pass": result.metrics.retrieval_pass,
            "faithfulness": result.metrics.faithfulness,
            "answer_relevancy": result.metrics.answer_relevancy,
            "latency_ms": result.metrics.latency_ms,
            "retrieved_urls": list(result.retrieved_urls),
            "answer": result.answer,
            "custom_scores": result.metrics.custom_scores,
        }
        for result in last_run_rows or ()
    ]
    run_payloads: list[JsonObject] = [
        {
            "run_index": run.run_index,
            "wall_time_s": run.wall_time_s,
            "retrieval_relevance": run.retrieval_relevance,
            "faithfulness": run.faithfulness,
            "answer_relevancy": run.answer_relevancy,
            "latency_p95_ms": run.latency_p95_ms,
            "custom_scores": run.custom_scores or {},
        }
        for run in runs
    ]
    return {
        "label": cell.label,
        "prompt_name": cell.prompt_name,
        "spawn_wall_time_s": spawn_wall_time_s,
        "config": config_snapshot(
            cell.config,
            criteria=criteria,
            prompt_name=cell.prompt_name,
        ),
        "runs": run_payloads,
        "averages": average_run_records(runs),
        "rows": row_payloads,
    }
