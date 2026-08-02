#!/usr/bin/env python3
"""Dump sample call/response pairs for key S019 experiment conditions.

Two golden rows (EN clinic hours + ES Nuevas Voces). Writes JSON for the canvas.

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_sample_calls.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from vecinita_embedding_client import EmbeddingClient
from vecinita_eval.golden import load_golden_rows
from vecinita_eval.modal_llm import ModalHttpLLM, warm_modal_llm
from vecinita_eval.sandbox import truncate_synthesis_context
from vecinita_llm_client import LlmClient
from vecinita_rag.language import detect_query_language
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RetrievedChunk
from vecinita_shared_schemas.eval_config import DEFAULT_EVAL_SYSTEM_PROMPT

# Reuse hybrid helpers
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
from spike_hybrid_sweep import (  # noqa: E402
    hybrid_rewrites,
    pack_p1,
    pack_p3,
    rerank_r1,
)
from spike_model_prompt_baseline import build_synth_prompt, pack_p0  # noqa: E402

_REPO = Path(__file__).resolve().parents[4]
_FIXTURE = _REPO / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
_OUT = (
    _REPO
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "reports"
    / "eval-experiments"
    / "sample-calls.json"
)
_MODEL = "qwen2.5:1.5b-instruct"
_SAMPLE_IDS = {
    ("community-free-clinic-hours", "en"),
    ("community-nuevas-voces", "es"),
}


def _merge(groups: list[list[RetrievedChunk]], top_k: int) -> list[RetrievedChunk]:
    best: dict[str, RetrievedChunk] = {}
    for group in groups:
        for chunk in group:
            key = str(chunk.chunk_id)
            prev = best.get(key)
            if prev is None or chunk.score > prev.score:
                best[key] = chunk
    return sorted(best.values(), key=lambda c: c.score, reverse=True)[:top_k]


def _embed_retry(embed: EmbeddingClient, q: str) -> list[float]:
    last: Exception | None = None
    for attempt in range(4):
        try:
            return embed.embed(q)
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2**attempt)
    assert last is not None
    raise last


def main() -> int:
    """Run sample dump for representative experiment stacks."""
    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: staging DATABASE_URL required", file=sys.stderr)
        return 1
    if os.environ.get("VECINITA_MODAL_OLLAMA_URL"):
        print("ERROR: unset VECINITA_MODAL_OLLAMA_URL", file=sys.stderr)
        return 1

    rows = [r for r in load_golden_rows(fixture_path=_FIXTURE) if (r.id, r.locale) in _SAMPLE_IDS]
    print(f"==> sample calls: {len(rows)} rows", flush=True)

    embed = EmbeddingClient(timeout=120.0)
    cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in cache:
            cache[q] = _embed_retry(embed, q)
        return cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=20,
        score_threshold=0.2,
    )

    client = LlmClient(
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id=_MODEL,
        require_proxy_key=True,
    )
    warm_modal_llm(client)
    llm = ModalHttpLLM(client=client, max_tokens=128, temperature=0.0, model_id=_MODEL)

    samples: list[dict[str, object]] = []

    for row in rows:
        print(f"==> {row.id}/{row.locale}", flush=True)
        pool = retriever.retrieve_chunks(row.question)
        pool_l0 = retriever.retrieve_chunks(
            row.question, language=detect_query_language(row.question)
        )
        # H7 merge
        rewrites = hybrid_rewrites(row.question, locale=row.locale)
        groups = []
        for rw in rewrites:
            if rw == row.question:
                groups.append(pool[:5])
            else:
                groups.append(retriever.retrieve_chunks(rw)[:5])
        h7 = _merge(groups, 5)
        r1 = rerank_r1(row.question, pool[:20], top_k=5)

        conditions: list[tuple[str, str, list[RetrievedChunk], str]] = [
            ("A0 / bare-ish P0+prompt", DEFAULT_EVAL_SYSTEM_PROMPT, pool[:5], "P0"),
            ("A2 P1+prompt (Hy0)", DEFAULT_EVAL_SYSTEM_PROMPT, pool[:5], "P1"),
            ("A2 P3+prompt", DEFAULT_EVAL_SYSTEM_PROMPT, pool[:5], "P3"),
            ("A4 R1+P1+prompt", DEFAULT_EVAL_SYSTEM_PROMPT, r1, "P1"),
            ("Hy1 H7+P1+prompt", DEFAULT_EVAL_SYSTEM_PROMPT, h7, "P1"),
            ("HyLang0 L0+P1+prompt", DEFAULT_EVAL_SYSTEM_PROMPT, pool_l0[:5], "P1"),
            ("D32 bare_p0 (no prompt)", "", pool[:5], "P0"),
            ("D32 bare_p1 (no prompt)", "", pool[:5], "P1"),
            ("D32 prompt_h7p1", DEFAULT_EVAL_SYSTEM_PROMPT, h7, "P1"),
        ]

        for label, system, chunks, pack_name in conditions:
            if pack_name == "P0":
                packed = pack_p0(chunks)
            elif pack_name == "P3":
                packed = pack_p3(chunks)
            else:
                packed = pack_p1(chunks)
            call = build_synth_prompt(
                question=row.question, context=packed, system_prompt=system
            )
            # Truncate stored call for readability but keep head+tail
            call_preview = call if len(call) <= 1800 else call[:900] + "\n…\n" + call[-700:]
            t0 = time.monotonic()
            response = llm.complete(call)
            answer = str(getattr(response, "text", response))
            ms = int((time.monotonic() - t0) * 1000)
            print(f"    {label}: {ms}ms → {answer[:80]!r}", flush=True)
            samples.append(
                {
                    "experiment": label,
                    "row_id": row.id,
                    "locale": row.locale,
                    "question": row.question,
                    "system_prompt_mode": "none" if not system.strip() else "default_eval",
                    "pack": pack_name,
                    "n_chunks": len(chunks),
                    "chunk_languages": [c.language for c in chunks],
                    "chunk_titles": [(c.title or "")[:60] for c in chunks],
                    "call_preview": call_preview,
                    "call_chars": len(call),
                    "context_chars": len(truncate_synthesis_context(packed)),
                    "answer": answer,
                    "latency_ms": ms,
                    "model_id": _MODEL,
                }
            )

    payload = {
        "model_id": _MODEL,
        "fixture": str(_FIXTURE),
        "sample_rows": sorted(f"{i}/{loc}" for i, loc in _SAMPLE_IDS),
        "samples": samples,
    }
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {_OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
