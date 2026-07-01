"""Deterministic retrieval scoring for golden eval rows."""

from __future__ import annotations

from vecinita_eval.golden import GoldenRow, RetrievalExpectation


def retrieval_rows(rows: list[GoldenRow]) -> list[GoldenRow]:
    """Return rows included in the retrieval relevance aggregate (hit + any_of)."""
    return [row for row in rows if row.retrieval_expectation in {"hit", "any_of"}]


def retrieval_expectation_passes(row: GoldenRow, retrieved_urls: list[str]) -> bool:
    """Return whether retrieval behavior matches the row expectation."""
    if row.retrieval_expectation == "hit":
        return bool(row.expected_doc_url and row.expected_doc_url in retrieved_urls)
    if row.retrieval_expectation == "any_of":
        return any(url in retrieved_urls for url in row.expected_doc_urls)
    if row.retrieval_expectation == "empty":
        return len(retrieved_urls) == 0
    if row.retrieval_expectation == "abstain":
        # Abstain rows are judged on answer behavior; retrieval may be empty or off-topic.
        return True
    msg = f"unsupported retrieval_expectation: {row.retrieval_expectation}"
    raise ValueError(msg)


def score_retrieval_row(row: GoldenRow, retrieved_urls: list[str]) -> bool:
    """Score one row for retrieval pass/fail."""
    return retrieval_expectation_passes(row, retrieved_urls)


def aggregate_retrieval_relevance(
    rows: list[GoldenRow],
    *,
    passes: dict[tuple[str, str], bool],
) -> float:
    """Compute aggregate retrieval relevance over hit + any_of rows only."""
    scored = retrieval_rows(rows)
    if not scored:
        return 1.0
    hits = sum(1 for row in scored if passes.get((row.id, row.locale), False))
    return hits / len(scored)


def is_scored_retrieval_expectation(expectation: RetrievalExpectation) -> bool:
    """Return True when the expectation participates in the ≥80% aggregate."""
    return expectation in {"hit", "any_of"}
