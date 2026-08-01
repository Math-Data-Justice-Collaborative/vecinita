"""S019-D34: staging golden must cover enough Spanish hit rows for ES metrics."""

from __future__ import annotations

from pathlib import Path

from vecinita_eval.golden import load_golden_rows

_STAGING = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "eval" / "qa_pairs_staging.json"
)


def test_staging_golden_has_at_least_six_scored_es_hit_rows() -> None:
    """Expanded ES golden supports locale breakdown beyond n=2."""
    rows = load_golden_rows(fixture_path=_STAGING)
    es_hits = [row for row in rows if row.locale == "es" and row.retrieval_expectation == "hit"]
    assert len(es_hits) >= 6
    assert all(row.expected_doc_url for row in es_hits)
    assert all(
        "/es/" in (row.expected_doc_url or "") or row.id.endswith("intro") for row in es_hits
    )
