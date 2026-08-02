#!/usr/bin/env python3
"""EV-016 model sweep under fixed RAG cell (S019-D16).

Fixed factors: staging golden, L_none retrieve top_k=5, R0, P1 packing.
Synthesis: candidate ``model_id`` on playground. Judges: pinned
``qwen2.5:1.5b-instruct`` (fair cross-model compare).

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_model_sweep.py \\
    --models g9v3:3b
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.playground_setup import (
    assert_no_legacy_ollama_url,
    make_playground_client,
    resolve_playground_base_url,
)
from vecinita_eval.retrieval import retrieval_rows, score_retrieval_row
from vecinita_eval.sandbox import truncate_synthesis_context
from vecinita_eval.sweep import parse_csv_strs
from vecinita_llm_client import LlmClient
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_SYSTEM_PROMPT
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE = _REPO / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_OUT_DIR = (
    _REPO
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "reports"
    / "eval-experiments"
)
_JUDGE_MODEL = "qwen2.5:1.5b-instruct"


def _pack_p1(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _embed_with_retry(embed: EmbeddingClient, question: str) -> list[float]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            return embed.embed(question)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2**attempt)
    assert last is not None
    raise last


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _synthesize(
    *,
    question: str,
    context: str,
    llm: ModalHttpLLM,
    system_prompt: str,
) -> str:
    capped = truncate_synthesis_context(context)
    prompt = (
        f"{system_prompt.strip()}\n\nContext:\n{capped}\n\n"
        f"Question: {question.strip()}\n\nAnswer:"
    )
    response = llm.complete(prompt)
    return str(getattr(response, "text", response))


def _run_model(  # noqa: PLR0913
    *,
    model_id: str,
    rows: list[GoldenRow],
    pool: dict[tuple[str, str], list[RetrievedChunk]],
    synth: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    system_prompt: str,
) -> dict[str, object]:
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_hits = 0
    scored_n = 0
    per_row: list[dict[str, object]] = []

    for row in rows:
        t0 = time.monotonic()
        chunks = pool[(row.id, row.locale)][:5]
        urls = [c.url for c in chunks if c.url]
        context = _pack_p1(chunks)
        answer = ""
        if chunks:
            answer = _synthesize(
                question=row.question,
                context=context,
                llm=synth,
                system_prompt=system_prompt,
            )
        retrieval_pass = score_retrieval_row(row, urls)
        if row.retrieval_expectation in {"hit", "any_of"}:
            scored_n += 1
            retrieval_hits += int(retrieval_pass)

        faith: float | None = None
        relevancy: float | None = None
        if answer.strip():
            if chunks and row.retrieval_expectation not in {"abstain", "empty"}:
                faith = judge.faithfulness(
                    question=row.question,
                    answer=answer,
                    context=context,
                )
            relevancy = judge.answer_relevancy(
                question=row.question,
                answer=answer,
                context=context,
            )
        faiths.append(faith)
        relevancies.append(relevancy)
        latency_ms = int((time.monotonic() - t0) * 1000)
        latencies.append(latency_ms)
        per_row.append(
            {
                "id": row.id,
                "locale": row.locale,
                "retrieval_pass": retrieval_pass,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "latency_ms": latency_ms,
                "n_chunks": len(chunks),
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    return {
        "model_id": model_id,
        "hf_repo": resolve_hf_repo(model_id),
        "pack": "P1",
        "rerank": "R0",
        "judge_model_id": _JUDGE_MODEL,
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "rows": per_row,
    }


def main(argv: list[str] | None = None) -> int:
    """Run model sweep cells under S019-D16 fixed factors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        required=True,
        help="Comma-separated playground tags (synthesis models)",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.2)
    args = parser.parse_args(argv)

    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    assert_no_legacy_ollama_url()

    models = parse_csv_strs(args.models)
    if not models:
        print("ERROR: no models", file=sys.stderr)
        return 1
    for mid in models:
        resolve_hf_repo(mid)  # fail fast locally

    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(f"==> model sweep: {len(models)} model(s), {len(rows)} rows, P1+R0")

    embed = EmbeddingClient(timeout=120.0)
    cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in cache:
            cache[q] = _embed_with_retry(embed, q)
        return cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=args.top_k,
        score_threshold=args.min_score,
    )

    print("==> retrieve once (R0 / L_none)")
    pool: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        pool[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        print(f"    {row.id}/{row.locale}: {len(pool[(row.id, row.locale)])}")

    # Judges on prod pin (stable); synthesis on playground per model.
    judge_client = LlmClient(
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id=_JUDGE_MODEL,
        require_proxy_key=True,
    )
    warm_modal_llm(judge_client)
    judge_llm = ModalHttpLLM(
        client=judge_client,
        max_tokens=128,
        temperature=0.0,
        model_id=_JUDGE_MODEL,
    )
    judge = LlamaIndexJudgeClient(judge_llm)

    playground_url = resolve_playground_base_url()
    print(f"==> playground={playground_url}")

    cells: list[dict[str, object]] = []
    for model_id in models:
        print(f"==> synth model={model_id} hf={resolve_hf_repo(model_id)}")
        t0 = time.monotonic()
        try:
            client = make_playground_client(model_id=model_id, timeout=900.0)
            warm_modal_llm(client)
            synth = ModalHttpLLM(
                client=client,
                max_tokens=128,
                temperature=0.0,
                model_id=model_id,
            )
            cell = _run_model(
                model_id=model_id,
                rows=list(rows),
                pool=pool,
                synth=synth,
                judge=judge,
                system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
            )
            cell["status"] = "complete"
            cell["wall_ms"] = int((time.monotonic() - t0) * 1000)
        except Exception as exc:  # noqa: BLE001 — per-model fail/skip (S019-D17)
            cell = {
                "model_id": model_id,
                "hf_repo": resolve_hf_repo(model_id),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "wall_ms": int((time.monotonic() - t0) * 1000),
            }
            print(f"    FAILED: {cell['error']}")
        else:
            print(
                f"    retrieval={cell.get('retrieval_relevance')} "
                f"faith={cell.get('faithfulness')} "
                f"relevancy={cell.get('answer_relevancy')} "
                f"p95={cell.get('latency_p95_ms')}"
            )
        cells.append(cell)

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = _OUT_DIR / f"{stamp}_model-sweep.json"
    payload = {
        "fixture": str(_FIXTURE),
        "fixed_cell": {
            "pack": "P1",
            "rerank": "R0",
            "top_k": args.top_k,
            "min_retrieval_score": args.min_score,
            "language_filter": None,
            "judge_model_id": _JUDGE_MODEL,
            "decision": "S019-D16",
        },
        "playground_url": playground_url,
        "scored_rows": len(retrieval_rows(rows)),
        "cells": cells,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {out}")
    return 0 if all(c.get("status") == "complete" for c in cells) else 2


if __name__ == "__main__":
    raise SystemExit(main())
