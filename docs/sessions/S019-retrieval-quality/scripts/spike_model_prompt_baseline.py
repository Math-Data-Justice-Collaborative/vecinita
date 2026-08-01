#!/usr/bin/env python3
"""EV-016 no-system-prompt baselines vs improvements (S019-D32).

For each synthesis model, measure a bare floor (empty system prompt) and
compare pack / prompt / H7 lifts. Judges stay pinned to prod 1.5B.

Conditions (per model)::

  bare_p0      no system prompt · R0 · P0 concat
  bare_p1      no system prompt · R0 · P1 headers
  prompt_p1    DEFAULT_EVAL_SYSTEM_PROMPT · R0 · P1  (prior model-sweep cell)
  prompt_h7p1  DEFAULT_EVAL_SYSTEM_PROMPT · H7 · P1  (Hy1 stack)

Default models: control + Tiny (T4-friendly). Pass ``--models`` for others
(S* may need playground GPU upsizing).

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_model_prompt_baseline.py
  uv run python .../spike_model_prompt_baseline.py \\
    --models qwen2.5:1.5b-instruct --conditions bare_p1,prompt_p1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

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
from vecinita_rag.language import detect_query_language
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
_REPORT_MD = (
    _REPO
    / "docs"
    / "sessions"
    / "S019-retrieval-quality"
    / "reports"
    / "spike-model-prompt-baseline.md"
)
_JUDGE_MODEL = "qwen2.5:1.5b-instruct"
_DEFAULT_MODELS = (
    "qwen2.5:1.5b-instruct",
    "g9v3:3b",
    "qwen3:4b-instruct-2507",
    "minicpm5:1b",
)
_CONTROL_USES_PROD = frozenset({"qwen2.5:1.5b-instruct"})

ConditionId = Literal["bare_p0", "bare_p1", "prompt_p1", "prompt_h7p1"]
PackName = Literal["P0", "P1"]


@dataclass(frozen=True, slots=True)
class ConditionSpec:
    """One prompt × pack × fan-out cell."""

    condition_id: ConditionId
    system_prompt: str
    pack: PackName
    use_h7: bool


CONDITION_SPECS: tuple[ConditionSpec, ...] = (
    ConditionSpec("bare_p0", "", "P0", False),
    ConditionSpec("bare_p1", "", "P1", False),
    ConditionSpec("prompt_p1", DEFAULT_EVAL_SYSTEM_PROMPT, "P1", False),
    ConditionSpec("prompt_h7p1", DEFAULT_EVAL_SYSTEM_PROMPT, "P1", True),
)


def build_synth_prompt(*, question: str, context: str, system_prompt: str) -> str:
    """Build the synthesis string; empty system_prompt = bare baseline."""
    capped = truncate_synthesis_context(context)
    body = f"Context:\n{capped}\n\nQuestion: {question.strip()}\n\nAnswer:"
    cleaned = system_prompt.strip()
    if not cleaned:
        return body
    return f"{cleaned}\n\n{body}"


def pack_p0(chunks: list[RetrievedChunk]) -> str:
    """Baseline concat of chunk texts."""
    return "\n\n".join(chunk.text for chunk in chunks)


def pack_p1(chunks: list[RetrievedChunk]) -> str:
    """Title + URL header per chunk."""
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _norm_query(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def hybrid_rewrites(question: str, *, locale: str) -> list[str]:
    """Cheap multi-query variants; Spanish-aware for es locale."""
    q = question.strip()
    variants = [q]
    if locale == "es":
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


def _delta(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return a - b


def compute_deltas(cells: dict[str, dict[str, object]]) -> dict[str, float | None]:
    """Compute pack / prompt / hybrid relevancy (and faith) lifts."""

    def rel(cid: str) -> float | None:
        cell = cells.get(cid)
        if cell is None:
            return None
        raw = cell.get("answer_relevancy")
        return float(raw) if isinstance(raw, (int, float)) else None

    def faith(cid: str) -> float | None:
        cell = cells.get(cid)
        if cell is None:
            return None
        raw = cell.get("faithfulness")
        return float(raw) if isinstance(raw, (int, float)) else None

    return {
        "pack_lift_relevancy": _delta(rel("bare_p1"), rel("bare_p0")),
        "pack_lift_faithfulness": _delta(faith("bare_p1"), faith("bare_p0")),
        "prompt_lift_relevancy": _delta(rel("prompt_p1"), rel("bare_p1")),
        "prompt_lift_faithfulness": _delta(faith("prompt_p1"), faith("bare_p1")),
        "hybrid_lift_relevancy": _delta(rel("prompt_h7p1"), rel("prompt_p1")),
        "hybrid_lift_faithfulness": _delta(faith("prompt_h7p1"), faith("prompt_p1")),
        "total_lift_vs_bare_p0_relevancy": _delta(rel("prompt_h7p1"), rel("bare_p0")),
        "total_lift_vs_bare_p0_faithfulness": _delta(faith("prompt_h7p1"), faith("bare_p0")),
    }


def answer_lang_match(*, answer: str, locale: str) -> bool:
    if not answer.strip():
        return False
    return detect_query_language(answer) == locale


def cross_lang_share(chunks: list[RetrievedChunk], query_lang: str) -> float | None:
    if not chunks:
        return None
    mismatch = sum(1 for c in chunks if (c.language or "") != query_lang)
    return mismatch / len(chunks)


def locale_breakdown(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for locale in ("en", "es"):
        subset = [r for r in rows if r.get("locale") == locale]
        faiths = [cast("float | None", r.get("faithfulness")) for r in subset]
        relevancies = [cast("float | None", r.get("answer_relevancy")) for r in subset]
        matches = [bool(r.get("answer_lang_match")) for r in subset]
        ret_rows = [r for r in subset if r.get("scored_retrieval") is True]
        hits = sum(1 for r in ret_rows if r.get("retrieval_pass") is True)
        out[locale] = {
            "n": len(subset),
            "retrieval_relevance": (hits / len(ret_rows)) if ret_rows else None,
            "faithfulness": _avg(faiths),
            "answer_relevancy": _avg(relevancies),
            "answer_lang_match_rate": (sum(matches) / len(matches)) if matches else None,
        }
    return out


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


def _pack(name: PackName, chunks: list[RetrievedChunk]) -> str:
    return pack_p1(chunks) if name == "P1" else pack_p0(chunks)


def _chunks_for_condition(
    *,
    row: GoldenRow,
    spec: ConditionSpec,
    pool: dict[tuple[str, str], list[RetrievedChunk]],
    retriever: CorpusPgvectorRetriever,
    top_k: int,
) -> list[RetrievedChunk]:
    base = pool[(row.id, row.locale)]
    if not spec.use_h7:
        return base[:top_k]
    rewrites = hybrid_rewrites(row.question, locale=row.locale)
    groups: list[list[RetrievedChunk]] = []
    for rw in rewrites:
        if rw == row.question:
            groups.append(base[:top_k])
        else:
            groups.append(retriever.retrieve_chunks(rw)[:top_k])
    return _merge_chunks(groups, top_k=top_k)


def _run_condition(  # noqa: PLR0913
    *,
    model_id: str,
    spec: ConditionSpec,
    rows: list[GoldenRow],
    pool: dict[tuple[str, str], list[RetrievedChunk]],
    retriever: CorpusPgvectorRetriever,
    synth: ModalHttpLLM,
    judge: LlamaIndexJudgeClient,
    top_k: int,
) -> dict[str, object]:
    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    retrieval_passes = 0
    scored = 0
    lang_matches = 0
    lang_scored = 0
    cross_shares: list[float] = []
    per_row: list[dict[str, object]] = []

    for row in rows:
        t0 = time.monotonic()
        chunks = _chunks_for_condition(
            row=row,
            spec=spec,
            pool=pool,
            retriever=retriever,
            top_k=top_k,
        )
        query_lang = detect_query_language(row.question)
        share = cross_lang_share(chunks, query_lang)
        if share is not None:
            cross_shares.append(share)
        urls = [c.url for c in chunks if c.url]
        packed = _pack(spec.pack, chunks)
        answer = ""
        if chunks:
            prompt = build_synth_prompt(
                question=row.question,
                context=packed,
                system_prompt=spec.system_prompt,
            )
            response = synth.complete(prompt)
            answer = str(getattr(response, "text", response))
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
                "scored_retrieval": scored_retrieval,
                "retrieval_pass": retrieval_pass,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "answer_lang_match": match,
                "cross_lang_share": share,
                "prompt_chars": len(spec.system_prompt),
                "context_chars": len(packed),
                "latency_ms": latency_ms,
            }
        )

    ordered = sorted(latencies)
    p95 = ordered[min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))] if ordered else 0
    return {
        "model_id": model_id,
        "condition": spec.condition_id,
        "system_prompt_mode": "none" if not spec.system_prompt.strip() else "default_eval",
        "pack": spec.pack,
        "use_h7": spec.use_h7,
        "retrieval_relevance": (retrieval_passes / scored) if scored else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p95_ms": p95,
        "answer_lang_match_rate": (lang_matches / lang_scored) if lang_scored else None,
        "mean_cross_lang_share": (sum(cross_shares) / len(cross_shares)) if cross_shares else None,
        "by_locale": locale_breakdown(per_row),
        "rows": per_row,
    }


def _write_report(payload: dict[str, object]) -> None:
    models = cast("list[dict[str, object]]", payload["models"])
    lines = [
        "# EV-016 model prompt baseline (S019-D32)",
        "",
        f"> **Run:** `{payload['run_id']}` · **Judge:** `{_JUDGE_MODEL}`  ",
        "> **Bare** = empty system prompt · **prompt_*** = `DEFAULT_EVAL_SYSTEM_PROMPT`",
        "",
        "## Per-model conditions",
        "",
        "| Model | Condition | prompt | pack | H7 | retrieval | faith | relevancy | "
        "lang_match | en_rel | es_rel | p95 |",
        "|-------|-----------|--------|------|----|-----------|-------|-----------|"
        "------------|--------|--------|-----|",
    ]
    for model_block in models:
        mid = cast("str", model_block["model_id"])
        if model_block.get("status") != "complete":
            lines.append(
                f"| {mid} | — | — | — | — | FAILED | — | — | — | — | — | — |"
            )
            continue
        for cell in cast("list[dict[str, object]]", model_block["conditions"]):
            by_loc = cast("dict[str, dict[str, object]]", cell["by_locale"])
            lines.append(
                f"| {mid} | {cell['condition']} | {cell['system_prompt_mode']} | "
                f"{cell['pack']} | {cell['use_h7']} | {cell['retrieval_relevance']} | "
                f"{cell['faithfulness']} | {cell['answer_relevancy']} | "
                f"{cell['answer_lang_match_rate']} | "
                f"{by_loc.get('en', {}).get('answer_relevancy')} | "
                f"{by_loc.get('es', {}).get('answer_relevancy')} | "
                f"{cell['latency_p95_ms']} |"
            )
    lines.extend(["", "## Deltas (vs bare / prior cell)", "", "| Model | pack Δrel | prompt Δrel | "
                  "hybrid Δrel | total Δrel vs bare_p0 | prompt Δfaith |",
                  "|-------|-----------|-------------|-------------|----------------------|---------------|"])
    for model_block in models:
        mid = cast("str", model_block["model_id"])
        if model_block.get("status") != "complete":
            continue
        d = cast("dict[str, float | None]", model_block["deltas"])
        lines.append(
            f"| {mid} | {d.get('pack_lift_relevancy')} | {d.get('prompt_lift_relevancy')} | "
            f"{d.get('hybrid_lift_relevancy')} | {d.get('total_lift_vs_bare_p0_relevancy')} | "
            f"{d.get('prompt_lift_faithfulness')} |"
        )
    lines.extend(
        [
            "",
            f"Artifact: `eval-experiments/{payload['run_id']}_model-prompt-baseline.json`",
            "",
        ]
    )
    _REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run bare vs improved prompt matrix across synthesis models."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        default=",".join(_DEFAULT_MODELS),
        help="Comma-separated playground tags (default: control + Tiny)",
    )
    parser.add_argument(
        "--conditions",
        default=",".join(c.condition_id for c in CONDITION_SPECS),
        help="Comma-separated condition ids",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=0, help="Limit golden rows (0=all)")
    args = parser.parse_args(argv)

    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    assert_no_legacy_ollama_url()

    models = parse_csv_strs(args.models)
    wanted = set(parse_csv_strs(args.conditions))
    specs = [c for c in CONDITION_SPECS if c.condition_id in wanted]
    if not models or not specs:
        print("ERROR: need models and conditions", file=sys.stderr)
        return 1
    for mid in models:
        resolve_hf_repo(mid)

    rows = load_golden_rows(fixture_path=_FIXTURE)
    if args.limit > 0:
        rows = rows[: args.limit]
    print(
        f"==> prompt baseline: {len(models)} model(s), {len(specs)} condition(s), "
        f"{len(rows)} rows",
        flush=True,
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
        top_k=max(args.top_k, 5),
        score_threshold=args.min_score,
    )

    print("==> retrieve once (R0 / L_none)", flush=True)
    pool: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        pool[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        print(f"    {row.id}/{row.locale}: {len(pool[(row.id, row.locale)])}", flush=True)

    judge_client = LlmClient(
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id=_JUDGE_MODEL,
        require_proxy_key=True,
    )
    warm_modal_llm(judge_client)
    judge = LlamaIndexJudgeClient(
        ModalHttpLLM(
            client=judge_client,
            max_tokens=128,
            temperature=0.0,
            model_id=_JUDGE_MODEL,
        )
    )

    playground_url = resolve_playground_base_url()
    print(f"==> playground={playground_url}", flush=True)

    model_blocks: list[dict[str, object]] = []
    for model_id in models:
        print(f"==> model={model_id} hf={resolve_hf_repo(model_id)}", flush=True)
        t0 = time.monotonic()
        try:
            if model_id in _CONTROL_USES_PROD:
                client = LlmClient(
                    os.environ["VECINITA_MODAL_LLM_URL"],
                    timeout=900.0,
                    model_id=model_id,
                    require_proxy_key=True,
                )
            else:
                client = make_playground_client(model_id=model_id, timeout=900.0)
            warm_modal_llm(client)
            synth = ModalHttpLLM(
                client=client,
                max_tokens=128,
                temperature=0.0,
                model_id=model_id,
            )
            condition_cells: list[dict[str, object]] = []
            by_id: dict[str, dict[str, object]] = {}
            for spec in specs:
                print(f"    ==> {spec.condition_id}", flush=True)
                cell = _run_condition(
                    model_id=model_id,
                    spec=spec,
                    rows=list(rows),
                    pool=pool,
                    retriever=retriever,
                    synth=synth,
                    judge=judge,
                    top_k=args.top_k,
                )
                condition_cells.append(cell)
                by_id[spec.condition_id] = cell
                by_loc = cast("dict[str, dict[str, object]]", cell["by_locale"])
                print(
                    f"       retrieval={cell['retrieval_relevance']} "
                    f"faith={cell['faithfulness']} "
                    f"relevancy={cell['answer_relevancy']} "
                    f"lang_match={cell['answer_lang_match_rate']} "
                    f"en_rel={by_loc['en'].get('answer_relevancy')} "
                    f"es_rel={by_loc['es'].get('answer_relevancy')} "
                    f"p95={cell['latency_p95_ms']}",
                    flush=True,
                )
            deltas = compute_deltas(by_id)
            print(f"    deltas={deltas}", flush=True)
            model_blocks.append(
                {
                    "model_id": model_id,
                    "hf_repo": resolve_hf_repo(model_id),
                    "status": "complete",
                    "synth_endpoint": (
                        "prod" if model_id in _CONTROL_USES_PROD else "playground"
                    ),
                    "wall_ms": int((time.monotonic() - t0) * 1000),
                    "conditions": condition_cells,
                    "deltas": deltas,
                }
            )
        except Exception as exc:  # noqa: BLE001 — per-model fail/skip
            err = f"{type(exc).__name__}: {exc}"
            print(f"    FAILED: {err}", flush=True)
            model_blocks.append(
                {
                    "model_id": model_id,
                    "hf_repo": resolve_hf_repo(model_id),
                    "status": "failed",
                    "error": err,
                    "wall_ms": int((time.monotonic() - t0) * 1000),
                }
            )

    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload: dict[str, object] = {
        "run_id": run_id,
        "decision": "S019-D32",
        "fixture": str(_FIXTURE),
        "judge_model_id": _JUDGE_MODEL,
        "playground_url": playground_url,
        "scored_rows": len(retrieval_rows(rows)),
        "conditions": [c.condition_id for c in specs],
        "models": model_blocks,
    }
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = _OUT_DIR / f"{run_id}_model-prompt-baseline.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_report(payload)
    print(f"==> wrote {out}", flush=True)
    print(f"==> wrote {_REPORT_MD}", flush=True)
    return 0 if all(m.get("status") == "complete" for m in model_blocks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
