#!/usr/bin/env python3
r"""Load experiment JSONs from a folder and aggregate metrics by config fields.

Pipeline step: load -> aggregate (for agent / canvas consumption).

Examples:
--------
Average retrieval + faithfulness by model and prompt::

  uv run python scripts/eval_aggregate_experiments.py \
    --results-dir data/eval-experiments \
    --group-by model_id,prompt_name,temperature \
    --metrics retrieval_relevance,faithfulness,wall_time_s,spawn_wall_time_s \
    --out data/eval-experiments/aggregate.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from vecinita_eval.experiments import aggregate_experiments, load_experiments
from vecinita_eval.sweep import parse_csv_strs

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_RESULTS = _REPO_ROOT / "data" / "eval-experiments"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate golden-eval experiment JSON files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    _ = parser.add_argument(
        "--results-dir",
        type=Path,
        default=_DEFAULT_RESULTS,
        help="Folder of experiment_*.json files",
    )
    _ = parser.add_argument(
        "--group-by",
        default="model_id,prompt_name,temperature,top_k",
        help="Comma-separated grouping fields from cell config",
    )
    _ = parser.add_argument(
        "--metrics",
        default="retrieval_relevance,faithfulness,answer_relevancy,wall_time_s,latency_p95_ms,spawn_wall_time_s",
        help="Comma-separated metrics to average",
    )
    _ = parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write aggregate JSON (default: <results-dir>/aggregate.json)",
    )
    args = parser.parse_args(argv)

    experiments = load_experiments(args.results_dir)
    if not experiments:
        print(f"ERROR: no experiment JSON files in {args.results_dir}", file=sys.stderr)
        return 1

    aggregate = aggregate_experiments(
        experiments,
        group_by=parse_csv_strs(args.group_by),
        metrics=parse_csv_strs(args.metrics),
    )
    out = args.out or (args.results_dir / "aggregate.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, indent=2, ensure_ascii=False))
    groups = aggregate["groups"]
    group_count = len(cast("list[object]", groups)) if isinstance(groups, list) else 0
    print(
        f"OK: aggregated {aggregate['experiment_count']} experiment(s) " +
        f"into {group_count} group(s) -> {out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
