"""T103.2 — JobOptions chunk_overlap_tokens validation (F49 / TC-192)."""

from __future__ import annotations

from typing import Final

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import JobOptions

_DEFAULT_OVERLAP: Final[int] = 32


def test_job_options_accepts_overlap_below_size() -> None:
    """Overlap strictly less than size is valid."""
    options = JobOptions.model_validate(
        {"chunk_size_tokens": 256, "chunk_overlap_tokens": _DEFAULT_OVERLAP}
    )
    assert options.chunk_overlap_tokens == _DEFAULT_OVERLAP


def test_job_options_rejects_overlap_equal_to_size() -> None:
    """TC-192: overlap >= size is rejected (AC-IR6)."""
    with pytest.raises(ValidationError, match="chunk_overlap_tokens"):
        JobOptions.model_validate({"chunk_size_tokens": 256, "chunk_overlap_tokens": 256})


def test_job_options_rejects_overlap_against_default_size_when_size_omitted() -> None:
    """When size omitted, overlap is checked against default size 256."""
    with pytest.raises(ValidationError, match="chunk_overlap_tokens"):
        JobOptions.model_validate({"chunk_overlap_tokens": 256})
