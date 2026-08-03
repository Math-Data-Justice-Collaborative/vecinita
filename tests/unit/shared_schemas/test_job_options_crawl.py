"""T109.4 — JobOptions crawl fields (F60 / api-contract)."""

from __future__ import annotations

from typing import Final

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import JobOptions

_DEFAULT_MAX_DEPTH: Final[int] = 2
_DEFAULT_MAX_PAGES: Final[int] = 25
_CUSTOM_MAX_DEPTH: Final[int] = 1
_CUSTOM_MAX_PAGES: Final[int] = 10


def test_job_options_crawl_defaults() -> None:
    """Crawl options are additive with crawl=false and depth/page defaults."""
    options = JobOptions.model_validate({})
    assert options.crawl is False
    assert options.max_depth == _DEFAULT_MAX_DEPTH
    assert options.max_pages == _DEFAULT_MAX_PAGES
    assert options.crawl_scope == "same_domain"


def test_job_options_accepts_crawl_true_with_limits() -> None:
    """POST /jobs may set crawl=true plus depth/page/scope (AC-SC7)."""
    options = JobOptions.model_validate(
        {
            "crawl": True,
            "max_depth": _CUSTOM_MAX_DEPTH,
            "max_pages": _CUSTOM_MAX_PAGES,
            "crawl_scope": "path_prefix",
        }
    )
    assert options.crawl is True
    assert options.max_depth == _CUSTOM_MAX_DEPTH
    assert options.max_pages == _CUSTOM_MAX_PAGES
    assert options.crawl_scope == "path_prefix"


def test_job_options_rejects_invalid_crawl_scope() -> None:
    """crawl_scope must be same_domain or path_prefix."""
    with pytest.raises(ValidationError, match="crawl_scope"):
        JobOptions.model_validate({"crawl_scope": "cross_domain"})


def test_job_options_rejects_non_positive_max_pages() -> None:
    """max_pages must be >= 1."""
    with pytest.raises(ValidationError):
        JobOptions.model_validate({"max_pages": 0})


def test_job_options_rejects_negative_max_depth() -> None:
    """max_depth must be >= 0."""
    with pytest.raises(ValidationError):
        JobOptions.model_validate({"max_depth": -1})
