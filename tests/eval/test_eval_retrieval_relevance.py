"""T59.5 / TC-111: ≥80% retrieval relevance on hit + any_of golden rows (F36)."""

from __future__ import annotations

import pytest
from vecinita_eval.golden import load_golden_rows
from vecinita_eval.retrieval import retrieval_rows, score_retrieval_row
from vecinita_eval.runner import run_golden_eval
from vecinita_rag.retriever import CorpusPgvectorRetriever

from tests.eval.conftest import eval_embed_fn

pytestmark = pytest.mark.integration

_RELEVANCE_THRESHOLD = 0.8


def test_eval_retrieval_relevance_at_least_eighty_percent(eval_db: str) -> None:
    """TC-111: retrieval relevance over hit + any_of rows meets the 80% threshold."""
    rows = load_golden_rows()
    scored_rows = retrieval_rows(rows)
    assert scored_rows, "golden fixture must contain hit/any_of rows"

    retriever = CorpusPgvectorRetriever(
        embed_fn=eval_embed_fn,
        database_url=eval_db,
        top_k=5,
    )

    hits = 0
    for row in scored_rows:
        chunks = retriever.retrieve_chunks(row.question)
        urls = [chunk.url for chunk in chunks if chunk.url]
        if score_retrieval_row(row, urls):
            hits += 1

    rate = hits / len(scored_rows)
    assert rate >= _RELEVANCE_THRESHOLD, (
        f"retrieval relevance {rate:.0%} below {_RELEVANCE_THRESHOLD:.0%} "
        f"({hits}/{len(scored_rows)} scored rows passed)"
    )


def test_eval_runner_aggregate_matches_retrieval_scorer(eval_db: str) -> None:
    """Runner aggregate retrieval relevance aligns with per-row scoring."""
    _results, summary = run_golden_eval(
        embed_fn=eval_embed_fn,
        database_url=eval_db,
        judge=None,
        llm=None,
    )
    assert summary.retrieval_relevance >= _RELEVANCE_THRESHOLD
