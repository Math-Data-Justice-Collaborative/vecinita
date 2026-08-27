#!/usr/bin/env python3
"""Generate data/fixtures/eval/baseline.json from a golden eval run (EV-028 / #181)."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from tests.helpers.eval_judge import MockEvalJudge
from tests.unit.rag.conftest import seed_eval_corpus
from vecinita_database.seeds.load import (
    _database_url,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_eval.baseline import DEFAULT_BASELINE_PATH, fixture_content_hash, write_baseline
from vecinita_eval.ci_embed import ci_eval_embed_fn
from vecinita_eval.golden import default_golden_fixture_path
from vecinita_eval.runner import run_golden_eval


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate golden eval baseline.json")
    _ = parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Output path for baseline.json",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    database_url = os.environ.get("DATABASE_URL") or _database_url()
    seed_eval_corpus(database_url=database_url)
    fixture_path = default_golden_fixture_path()
    _results, summary = run_golden_eval(
        embed_fn=ci_eval_embed_fn,
        database_url=database_url,
        judge=MockEvalJudge(),
        llm=None,
        fixture_path=fixture_path,
    )
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    _ = write_baseline(
        summary=summary,
        fixture_ref=fixture_content_hash(fixture_path),
        generated_at=generated_at,
        path=args.output,
    )
    print(f"Wrote baseline to {args.output}")
    print(
        "metrics:",
        {
            "retrieval_relevance": summary.retrieval_relevance,
            "faithfulness": summary.faithfulness,
            "answer_relevancy": summary.answer_relevancy,
            "latency_p95_ms": summary.latency_p95_ms,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
