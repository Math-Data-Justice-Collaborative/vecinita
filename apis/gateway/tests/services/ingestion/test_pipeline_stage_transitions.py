"""Normative pipeline stage transitions (data-model § Page ingestion job)."""

from __future__ import annotations

import pytest

from src.services.ingestion import pipeline_stage as ps

pytestmark = pytest.mark.unit


def test_persisting_to_partial_allowed() -> None:
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_PERSISTING, ps.PIPELINE_STAGE_PARTIAL)


def test_happy_path_chain_allowed() -> None:
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_QUEUED, ps.PIPELINE_STAGE_SCRAPING)
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_SCRAPING, ps.PIPELINE_STAGE_CHUNKING)
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_CHUNKING, ps.PIPELINE_STAGE_LLM)
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_LLM, ps.PIPELINE_STAGE_EMBEDDING)
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_EMBEDDING, ps.PIPELINE_STAGE_PERSISTING)
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_PERSISTING, ps.PIPELINE_STAGE_SUCCEEDED)


@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (ps.PIPELINE_STAGE_SCRAPING, ps.PIPELINE_STAGE_NO_INDEXABLE),
        (ps.PIPELINE_STAGE_SCRAPING, ps.PIPELINE_STAGE_SCRAPE_FAILED),
    ],
)
def test_scrape_outcomes_allowed(src: str, dst: str) -> None:
    ps.validate_pipeline_stage_transition(src, dst)


def test_duplicate_skipped_from_queued_allowed() -> None:
    ps.validate_pipeline_stage_transition(
        ps.PIPELINE_STAGE_QUEUED, ps.PIPELINE_STAGE_DUPLICATE_SKIPPED
    )


def test_idempotent_same_stage_allowed() -> None:
    ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_CHUNKING, ps.PIPELINE_STAGE_CHUNKING)


@pytest.mark.parametrize(
    ("src", "dst"),
    [
        (ps.PIPELINE_STAGE_QUEUED, ps.PIPELINE_STAGE_EMBEDDING),
        (ps.PIPELINE_STAGE_SCRAPING, ps.PIPELINE_STAGE_EMBEDDING),
        (ps.PIPELINE_STAGE_CHUNKING, ps.PIPELINE_STAGE_SUCCEEDED),
        (ps.PIPELINE_STAGE_LLM, ps.PIPELINE_STAGE_SCRAPING),
    ],
)
def test_forbidden_skip_or_regress_raises(src: str, dst: str) -> None:
    with pytest.raises(ps.PipelineStageTransitionError):
        ps.validate_pipeline_stage_transition(src, dst)


def test_terminal_locked() -> None:
    with pytest.raises(ps.PipelineStageTransitionError):
        ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_SUCCEEDED, ps.PIPELINE_STAGE_QUEUED)


def test_partial_is_terminal_for_lock() -> None:
    assert ps.is_terminal_pipeline_stage(ps.PIPELINE_STAGE_PARTIAL) is True
    with pytest.raises(ps.PipelineStageTransitionError):
        ps.validate_pipeline_stage_transition(ps.PIPELINE_STAGE_PARTIAL, ps.PIPELINE_STAGE_LLM)
