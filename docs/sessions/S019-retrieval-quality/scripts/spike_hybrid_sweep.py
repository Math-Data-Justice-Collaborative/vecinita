#!/usr/bin/env python3
"""EV-016 hybrid sweep (S019-D29 option A): Hy0–Hy4 + language/top_k reruns.

Measures packing × H7 fan-out × optional R1 with EN/ES locale breakdown,
answer-language match, and cross-lang chunk share.

Cells::

  Hy0        R0 + P1                 (control)
  Hy1        H7 + P1
  Hy2        H7 + P3
  Hy3        H7 + R1 + P1
  Hy4        H7 + R1 + P3
  HyLang0    L0 language filter + R0 + P1  (prod-shaped lang)
  HyK8       R0 top_k=8 + P1               (A1 rerun with packing)

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_hybrid_sweep.py
  uv run python .../spike_hybrid_sweep.py --cells Hy0,Hy1,HyLang0 --limit 3
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast
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
from vecinita_eval.sweep import parse_csv_strs
from vecinita_llm_client import LlmClient
from vecinita_rag.language import detect_query_language
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_SYSTEM_PROMPT

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
_REPORT_MD = (
    _REPO
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "reports"
    / "spike-hybrid-plan.md"
)
_MODEL = "qwen2.5:1.5b-instruct"
_TOKEN_RE = re.compile(r"[a-z0-9áéíóúñü]+", re.IGNORECASE)

CellId = Literal["Hy0", "Hy1", "Hy2", "Hy3", "Hy4", "HyLang0", "HyK8"]
PackName = Literal["P1", "P3"]

_ALL_CELLS: tuple[CellId, ...] = (
    "Hy0",
    "Hy1",
    "Hy2",
    "Hy3",
    "Hy4",
    "HyLang0",
    "HyK8",
)


@dataclass(frozen=True, slots=True)
class CellSpec:
    """Hybrid cell configuration."""

    cell_id: CellId
    pack: PackName
    use_h7: bool
    use_r1: bool
    top_k: int
    language_mode: Literal["none", "l0"]
    pool_n: int


_SPECS: dict[CellId, CellSpec] = {
    "Hy0": CellSpec("Hy0", "P1", False, False, 5, "none", 5),
    "Hy1": CellSpec("Hy1", "P1", True, False, 5, "none", 5),
    "Hy2": CellSpec("Hy2", "P3", True, False, 5, "none", 5),
    "Hy3": CellSpec("Hy3", "P1", True, True, 5, "none", 20),
    "Hy4": CellSpec("Hy4", "P3", True, True, 5, "none", 20),
    "HyLang0": CellSpec("HyLang0", "P1", False, False, 5, "l0", 5),
    "HyK8": CellSpec("HyK8", "P1", False, False, 8, "none", 8),
}


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _TOKEN_RE.finditer(text)}


def _norm_query(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def pack_p1(chunks: list[RetrievedChunk]) -> str:
    """Title + URL header per chunk."""
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _dedupe_by_document(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
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


def pack_p3(
    chunks: list[RetrievedChunk],
    *,
    max_chars: int = DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS,
) -> str:
    """P1 + dedupe by document_id + char budget."""
    return truncate_synthesis_context(pack_p1(_dedupe_by_document(chunks)), max_chars=max_chars)


def cross_lang_share(chunks: list[RetrievedChunk], query_lang: str) -> float | None:
    """Fraction of chunks whose language differs from the query language."""
    if not chunks:
        return None
    mismatch = sum(1 for c in chunks if (c.language or "") != query_lang)
    return mismatch / len(chunks)


def answer_lang_match(*, answer: str, locale: str) -> bool:
    """True when detected answer language equals the golden locale."""
    if not answer.strip():
        return False
    return detect_query_language(answer) == locale


def hybrid_rewrites(question: str, *, locale: str) -> list[str]:
    """Cheap multi-query variants; Spanish-aware for es locale."""
    q = question.strip()
    variants = [q]
    if locale == "es":
        lowered = q.lower()
        if "cómo" in lowered or "como" in lowered:
            variants.append(
                q.replace("Cómo", "Qué").replace("cómo", "qué").replace("Como", "Qué").replace(
                    "como", "qué"
                )
            )
        if "?" in q or "¿" in q:
            variants.append(q.rstrip("?").rstrip("¿") + " en Providence RI?")
    else:
        if "how" in q.lower():
            variants.append(q.replace("How", "What").replace("how", "what"))
        if "?" in q:
            variants.append(q.rstrip("?") + " in Providence RI?")
    seen: set[str] = set()
    out: list[str] = []
    for variant in variants:
        key = _norm_query(variant)
        if key not in seen:
            seen.add(key)
            out.append(variant)
    return out[:3]


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


def _merge_chunks(groups: list[list[RetrievedChunk]], *, top_k: int) -> list[RetrievedChunk]:
    best: dict[str, RetrievedChunk] = {}
    for group in groups:
        for chunk in group:
            key = str(chunk.chunk_id)
            prev = best.get(key)
            if prev is None or chunk.score > prev.score:
                best[key] = chunk
    ranked = sorted(best.values(), key=lambda c: c.score, reverse=True)
    return ranked[:top_k]


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def locale_breakdown(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Aggregate retrieval / faith / relevancy / lang metrics by locale."""
    out: dict[str, dict[str, object]] = {}
    for locale in ("en", "es"):
        subset = [r for r in rows if r.get("locale") == locale]
        faiths = [cast("float | None", r.get("faithfulness")) for r in subset]
        relevancies = [cast("float | None", r.get("answer_relevancy")) for r in subset]
        matches = [bool(r.get("answer_lang_match")) for r in subset]
        shares = [
            cast("float", r["cross_lang_share"])
            for r in subset
            if isinstance(r.get("cross_lang_share"), float)
        ]
        scored = [
            r
            for r in subset
            if r.get("retrieval_expectation") in {"hit", "any_of"}
            or "retrieval_pass" in r
        ]
        # Prefer explicit scored flag when present; else use all with retrieval_pass.
        retrieval_rows_local = [
            r for r in subset if r.get("scored_retrieval") is True
        ] or [r for r in subset if "retrieval_pass" in r]
        hits = sum(1 for r in retrieval_rows_local if r.get("retrieval_pass") is True)
        n_ret = len(retrieval_rows_local)
        _ = scored  # kept for clarity; retrieval uses retrieval_rows_local
        out[locale] = {
            "n": len(subset),
            "retrieval_relevance": (hits / n_ret) if n_ret else None,
            "faithfulness": _avg(faiths),
            "answer_relevancy": _avg(relevancies),
            "answer_lang_match_rate": (sum(matches) / len(matches)) if matches else None,
            "mean_cross_lang_share": (sum(shares) / len(shares)) if shares else None,
        }
    return out


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


def _pack(name: PackName, chunks: list[RetrievedChunk]) -> str:
    if name == "P3":
        return pack_p3(chunks)
    return pack_p1(chunks)


def _retrieve_for_row(
    *,
    row: GoldenRow,
    retriever: CorpusPgvectorRetriever,
    language_mode: Literal["none", "l0"],
    pool_n: int,
) -> list[RetrievedChunk]:
    lang = detect_query_language(row.question) if language_mode == "l0" else None
    return retriever.retrieve_chunks(row.question, language=lang)[:pool_n]


def _chunks_for_cell(
    *,
    row: GoldenRow,
    spec: CellSpec,
    retriever: CorpusPgvectorRetriever,
    base_pool: dict[tuple[str, str, str], list[RetrievedChunk]],
) -> tuple[list[RetrievedChunk], list[str]]:
    """Return (keep_k chunks, rewrite list used)."""
    cache_key = (row.id, row.locale, f"{spec.language_mode}:{spec.pool_n}")
    if cache_key not in base_pool:
        base_pool[cache_key] = _retrieve_for_row(
            row=row,
            retriever=retriever,
            language_mode=spec.language_mode,
            pool_n=spec.pool_n,
        )
    pool = base_pool[cache_key]
    rewrites = [row.question]
    if spec.use_h7:
        rewrites = hybrid_rewrites(row.question, locale=row.locale)
        groups: list[list[RetrievedChunk]] = []
        for rw in rewrites:
            if rw == row.question:
                groups.append(pool[: spec.pool_n])
            else:
                lang = detect_query_language(rw) if spec.language_mode == "l0" else None
                groups.append(retriever.retrieve_chunks(rw, language=lang)[: spec.pool_n])
        merged = _merge_chunks(groups, top_k=spec.pool_n)
    else:
        merged = pool[: spec.pool_n]
    if spec.use_r1:
        kept = rerank_r1(row.question, merged, top_k=spec.top_k)
    else:
        kept = merged[: spec.top_k]
    return kept, rewrites


def _run_cell(  # noqa: PLR0913
    *,
    spec: CellSpec,
    rows: list[GoldenRow],
    retriever: CorpusPgvectorRetriever,
    base_pool: dict[tuple[str, str, str], list[RetrievedChunk]],
    llm: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    system_prompt: str,
) -> dict[str, object]:
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_passes = 0
    scored = 0
    lang_matches = 0
    lang_scored = 0
    cross_shares: list[float] = []
    context_chars: list[int] = []
    per_row: list[dict[str, object]] = []

    for row in rows:
        t0 = time.monotonic()
        chunks, rewrites = _chunks_for_cell(
            row=row,
            spec=spec,
            retriever=retriever,
            base_pool=base_pool,
        )
        query_lang = detect_query_language(row.question)
        share = cross_lang_share(chunks, query_lang)
        if share is not None:
            cross_shares.append(share)
        urls = [c.url for c in chunks if c.url]
        packed = _pack(spec.pack, chunks)
        context_chars.append(len(packed))
        answer = ""
        if chunks:
            answer = _synthesize(
                question=row.question,
                context=packed,
                llm=llm,
                system_prompt=system_prompt,
            )
        retrieval_pass = score_retrieval_row(row, urls)
        scored_retrieval = row.retrieval_expectation in {"hit", "any_of"}
        if scored_retrieval:
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
        match = answer_lang_match(answer=answer, locale=row.locale)
        if answer.strip():
            lang_scored += 1
            lang_matches += int(match)
        faiths.append(faith)
        relevancies.append(relevancy)
        latency_ms = int((time.monotonic() - t0) * 1000)
        latencies.append(latency_ms)
        per_row.append(
            {
                "id": row.id,
                "locale": row.locale,
                "query_language": query_lang,
                "locale_query_lang_match": query_lang == row.locale,
                "retrieval_expectation": row.retrieval_expectation,
                "scored_retrieval": scored_retrieval,
                "retrieval_pass": retrieval_pass,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "answer_lang_match": match,
                "answer_language": detect_query_language(answer) if answer.strip() else None,
                "cross_lang_share": share,
                "chunk_languages": [c.language for c in chunks],
                "n_chunks": len(chunks),
                "n_docs": len({c.document_id for c in chunks}),
                "context_chars": len(packed),
                "n_rewrites": len(rewrites),
                "rewrites": rewrites,
                "latency_ms": latency_ms,
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    by_locale = locale_breakdown(per_row)
    return {
        "cell": spec.cell_id,
        "pack": spec.pack,
        "use_h7": spec.use_h7,
        "use_r1": spec.use_r1,
        "top_k": spec.top_k,
        "language_mode": spec.language_mode,
        "retrieval_relevance": (retrieval_passes / scored) if scored else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "answer_lang_match_rate": (lang_matches / lang_scored) if lang_scored else None,
        "mean_cross_lang_share": (sum(cross_shares) / len(cross_shares)) if cross_shares else None,
        "mean_context_chars": (
            sum(context_chars) / len(context_chars) if context_chars else 0.0
        ),
        "by_locale": by_locale,
        "rows": per_row,
    }


def _append_report(payload: dict[str, object], path: Path) -> None:
    cells = cast("list[dict[str, object]]", payload["cells"])
    lines = [
        "",
        f"## Hybrid sweep results ({payload['run_id']})",
        "",
        "| Cell | stack | retrieval | faith | relevancy | lang_match | cross_lang | "
        "en_rel | es_rel | p95_ms |",
        "|------|-------|-----------|-------|-----------|------------|------------|"
        "--------|--------|--------|",
    ]
    for cell in cells:
        by_loc = cast("dict[str, dict[str, object]]", cell["by_locale"])
        en_rel = by_loc.get("en", {}).get("answer_relevancy")
        es_rel = by_loc.get("es", {}).get("answer_relevancy")
        stack = (
            f"{'H7+' if cell['use_h7'] else ''}"
            f"{'R1+' if cell['use_r1'] else ''}"
            f"{cell['pack']}"
            f"{'+L0' if cell['language_mode'] == 'l0' else ''}"
            f"{'+k8' if cell['top_k'] == 8 else ''}"
        )
        if stack.startswith("+"):
            stack = stack[1:]
        if not cell["use_h7"] and not cell["use_r1"]:
            stack = f"R0+{cell['pack']}"
            if cell["language_mode"] == "l0":
                stack += "+L0"
            if cell["top_k"] == 8:
                stack += "+k8"
        lines.append(
            f"| {cell['cell']} | {stack} | {cell['retrieval_relevance']} | "
            f"{cell['faithfulness']} | {cell['answer_relevancy']} | "
            f"{cell['answer_lang_match_rate']} | {cell['mean_cross_lang_share']} | "
            f"{en_rel} | {es_rel} | {cell['latency_p95_ms']} |"
        )
    lines.extend(
        [
            "",
            f"Artifact: `eval-experiments/{payload['run_id']}_hybrid-sweep.json`",
            "",
        ]
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    """Run hybrid Hy0–Hy4 + language/top_k cells against staging golden."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cells",
        default=",".join(_ALL_CELLS),
        help="Comma-separated cell ids (default: all)",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit golden rows (0=all)")
    args = parser.parse_args(argv)

    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL (ondigitalocean)", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL (ADR-037)", file=sys.stderr)
        return 1
    if not os.environ.get("VECINITA_MODAL_LLM_URL"):
        print("ERROR: VECINITA_MODAL_LLM_URL required", file=sys.stderr)
        return 1

    requested = cast("list[CellId]", parse_csv_strs(args.cells))
    for cell_id in requested:
        if cell_id not in _SPECS:
            print(f"ERROR: unknown cell {cell_id}", file=sys.stderr)
            return 1

    rows = load_golden_rows(fixture_path=_FIXTURE)
    if args.limit > 0:
        rows = rows[: args.limit]
    print(
        f"==> hybrid sweep: {len(rows)} rows, cells={requested}, model={_MODEL}",
        flush=True,
    )

    embed = EmbeddingClient(timeout=120.0)
    vectors: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in vectors:
            vectors[q] = _embed_with_retry(embed, q)
        return vectors[q]

    # Retriever top_k large enough for R1 pools / k=8
    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=20,
        score_threshold=float(os.environ.get("SPIKE_MIN_SCORE", "0.2")),
    )

    llm_client = LlmClient(
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id=_MODEL,
        require_proxy_key=True,
    )
    warm_modal_llm(llm_client)
    llm = ModalHttpLLM(
        client=llm_client,
        max_tokens=128,
        temperature=0.0,
        model_id=_MODEL,
    )
    judge = LlamaIndexJudgeClient(llm)

    base_pool: dict[tuple[str, str, str], list[RetrievedChunk]] = {}
    cells: list[dict[str, object]] = []
    for cell_id in requested:
        spec = _SPECS[cell_id]
        print(f"==> {cell_id}", flush=True)
        cell = _run_cell(
            spec=spec,
            rows=rows,
            retriever=retriever,
            base_pool=base_pool,
            llm=llm,
            judge=judge,
            system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        )
        cells.append(cell)
        by_loc = cast("dict[str, dict[str, object]]", cell["by_locale"])
        print(
            f"    retrieval={cell['retrieval_relevance']} "
            f"faith={cell['faithfulness']} "
            f"relevancy={cell['answer_relevancy']} "
            f"lang_match={cell['answer_lang_match_rate']} "
            f"cross_lang={cell['mean_cross_lang_share']} "
            f"en_rel={by_loc['en'].get('answer_relevancy')} "
            f"es_rel={by_loc['es'].get('answer_relevancy')} "
            f"p95={cell['latency_p95_ms']}",
            flush=True,
        )

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload: dict[str, object] = {
        "run_id": run_id,
        "fixture": str(_FIXTURE),
        "model": _MODEL,
        "scored_rows": len(retrieval_rows(rows)),
        "decision": "S019-D29",
        "option": "A",
        "cells": cells,
    }
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _OUT_DIR / f"{run_id}_hybrid-sweep.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {out_path}", flush=True)
    if _REPORT_MD.is_file():
        _append_report(payload, _REPORT_MD)
        print(f"==> appended results to {_REPORT_MD}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
