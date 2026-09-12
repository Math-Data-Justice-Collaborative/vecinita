"""BUG-2026-09-09: food assistance + Providence must not waste H7 rewrite slots."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_rag.multi_query import heuristic_rewrites, multi_query_retrieve
from vecinita_rag.types import RetrievedChunk

pytestmark = pytest.mark.unit


def test_bug_2026_09_09_en_providence_food_assistance_gets_pantry_synonym() -> None:
    """Providence + food assistance must fan out to pantry lexicon, not duplicate location."""
    question = "Where can I get food assistance in Providence?"
    variants = heuristic_rewrites(question, locale="en")
    joined = " ".join(variants).lower()
    assert "in providence ri?" not in joined
    assert "food pantry providence" in joined


def test_bug_2026_09_09_synonym_retrieve_recovers_pantry_hits() -> None:
    """Empty primary retrieve still merges pantry hits from the synonym variant."""
    pantry = RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        text="City of Providence food pantry hours",
        score=0.88,
        title="Food Pantries",
        url="https://example.org/pantries",
        language="en",
    )

    def retrieve_fn(q: str) -> list[RetrievedChunk]:
        if "food pantry" in q.lower() or "food bank" in q.lower():
            return [pantry]
        return []

    hits = multi_query_retrieve(
        "Where can I get food assistance in Providence?",
        locale="en",
        top_k=3,
        retrieve_fn=retrieve_fn,
        enabled=True,
        count=3,
    )
    assert hits == [pantry]
