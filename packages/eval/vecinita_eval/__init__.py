"""Golden-set RAG evaluation harness (F36, EV-008)."""

from vecinita_eval.golden import GoldenRow, load_golden_rows
from vecinita_eval.retrieval import (
    aggregate_retrieval_relevance,
    retrieval_expectation_passes,
    score_retrieval_row,
)

__all__ = [
    "GoldenRow",
    "aggregate_retrieval_relevance",
    "load_golden_rows",
    "retrieval_expectation_passes",
    "score_retrieval_row",
]
