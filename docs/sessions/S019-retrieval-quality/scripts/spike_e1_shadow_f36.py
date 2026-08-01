#!/usr/bin/env python3
"""EV-016 S019-D36: E1 F41 shadow populate + Hy0/Hy1 F36 vs E0 live.

1. Create dry_run rebuild_run stamped ``intfloat/multilingual-e5-small``
2. Embed live chunk texts with Modal MultiEmbedSpike E1 → shadow/batch
3. Run Hy0/Hy1 F36 on E0 live (prod EmbeddingClient) and E1 shadow (E1 queries)

Does **not** promote shadow. Prod embed pin unchanged.

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_e1_shadow_f36.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar, cast
from urllib.parse import urlparse
from uuid import UUID

_T = TypeVar("_T")

import modal
import psycopg
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClient
from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.judges import LlamaIndexJudgeClient
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.retrieval import score_retrieval_row
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
_MODAL_SCRIPT = Path(__file__).resolve().parent / "spike_embed_models_modal.py"
_HYBRID = Path(__file__).resolve().parent / "spike_hybrid_sweep.py"
_MODEL = "qwen2.5:1.5b-instruct"
_E1_MODEL_ID = "intfloat/multilingual-e5-small"
_BATCH_DOCS = 8
_EMBED_BATCH = 64

sys.path.insert(0, str(_HYBRID.parent))
from spike_hybrid_sweep import (  # noqa: E402
    CellSpec,
    _avg,
    _merge_chunks,
    _pack,
    _synthesize,
    cross_lang_share,
    hybrid_rewrites,
    locale_breakdown,
    pack_p1,
)

_ = pack_p1  # re-export used via _pack


def _assert_staging_db(url: str) -> None:
    host = urlparse(url).hostname or ""
    if "ondigitalocean.com" not in host:
        msg = f"expected staging DO Postgres, got {host!r}"
        raise RuntimeError(msg)


def _http_json(
    method: str,
    url: str,
    *,
    token: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        msg = f"{method} {url} -> {exc.code}: {detail[:500]}"
        raise RuntimeError(msg) from exc
    loaded = json.loads(body) if body else {}
    if not isinstance(loaded, dict):
        msg = f"expected JSON object from {url}"
        raise TypeError(msg)
    return cast("dict[str, object]", loaded)


def load_live_docs(database_url: str) -> list[dict[str, object]]:
    """Group live chunks by document URL for shadow batch upload."""
    _assert_staging_db(database_url)
    by_url: dict[str, list[dict[str, object]]] = {}
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.url, c.chunk_index, c.text
                FROM documents d
                JOIN chunks c ON c.document_id = d.id
                ORDER BY d.url, c.chunk_index
                """
            )
            for url, chunk_index, text in cur.fetchall():
                by_url.setdefault(str(url), []).append(
                    {"chunk_index": int(chunk_index), "text": str(text)}
                )
    return [{"url": url, "chunks": chunks} for url, chunks in by_url.items()]


def e1_embed_fn_factory(remote: object) -> Callable[[str], list[float]]:
    """Query embedder for E1 (e5 query: prefix)."""

    def _embed(question: str) -> list[float]:
        vectors = remote.embed_batch.remote("E1", [question], for_query=True)  # type: ignore[attr-defined]
        assert isinstance(vectors, list) and vectors
        vec = vectors[0]
        assert isinstance(vec, list) and len(vec) == EMBEDDING_DIMENSION
        return [float(x) for x in vec]

    return _embed


def _with_llm_retry(fn: Callable[[], _T], *, label: str, attempts: int = 5) -> _T:
    """Retry Modal LLM calls on transient timeouts."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001  # Modal / httpx transient
            last = exc
            wait = min(90, 2**attempt * 5)
            print(
                f"  retry {label} attempt={attempt + 1}/{attempts} "
                f"wait={wait}s err={type(exc).__name__}"
            )
            time.sleep(wait)
    assert last is not None
    raise last


def populate_e1_shadow(
    *,
    write_url: str,
    token: str,
    database_url: str,
    remote: object,
) -> UUID:
    """Create rebuild_run and upload E1 shadow embeddings for the live corpus."""
    created = _http_json(
        "POST",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/runs",
        token=token,
        payload={
            "mode": "reembed",
            "dry_run": True,
            "force": True,
            "status": "running",
            "embedding_model_id": _E1_MODEL_ID,
            "embedding_dim": EMBEDDING_DIMENSION,
            "chunk_size_tokens": 512,
        },
    )
    rebuild_run_id = UUID(str(created["rebuild_run_id"]))
    print(f"rebuild_run_id={rebuild_run_id}")

    docs = load_live_docs(database_url)
    print(f"live_docs={len(docs)} chunks={sum(len(cast('list[object]', d['chunks'])) for d in docs)}")

    for start in range(0, len(docs), _BATCH_DOCS):
        batch_docs = docs[start : start + _BATCH_DOCS]
        texts: list[str] = []
        owners: list[tuple[int, int]] = []
        for di, doc in enumerate(batch_docs):
            chunks = cast("list[dict[str, object]]", doc["chunks"])
            for ci, chunk in enumerate(chunks):
                texts.append(str(chunk["text"]))
                owners.append((di, ci))
        vectors: list[list[float]] = []
        for t0 in range(0, len(texts), _EMBED_BATCH):
            part = remote.embed_batch.remote(  # type: ignore[attr-defined]
                "E1",
                texts[t0 : t0 + _EMBED_BATCH],
                for_query=False,
            )
            assert isinstance(part, list)
            vectors.extend(part)
        assert len(vectors) == len(texts)
        for (di, ci), vec in zip(owners, vectors, strict=True):
            chunks = cast("list[dict[str, object]]", batch_docs[di]["chunks"])
            chunks[ci]["embedding"] = vec

        payload_docs: list[dict[str, object]] = []
        for doc in batch_docs:
            chunks_out = []
            for chunk in cast("list[dict[str, object]]", doc["chunks"]):
                chunks_out.append(
                    {
                        "chunk_index": chunk["chunk_index"],
                        "text": chunk["text"],
                        "embedding": chunk["embedding"],
                    }
                )
            payload_docs.append(
                {
                    "url": doc["url"],
                    "rebuild_run_id": str(rebuild_run_id),
                    "chunks": chunks_out,
                }
            )
        result = _http_json(
            "POST",
            f"{write_url.rstrip('/')}/internal/v1/rebuild/{rebuild_run_id}/shadow/batch",
            token=token,
            payload={"documents": payload_docs},
        )
        print(f"  shadow batch upserted={result.get('upserted_chunks')}")

    _http_json(
        "PATCH",
        f"{write_url.rstrip('/')}/internal/v1/rebuild/{rebuild_run_id}",
        token=token,
        payload={"status": "completed"},
    )
    return rebuild_run_id


def _retrieve_for_row(
    *,
    row: GoldenRow,
    retriever: CorpusPgvectorRetriever,
    rebuild_run_id: UUID | None,
    pool_n: int,
) -> list[RetrievedChunk]:
    return retriever.retrieve_chunks(
        row.question,
        rebuild_run_id=rebuild_run_id,
    )[:pool_n]


def _chunks_for_cell(
    *,
    row: GoldenRow,
    spec: CellSpec,
    retriever: CorpusPgvectorRetriever,
    rebuild_run_id: UUID | None,
    base_pool: dict[tuple[str, str, str], list[RetrievedChunk]],
) -> list[RetrievedChunk]:
    cache_key = (row.id, row.locale, f"{rebuild_run_id}:{spec.pool_n}")
    if cache_key not in base_pool:
        base_pool[cache_key] = _retrieve_for_row(
            row=row,
            retriever=retriever,
            rebuild_run_id=rebuild_run_id,
            pool_n=spec.pool_n,
        )
    pool = base_pool[cache_key]
    if not spec.use_h7:
        return pool[: spec.top_k]
    rewrites = hybrid_rewrites(row.question, locale=row.locale)
    groups: list[list[RetrievedChunk]] = []
    for rw in rewrites:
        if rw == row.question:
            groups.append(pool[: spec.pool_n])
        else:
            groups.append(
                retriever.retrieve_chunks(rw, rebuild_run_id=rebuild_run_id)[: spec.pool_n]
            )
    return _merge_chunks(groups, top_k=spec.top_k)


def _run_cell(  # noqa: PLR0913
    *,
    cell_id: str,
    spec: CellSpec,
    rows: list[GoldenRow],
    retriever: CorpusPgvectorRetriever,
    rebuild_run_id: UUID | None,
    llm: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
) -> dict[str, object]:
    base_pool: dict[tuple[str, str, str], list[RetrievedChunk]] = {}
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    retrieval_passes = 0
    scored = 0
    lang_matches = 0
    lang_scored = 0
    cross_shares: list[float] = []
    per_row: list[dict[str, object]] = []
    system_prompt = DEFAULT_EVAL_SYSTEM_PROMPT

    for row in rows:
        t0 = time.monotonic()
        chunks = _chunks_for_cell(
            row=row,
            spec=spec,
            retriever=retriever,
            rebuild_run_id=rebuild_run_id,
            base_pool=base_pool,
        )
        query_lang = detect_query_language(row.question)
        share = cross_lang_share(chunks, query_lang)
        if share is not None:
            cross_shares.append(share)
        urls = [c.url for c in chunks if c.url]
        packed = _pack(spec.pack, chunks)
        answer = ""
        if chunks:
            answer = _with_llm_retry(
                lambda: _synthesize(
                    question=row.question,
                    context=packed,
                    llm=llm,
                    system_prompt=system_prompt,
                ),
                label=f"synth:{row.id}:{row.locale}",
            )
        retrieval_pass = score_retrieval_row(row, urls)
        scored_retrieval = row.retrieval_expectation in {"hit", "any_of"}
        if scored_retrieval:
            scored += 1
            if retrieval_pass:
                retrieval_passes += 1
        faith: float | None = None
        relevancy: float | None = None
        if answer.strip():
            if chunks and row.retrieval_expectation not in {"abstain", "empty"}:
                faith = _with_llm_retry(
                    lambda: judge.faithfulness(
                        question=row.question,
                        answer=answer,
                        context=packed,
                    ),
                    label=f"faith:{row.id}:{row.locale}",
                )
            relevancy = _with_llm_retry(
                lambda: judge.answer_relevancy(
                    question=row.question,
                    answer=answer,
                    context=packed,
                ),
                label=f"rel:{row.id}:{row.locale}",
            )

        faiths.append(faith)
        relevancies.append(relevancy)
        ans_lang = detect_query_language(answer) if answer else None
        lang_match = bool(answer.strip()) and ans_lang == row.locale
        if answer.strip():
            lang_scored += 1
            if lang_match:
                lang_matches += 1
        per_row.append(
            {
                "id": row.id,
                "locale": row.locale,
                "retrieval_pass": retrieval_pass,
                "scored_retrieval": scored_retrieval,
                "retrieval_expectation": row.retrieval_expectation,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "answer_lang_match": lang_match,
                "cross_lang_share": share,
                "latency_ms": int((time.monotonic() - t0) * 1000),
                "retrieved_urls": urls[:5],
                "answer_preview": answer[:240],
            }
        )


    summary = {
        "cell_id": cell_id,
        "rebuild_run_id": str(rebuild_run_id) if rebuild_run_id else None,
        "embedding": "E1" if rebuild_run_id else "E0",
        "retrieval_relevance": (retrieval_passes / scored) if scored else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "answer_lang_match_rate": (lang_matches / lang_scored) if lang_scored else None,
        "mean_cross_lang_share": (sum(cross_shares) / len(cross_shares)) if cross_shares else None,
        "by_locale": locale_breakdown(per_row),
    }
    print(cell_id, summary)
    return {"summary": summary, "rows": per_row}


def compare_lift(e0: dict[str, object], e1: dict[str, object]) -> dict[str, object]:
    """Compare E1 Hy1 vs E0 Hy1 relevancy / ES relevancy / EN regression."""
    e0_rel = e0.get("answer_relevancy")
    e1_rel = e1.get("answer_relevancy")
    e0_es = cast("dict[str, object]", cast("dict[str, object]", e0.get("by_locale") or {}).get("es") or {})
    e1_es = cast("dict[str, object]", cast("dict[str, object]", e1.get("by_locale") or {}).get("es") or {})
    e0_en = cast("dict[str, object]", cast("dict[str, object]", e0.get("by_locale") or {}).get("en") or {})
    e1_en = cast("dict[str, object]", cast("dict[str, object]", e1.get("by_locale") or {}).get("en") or {})
    return {
        "overall_relevancy_delta": (
            float(cast("float", e1_rel)) - float(cast("float", e0_rel))
            if isinstance(e0_rel, (int, float)) and isinstance(e1_rel, (int, float))
            else None
        ),
        "es_relevancy_delta": (
            float(cast("float", e1_es["answer_relevancy"]))
            - float(cast("float", e0_es["answer_relevancy"]))
            if isinstance(e0_es.get("answer_relevancy"), (int, float))
            and isinstance(e1_es.get("answer_relevancy"), (int, float))
            else None
        ),
        "en_relevancy_delta": (
            float(cast("float", e1_en["answer_relevancy"]))
            - float(cast("float", e0_en["answer_relevancy"]))
            if isinstance(e0_en.get("answer_relevancy"), (int, float))
            and isinstance(e1_en.get("answer_relevancy"), (int, float))
            else None
        ),
        "e0_hy1": e0,
        "e1_hy1": e1,
    }


def main() -> int:
    """Populate E1 shadow and run Hy0/Hy1 F36 compare."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-run-id",
        default="",
        help="Reuse an existing E1 shadow rebuild_run_id (skip populate)",
    )
    parser.add_argument(
        "--cells",
        default="E0_Hy0,E0_Hy1,E1_Hy0,E1_Hy1",
        help="Comma-separated cells to run",
    )
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "").strip()
    write_url = os.environ.get("VECINITA_STAGING_WRITE_URL", "").strip()
    jwt_path = Path("/tmp/vecinita_admin_jwt.txt")
    if not database_url or not write_url or not jwt_path.is_file():
        print(
            "Need DATABASE_URL, VECINITA_STAGING_WRITE_URL, /tmp/vecinita_admin_jwt.txt",
            file=sys.stderr,
        )
        return 2
    token = jwt_path.read_text(encoding="utf-8").strip()

    import subprocess

    print("deploying MultiEmbedSpike…")
    subprocess.run(["modal", "deploy", str(_MODAL_SCRIPT)], check=True, cwd=str(_REPO))
    MultiEmbed = modal.Cls.from_name("vecinita-spike-embed-models", "MultiEmbedSpike")
    remote = MultiEmbed()

    if args.rebuild_run_id.strip():
        rebuild_run_id = UUID(args.rebuild_run_id.strip())
        print(f"reusing rebuild_run_id={rebuild_run_id}")
    else:
        rebuild_run_id = populate_e1_shadow(
            write_url=write_url,
            token=token,
            database_url=database_url,
            remote=remote,
        )

    rows = load_golden_rows(fixture_path=_FIXTURE)
    print(f"golden_rows={len(rows)}")

    llm_client = LlmClient(model_id=_MODEL, timeout=180.0)
    warm_modal_llm(llm_client)
    llm = ModalHttpLLM(client=llm_client, model=_MODEL)
    judge = LlamaIndexJudgeClient(llm)

    db_url = (
        database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgresql://")
        else database_url
    )
    e0_embed = EmbeddingClient()
    e0_retriever = CorpusPgvectorRetriever(
        embed_fn=lambda q: e0_embed.embed(q),
        database_url=db_url,
        top_k=20,
        score_threshold=0.2,
    )
    e1_retriever = CorpusPgvectorRetriever(
        embed_fn=e1_embed_fn_factory(remote),
        database_url=db_url,
        top_k=20,
        score_threshold=0.2,
    )

    hy0 = CellSpec("Hy0", "P1", False, False, 5, "none", 5)
    hy1 = CellSpec("Hy1", "P1", True, False, 5, "none", 5)

    cell_map: dict[str, tuple[CellSpec, CorpusPgvectorRetriever, UUID | None]] = {
        "E0_Hy0": (hy0, e0_retriever, None),
        "E0_Hy1": (hy1, e0_retriever, None),
        "E1_Hy0": (hy0, e1_retriever, rebuild_run_id),
        "E1_Hy1": (hy1, e1_retriever, rebuild_run_id),
    }
    selected = [c.strip() for c in args.cells.split(",") if c.strip()]

    report: dict[str, object] = {
        "started_at": datetime.now(UTC).isoformat(),
        "decision": "S019-D36",
        "e1_model": _E1_MODEL_ID,
        "rebuild_run_id": str(rebuild_run_id),
        "fixture": str(_FIXTURE),
        "model": _MODEL,
        "cells": {},
    }

    for cell_id in selected:
        if cell_id not in cell_map:
            print(f"unknown cell {cell_id}", file=sys.stderr)
            return 2
        spec, retriever, rid = cell_map[cell_id]
        print(f"running {cell_id}…")
        warm_modal_llm(llm_client)
        report["cells"][cell_id] = _run_cell(
            cell_id=cell_id,
            spec=spec,
            rows=rows,
            retriever=retriever,
            rebuild_run_id=rid,
            llm=llm,
            judge=judge,
        )

    if "E0_Hy1" in report["cells"] and "E1_Hy1" in report["cells"]:
        e0_hy1 = cast(
            "dict[str, object]",
            cast("dict[str, object]", report["cells"]["E0_Hy1"])["summary"],
        )
        e1_hy1 = cast(
            "dict[str, object]",
            cast("dict[str, object]", report["cells"]["E1_Hy1"])["summary"],
        )
        report["compare_hy1"] = compare_lift(e0_hy1, e1_hy1)

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = _OUT_DIR / f"{stamp}_e1-shadow-f36.json"
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", out)
    if "compare_hy1" in report:
        print("compare_hy1", report["compare_hy1"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
