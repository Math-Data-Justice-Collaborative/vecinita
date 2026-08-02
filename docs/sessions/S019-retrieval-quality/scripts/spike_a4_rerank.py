#!/usr/bin/env python3
"""EV-016 A4 cheap rerank ablation on staging golden (read-only).

R0 — dense top_k (baseline)
R1 — retrieve N → rescore: dense_score * (1 + title_token_overlap) with doc diversity
R2 — retrieve N → rescore by question/token overlap on title+text; keep top_k

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_a4_rerank.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import load_golden_rows
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
    / "spike-a4-rerank.json"
)

_TOKEN_RE = re.compile(r"[a-z0-9áéíóúñü]+", re.IGNORECASE)

RerankFn = Callable[[str, list[RetrievedChunk], int], list[RetrievedChunk]]


@dataclass(frozen=True, slots=True)
class RerankVariant:
    """Named cheap rerank strategy."""

    name: str
    retrieve_n: int
    rerank: RerankFn


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}


def rerank_r0(_question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Dense order unchanged."""
    return chunks[:top_k]


def rerank_r1(question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Dense score × (1 + title overlap) with soft penalty for duplicate docs."""
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


def rerank_r2(question: str, chunks: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    """Lexical overlap on title+text; break ties with dense score."""
    q_toks = _tokens(question)
    scored: list[tuple[float, float, RetrievedChunk]] = []
    for chunk in chunks:
        blob = f"{chunk.title or ''}\n{chunk.text}"
        c_toks = _tokens(blob)
        if not q_toks:
            overlap = 0.0
        else:
            overlap = len(q_toks & c_toks) / len(q_toks)
        scored.append((overlap, chunk.score, chunk))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [chunk for _, _, chunk in scored[:top_k]]


VARIANTS: tuple[RerankVariant, ...] = (
    RerankVariant("R0", retrieve_n=5, rerank=rerank_r0),
    RerankVariant("R1", retrieve_n=20, rerank=rerank_r1),
    RerankVariant("R2", retrieve_n=20, rerank=rerank_r2),
)


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


def _pack_p0(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(chunk.text for chunk in chunks)


def _pack_p1(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


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
    variant: RerankVariant,
    pack_name: str,
    pack: Callable[[list[RetrievedChunk]], str],
    rows: list[object],
    pool: dict[tuple[str, str], list[RetrievedChunk]],
    llm: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    top_k: int,
    system_prompt: str,
) -> dict[str, object]:
    from vecinita_eval.golden import GoldenRow

    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_hits = 0
    scored_n = 0
    per_row: list[dict[str, object]] = []

    for raw in rows:
        row = raw if isinstance(raw, GoldenRow) else raw  # type: ignore[assignment]
        assert isinstance(row, GoldenRow)
        t0 = time.monotonic()
        candidates = pool[(row.id, row.locale)]
        chosen = variant.rerank(row.question, candidates, top_k)
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
        "rerank": variant.name,
        "pack": pack_name,
        "retrieve_n": variant.retrieve_n,
        "top_k": top_k,
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "rows": per_row,
    }


def main() -> int:
    """Run A4 cheap rerank ablation."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL", file=sys.stderr)
        return 1

    top_k = int(os.environ.get("SPIKE_TOP_K", "5"))
    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    retrieve_n_max = max(v.retrieve_n for v in VARIANTS)
    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(f"==> A4 rerank: {len(rows)} rows, keep_k={top_k}, pool_n={retrieve_n_max}")

    embed = EmbeddingClient(timeout=120.0)
    cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in cache:
            cache[q] = _embed_with_retry(embed, q)
        return cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=retrieve_n_max,
        score_threshold=min_score,
    )

    print("==> retrieving pool once per row")
    pool: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        pool[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        print(f"    {row.id}/{row.locale}: pool={len(pool[(row.id, row.locale)])}")

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

    # Isolation cells: P0 packing. Combo cells: best packing P1 with each rerank.
    cells: list[dict[str, object]] = []
    plans: list[tuple[str, RerankVariant, str, Callable[[list[RetrievedChunk]], str]]] = []
    for variant in VARIANTS:
        plans.append((f"{variant.name}+P0", variant, "P0", _pack_p0))
    for variant in VARIANTS:
        plans.append((f"{variant.name}+P1", variant, "P1", _pack_p1))

    for label, variant, pack_name, pack in plans:
        print(f"==> {label}")
        cell = _run_cell(
            label=label,
            variant=variant,
            pack_name=pack_name,
            pack=pack,
            rows=list(rows),
            pool=pool,
            llm=llm,
            judge=judge,
            top_k=top_k,
            system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
        cells.append(cell)
        print(
            f"    retrieval={cell['retrieval_relevance']} "
            f"faith={cell['faithfulness']} "
            f"relevancy={cell['answer_relevancy']} "
            f"p95={cell['latency_p95_ms']}"
        )

    payload = {
        "fixture": str(_FIXTURE),
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "retrieve_n_max": retrieve_n_max,
        "scored_rows": len(retrieval_rows(rows)),
        "cells": cells,
    }
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
