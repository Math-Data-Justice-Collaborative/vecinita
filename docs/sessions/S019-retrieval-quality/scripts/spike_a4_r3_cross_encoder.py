#!/usr/bin/env python3
"""EV-016 A4-R3 cross-encoder rerank on Modal (S019-D8 / S019-D14).

Retrieve N=20 dense (no language filter, matching prior A4), score with
``BAAI/bge-reranker-base`` on Modal T4, keep top_k=5. Compare vs R0 and prior
best R1 under P0/P1 packing.

Usage (repo root)::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  export PATH="$PWD/.venv/bin:$PATH"
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_a4_r3_cross_encoder.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from spike_a4_r3_ce_modal import CE_MODEL, CrossEncoderRerank, app as _spike_app
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
    / "S019-retrieval-quality"
    / "reports"
    / "spike-a4-r3-cross-encoder.json"
)

_PASSAGE_CHAR_CAP = 1500
_TOKEN_RE = re.compile(r"[a-z0-9áéíóúñü]+", re.IGNORECASE)

def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}


def _passage_for_ce(chunk: RetrievedChunk) -> str:
    title = (chunk.title or "").strip()
    body = chunk.text.strip()
    if len(body) > _PASSAGE_CHAR_CAP:
        body = body[:_PASSAGE_CHAR_CAP]
    if title:
        return f"{title}\n{body}"
    return body


def rerank_r0(_question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    return chunks[:top_k]


def rerank_r1(question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Prior A4 heuristic (for same-run comparison)."""
    q_toks = _tokens(question)
    seen_docs: set[object] = set()
    scored: list[tuple[float, RetrievedChunk]] = []
    for chunk in chunks:
        title = chunk.title or ""
        overlap = len(q_toks & _tokens(title)) / max(len(q_toks), 1)
        diversity = 0.85 if chunk.document_id in seen_docs else 1.0
        seen_docs.add(chunk.document_id)
        scored.append((chunk.score * (1.0 + overlap) * diversity, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def rerank_r3_from_scores(
    chunks: list[RetrievedChunk],
    scores: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    ranked = sorted(zip(scores, chunks, strict=True), key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]


def _pack_p0(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(chunk.text for chunk in chunks)


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


def _run_cell(  # noqa: PLR0913
    *,
    label: str,
    rerank_name: str,
    choose: Callable[[GoldenRow, list[RetrievedChunk]], list[RetrievedChunk]],
    pack_name: str,
    pack: Callable[[list[RetrievedChunk]], str],
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
        context = pack(chosen)
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
        "pack": pack_name,
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "rows": per_row,
    }


def main() -> int:
    """Run A4-R3 cross-encoder ablation via Modal."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL", file=sys.stderr)
        return 1

    top_k = int(os.environ.get("SPIKE_TOP_K", "5"))
    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    retrieve_n = int(os.environ.get("SPIKE_RETRIEVE_N", "20"))
    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(
        f"==> A4-R3 CE: {len(rows)} rows, keep_k={top_k}, pool_n={retrieve_n}, "
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

    print("==> Modal CE scoring (T4)")
    ce_t0 = time.monotonic()
    batches: list[dict[str, object]] = []
    batch_keys: list[tuple[str, str]] = []
    for row in rows:
        key = (row.id, row.locale)
        chunks = pool[key]
        batches.append(
            {
                "query": row.question,
                "passages": [_passage_for_ce(c) for c in chunks],
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
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id="qwen2.5:1.5b-instruct",
        require_proxy_key=True,
    )
    warm_modal_llm(llm_client)
    llm = ModalHttpLLM(
        client=llm_client,
        max_tokens=128,
        temperature=0.0,
        model_id="qwen2.5:1.5b-instruct",
    )
    judge = LlamaIndexJudgeClient(llm)

    def choose_r0(row: GoldenRow, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return rerank_r0(row.question, chunks, top_k)

    def choose_r1(row: GoldenRow, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return rerank_r1(row.question, chunks, top_k)

    def choose_r3(row: GoldenRow, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        scores = ce_scores[(row.id, row.locale)]
        return rerank_r3_from_scores(chunks, scores, top_k)

    plans: list[
        tuple[str, str, Callable[[GoldenRow, list[RetrievedChunk]], list[RetrievedChunk]], str, Callable[[list[RetrievedChunk]], str]]
    ] = [
        ("R0+P0", "R0", choose_r0, "P0", _pack_p0),
        ("R1+P0", "R1", choose_r1, "P0", _pack_p0),
        ("R3+P0", "R3", choose_r3, "P0", _pack_p0),
        ("R0+P1", "R0", choose_r0, "P1", _pack_p1),
        ("R1+P1", "R1", choose_r1, "P1", _pack_p1),
        ("R3+P1", "R3", choose_r3, "P1", _pack_p1),
    ]

    cells: list[dict[str, object]] = []
    for label, rerank_name, choose, pack_name, pack in plans:
        print(f"==> {label}")
        cell = _run_cell(
            label=label,
            rerank_name=rerank_name,
            choose=choose,
            pack_name=pack_name,
            pack=pack,
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

    # Rough Modal cost note (T4 ~$0.59/hr on-demand; wall clock for CE phase only)
    ce_hours = ce_ms / 3_600_000
    est_t4_usd = round(ce_hours * 0.59, 4)

    payload = {
        "fixture": str(_FIXTURE),
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "retrieve_n": retrieve_n,
        "ce_model": CE_MODEL,
        "ce_gpu": "T4",
        "ce_passage_char_cap": _PASSAGE_CHAR_CAP,
        "ce_scoring_wall_ms": ce_ms,
        "ce_modal_cost_estimate_usd": est_t4_usd,
        "ce_cost_note": (
            f"Wall-clock CE phase {ce_ms}ms on Modal T4; rough on-demand "
            f"estimate ${est_t4_usd} (excludes cold start billed elsewhere; "
            "S019-D8). Not a billing invoice."
        ),
        "scored_rows": len(retrieval_rows(rows)),
        "cells": cells,
    }
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    print(f"==> CE cost note: {payload['ce_cost_note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
