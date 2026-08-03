"""Unit tests for RAG package constants (TC-193 / F50)."""

from __future__ import annotations

from vecinita_rag.constants import DEFAULT_TOP_K, MAX_TOP_K, MIN_TOP_K

_EXPECTED_DEFAULT_TOP_K = 8


def test_default_top_k_is_eight() -> None:
    """TC-193 / AC-RQ8: packages/rag DEFAULT_TOP_K is 8 (F50 / #158)."""
    assert DEFAULT_TOP_K == _EXPECTED_DEFAULT_TOP_K
    assert MIN_TOP_K <= DEFAULT_TOP_K <= MAX_TOP_K
