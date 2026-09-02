"""TC-320-01 companion: answer_path allow-list (F85)."""

from __future__ import annotations

import pytest
from vecinita_shared_schemas.answer_path import UnknownAnswerPathError, validate_answer_path


def test_validate_answer_path_accepts_allow_list() -> None:
    """faq_bypass and rag_llm are the only valid answer_path values."""
    assert validate_answer_path("faq_bypass") == "faq_bypass"
    assert validate_answer_path("rag_llm") == "rag_llm"


def test_validate_answer_path_rejects_cold_kind_and_prompts() -> None:
    """Do not overload cold_kind or accept prompt-like keys as paths."""
    with pytest.raises(UnknownAnswerPathError):
        _ = validate_answer_path("snapshot_restore")
    with pytest.raises(UnknownAnswerPathError):
        _ = validate_answer_path("warm")
    with pytest.raises(UnknownAnswerPathError):
        _ = validate_answer_path({"question": "x"})
