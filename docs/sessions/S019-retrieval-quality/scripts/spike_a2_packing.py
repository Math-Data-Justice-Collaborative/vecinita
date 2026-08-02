#!/usr/bin/env python3
"""EV-016 A2 packing ablation on staging golden (read-only corpus).

Prototypes only — not production. Measures answer metrics for:
  P0 baseline concat
  P1 title+url headers
  P2 P1 + dedupe by document_id (keep highest score)
  P3 P2 + token/char budget (same cap as sandbox truncate)

Usage (from repo root)::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_a2_packing.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.retrieval import retrieval_rows, score_retrieval_row
from vecinita_eval.sandbox import (
    DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
    truncate_synthesis_context,
)
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
    / "spike-a2-packing.json"
)

PackFn = Callable[[list[RetrievedChunk]], str]


@dataclass(frozen=True, slots=True)
class PackVariant:
    """Named packing strategy for A2."""

    name: str
    pack: PackFn


def pack_p0(chunks: list[RetrievedChunk]) -> str:
    """Baseline: join raw chunk texts."""
    return "\n\n".join(chunk.text for chunk in chunks)


def pack_p1(chunks: list[RetrievedChunk]) -> str:
    """Title + URL header per chunk."""
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _dedupe_by_document(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Keep highest-score chunk per document_id (stable order by first appearance)."""
    best: dict[UUID, RetrievedChunk] = {}
    order: list[UUID] = []
    for chunk in chunks:
        doc_id = chunk.document_id
        if doc_id not in best:
            order.append(doc_id)
            best[doc_id] = chunk
            continue
        if chunk.score > best[doc_id].score:
            best[doc_id] = chunk
    return [best[doc_id] for doc_id in order]


def pack_p2(chunks: list[RetrievedChunk]) -> str:
    """P1 + dedupe by document_id."""
    return pack_p1(_dedupe_by_document(chunks))


def pack_p3(chunks: list[RetrievedChunk]) -> str:
    """P2 + char budget (sandbox default)."""
    return truncate_synthesis_context(
        pack_p2(chunks),
        max_chars=DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
    )


VARIANTS: tuple[PackVariant, ...] = (
    PackVariant("P0", pack_p0),
    PackVariant("P1", pack_p1),
    PackVariant("P2", pack_p2),
    PackVariant("P3", pack_p3),
)


def _embed_with_retry(embed: EmbeddingClient, question: str) -> list[float]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            return embed.embed(question)
        except Exception as exc:  # noqa: BLE001  # Modal cold-start / transient HTTP
            last = exc
            time.sleep(2**attempt)
    assert last is not None
    raise last


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


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _run_variant(  # noqa: PLR0913
    *,
    name: str,
    pack: PackFn,
    rows: list[GoldenRow],
    cached_chunks: dict[tuple[str, str], list[RetrievedChunk]],
    llm: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    system_prompt: str,
) -> dict[str, object]:
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_passes = 0
    scored = 0
    per_row: list[dict[str, object]] = []
    context_chars: list[int] = []
    unique_docs: list[int] = []

    for row in rows:
        t0 = time.monotonic()
        chunks = cached_chunks[(row.id, row.locale)]
        urls = [c.url for c in chunks if c.url]
        packed = pack(chunks)
        context_chars.append(len(packed))
        unique_docs.append(len({c.document_id for c in chunks}))
        if name in {"P2", "P3"}:
            unique_docs[-1] = len({c.document_id for c in _dedupe_by_document(chunks)})

        answer = _synthesize(
            question=row.question,
            context=packed,
            llm=llm,
            system_prompt=system_prompt,
        )
        _ = detect_query_language(row.question)

        retrieval_pass = score_retrieval_row(row, urls)
        if row.retrieval_expectation in {"hit", "any_of"}:
            scored += 1
            retrieval_passes += int(retrieval_pass)

        faith: float | None = None
        relevancy: float | None = None
        if answer.strip():
            if chunks and row.retrieval_expectation not in {"abstain", "empty"}:
                faith = judge.faithfulness(
                    question=row.question,
                    answer=answer,
                    context=packed,
                )
            relevancy = judge.answer_relevancy(
                question=row.question,
                answer=answer,
                context=packed,
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
                "context_chars": len(packed),
                "n_chunks_in": len(chunks),
                "n_docs_packed": unique_docs[-1],
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    return {
        "name": name,
        "retrieval_relevance": (retrieval_passes / scored) if scored else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "mean_context_chars": sum(context_chars) / len(context_chars) if context_chars else 0,
        "mean_docs_packed": sum(unique_docs) / len(unique_docs) if unique_docs else 0,
        "rows": per_row,
    }


def main() -> int:
    """Run A2 packing ablation against staging golden."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL (ondigitalocean)", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL (ADR-037)", file=sys.stderr)
        return 1

    top_k = int(os.environ.get("SPIKE_TOP_K", "5"))
    min_score = float(os.environ.get("SPIKE_MIN_SCORE", "0.2"))
    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(f"==> A2 packing: {len(rows)} rows, top_k={top_k}, min_score={min_score}")

    embed = EmbeddingClient(timeout=120.0)
    vectors: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in vectors:
            vectors[q] = _embed_with_retry(embed, q)
        return vectors[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=top_k,
        score_threshold=min_score,
    )

    print("==> retrieving once per row")
    cached: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        cached[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        n_dup = len(cached[(row.id, row.locale)]) - len(
            {c.document_id for c in cached[(row.id, row.locale)]}
        )
        print(
            f"    {row.id}/{row.locale}: chunks={len(cached[(row.id, row.locale)])} "
            f"extra_dup_chunks={n_dup}"
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

    # Packer smoke (no LLM): char savings
    sample = next(iter(cached.values()))
    print("==> packer char lengths on first row chunks:")
    for variant in VARIANTS:
        packed = variant.pack(sample)
        print(f"    {variant.name}: chars={len(packed)} docs_in={len({c.document_id for c in sample})}")

    cells: list[dict[str, object]] = []
    for variant in VARIANTS:
        print(f"==> {variant.name}")
        cell = _run_variant(
            name=variant.name,
            pack=variant.pack,
            rows=rows,
            cached_chunks=cached,
            llm=llm,
            judge=judge,
            system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
        cells.append(cell)
        print(
            f"    retrieval={cell['retrieval_relevance']} "
            f"faith={cell['faithfulness']} "
            f"relevancy={cell['answer_relevancy']} "
            f"p95={cell['latency_p95_ms']} "
            f"mean_chars={cell['mean_context_chars']:.0f}"
        )

    payload = {
        "fixture": str(_FIXTURE),
        "top_k": top_k,
        "min_retrieval_score": min_score,
        "scored_rows": len(retrieval_rows(rows)),
        "variants": cells,
    }
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}")
    return 0


if __name__ == "__main__":
    # Cast unused import for type checkers that flag GoldenRow only in annotations
    _ = cast("object", GoldenRow)
    raise SystemExit(main())
