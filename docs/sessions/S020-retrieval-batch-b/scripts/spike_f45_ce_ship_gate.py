#!/usr/bin/env python3
"""EV-017 F45 CE ship-gate spike on Modal T4 (RD-204, S020-D5/D11/D15).

Retrieve N=20 dense (L_none), score with ``BAAI/bge-reranker-v2-m3`` on ephemeral
Modal T4, keep top_k=5, pack P1, synthesize via **prod** ChatRAG LLM URL
(``VECINITA_MODAL_LLM_URL`` — never playground). Compare CE vs dense baseline
against TC-184 floors (relevancy ≥ 0.28, faith ≥ 0.91).

Usage (repo root)::

  set -a && source .env && set +a
  export PATH="$PWD/.venv/bin:$PATH"
  uv run python docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.retrieval import retrieval_rows, score_retrieval_row
from vecinita_eval.sandbox import truncate_synthesis_context
from vecinita_llm_client import LlmClient
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_SYSTEM_PROMPT

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE = _REPO / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_OUT = (
    _REPO
    / "docs"
    / "sessions"
    / "S020-retrieval-batch-b"
    / "reports"
    / "spike-f45-ce-ship-gate.json"
)

PASSAGE_CHAR_CAP = 1500
SHIP_RELEVANCY_FLOOR = 0.28
SHIP_FAITH_FLOOR = 0.91
_PROD_LLM_MODEL = "qwen2.5:1.5b-instruct"


def passage_for_ce(title: str | None, text: str) -> str:
    """Build a CE pair passage: optional title + body capped at ``PASSAGE_CHAR_CAP``."""
    body = text.strip()
    if len(body) > PASSAGE_CHAR_CAP:
        body = body[:PASSAGE_CHAR_CAP]
    cleaned_title = (title or "").strip()
    if cleaned_title:
        return f"{cleaned_title}\n{body}"
    return body


def ship_gate_pass(*, relevancy: float | None, faith: float | None) -> bool:
    """Return True when CE cell clears TC-184 / AC-BB9 floors."""
    if relevancy is None or faith is None:
        return False
    return relevancy >= SHIP_RELEVANCY_FLOOR and faith >= SHIP_FAITH_FLOOR


def _passage_from_chunk(chunk: RetrievedChunk) -> str:
    return passage_for_ce(chunk.title, chunk.text)


def _pack_p1(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _keep_dense(chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    return chunks[:top_k]


def _rerank_from_scores(
    chunks: list[RetrievedChunk],
    scores: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    ranked = sorted(zip(scores, chunks, strict=True), key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]


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


def _synthesize(*, question: str, context: str, llm: ModalHttpLLM, system_prompt: str) -> str:
    capped = truncate_synthesis_context(context)
    prompt = (
        f"{system_prompt.strip()}\n\nContext:\n{capped}\n\n"
        f"Question: {question.strip()}\n\nAnswer:"
    )
    response = llm.complete(prompt)
    return str(getattr(response, "text", response))


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _as_optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    msg = f"expected float metric, got {type(value).__name__}"
    raise TypeError(msg)


def _run_cell(  # noqa: PLR0913
    *,
    label: str,
    rerank_name: str,
    choose: Callable[[GoldenRow, list[RetrievedChunk]], list[RetrievedChunk]],
    rows: list[GoldenRow],
    pool: dict[tuple[str, str], list[RetrievedChunk]],
    llm: ModalHttpLLM,
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
        candidates = pool[(row.id, row.locale)]
        chosen = choose(row, candidates)
        urls = [c.url for c in chosen if c.url]
        context = _pack_p1(chosen)
        answer = _synthesize(
            question=row.question,
            context=context,
            llm=llm,
            system_prompt=system_prompt,
        )
        retrieval_pass = score_retrieval_row(row, urls)
        if row.retrieval_expectation in {"hit", "any_of"}:
            scored_n += 1
            retrieval_hits += int(retrieval_pass)

        faith: float | None = None
        relevancy: float | None = None
        if answer.strip():
            if chosen and row.retrieval_expectation not in {"abstain", "empty"}:
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
                "urls": urls,
                "n_chosen": len(chosen),
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    return {
        "label": label,
        "rerank": rerank_name,
        "pack": "P1",
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "rows": per_row,
    }


def main() -> int:
    """Run F45 CE ship-gate spike via ephemeral Modal T4."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_LLM_PLAYGROUND_URL") and not os.environ.get(
        "VECINITA_MODAL_LLM_URL"
    ):
        print(
            "ERROR: ChatRAG/spike must use VECINITA_MODAL_LLM_URL (prod), not playground alone",
            file=sys.stderr,
        )
        return 1
    llm_url = os.environ.get("VECINITA_MODAL_LLM_URL", "").strip()
    if not llm_url:
        print("ERROR: set VECINITA_MODAL_LLM_URL (prod ChatRAG LLM)", file=sys.stderr)
        return 1
    if "llm-playground" in llm_url:
        print(
            "ERROR: VECINITA_MODAL_LLM_URL must not point at playground (S020-D15)",
            file=sys.stderr,
        )
        return 1

    # Lazy Modal import so unit tests can load helpers without Modal SDK side effects.
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from spike_f45_ce_modal import CE_MODEL, CrossEncoderRerank
    from spike_f45_ce_modal import app as _spike_app

    top_k = int(os.environ.get("SPIKE_TOP_K", "5"))
    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    retrieve_n = int(os.environ.get("SPIKE_RETRIEVE_N", "20"))
    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(
        f"==> F45 CE ship-gate: {len(rows)} rows, keep_k={top_k}, pool_n={retrieve_n}, "
        f"model={CE_MODEL}"
    )

    embed = EmbeddingClient(timeout=120.0)
    cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in cache:
            cache[q] = _embed_with_retry(embed, q)
        return cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=retrieve_n,
        score_threshold=min_score,
    )

    print("==> retrieving pool once per row (L_none)")
    pool: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        pool[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        print(f"    {row.id}/{row.locale}: pool={len(pool[(row.id, row.locale)])}")

    print("==> Modal CE scoring (T4, ephemeral)")
    ce_t0 = time.monotonic()
    batches: list[dict[str, object]] = []
    batch_keys: list[tuple[str, str]] = []
    for row in rows:
        key = (row.id, row.locale)
        chunks = pool[key]
        batches.append(
            {
                "query": row.question,
                "passages": [_passage_from_chunk(c) for c in chunks],
            }
        )
        batch_keys.append(key)

    with _spike_app.run():
        scorer = CrossEncoderRerank()
        all_scores = scorer.score_batches.remote(batches)

    ce_ms = int((time.monotonic() - ce_t0) * 1000)
    ce_scores: dict[tuple[str, str], list[float]] = dict(zip(batch_keys, all_scores, strict=True))
    print(f"==> CE scoring done in {ce_ms}ms for {len(batches)} batches")

    llm_client = LlmClient(
        llm_url,
        timeout=900.0,
        model_id=_PROD_LLM_MODEL,
        require_proxy_key=True,
    )
    warm_modal_llm(llm_client)
    llm = ModalHttpLLM(
        client=llm_client,
        max_tokens=128,
        temperature=0.0,
        model_id=_PROD_LLM_MODEL,
    )
    judge = LlamaIndexJudgeClient(llm)

    def choose_dense(_row: GoldenRow, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return _keep_dense(chunks, top_k)

    def choose_ce(row: GoldenRow, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        scores = ce_scores[(row.id, row.locale)]
        return _rerank_from_scores(chunks, scores, top_k)

    cells: list[dict[str, object]] = []
    for label, rerank_name, choose in (
        ("R0+P1", "R0", choose_dense),
        ("CE+P1", "CE", choose_ce),
    ):
        print(f"==> {label}")
        cell = _run_cell(
            label=label,
            rerank_name=rerank_name,
            choose=choose,
            rows=list(rows),
            pool=pool,
            llm=llm,
            judge=judge,
            system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
        cells.append(cell)
        print(
            f"    retrieval={cell['retrieval_relevance']} "
            f"faith={cell['faithfulness']} "
            f"relevancy={cell['answer_relevancy']} "
            f"p95={cell['latency_p95_ms']}"
        )

    ce_cell = next(c for c in cells if c["label"] == "CE+P1")
    ce_relevancy = _as_optional_float(ce_cell["answer_relevancy"])
    ce_faith = _as_optional_float(ce_cell["faithfulness"])
    gate_ok = ship_gate_pass(relevancy=ce_relevancy, faith=ce_faith)

    ce_hours = ce_ms / 3_600_000
    est_t4_usd = round(ce_hours * 0.59, 4)

    payload = {
        "fixture": str(_FIXTURE),
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "retrieve_n": retrieve_n,
        "ce_model": CE_MODEL,
        "ce_gpu": "T4",
        "ce_app": "vecinita-spike-f45-rerank",
        "ce_passage_char_cap": PASSAGE_CHAR_CAP,
        "ce_scoring_wall_ms": ce_ms,
        "ce_modal_cost_estimate_usd": est_t4_usd,
        "llm_url_kind": "prod",
        "ship_relevancy_floor": SHIP_RELEVANCY_FLOOR,
        "ship_faith_floor": SHIP_FAITH_FLOOR,
        "ship_gate_pass": gate_ok,
        "scored_rows": len(retrieval_rows(rows)),
        "cells": cells,
    }
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    print(f"==> ship_gate_pass={gate_ok} (need relevancy≥{SHIP_RELEVANCY_FLOOR}, faith≥{SHIP_FAITH_FLOOR})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
