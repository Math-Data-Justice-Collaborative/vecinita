#!/usr/bin/env python3
"""T76.7 / AC-E32: live smoke — golden eval uses qwen3:8b on vecinita-llm only.

Read-only against staging Postgres (no corpus reset). Requires:
  VECINITA_MODAL_LLM_URL, VECINITA_MODAL_EMBED_URL, DATABASE_URL
Must NOT set VECINITA_MODAL_OLLAMA_URL (ADR-037).

Usage:
  set -a && source prod.env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python scripts/smoke/t76_7_golden_eval_qwen3_llm.py
  uv run python scripts/smoke/t76_7_golden_eval_qwen3_llm.py --limit 1
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import load_golden_rows
from vecinita_eval.modal_llm import eval_runtime_for_config
from vecinita_eval.runner import _evaluate_rows  # pyright: ignore[reportPrivateUsage]
from vecinita_llm_client import LlmClient
from vecinita_shared_schemas.eval_config import EvalConfig

_MODEL_ID = os.environ.get("VECINITA_SMOKE_MODEL_ID", "qwen3:8b")
_ENV_LLM = "VECINITA_MODAL_LLM_URL"
_ENV_OLLAMA = "VECINITA_MODAL_OLLAMA_URL"
_ENV_EMBED = "VECINITA_MODAL_EMBED_URL"
_ENV_DB = "DATABASE_URL"


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"ERROR: {name} is required", file=sys.stderr)
        sys.exit(1)
    return value


def _modal_llm_smoke() -> None:
    """Warm and generate with sandbox model_id on vecinita-llm."""
    _require_env(_ENV_LLM)
    if os.environ.get(_ENV_OLLAMA):
        print(f"ERROR: {_ENV_OLLAMA} must be unset (ADR-037)", file=sys.stderr)
        sys.exit(1)

    client = LlmClient(model_id=_MODEL_ID, timeout=900.0)
    try:
        print(f"==> POST /generate model_id={_MODEL_ID!r} (loads model if needed)")
        t1 = time.perf_counter()
        text = client.generate(
            "Reply with exactly: smoke-ok",
            max_tokens=16,
            temperature=0.0,
            model_id=_MODEL_ID,
        )
        elapsed = time.perf_counter() - t1
        print(f"    generate ({elapsed:.1f}s): {text!r}")
        if not text.strip():
            print("ERROR: empty generate response", file=sys.stderr)
            sys.exit(1)
    finally:
        client.close()


def _golden_row_smoke(*, limit: int) -> None:
    """Run golden-set rows through sandbox RAG with qwen3:8b on vecinita-llm."""
    database_url = _require_env(_ENV_DB)
    _require_env(_ENV_EMBED)
    if os.environ.get(_ENV_OLLAMA):
        print(f"ERROR: {_ENV_OLLAMA} must be unset (ADR-037)", file=sys.stderr)
        sys.exit(1)

    config = EvalConfig(
        model_id=_MODEL_ID,
        max_tokens=64,
        temperature=0.2,
        top_k=5,
    )
    judge, llm = eval_runtime_for_config(config)
    if judge is None or llm is None:
        print(f"ERROR: eval_runtime_for_config failed — check {_ENV_LLM}", file=sys.stderr)
        sys.exit(1)

    rows = load_golden_rows()[:limit]
    print(f"==> Golden eval smoke: {len(rows)} row(s), model_id={_MODEL_ID!r}")

    embed_client = EmbeddingClient()

    def embed_fn(question: str) -> list[float]:
        return embed_client.embed(question)

    try:
        t0 = time.perf_counter()
        results, summary = _evaluate_rows(
            rows=rows,
            embed_fn=embed_fn,
            database_url=database_url,
            judge=judge,
            groundedness=None,
            llm=llm,
            retriever_top_k=config.top_k,
            score_threshold=config.min_retrieval_score,
            criteria=[],
            system_prompt=config.system_prompt,
            adhoc=False,
        )
        elapsed = time.perf_counter() - t0
    finally:
        embed_client.close()

    failed = [r for r in results if not r.answer.strip()]
    if failed:
        print(f"ERROR: {len(failed)} row(s) produced empty answers", file=sys.stderr)
        sys.exit(1)

    print(f"    completed in {elapsed:.1f}s")
    print(f"    retrieval_relevance={summary.retrieval_relevance:.2f}")
    print(f"    latency_p95_ms={summary.latency_p95_ms}")
    for row in results:
        print(
            f"    - {row.row.id}: answer_len={len(row.answer)} latency={row.metrics.latency_ms}ms"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=2,
        help="Golden rows to evaluate (default 2 for smoke speed)",
    )
    parser.add_argument(
        "--skip-golden",
        action="store_true",
        help="Only run Modal warm/generate smoke",
    )
    args = parser.parse_args()

    _modal_llm_smoke()
    if not args.skip_golden:
        _golden_row_smoke(limit=max(1, args.limit))
    print("OK: T76.7 smoke passed")


if __name__ == "__main__":
    main()
