"""Orchestrate golden-set eval runs through the RAG pipeline."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from vecinita_rag.engine import answer_without_context, synthesize_with_llm
from vecinita_rag.language import detect_query_language
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_rag.types import RagAnswer, RetrievedChunk
from vecinita_shared_schemas.eval_config import EvalConfig

from vecinita_eval.criteria import (
    EvalCriterionDef,
    aggregate_custom_scores,
    score_custom_criteria,
)
from vecinita_eval.golden import GoldenLocale, GoldenRow, load_golden_rows
from vecinita_eval.groundedness import GroundednessScorer, LlamaIndexFaithfulnessScorer
from vecinita_eval.retrieval import (
    aggregate_retrieval_relevance,
    retrieval_expectation_passes,
    score_retrieval_row,
)
from vecinita_eval.sandbox import synthesize_with_system_prompt

if TYPE_CHECKING:
    from llama_index.core.llms import LLM

    from vecinita_eval.judges import JudgeClient

EmbedFn = Callable[[str], list[float]]


@dataclass(frozen=True, slots=True)
class RowMetrics:
    """Per-row eval metrics."""

    retrieval_pass: bool
    faithfulness: float | None
    answer_relevancy: float | None
    latency_ms: int
    custom_scores: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class RowResult:
    """Full result for one golden row."""

    row: GoldenRow
    retrieved_urls: list[str]
    answer: str
    metrics: RowMetrics


@dataclass(frozen=True, slots=True)
class EvalSummary:
    """Aggregate metrics for a golden-set run."""

    retrieval_relevance: float
    faithfulness: float | None
    answer_relevancy: float | None
    latency_p95_ms: int
    custom_scores: dict[str, float] | None = None


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[index]


def _aggregate_optional(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _answer_for_row(
    *,
    row: GoldenRow,
    chunks: list[RetrievedChunk],
    llm: LLM | None,
    system_prompt: str | None = None,
) -> RagAnswer:
    if not chunks:
        return answer_without_context(row.question)
    if llm is None:
        return answer_without_context(row.question)
    if system_prompt is not None:
        return synthesize_with_system_prompt(
            row.question,
            chunks,
            llm,
            system_prompt=system_prompt,
        )
    return synthesize_with_llm(row.question, chunks, llm)


def _adhoc_golden_row(question: str) -> GoldenRow:
    locale = cast("GoldenLocale", detect_query_language(question))
    return GoldenRow(
        id="adhoc",
        locale=locale,
        domain="community",
        question=question,
        retrieval_expectation="hit",
        required_facts=("adhoc",),
    )


def _abstain_answer_ok(answer: str) -> bool:
    lowered = answer.lower()
    no_info_markers = (
        "not available",
        "no information",
        "don't have",
        "do not have",
        "cannot find",
        "can't find",
        "no relevant",
        "not in the corpus",
        "no tengo",
        "no disponible",
        "no encuentro",
    )
    phone_markers = ("@", "555-", "555 ", "phone number is", "call me at")
    if any(marker in lowered for marker in phone_markers):
        return False
    return any(marker in lowered for marker in no_info_markers)


def _evaluate_rows(  # noqa: PLR0913, C901, PLR0912
    *,
    rows: list[GoldenRow],
    embed_fn: EmbedFn,
    database_url: str,
    judge: JudgeClient | None,
    groundedness: GroundednessScorer | None,
    llm: LLM | None,
    retriever_top_k: int,
    score_threshold: float,
    criteria: list[EvalCriterionDef],
    system_prompt: str | None,
    adhoc: bool,
) -> tuple[list[RowResult], EvalSummary]:
    retriever = CorpusPgvectorRetriever(
        embed_fn=embed_fn,
        database_url=database_url,
        top_k=retriever_top_k,
        score_threshold=score_threshold,
    )
    scorer = groundedness
    if scorer is None and judge is not None and not hasattr(judge, "faithfulness"):
        scorer = LlamaIndexFaithfulnessScorer(judge)

    results: list[RowResult] = []
    retrieval_passes: dict[tuple[str, str], bool] = {}
    latencies: list[int] = []
    custom_per_row: list[dict[str, float]] = []

    for row in rows:
        start = time.monotonic()
        chunks = retriever.retrieve_chunks(row.question)
        retrieved_urls = [chunk.url for chunk in chunks if chunk.url]
        rag_answer = _answer_for_row(
            row=row,
            chunks=chunks,
            llm=llm,
            system_prompt=system_prompt,
        )
        answer = rag_answer.answer
        context = "\n\n".join(chunk.text for chunk in chunks)

        if adhoc:
            retrieval_pass = bool(retrieved_urls)
        else:
            retrieval_pass = score_retrieval_row(row, retrieved_urls)
            retrieval_passes[(row.id, row.locale)] = retrieval_pass

            if row.retrieval_expectation == "abstain":
                retrieval_pass = _abstain_answer_ok(answer)
                retrieval_passes[(row.id, row.locale)] = retrieval_pass
            elif row.retrieval_expectation == "empty":
                retrieval_pass = len(retrieved_urls) == 0 and _abstain_answer_ok(answer)
                retrieval_passes[(row.id, row.locale)] = retrieval_pass

        faithfulness: float | None = None
        answer_relevancy: float | None = None

        if judge is not None and answer.strip():
            if chunks and (adhoc or row.retrieval_expectation not in {"abstain", "empty"}):
                if scorer is not None:
                    faithfulness = scorer.score(row=row, answer=answer, context=context)
                elif hasattr(judge, "faithfulness"):
                    faithfulness = judge.faithfulness(  # pyright: ignore[reportUnknownMemberType]
                        question=row.question,
                        answer=answer,
                        context=context,
                    )
            answer_relevancy = judge.answer_relevancy(  # pyright: ignore[reportUnknownMemberType]
                question=row.question,
                answer=answer,
                context=context,
            )

        custom_scores = score_custom_criteria(
            judge=judge,
            question=row.question,
            answer=answer,
            context=context,
            criteria=criteria,
        )
        if custom_scores:
            custom_per_row.append(custom_scores)

        latency_ms = int((time.monotonic() - start) * 1000)
        latencies.append(latency_ms)
        results.append(
            RowResult(
                row=row,
                retrieved_urls=retrieved_urls,
                answer=answer,
                metrics=RowMetrics(
                    retrieval_pass=retrieval_pass,
                    faithfulness=faithfulness,
                    answer_relevancy=answer_relevancy,
                    latency_ms=latency_ms,
                    custom_scores=custom_scores or None,
                ),
            )
        )

    if adhoc:
        retrieval_relevance = 1.0
    else:
        retrieval_relevance = aggregate_retrieval_relevance(rows, passes=retrieval_passes)

    summary = EvalSummary(
        retrieval_relevance=retrieval_relevance,
        faithfulness=_aggregate_optional([r.metrics.faithfulness for r in results]),
        answer_relevancy=_aggregate_optional([r.metrics.answer_relevancy for r in results]),
        latency_p95_ms=_percentile(latencies, 95.0),
        custom_scores=aggregate_custom_scores(custom_per_row) or None,
    )
    return results, summary


def run_golden_eval(  # noqa: PLR0913
    *,
    embed_fn: EmbedFn,
    database_url: str,
    judge: JudgeClient | None = None,
    groundedness: GroundednessScorer | None = None,
    llm: LLM | None = None,
    fixture_path: str | Path | None = None,
    top_k: int = 5,
    criteria: list[EvalCriterionDef] | None = None,
    config: EvalConfig | None = None,
) -> tuple[list[RowResult], EvalSummary]:
    """Execute the golden set and return per-row results + aggregates."""
    path = Path(fixture_path) if fixture_path is not None else None
    rows = load_golden_rows(fixture_path=path)
    retriever_top_k = config.top_k if config is not None else top_k
    score_threshold = config.min_retrieval_score if config is not None else 0.5
    system_prompt = config.system_prompt if config is not None else None
    return _evaluate_rows(
        rows=rows,
        embed_fn=embed_fn,
        database_url=database_url,
        judge=judge,
        groundedness=groundedness,
        llm=llm,
        retriever_top_k=retriever_top_k,
        score_threshold=score_threshold,
        criteria=criteria or [],
        system_prompt=system_prompt,
        adhoc=False,
    )


def run_adhoc_eval(  # noqa: PLR0913
    *,
    embed_fn: EmbedFn,
    database_url: str,
    question: str,
    judge: JudgeClient | None = None,
    groundedness: GroundednessScorer | None = None,
    llm: LLM | None = None,
    criteria: list[EvalCriterionDef] | None = None,
    config: EvalConfig | None = None,
) -> tuple[list[RowResult], EvalSummary]:
    """Execute one ad-hoc playground question through sandbox RAG + judge."""
    resolved = config or EvalConfig()
    row = _adhoc_golden_row(question)
    return _evaluate_rows(
        rows=[row],
        embed_fn=embed_fn,
        database_url=database_url,
        judge=judge,
        groundedness=groundedness,
        llm=llm,
        retriever_top_k=resolved.top_k,
        score_threshold=resolved.min_retrieval_score,
        criteria=criteria or [],
        system_prompt=resolved.system_prompt,
        adhoc=True,
    )


def edge_case_assertions(results: list[RowResult]) -> dict[str, bool]:
    """Return pass/fail map for TC-113 edge rows."""
    by_id = {result.row.id: result for result in results}
    checks: dict[str, bool] = {}
    abstain = by_id.get("edge-abstain-mayor-phone")
    if abstain is not None:
        checks["edge-abstain-mayor-phone"] = _abstain_answer_ok(abstain.answer)
    ambiguous = by_id.get("edge-ambiguous-housing")
    if ambiguous is not None:
        checks["edge-ambiguous-housing"] = retrieval_expectation_passes(
            ambiguous.row,
            ambiguous.retrieved_urls,
        )
    empty = by_id.get("edge-empty-quantum")
    if empty is not None:
        checks["edge-empty-quantum"] = len(empty.retrieved_urls) == 0 and _abstain_answer_ok(
            empty.answer
        )
    return checks
