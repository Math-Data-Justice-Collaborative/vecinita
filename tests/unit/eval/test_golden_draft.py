"""Unit tests for golden example drafting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from vecinita_eval.golden_draft import (
    append_golden_rows,
    build_golden_row,
    parse_golden_draft,
)

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit


def test_build_golden_row_requires_url_for_hit() -> None:
    """Hit expectation without expected_doc_url raises."""
    with pytest.raises(ValueError, match="expected_doc_url"):
        build_golden_row(
            case_id="x",
            locale="en",
            domain="community",
            question="q",
            retrieval_expectation="hit",
            required_facts=["f"],
        )


def test_parse_and_append_golden_draft(tmp_path: Path) -> None:
    """Draft JSON appends into a fixture file without colliding ids."""
    fixture = tmp_path / "qa_pairs.json"
    rows = parse_golden_draft(
        {
            "id": "community-new-case",
            "locale": "en",
            "domain": "community",
            "question": "Where is bilingual story time?",
            "expected_doc_url": "fixture://corpus/en/community-resources.md",
            "retrieval_expectation": "hit",
            "required_facts": ["Bilingual story time on weekends"],
        }
    )
    merged = append_golden_rows(fixture_path=fixture, new_rows=rows)
    assert len(merged) == 1
    again = parse_golden_draft(
        [
            {
                "id": "community-new-case",
                "locale": "es",
                "domain": "community",
                "question": "¿Dónde hay cuentacuentos bilingüe?",
                "expected_doc_url": "fixture://corpus/es/recursos-comunitarios.md",
                "retrieval_expectation": "hit",
                "required_facts": ["Cuentacuentos bilingüe los fines de semana"],
            }
        ]
    )
    merged2 = append_golden_rows(fixture_path=fixture, new_rows=again)
    expected_rows = 2
    assert len(merged2) == expected_rows
    with pytest.raises(ValueError, match="already exist"):
        append_golden_rows(fixture_path=fixture, new_rows=again)
