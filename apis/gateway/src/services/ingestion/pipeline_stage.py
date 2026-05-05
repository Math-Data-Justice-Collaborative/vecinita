"""Normative pipeline stage transitions for queued page ingestion.

v1 uses a **Postgres-backed durable queue**: job rows (and related tables) are the source of
truth for queue position and lifecycle. Do **not** introduce a separate message broker for
stage bookkeeping unless a later spec explicitly adds one (see ``research.md`` Decision 5).

Stage strings follow ``specs/012-queued-page-ingestion-pipeline/data-model.md`` § Page
ingestion job. ``scraping_jobs.status`` may still carry legacy worker labels (e.g.
``crawling``); map or mirror those at persistence boundaries when wiring metadata.
"""

from __future__ import annotations

# Normative fine-grained stages (data-model § State transitions).
PIPELINE_STAGE_QUEUED = "queued"
PIPELINE_STAGE_SCRAPING = "scraping"
PIPELINE_STAGE_CHUNKING = "chunking"
PIPELINE_STAGE_LLM = "llm"
PIPELINE_STAGE_EMBEDDING = "embedding"
PIPELINE_STAGE_PERSISTING = "persisting"
PIPELINE_STAGE_SUCCEEDED = "succeeded"
PIPELINE_STAGE_FAILED = "failed"
PIPELINE_STAGE_PARTIAL = "partial"
PIPELINE_STAGE_NO_INDEXABLE = "no_indexable_content"
PIPELINE_STAGE_SCRAPE_FAILED = "scrape_failed"
PIPELINE_STAGE_DUPLICATE_SKIPPED = "duplicate_skipped"

TERMINAL_PIPELINE_STAGES: frozenset[str] = frozenset(
    {
        PIPELINE_STAGE_SUCCEEDED,
        PIPELINE_STAGE_FAILED,
        PIPELINE_STAGE_PARTIAL,
        PIPELINE_STAGE_NO_INDEXABLE,
        PIPELINE_STAGE_SCRAPE_FAILED,
        PIPELINE_STAGE_DUPLICATE_SKIPPED,
    }
)

# Allowed directed edges (monotonic happy path + explicit branches).
_ALLOWED_FROM: dict[str, frozenset[str]] = {
    PIPELINE_STAGE_QUEUED: frozenset(
        {PIPELINE_STAGE_SCRAPING, PIPELINE_STAGE_DUPLICATE_SKIPPED, PIPELINE_STAGE_FAILED}
    ),
    PIPELINE_STAGE_SCRAPING: frozenset(
        {
            PIPELINE_STAGE_CHUNKING,
            PIPELINE_STAGE_NO_INDEXABLE,
            PIPELINE_STAGE_SCRAPE_FAILED,
            PIPELINE_STAGE_FAILED,
        }
    ),
    PIPELINE_STAGE_CHUNKING: frozenset({PIPELINE_STAGE_LLM, PIPELINE_STAGE_FAILED}),
    PIPELINE_STAGE_LLM: frozenset({PIPELINE_STAGE_EMBEDDING, PIPELINE_STAGE_FAILED}),
    PIPELINE_STAGE_EMBEDDING: frozenset({PIPELINE_STAGE_PERSISTING, PIPELINE_STAGE_FAILED}),
    PIPELINE_STAGE_PERSISTING: frozenset(
        {PIPELINE_STAGE_SUCCEEDED, PIPELINE_STAGE_PARTIAL, PIPELINE_STAGE_FAILED}
    ),
}


class PipelineStageTransitionError(ValueError):
    """Raised when a pipeline stage transition violates the normative state machine."""


def normalize_pipeline_stage(stage: str) -> str:
    return stage.strip().lower()


def is_terminal_pipeline_stage(stage: str) -> bool:
    return normalize_pipeline_stage(stage) in TERMINAL_PIPELINE_STAGES


def validate_pipeline_stage_transition(before: str, after: str) -> None:
    """Raise ``PipelineStageTransitionError`` if ``after`` is not allowed from ``before``.

    Idempotent no-op: ``before == after`` is always allowed (duplicate status posts).
    """
    b = normalize_pipeline_stage(before)
    a = normalize_pipeline_stage(after)
    if b == a:
        return
    if b in TERMINAL_PIPELINE_STAGES:
        raise PipelineStageTransitionError(
            f"cannot transition from terminal pipeline stage {b!r} to {a!r}"
        )
    allowed = _ALLOWED_FROM.get(b)
    if allowed is None:
        raise PipelineStageTransitionError(f"unknown pipeline stage {b!r}")
    if a not in allowed:
        raise PipelineStageTransitionError(f"transition {b!r} -> {a!r} is not allowed")


# Short machine codes for operator surfaces / FR-014 mapping (extend with US2 tasks).
ERROR_CATEGORY_TRANSIENT = "transient"
ERROR_CATEGORY_PERMANENT = "permanent"
ERROR_CATEGORY_POLICY = "policy_blocked"
ERROR_CATEGORY_CONFIG = "configuration"
