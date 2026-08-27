#!/usr/bin/env python3
r"""Sample CLI: sweep models + EvalConfig params over the golden set (+ extras).

Spawns (warms) each model, records spawn + eval wall times, scores each config,
optionally repeats runs and averages, and writes a full config snapshot
(model parameters, model type / HF repo, system prompt, rubric rules).

Requires (staging-style env, read-only corpus):
  VECINITA_MODAL_LLM_URL, VECINITA_MODAL_EMBED_URL, DATABASE_URL
  VECINITA_MODAL_PROXY_KEY (when generate/warm require it)
Must NOT set VECINITA_MODAL_OLLAMA_URL (ADR-037).

Examples:
--------
Quick dry-run of the grid (no LLM calls)::

  uv run python scripts/eval_sweep_golden_models.py \
    --models qwen2.5:1.5b-instruct,qwen3:8b \
    --temperatures 0.0,0.2 \
    --top-k 3,5 \
    --dry-run

Live multi-run sweep with rules + system prompt::

  set -a && source prod.env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python scripts/eval_sweep_golden_models.py \
    --models qwen2.5:1.5b-instruct,qwen3:8b \
    --temperatures 0.0,0.2 \
    --runs 3 \
    --system-prompt-file data/fixtures/eval/sample_system_prompt.txt \
    --rules-file data/fixtures/eval/sample_rules.json \
    --extra-fixture data/fixtures/eval/similar_examples.json \
    --limit 4 \
    --out /tmp/eval-sweep.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import httpx
from vecinita_embedding_client import EmbeddingClient, EmbeddingClientError
from vecinita_eval.criteria import EvalCriterionDef
from vecinita_eval.experiments import new_experiment_id, write_experiment
from vecinita_eval.golden import load_golden_rows
from vecinita_eval.modal_llm import eval_runtime_for_config, warm_modal_llm
from vecinita_eval.runner import (
    _evaluate_rows as evaluate_rows,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_eval.sweep import (
    PromptVariant,
    SweepRunRecord,
    build_config_grid,
    filter_golden_rows,
    load_prompt_variants,
    parse_csv_floats,
    parse_csv_ints,
    parse_csv_strs,
    resolve_model_type,
    summarize_cell,
)
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.eval_config import (
    DEFAULT_EVAL_MODEL_ID,
    DEFAULT_EVAL_SYSTEM_PROMPT,
    EvalConfig,
)
from vecinita_shared_schemas.json_types import as_json_object

if TYPE_CHECKING:
    from collections.abc import Callable

    from vecinita_eval.golden import GoldenRow
    from vecinita_eval.runner import EvalSummary, RowResult
    from vecinita_eval.sweep import SweepCell
    from vecinita_shared_schemas.json_types import JsonObject

    EmbedFn = Callable[[str], list[float]]

_ENV_LLM = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA = "VECINITA_MODAL_OLLAMA_URL"
_ENV_EMBED = "VECINITA_MODAL_EMBED_URL"
_ENV_DB = "DATABASE_URL"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_GOLDEN = _REPO_ROOT / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_DEFAULT_RESULTS = _REPO_ROOT / "data" / "eval-experiments"
_EVAL_LLM_TIMEOUT_S = 900.0


@dataclass(frozen=True, slots=True)
class _RowSelection:
    """Fixture paths and filters for loading golden (+ optional extra) rows."""

    fixture: Path
    extra_fixture: Path | None
    ids: set[str] | None
    domains: set[str] | None
    locales: set[str] | None
    limit: int | None


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"ERROR: {name} is required", file=sys.stderr)
        sys.exit(1)
    return value


def _assert_no_ollama_url() -> None:
    if os.environ.get(_ENV_OLLAMA):
        print(f"ERROR: {_ENV_OLLAMA} must be unset (ADR-037)", file=sys.stderr)
        sys.exit(1)


def _load_rules(path: Path | None) -> list[EvalCriterionDef]:
    if path is None:
        return []
    loaded = cast("object", json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(loaded, list):
        print(f"ERROR: rules file must be a JSON array: {path}", file=sys.stderr)
        sys.exit(1)
    criteria: list[EvalCriterionDef] = []
    for item in cast("list[object]", loaded):
        obj = as_json_object(item)
        slug = obj.get("slug")
        rubric = obj.get("rubric")
        if not isinstance(slug, str) or not slug.strip():
            print(f"ERROR: rule missing slug in {path}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(rubric, str) or not rubric.strip():
            print(f"ERROR: rule {slug!r} missing rubric in {path}", file=sys.stderr)
            sys.exit(1)
        criteria.append(EvalCriterionDef(slug=slug.strip(), rubric=rubric.strip()))
    return criteria


def _load_prompt_variants_from_args(args: argparse.Namespace) -> list[PromptVariant]:
    prompt_files = [Path(p) for p in parse_csv_strs(args.system_prompt_files)]
    if args.system_prompt_file is not None:
        prompt_files.append(args.system_prompt_file)
    try:
        return load_prompt_variants(
            paths=prompt_files,
            prompt_dir=args.system_prompt_dir,
            inline=args.system_prompt,
            default_text=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def _print_comparison_table(payloads: list[JsonObject]) -> None:
    headers = (
        "label",
        "spawn_s",
        "avg_wall",
        "retrieval",
        "faith",
        "relevancy",
        "p95_ms",
        "runs",
    )
    print("\n==> Comparison (averages)")
    print(
        f"{headers[0]:<48} {headers[1]:>8} {headers[2]:>8} {headers[3]:>9} " +
        f"{headers[4]:>7} {headers[5]:>9} {headers[6]:>7} {headers[7]:>5}"
    )
    for item in payloads:
        averages = item.get("averages")
        if not isinstance(averages, dict):
            continue
        config = item.get("config")
        label = str(item.get("label", ""))
        spawn = item.get("spawn_wall_time_s")
        retrieval = averages.get("retrieval_relevance")
        faith = averages.get("faithfulness")
        relevancy = averages.get("answer_relevancy")
        p95 = averages.get("latency_p95_ms")
        wall = averages.get("wall_time_s")
        run_count = averages.get("run_count")
        spawn_s = f"{spawn:.1f}" if isinstance(spawn, float) else "-"
        wall_s = f"{wall:.1f}" if isinstance(wall, float) else "-"
        retrieval_s = f"{retrieval:.2f}" if isinstance(retrieval, float) else "-"
        faith_s = f"{faith:.2f}" if isinstance(faith, float) else "-"
        relevancy_s = f"{relevancy:.2f}" if isinstance(relevancy, float) else "-"
        p95_s = f"{p95:.0f}" if isinstance(p95, float) else "-"
        runs_s = f"{run_count}" if isinstance(run_count, int) else "-"
        print(
            f"{label:<48} {spawn_s:>8} {wall_s:>8} {retrieval_s:>9} " +
            f"{faith_s:>7} {relevancy_s:>9} {p95_s:>7} {runs_s:>5}"
        )
        if isinstance(config, dict):
            model_type = config.get("model_type")
            if isinstance(model_type, str):
                print(f"    model_type={model_type}")


def _load_rows(selection: _RowSelection) -> list[GoldenRow]:
    rows = load_golden_rows(fixture_path=selection.fixture)
    if selection.extra_fixture is not None:
        rows = [*rows, *load_golden_rows(fixture_path=selection.extra_fixture)]
    return filter_golden_rows(
        rows,
        ids=selection.ids,
        domains=selection.domains,
        locales=selection.locales,
        limit=selection.limit,
    )


def _spawn_model(model_id: str) -> float:
    """Warm/spawn the Modal engine for ``model_id``; return wall seconds."""
    print(f"==> Spawning model_id={model_id!r} type={resolve_model_type(model_id)!r}")
    client = LlmClient(model_id=model_id, timeout=_EVAL_LLM_TIMEOUT_S)
    try:
        t0 = time.perf_counter()
        warm_modal_llm(client)
        # Touch generate so first-token load is included in spawn wall time.
        _ = client.generate(
            "Reply with exactly: ready",
            max_tokens=8,
            temperature=0.0,
            model_id=model_id,
        )
        return time.perf_counter() - t0
    finally:
        client.close()


@dataclass(frozen=True, slots=True)
class _EvalPassRequest:
    """Inputs for one eval pass of a sweep cell."""

    cell: SweepCell
    rows: list[GoldenRow]
    database_url: str
    embed_fn: EmbedFn
    skip_judge: bool
    criteria: list[EvalCriterionDef]


def _run_once(
    request: _EvalPassRequest,
) -> tuple[list[RowResult], EvalSummary, float]:
    judge, llm = eval_runtime_for_config(request.cell.config)
    if llm is None:
        print(f"ERROR: eval_runtime_for_config failed - check {_ENV_LLM}", file=sys.stderr)
        sys.exit(1)
    judge_client = None if request.skip_judge else judge

    t0 = time.perf_counter()
    results, summary = evaluate_rows(
        rows=request.rows,
        embed_fn=request.embed_fn,
        database_url=request.database_url,
        judge=judge_client,
        groundedness=None,
        llm=llm,
        retriever_top_k=request.cell.config.top_k,
        score_threshold=request.cell.config.min_retrieval_score,
        criteria=request.criteria,
        system_prompt=request.cell.config.system_prompt,
        adhoc=False,
    )
    return results, summary, time.perf_counter() - t0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sweep models/parameters over the golden eval set.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    _ = parser.add_argument(
        "--models",
        default=DEFAULT_EVAL_MODEL_ID,
        help=f"Comma-separated model_id tags (default: {DEFAULT_EVAL_MODEL_ID})",
    )
    _ = parser.add_argument(
        "--temperatures",
        default="0.2",
        help="Comma-separated synthesis temperatures (default: 0.2)",
    )
    _ = parser.add_argument(
        "--top-k",
        default="5",
        dest="top_k",
        help="Comma-separated retriever top_k values (default: 5)",
    )
    _ = parser.add_argument(
        "--max-tokens",
        default="256",
        dest="max_tokens",
        help="Comma-separated max_tokens values (default: 256)",
    )
    _ = parser.add_argument(
        "--min-retrieval-score",
        default="0.2",
        dest="min_retrieval_score",
        help="Comma-separated min_retrieval_score values (default: 0.2)",
    )
    _ = parser.add_argument(
        "--judge-temperature",
        default="0.2",
        dest="judge_temperature",
        help="Comma-separated judge temperatures (default: 0.2)",
    )
    _ = parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Repeat each config this many times and average scores/wall times",
    )
    _ = parser.add_argument(
        "--system-prompt",
        default=None,
        help="Inline sandbox system prompt (single prompt variant named 'inline')",
    )
    _ = parser.add_argument(
        "--system-prompt-file",
        type=Path,
        default=None,
        help="Single system prompt file (stem becomes prompt_name)",
    )
    _ = parser.add_argument(
        "--system-prompt-files",
        default="",
        help="Comma-separated system prompt files (multi-prompt sweep dimension)",
    )
    _ = parser.add_argument(
        "--system-prompt-dir",
        type=Path,
        default=None,
        help="Directory of *.txt prompts (each file is a prompt variant)",
    )
    _ = parser.add_argument(
        "--rules-file",
        type=Path,
        default=None,
        help="JSON array of {slug, rubric} custom judge criteria",
    )
    _ = parser.add_argument(
        "--fixture",
        type=Path,
        default=_DEFAULT_GOLDEN,
        help="Golden qa_pairs.json path",
    )
    _ = parser.add_argument(
        "--extra-fixture",
        type=Path,
        default=None,
        help="Optional extra/similar examples JSON (same schema as golden)",
    )
    _ = parser.add_argument("--ids", default="", help="Comma-separated case ids to include")
    _ = parser.add_argument(
        "--domains",
        default="",
        help="Comma-separated domains: community,housing,legal,edge",
    )
    _ = parser.add_argument("--locales", default="", help="Comma-separated locales: en,es")
    _ = parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max rows after filters (0 = all)",
    )
    _ = parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip faithfulness/relevancy/rubric judges (faster retrieval-only compare)",
    )
    _ = parser.add_argument(
        "--skip-spawn",
        action="store_true",
        help="Skip explicit warm/spawn timing (still uses eval_runtime warm)",
    )
    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the config grid and selected rows without calling Modal/DB",
    )
    _ = parser.add_argument(
        "--results-dir",
        type=Path,
        default=_DEFAULT_RESULTS,
        help="Directory to drop experiment JSON files (default: data/eval-experiments)",
    )
    _ = parser.add_argument(
        "--experiment-id",
        default="",
        help="Optional experiment id slug (default: auto timestamp id)",
    )
    _ = parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Also write a copy of the experiment JSON to this path",
    )
    _ = parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write JSON under --results-dir",
    )
    args = parser.parse_args(argv)

    if args.runs < 1:
        print("ERROR: --runs must be >= 1", file=sys.stderr)
        return 1

    prompts = _load_prompt_variants_from_args(args)
    criteria = _load_rules(args.rules_file)
    base = EvalConfig()

    cells = build_config_grid(
        models=parse_csv_strs(args.models),
        temperatures=parse_csv_floats(args.temperatures),
        top_ks=parse_csv_ints(args.top_k),
        max_tokens_list=parse_csv_ints(args.max_tokens),
        min_retrieval_scores=parse_csv_floats(args.min_retrieval_score),
        judge_temperatures=parse_csv_floats(args.judge_temperature),
        prompts=prompts,
        base=base,
    )
    id_set = set(parse_csv_strs(args.ids)) or None
    domain_set = set(parse_csv_strs(args.domains)) or None
    locale_set = set(parse_csv_strs(args.locales)) or None
    limit = args.limit if args.limit > 0 else None

    rows = _load_rows(
        _RowSelection(
            fixture=args.fixture,
            extra_fixture=args.extra_fixture,
            ids=id_set,
            domains=domain_set,
            locales=locale_set,
            limit=limit,
        )
    )
    if not rows:
        print("ERROR: no golden rows matched filters", file=sys.stderr)
        return 1

    print(f"==> Sweep: {len(cells)} config(s) x {len(rows)} row(s) x {args.runs} run(s)")
    print(f"==> Prompts: {len(prompts)}")
    for prompt in prompts:
        print(f"    - {prompt.name} ({len(prompt.text)} chars)")
    print(f"==> Rules: {len(criteria)} criterion(s)")
    for cell in cells:
        print(f"    - {cell.label} type={resolve_model_type(cell.config.model_id)!r}")
    print("==> Rows:")
    for row in rows:
        print(f"    - {row.id} [{row.locale}/{row.domain}] {row.question[:60]!r}")

    if args.dry_run:
        print("OK: dry-run only (no eval executed)")
        return 0

    _assert_no_ollama_url()
    database_url = _require_env(_ENV_DB)
    _ = _require_env(_ENV_LLM)
    _ = _require_env(_ENV_EMBED)

    # Modal cold-start / InternalFailure can exceed the default 30s read timeout.
    embed_client = EmbeddingClient(timeout=120.0)

    def embed_fn(question: str) -> list[float]:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                return embed_client.embed(question)
            except (EmbeddingClientError, httpx.HTTPError, httpx.TimeoutException) as exc:
                last_exc = exc
                time.sleep(2.0 * (attempt + 1))
        if last_exc is None:
            msg = "embed retries exhausted without an exception"
            raise RuntimeError(msg)
        raise last_exc

    spawn_times: dict[str, float] = {}
    payloads: list[JsonObject] = []
    try:
        for index, cell in enumerate(cells, start=1):
            model_id = cell.config.model_id
            if model_id not in spawn_times:
                if args.skip_spawn:
                    spawn_times[model_id] = 0.0
                else:
                    spawn_times[model_id] = _spawn_model(model_id)
                    print(f"    spawn_wall_time_s={spawn_times[model_id]:.1f}")

            print(f"\n==> [{index}/{len(cells)}] {cell.label}")
            run_records: list[SweepRunRecord] = []
            last_results: list[RowResult] = []
            for run_index in range(1, args.runs + 1):
                print(f"    run {run_index}/{args.runs} ...", flush=True)
                results, summary, elapsed = _run_once(
                    _EvalPassRequest(
                        cell=cell,
                        rows=rows,
                        database_url=database_url,
                        embed_fn=embed_fn,
                        skip_judge=args.skip_judge,
                        criteria=[] if args.skip_judge else criteria,
                    )
                )
                last_results = results
                run_records.append(
                    SweepRunRecord(
                        run_index=run_index,
                        wall_time_s=elapsed,
                        retrieval_relevance=summary.retrieval_relevance,
                        faithfulness=summary.faithfulness,
                        answer_relevancy=summary.answer_relevancy,
                        latency_p95_ms=float(summary.latency_p95_ms),
                        custom_scores=summary.custom_scores,
                    )
                )
                print(
                    f"      wall={elapsed:.1f}s " +
                    f"retrieval={summary.retrieval_relevance:.2f} " +
                    f"faith={summary.faithfulness} " +
                    f"relevancy={summary.answer_relevancy} " +
                    f"p95={summary.latency_p95_ms}ms"
                )

            payload = summarize_cell(
                cell=cell,
                spawn_wall_time_s=spawn_times[model_id],
                runs=run_records,
                last_run_rows=last_results,
                criteria=criteria,
            )
            payloads.append(payload)
            averages = as_json_object(payload["averages"])
            print(
                f"    avg wall={averages['wall_time_s']}s " +
                f"retrieval={averages['retrieval_relevance']} " +
                f"faith={averages['faithfulness']} " +
                f"relevancy={averages['answer_relevancy']}"
            )
    finally:
        embed_client.close()

    _print_comparison_table(payloads)

    experiment_payload: JsonObject = {
        "runs_per_config": args.runs,
        "row_count": len(rows),
        "prompts": [{"name": p.name, "system_prompt": p.text} for p in prompts],
        "rules": [{"slug": c.slug, "rubric": c.rubric} for c in criteria],
        "cells": payloads,
    }
    experiment_id = args.experiment_id.strip() or new_experiment_id(slug="golden-sweep")

    if not args.no_save:
        saved = write_experiment(
            results_dir=args.results_dir,
            experiment_id=experiment_id,
            payload=experiment_payload,
        )
        print(f"\nWrote experiment JSON: {saved}")

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(
                {"experiment_id": experiment_id, **experiment_payload}, indent=2, ensure_ascii=False
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {args.out}")

    print("\nOK: sweep complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
