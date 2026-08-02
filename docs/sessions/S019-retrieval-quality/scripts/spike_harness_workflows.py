#!/usr/bin/env python3
"""EV-016 harness H0-H9: cache + intent/answer class + graph-shaped workflows.

LangGraph-**schema-compatible** state machines (S0-S8) without adding the
``langgraph`` package - measure workflow value before ADR-006 amend (S019-D27).
Eval/playground only; not ChatRAG prod.

Usage::

  set -a && source .env && set +a
  unset VECINITA_MODAL_OLLAMA_URL
  uv run python docs/sessions/S019-retrieval-quality/scripts/spike_harness_workflows.py
  uv run python .../spike_harness_workflows.py --cells H0,H1,H3 --limit 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict, cast

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
    / "spike-harness-cache.md"
)
_MODEL = "qwen2.5:1.5b-instruct"
_TOP_K = 5

Intent = Literal[
    "faq_lookup",
    "corpus_qa",
    "chitchat",
    "out_of_scope",
    "unsafe",
    "clarify_needed",
]
AnswerClass = Literal[
    "grounded",
    "weak_grounding",
    "refuse",
    "clarify",
    "retry_retrieve",
]
CacheHit = Literal["none", "exact", "semantic", "retrieve"]
CellId = Literal["H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9"]

_CELL_SCHEMA: dict[CellId, str] = {
    "H0": "S0",
    "H1": "S1",
    "H2": "S2",
    "H3": "S3",
    "H4": "S4",
    "H5": "S5",
    "H6": "S6",
    "H7": "S7",
    "H8": "S8",
    "H9": "S3+S1",
}

_CHITCHAT = re.compile(
    r"^\s*(hi|hello|hey|thanks|thank you|hola|gracias|good (morning|afternoon))\b",
    re.IGNORECASE,
)
_UNSAFE = re.compile(r"\b(kill|bomb|weapon|hack into|credit card)\b", re.IGNORECASE)
_OOS = re.compile(
    r"\b(stock price|bitcoin|crypto|nba score|movie times)\b",
    re.IGNORECASE,
)
_REFUSE_PHRASE = re.compile(
    r"\b(i (do not|don't) know|not (enough|sufficient) (info|information|"
    r"context)|cannot answer|no (relevant )?information)\b",
    re.IGNORECASE,
)


class CacheRouterState(TypedDict):
    """S1 — cache lookup then retrieve/synth/store."""

    query: str
    norm_query: str
    cache_hit: CacheHit
    chunks: list[RetrievedChunk]
    answer: str
    llm_calls: int


class IntentRouterState(TypedDict):
    """S3 — intent classify then branch."""

    query: str
    intent: Intent
    route: str
    chunks: list[RetrievedChunk]
    answer: str
    llm_calls: int


class GradeLoopState(TypedDict):
    """S4 — synth then answer-class loop."""

    query: str
    chunks: list[RetrievedChunk]
    draft_answer: str
    answer_class: AnswerClass
    retries: int
    final_answer: str
    llm_calls: int


class DualAgentState(TypedDict):
    """S5 — retriever agent → synthesizer agent."""

    query: str
    retrieve_notes: str
    chunks: list[RetrievedChunk]
    synth_answer: str
    llm_calls: int


class TriadAgentState(TypedDict):
    """S6 — supervisor + retrieve + synth + critic."""

    query: str
    supervisor_plan: str
    chunks: list[RetrievedChunk]
    draft: str
    critique: str
    answer_class: AnswerClass
    loops: int
    final: str
    llm_calls: int


class FanOutState(TypedDict):
    """S7 — multi-query fan-out merge."""

    query: str
    rewrites: list[str]
    per_rewrite_chunks: list[list[RetrievedChunk]]
    merged: list[RetrievedChunk]
    answer: str
    llm_calls: int


class IntentGradeState(TypedDict):
    """S8 — intent then answer class."""

    query: str
    intent: Intent
    route: str
    chunks: list[RetrievedChunk]
    draft: str
    answer_class: AnswerClass
    final: str
    llm_calls: int


@dataclass
class HarnessCaches:
    """Process-local caches (ADR-004: no identity keys)."""

    exact_answers: dict[str, str] = field(default_factory=dict)
    retrieve: dict[str, list[RetrievedChunk]] = field(default_factory=dict)
    embed_vectors: dict[str, list[float]] = field(default_factory=dict)
    semantic_answers: list[tuple[list[float], str]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RowOutcome:
    """Per-row harness result."""

    answer: str
    chunks: list[RetrievedChunk]
    llm_calls: int
    cache_hit: CacheHit
    intent: Intent | None
    answer_class: AnswerClass | None
    schema: str
    extras: dict[str, object]


@dataclass
class Runtime:
    """Shared clients + retrieve pool for one harness run."""

    pool: dict[tuple[str, str], list[RetrievedChunk]]
    synth: ModalHttpLLM
    system_prompt: str
    caches: HarnessCaches
    embed_fn: Callable[[str], list[float]]
    retriever: CorpusPgvectorRetriever
    semantic_threshold: float = 0.92


def _norm_query(q: str) -> str:
    return re.sub(r"\s+", " ", q.strip().lower())


def _pack_p1(chunks: list[RetrievedChunk]) -> str:
    parts: list[str] = []
    for chunk in chunks:
        title = (chunk.title or "").strip() or "(untitled)"
        url = (chunk.url or "").strip() or "(no-url)"
        parts.append(f"Source: {title}\nURL: {url}\n{chunk.text}")
    return "\n\n".join(parts)


def _pack_p1_prefix_stable(chunks: list[RetrievedChunk]) -> str:
    """S2: sort by url then chunk text for stabler prefix across near-dup queries."""
    ordered = sorted(
        chunks,
        key=lambda c: ((c.url or ""), (c.title or ""), c.text[:80]),
    )
    return _pack_p1(ordered)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def classify_intent(question: str) -> Intent:
    """Heuristic intent labels for S3/S8/S9 (no extra LLM)."""
    q = question.strip()
    if len(q) < 8 or (q.endswith("?") and len(q.split()) <= 2):
        return "clarify_needed"
    if _CHITCHAT.search(q):
        return "chitchat"
    if _UNSAFE.search(q):
        return "unsafe"
    if _OOS.search(q):
        return "out_of_scope"
    # FAQ-ish short factual asks — still corpus_qa on golden; tag faq for cache path.
    if len(q.split()) <= 12 and q.endswith("?"):
        return "faq_lookup"
    return "corpus_qa"


def classify_answer(
    *,
    answer: str,
    chunks: list[RetrievedChunk],
) -> AnswerClass:
    """Heuristic answer class for S4/S6/S8."""
    if not chunks:
        return "refuse"
    text = answer.strip()
    if not text or _REFUSE_PHRASE.search(text):
        return "refuse"
    if len(chunks) == 1 and chunks[0].score < 0.35:
        return "weak_grounding"
    if len(text) < 40:
        return "weak_grounding"
    return "grounded"


def _synthesize(rt: Runtime, question: str, chunks: list[RetrievedChunk]) -> str:
    context = _pack_p1(chunks)
    capped = truncate_synthesis_context(context)
    prompt = (
        f"{rt.system_prompt.strip()}\n\nContext:\n{capped}\n\n"
        f"Question: {question.strip()}\n\nAnswer:"
    )
    response = rt.synth.complete(prompt)
    return str(getattr(response, "text", response))


def _synthesize_packed(rt: Runtime, question: str, packed: str) -> str:
    capped = truncate_synthesis_context(packed)
    prompt = (
        f"{rt.system_prompt.strip()}\n\nContext:\n{capped}\n\n"
        f"Question: {question.strip()}\n\nAnswer:"
    )
    response = rt.synth.complete(prompt)
    return str(getattr(response, "text", response))


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


def _rewrites(question: str) -> list[str]:
    """Cheap multi-query variants (no LLM) for S7."""
    q = question.strip()
    variants = [q]
    if "how" in q.lower():
        variants.append(q.replace("How", "What").replace("how", "what"))
    if "?" in q:
        variants.append(q.rstrip("?") + " in Providence RI?")
    # Dedup preserve order
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        n = _norm_query(v)
        if n not in seen:
            seen.add(n)
            out.append(v)
    return out[:3]


def _lookup_semantic(rt: Runtime, question: str) -> str | None:
    vec = rt.embed_fn(question)
    best_score = 0.0
    best_answer: str | None = None
    for cached_vec, answer in rt.caches.semantic_answers:
        score = _cosine(vec, cached_vec)
        if score >= rt.semantic_threshold and score > best_score:
            best_score = score
            best_answer = answer
    return best_answer


def _store_caches(rt: Runtime, question: str, answer: str, chunks: list[RetrievedChunk]) -> None:
    nq = _norm_query(question)
    rt.caches.exact_answers[nq] = answer
    rt.caches.retrieve[nq] = chunks
    vec = rt.embed_fn(question)
    rt.caches.semantic_answers.append((vec, answer))


def run_h0(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S0 baseline."""
    chunks = rt.pool[(row.id, row.locale)][:_TOP_K]
    answer = _synthesize(rt, row.question, chunks)
    return RowOutcome(
        answer=answer,
        chunks=chunks,
        llm_calls=1,
        cache_hit="none",
        intent=None,
        answer_class=None,
        schema="S0",
        extras={},
    )


def run_h1(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S1 cache cascade: exact → semantic → retrieve → generate."""
    state: CacheRouterState = {
        "query": row.question,
        "norm_query": _norm_query(row.question),
        "cache_hit": "none",
        "chunks": [],
        "answer": "",
        "llm_calls": 0,
    }
    nq = state["norm_query"]
    if nq in rt.caches.exact_answers:
        state["cache_hit"] = "exact"
        state["answer"] = rt.caches.exact_answers[nq]
        state["chunks"] = rt.caches.retrieve.get(nq, rt.pool[(row.id, row.locale)][:_TOP_K])
    else:
        semantic = _lookup_semantic(rt, row.question)
        if semantic is not None:
            state["cache_hit"] = "semantic"
            state["answer"] = semantic
            state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
        elif nq in rt.caches.retrieve:
            state["cache_hit"] = "retrieve"
            state["chunks"] = rt.caches.retrieve[nq]
            state["answer"] = _synthesize(rt, row.question, state["chunks"])
            state["llm_calls"] = 1
            _store_caches(rt, row.question, state["answer"], state["chunks"])
        else:
            state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
            state["answer"] = _synthesize(rt, row.question, state["chunks"])
            state["llm_calls"] = 1
            _store_caches(rt, row.question, state["answer"], state["chunks"])
    return RowOutcome(
        answer=state["answer"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit=state["cache_hit"],
        intent=None,
        answer_class=None,
        schema="S1",
        extras={"norm_query": nq},
    )


def run_h2(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S2 prefix-stable packing."""
    chunks = rt.pool[(row.id, row.locale)][:_TOP_K]
    packed = _pack_p1_prefix_stable(chunks)
    answer = _synthesize_packed(rt, row.question, packed)
    return RowOutcome(
        answer=answer,
        chunks=chunks,
        llm_calls=1,
        cache_hit="none",
        intent=None,
        answer_class=None,
        schema="S2",
        extras={"pack": "P1_prefix_stable"},
    )


def run_h3(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S3 intent router."""
    intent = classify_intent(row.question)
    state: IntentRouterState = {
        "query": row.question,
        "intent": intent,
        "route": "rag",
        "chunks": [],
        "answer": "",
        "llm_calls": 0,
    }
    if intent in ("chitchat",):
        state["route"] = "chitchat"
        state["answer"] = (
            "Hello! I can help with community resources in Providence. "
            "What would you like to know?"
        )
    elif intent == "unsafe":
        state["route"] = "refuse"
        state["answer"] = "I cannot help with that request."
    elif intent == "out_of_scope":
        state["route"] = "refuse"
        state["answer"] = (
            "That is outside my community-resources knowledge. "
            "Ask about local clinics, programs, or services."
        )
    elif intent == "clarify_needed":
        state["route"] = "clarify"
        state["answer"] = "Could you clarify which community service or program you mean?"
    elif intent == "faq_lookup":
        state["route"] = "faq"
        nq = _norm_query(row.question)
        if nq in rt.caches.exact_answers:
            state["answer"] = rt.caches.exact_answers[nq]
            state["chunks"] = rt.caches.retrieve.get(nq, [])
        else:
            state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
            state["answer"] = _synthesize(rt, row.question, state["chunks"])
            state["llm_calls"] = 1
            _store_caches(rt, row.question, state["answer"], state["chunks"])
    else:
        state["route"] = "rag"
        state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
        state["answer"] = _synthesize(rt, row.question, state["chunks"])
        state["llm_calls"] = 1
    return RowOutcome(
        answer=state["answer"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit="exact" if state["route"] == "faq" and state["llm_calls"] == 0 else "none",
        intent=intent,
        answer_class=None,
        schema="S3",
        extras={"route": state["route"]},
    )


def run_h4(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S4 grade loop — one retrieve retry on weak grounding."""
    chunks = list(rt.pool[(row.id, row.locale)][:_TOP_K])
    state: GradeLoopState = {
        "query": row.question,
        "chunks": chunks,
        "draft_answer": "",
        "answer_class": "grounded",
        "retries": 0,
        "final_answer": "",
        "llm_calls": 0,
    }
    state["draft_answer"] = _synthesize(rt, row.question, state["chunks"])
    state["llm_calls"] += 1
    state["answer_class"] = classify_answer(
        answer=state["draft_answer"],
        chunks=state["chunks"],
    )
    if state["answer_class"] in ("weak_grounding", "retry_retrieve") and state["retries"] < 1:
        state["retries"] = 1
        # Retry: drop lowest-score chunk, re-retrieve from pool with +2 overflow if any
        wider = rt.pool[(row.id, row.locale)][: _TOP_K + 2]
        state["chunks"] = wider[:_TOP_K] if len(wider) > _TOP_K else wider
        state["draft_answer"] = _synthesize(rt, row.question, state["chunks"])
        state["llm_calls"] += 1
        state["answer_class"] = classify_answer(
            answer=state["draft_answer"],
            chunks=state["chunks"],
        )
    if state["answer_class"] == "refuse":
        state["final_answer"] = (
            "I do not have enough grounded information in the corpus to answer that."
        )
    else:
        state["final_answer"] = state["draft_answer"]
    return RowOutcome(
        answer=state["final_answer"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit="none",
        intent=None,
        answer_class=state["answer_class"],
        schema="S4",
        extras={"retries": state["retries"]},
    )


def run_h5(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S5 dual agents — typed handoff only (same retrieve+synth)."""
    state: DualAgentState = {
        "query": row.question,
        "retrieve_notes": "",
        "chunks": [],
        "synth_answer": "",
        "llm_calls": 0,
    }
    # Retriever agent
    state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
    state["retrieve_notes"] = f"retriever_agent: returned {len(state['chunks'])} chunks"
    # Synthesizer agent
    state["synth_answer"] = _synthesize(rt, row.question, state["chunks"])
    state["llm_calls"] = 1
    return RowOutcome(
        answer=state["synth_answer"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit="none",
        intent=None,
        answer_class=None,
        schema="S5",
        extras={"retrieve_notes": state["retrieve_notes"]},
    )


def run_h6(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S6 triad + critic — one critique loop if weak."""
    state: TriadAgentState = {
        "query": row.question,
        "supervisor_plan": "retrieve→synth→critic",
        "chunks": rt.pool[(row.id, row.locale)][:_TOP_K],
        "draft": "",
        "critique": "",
        "answer_class": "grounded",
        "loops": 0,
        "final": "",
        "llm_calls": 0,
    }
    state["draft"] = _synthesize(rt, row.question, state["chunks"])
    state["llm_calls"] += 1
    state["answer_class"] = classify_answer(answer=state["draft"], chunks=state["chunks"])
    # Critic agent (heuristic + optional short LLM self-check skipped for cost)
    if state["answer_class"] == "weak_grounding" and state["loops"] < 1:
        state["loops"] = 1
        state["critique"] = "critic: weak grounding — regenerate with stricter context"
        # Keep only top-3 by score
        state["chunks"] = sorted(state["chunks"], key=lambda c: c.score, reverse=True)[:3]
        state["draft"] = _synthesize(rt, row.question, state["chunks"])
        state["llm_calls"] += 1
        state["answer_class"] = classify_answer(answer=state["draft"], chunks=state["chunks"])
    if state["answer_class"] == "refuse":
        state["final"] = (
            "I do not have enough grounded information in the corpus to answer that."
        )
    else:
        state["final"] = state["draft"]
    return RowOutcome(
        answer=state["final"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit="none",
        intent=None,
        answer_class=state["answer_class"],
        schema="S6",
        extras={
            "supervisor_plan": state["supervisor_plan"],
            "critique": state["critique"],
            "loops": state["loops"],
        },
    )


def run_h7(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S7 multi-query fan-out."""
    rewrites = _rewrites(row.question)
    state: FanOutState = {
        "query": row.question,
        "rewrites": rewrites,
        "per_rewrite_chunks": [],
        "merged": [],
        "answer": "",
        "llm_calls": 0,
    }
    for rw in rewrites:
        if rw == row.question:
            state["per_rewrite_chunks"].append(rt.pool[(row.id, row.locale)][:_TOP_K])
        else:
            # Live retrieve for rewrite (read-only)
            state["per_rewrite_chunks"].append(rt.retriever.retrieve_chunks(rw)[:_TOP_K])
    state["merged"] = _merge_chunks(state["per_rewrite_chunks"], top_k=_TOP_K)
    state["answer"] = _synthesize(rt, row.question, state["merged"])
    state["llm_calls"] = 1
    return RowOutcome(
        answer=state["answer"],
        chunks=state["merged"],
        llm_calls=state["llm_calls"],
        cache_hit="none",
        intent=None,
        answer_class=None,
        schema="S7",
        extras={"rewrites": rewrites, "n_rewrites": len(rewrites)},
    )


def run_h8(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S8 intent + answer classification."""
    intent = classify_intent(row.question)
    state: IntentGradeState = {
        "query": row.question,
        "intent": intent,
        "route": "rag",
        "chunks": [],
        "draft": "",
        "answer_class": "grounded",
        "final": "",
        "llm_calls": 0,
    }
    if intent in ("chitchat", "unsafe", "out_of_scope", "clarify_needed"):
        # Reuse H3 early exits
        early = run_h3(rt, row)
        early_class: AnswerClass
        if intent == "chitchat":
            early_class = "grounded"
        elif intent == "clarify_needed":
            early_class = "clarify"
        else:
            early_class = "refuse"
        return RowOutcome(
            answer=early.answer,
            chunks=early.chunks,
            llm_calls=early.llm_calls,
            cache_hit=early.cache_hit,
            intent=intent,
            answer_class=early_class,
            schema="S8",
            extras={"route": early.extras.get("route", "early")},
        )
    state["chunks"] = rt.pool[(row.id, row.locale)][:_TOP_K]
    state["draft"] = _synthesize(rt, row.question, state["chunks"])
    state["llm_calls"] = 1
    state["answer_class"] = classify_answer(answer=state["draft"], chunks=state["chunks"])
    if state["answer_class"] == "refuse":
        state["final"] = (
            "I do not have enough grounded information in the corpus to answer that."
        )
    elif state["answer_class"] == "clarify":
        state["final"] = "Could you clarify which program or service you mean?"
    else:
        state["final"] = state["draft"]
    return RowOutcome(
        answer=state["final"],
        chunks=state["chunks"],
        llm_calls=state["llm_calls"],
        cache_hit="none",
        intent=intent,
        answer_class=state["answer_class"],
        schema="S8",
        extras={"route": "rag"},
    )


def run_h9(rt: Runtime, row: GoldenRow) -> RowOutcome:
    """S3+S1 — intent router in front of cache cascade."""
    intent = classify_intent(row.question)
    if intent in ("chitchat", "unsafe", "out_of_scope", "clarify_needed"):
        early = run_h3(rt, row)
        return RowOutcome(
            answer=early.answer,
            chunks=early.chunks,
            llm_calls=early.llm_calls,
            cache_hit=early.cache_hit,
            intent=intent,
            answer_class=None,
            schema="S3+S1",
            extras={"route": early.extras.get("route", "early"), "stacked": True},
        )
    # FAQ / corpus → cache cascade
    cascaded = run_h1(rt, row)
    return RowOutcome(
        answer=cascaded.answer,
        chunks=cascaded.chunks,
        llm_calls=cascaded.llm_calls,
        cache_hit=cascaded.cache_hit,
        intent=intent,
        answer_class=None,
        schema="S3+S1",
        extras={"route": "cache_cascade", "stacked": True},
    )


_RUNNERS: dict[CellId, Callable[[Runtime, GoldenRow], RowOutcome]] = {
    "H0": run_h0,
    "H1": run_h1,
    "H2": run_h2,
    "H3": run_h3,
    "H4": run_h4,
    "H5": run_h5,
    "H6": run_h6,
    "H7": run_h7,
    "H8": run_h8,
    "H9": run_h9,
}


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _p95(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))
    return ordered[idx]


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


def _run_cell(
    *,
    cell_id: CellId,
    rows: list[GoldenRow],
    rt: Runtime,
    judge: LlamaIndexJudgeClient,
) -> dict[str, object]:
    runner = _RUNNERS[cell_id]
    # Fresh caches per cell. H1/H9: warm-pass once so hit-rate reflects replay.
    rt.caches = HarnessCaches()
    if cell_id in ("H1", "H9"):
        print(f"    warm-pass caches for {cell_id}…")
        for row in rows:
            runner(rt, row)

    faiths: list[float | None] = []
    relevancies: list[float | None] = []
    latencies: list[int] = []
    llm_calls_total = 0
    cache_hits = 0
    retrieval_hits = 0
    scored_n = 0
    per_row: list[dict[str, object]] = []
    intent_counts: dict[str, int] = {}
    answer_class_counts: dict[str, int] = {}

    for row in rows:
        t0 = time.monotonic()
        outcome = runner(rt, row)
        latency_ms = int((time.monotonic() - t0) * 1000)
        latencies.append(latency_ms)
        llm_calls_total += outcome.llm_calls
        if outcome.cache_hit != "none":
            cache_hits += 1
        if outcome.intent is not None:
            intent_counts[outcome.intent] = intent_counts.get(outcome.intent, 0) + 1
        if outcome.answer_class is not None:
            answer_class_counts[outcome.answer_class] = (
                answer_class_counts.get(outcome.answer_class, 0) + 1
            )

        urls = [c.url for c in outcome.chunks if c.url]
        context = _pack_p1(outcome.chunks)
        retrieval_pass = score_retrieval_row(row, urls)
        if row.retrieval_expectation in {"hit", "any_of"}:
            scored_n += 1
            retrieval_hits += int(retrieval_pass)

        faith: float | None = None
        relevancy: float | None = None
        try:
            if outcome.answer.strip():
                if (
                    outcome.chunks
                    and row.retrieval_expectation not in {"abstain", "empty"}
                ):
                    faith = judge.faithfulness(
                        question=row.question,
                        answer=outcome.answer,
                        context=context,
                    )
                relevancy = judge.answer_relevancy(
                    question=row.question,
                    answer=outcome.answer,
                    context=context,
                )
        except Exception as exc:  # noqa: BLE001
            print(f"    judge-error {row.id}/{row.locale}: {type(exc).__name__}: {exc}")
            per_row.append(
                {
                    "id": row.id,
                    "locale": row.locale,
                    "error": f"{type(exc).__name__}: {exc}",
                    "latency_ms": latency_ms,
                    "llm_calls": outcome.llm_calls,
                    "cache_hit": outcome.cache_hit,
                    "schema": outcome.schema,
                    "retrieval_pass": retrieval_pass,
                }
            )
            continue

        faiths.append(faith)
        relevancies.append(relevancy)

        per_row.append(
            {
                "id": row.id,
                "locale": row.locale,
                "faithfulness": faith,
                "answer_relevancy": relevancy,
                "retrieval_pass": retrieval_pass,
                "latency_ms": latency_ms,
                "llm_calls": outcome.llm_calls,
                "cache_hit": outcome.cache_hit,
                "intent": outcome.intent,
                "answer_class": outcome.answer_class,
                "schema": outcome.schema,
                "extras": outcome.extras,
                "answer_sha1": hashlib.sha1(  # noqa: S324 — fingerprint only
                    outcome.answer.encode()
                ).hexdigest()[:12],
            }
        )

    n = len(rows) or 1
    return {
        "cell_id": cell_id,
        "schema": _CELL_SCHEMA[cell_id],
        "status": "complete",
        "n_rows": len(rows),
        "retrieval_relevance": (retrieval_hits / scored_n) if scored_n else None,
        "faithfulness": _avg(faiths),
        "answer_relevancy": _avg(relevancies),
        "latency_p50_ms": sorted(latencies)[len(latencies) // 2] if latencies else None,
        "latency_p95_ms": _p95(latencies),
        "llm_calls_total": llm_calls_total,
        "llm_calls_per_row": llm_calls_total / n,
        "cache_hit_rate": cache_hits / n,
        "intent_counts": intent_counts,
        "answer_class_counts": answer_class_counts,
        "rows": per_row,
    }


def main(argv: list[str] | None = None) -> int:
    """Run harness cells H0–H9 under fixed RAG factors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cells",
        default="H0,H1,H2,H3,H4,H5,H6,H7,H8,H9",
        help="Comma-separated cell ids",
    )
    parser.add_argument("--limit", type=int, default=0, help="Max golden rows (0=all)")
    parser.add_argument("--top-k", type=int, default=_TOP_K)
    parser.add_argument("--min-score", type=float, default=0.2)
    parser.add_argument(
        "--model",
        default=_MODEL,
        help="Playground synth+judge model tag (default prod pin)",
    )
    args = parser.parse_args(argv)

    if "ondigitalocean.com" not in os.environ.get("DATABASE_URL", ""):
        print("ERROR: expected staging DATABASE_URL", file=sys.stderr)
        return 1
    assert_no_legacy_ollama_url()

    raw_cells = parse_csv_strs(args.cells)
    cells: list[CellId] = []
    for raw in raw_cells:
        key = raw.strip().upper()
        if key not in _RUNNERS:
            print(f"ERROR: unknown cell {raw!r}", file=sys.stderr)
            return 1
        cells.append(cast("CellId", key))

    rows = list(load_golden_rows(fixture_path=_FIXTURE))
    if args.limit > 0:
        rows = rows[: args.limit]
    print(f"==> harness: cells={cells} rows={len(rows)} model={args.model}")

    embed = EmbeddingClient(timeout=120.0)
    embed_cache: dict[str, list[float]] = {}

    def embed_fn(q: str) -> list[float]:
        if q not in embed_cache:
            embed_cache[q] = _embed_with_retry(embed, q)
        return embed_cache[q]

    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=os.environ["DATABASE_URL"],
        top_k=max(args.top_k, _TOP_K + 2),
        score_threshold=args.min_score,
    )

    print("==> retrieve once (R0 pool)")
    pool: dict[tuple[str, str], list[RetrievedChunk]] = {}
    for row in rows:
        pool[(row.id, row.locale)] = retriever.retrieve_chunks(row.question)
        print(f"    {row.id}/{row.locale}: {len(pool[(row.id, row.locale)])}")

    playground_url = resolve_playground_base_url()
    print(f"==> playground={playground_url}")
    # Judges on prod pin (stable) — same as model sweep; synth on playground.
    judge_client = LlmClient(
        os.environ["VECINITA_MODAL_LLM_URL"],
        timeout=900.0,
        model_id=args.model,
        require_proxy_key=True,
    )
    warm_modal_llm(judge_client)
    judge_llm = ModalHttpLLM(
        client=judge_client,
        max_tokens=128,
        temperature=0.0,
        model_id=args.model,
    )
    judge = LlamaIndexJudgeClient(judge_llm)

    client = make_playground_client(model_id=args.model, timeout=900.0)
    warm_modal_llm(client)
    synth = ModalHttpLLM(
        client=client,
        max_tokens=128,
        temperature=0.0,
        model_id=args.model,
    )

    rt = Runtime(
        pool=pool,
        synth=synth,
        system_prompt=DEFAULT_EVAL_SYSTEM_PROMPT,
        caches=HarnessCaches(),
        embed_fn=embed_fn,
        retriever=retriever,
    )

    results: list[dict[str, object]] = []
    for cell_id in cells:
        print(f"==> cell {cell_id} schema={_CELL_SCHEMA[cell_id]}")
        t0 = time.monotonic()
        try:
            cell = _run_cell(cell_id=cell_id, rows=rows, rt=rt, judge=judge)
            cell["wall_ms"] = int((time.monotonic() - t0) * 1000)
        except Exception as exc:  # noqa: BLE001
            cell = {
                "cell_id": cell_id,
                "schema": _CELL_SCHEMA[cell_id],
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
                f"p95={cell.get('latency_p95_ms')} "
                f"llm/row={cell.get('llm_calls_per_row')} "
                f"cache_hit={cell.get('cache_hit_rate')}"
            )
        results.append(cell)

    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = _OUT_DIR / f"{stamp}_harness-workflows.json"
    payload = {
        "fixture": str(_FIXTURE),
        "decision": "S019-D28",
        "note": (
            "Graph-shaped TypedDict workflows (LangGraph-schema-compatible); "
            "langgraph package not added until ADR-006 amend"
        ),
        "fixed_cell": {
            "pack": "P1",
            "rerank": "R0",
            "top_k": args.top_k,
            "min_retrieval_score": args.min_score,
            "model_id": args.model,
        },
        "playground_url": playground_url,
        "scored_rows": len(retrieval_rows(rows)),
        "cells": results,
        "report": str(_REPORT_MD),
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"==> wrote {out}")
    return 0 if all(c.get("status") == "complete" for c in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
