#!/usr/bin/env python3
"""EV-016 A3 soft language filter ablation on staging golden (read-only).

L0 — strict same-language (prod ChatRAG path)
L1 — same-lang first; if empty → retry without language filter
L2 — same-lang first; if empty → retry opposite language only

Packing fixed to P0 (concat) so language is isolated from A2.

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_a3_language.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.retrieval import retrieval_rows, score_retrieval_row
from vecinita_eval.sandbox import truncate_synthesis_context
from vecinita_llm_client import LlmClient
from vecinita_rag.language import detect_query_language
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
    / "spike-a3-language.json"
)


@dataclass(frozen=True, slots=True)
class LangRetrieveResult:
    """Chunks plus whether a fallback pass ran."""

    chunks: list[RetrievedChunk]
    detected_language: str
    fallback_triggered: bool
    first_pass_empty: bool
    strategy: str


RetrieveFn = Callable[[str, CorpusPgvectorRetriever, int, float], LangRetrieveResult]


def _opposite(language: str) -> str:
    return "es" if language == "en" else "en"


def retrieve_l0(
    question: str,
    retriever: CorpusPgvectorRetriever,
    top_k: int,
    min_score: float,
) -> LangRetrieveResult:
    """Strict same-language filter (prod)."""
    lang = detect_query_language(question)
    chunks = retriever.retrieve_chunks(
        question,
        language=lang,
        top_k=top_k,
        score_threshold=min_score,
    )
    return LangRetrieveResult(
        chunks=chunks,
        detected_language=lang,
        fallback_triggered=False,
        first_pass_empty=not chunks,
        strategy="L0",
    )


def retrieve_l1(
    question: str,
    retriever: CorpusPgvectorRetriever,
    top_k: int,
    min_score: float,
) -> LangRetrieveResult:
    """Same-lang first; if empty → retry without language."""
    lang = detect_query_language(question)
    first = retriever.retrieve_chunks(
        question,
        language=lang,
        top_k=top_k,
        score_threshold=min_score,
    )
    if first:
        return LangRetrieveResult(
            chunks=first,
            detected_language=lang,
            fallback_triggered=False,
            first_pass_empty=False,
            strategy="L1",
        )
    second = retriever.retrieve_chunks(
        question,
        language=None,
        top_k=top_k,
        score_threshold=min_score,
    )
    return LangRetrieveResult(
        chunks=second,
        detected_language=lang,
        fallback_triggered=True,
        first_pass_empty=True,
        strategy="L1",
    )


def retrieve_l2(
    question: str,
    retriever: CorpusPgvectorRetriever,
    top_k: int,
    min_score: float,
) -> LangRetrieveResult:
    """Same-lang first; if empty → opposite language only."""
    lang = detect_query_language(question)
    first = retriever.retrieve_chunks(
        question,
        language=lang,
        top_k=top_k,
        score_threshold=min_score,
    )
    if first:
        return LangRetrieveResult(
            chunks=first,
            detected_language=lang,
            fallback_triggered=False,
            first_pass_empty=False,
            strategy="L2",
        )
    other = _opposite(lang)
    second = retriever.retrieve_chunks(
        question,
        language=other,
        top_k=top_k,
        score_threshold=min_score,
    )
    return LangRetrieveResult(
        chunks=second,
        detected_language=lang,
        fallback_triggered=True,
        first_pass_empty=True,
        strategy="L2",
    )


def retrieve_none(
    question: str,
    retriever: CorpusPgvectorRetriever,
    top_k: int,
    min_score: float,
) -> LangRetrieveResult:
    """No language filter — matches A0/A2/A4 spike retrieve path."""
    lang = detect_query_language(question)
    chunks = retriever.retrieve_chunks(
        question,
        language=None,
        top_k=top_k,
        score_threshold=min_score,
    )
    return LangRetrieveResult(
        chunks=chunks,
        detected_language=lang,
        fallback_triggered=False,
        first_pass_empty=not chunks,
        strategy="L_none",
    )


VARIANTS: tuple[tuple[str, RetrieveFn], ...] = (
    ("L_none", retrieve_none),
    ("L0", retrieve_l0),
    ("L1", retrieve_l1),
    ("L2", retrieve_l2),
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


def _cross_lang_share(chunks: list[RetrievedChunk], detected: str) -> float | None:
    if not chunks:
        return None
    mismatch = sum(1 for c in chunks if (c.language or "") != detected)
    return mismatch / len(chunks)


def _run_cell(  # noqa: PLR0913
    *,
    label: str,
    retrieve: RetrieveFn,
    rows: list[GoldenRow],
    retriever: CorpusPgvectorRetriever,
    llm: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    top_k: int,
    min_score: float,
    system_prompt: str,
) -> dict[str, object]:
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_hits = 0
    scored_n = 0
    empty_final = 0
    first_pass_empty = 0
    fallback_n = 0
    cross_shares: list[float] = []
    per_row: list[dict[str, object]] = []

    for row in rows:
        t0 = time.monotonic()
        result = retrieve(row.question, retriever, top_k, min_score)
        if result.first_pass_empty:
            first_pass_empty += 1
        if result.fallback_triggered:
            fallback_n += 1
        if not result.chunks:
            empty_final += 1
        share = _cross_lang_share(result.chunks, result.detected_language)
        if share is not None:
            cross_shares.append(share)

        urls = [c.url for c in result.chunks if c.url]
        context = _pack_p0(result.chunks)
        answer = ""
        if result.chunks:
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
            if result.chunks and row.retrieval_expectation not in {"abstain", "empty"}:
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
                "detected_language": result.detected_language,
                "first_pass_empty": result.first_pass_empty,
                "fallback_triggered": result.fallback_triggered,
                "n_chunks": len(result.chunks),
                "cross_lang_share": share,
                "retrieval_pass": retrieval_pass,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "latency_ms": latency_ms,
                "urls": urls,
                "chunk_languages": [c.language for c in result.chunks],
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    return {
        "label": label,
        "pack": "P0",
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "n_rows": len(rows),
        "n_first_pass_empty": first_pass_empty,
        "n_fallback_triggered": fallback_n,
        "n_empty_final": empty_final,
        "mean_cross_lang_share": _avg(cross_shares) if cross_shares else None,
        "rows": per_row,
    }


def main() -> int:
    """Run A3 soft language filter ablation."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL", file=sys.stderr)
        return 1

    top_k = int(os.environ.get("SPIKE_TOP_K", "5"))
    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(f"==> A3 language: {len(rows)} rows, top_k={top_k}, min_score={min_score}")

    embed = EmbeddingClient(timeout=120.0)
    cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in cache:
            cache[q] = _embed_with_retry(embed, q)
        return cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=top_k,
        score_threshold=min_score,
    )

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

    cells: list[dict[str, object]] = []
    for label, retrieve in VARIANTS:
        print(f"==> {label}")
        cell = _run_cell(
            label=label,
            retrieve=retrieve,
            rows=list(rows),
            retriever=retriever,
            llm=llm,
            judge=judge,
            top_k=top_k,
            min_score=min_score,
            system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
        cells.append(cell)
        print(
            f"    retrieval={cell['retrieval_relevance']} "
            f"faith={cell['faithfulness']} "
            f"relevancy={cell['answer_relevancy']} "
            f"p95={cell['latency_p95_ms']} "
            f"first_empty={cell['n_first_pass_empty']} "
            f"fallback={cell['n_fallback_triggered']} "
            f"empty_final={cell['n_empty_final']} "
            f"cross_share={cell['mean_cross_lang_share']}"
        )

    payload = {
        "fixture": str(_FIXTURE),
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "pack": "P0",
        "scored_rows": len(retrieval_rows(rows)),
        "note": (
            "L_none matches prior A0/A2/A4 retrieve (no language filter). "
            "L0 is prod ChatRAG strict filter. L1/L2 soft fallbacks."
        ),
        "cells": cells,
    }
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
