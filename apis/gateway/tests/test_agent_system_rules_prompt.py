"""Regression checks for agent system-rules prompt content."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

RULES_PATH = Path(__file__).resolve().parents[1] / "src/agent/data/system_rules.md"


def test_system_rules_cover_summary_and_vague_requests() -> None:
    content = RULES_PATH.read_text(encoding="utf-8")

    assert '"summarize this" or "what is this"' in content
    assert "return a concise summary in 3 bullet points" in content
    assert "prefer clarification over guessing" in content
