"""Admin-defined eval criteria CRUD (ADR-034)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import text
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_str,
    row_str_optional,
    row_uuid,
)
from vecinita_shared_schemas.internal_write import (
    EvalCriterionCreateRequest,
    EvalCriterionListResponse,
    EvalCriterionResponse,
    EvalCriterionUpdateRequest,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sqlalchemy.engine import Engine


def list_eval_criteria(engine: Engine) -> EvalCriterionListResponse:
    """Return all eval criteria ordered by slug."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, slug, label, description, scorer_type, rubric,
                           enabled, created_at, updated_at
                    FROM eval_criteria
                    ORDER BY slug ASC
                    """
                )
            )
            .mappings()
            .all()
        )
    return EvalCriterionListResponse(items=[_criterion_from_row(mapping_row(row)) for row in rows])


def create_eval_criterion(
    engine: Engine,
    *,
    body: EvalCriterionCreateRequest,
) -> EvalCriterionResponse:
    """Insert a new eval criterion."""
    criterion_id = uuid4()
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO eval_criteria (
                    id, slug, label, description, scorer_type, rubric, enabled,
                    created_at, updated_at
                )
                VALUES (
                    :id, :slug, :label, :description, :scorer_type, :rubric, :enabled,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": criterion_id,
                "slug": body.slug,
                "label": body.label,
                "description": body.description,
                "scorer_type": body.scorer_type,
                "rubric": body.rubric,
                "enabled": body.enabled,
                "created_at": now,
                "updated_at": now,
            },
        )
    return EvalCriterionResponse(
        criterion_id=criterion_id,
        slug=body.slug,
        label=body.label,
        description=body.description,
        scorer_type=body.scorer_type,
        rubric=body.rubric,
        enabled=body.enabled,
        created_at=now,
        updated_at=now,
    )


def update_eval_criterion(
    engine: Engine,
    *,
    criterion_id: UUID,
    body: EvalCriterionUpdateRequest,
) -> EvalCriterionResponse | None:
    """Patch one eval criterion; returns None when missing."""
    existing = get_eval_criterion(engine, criterion_id=criterion_id)
    if existing is None:
        return None
    label = body.label if body.label is not None else existing.label
    description = body.description if body.description is not None else existing.description
    rubric = body.rubric if body.rubric is not None else existing.rubric
    enabled = body.enabled if body.enabled is not None else existing.enabled
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE eval_criteria
                SET label = :label,
                    description = :description,
                    rubric = :rubric,
                    enabled = :enabled,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": criterion_id,
                "label": label,
                "description": description,
                "rubric": rubric,
                "enabled": enabled,
                "updated_at": now,
            },
        )
    return EvalCriterionResponse(
        criterion_id=criterion_id,
        slug=existing.slug,
        label=label,
        description=description,
        scorer_type=existing.scorer_type,
        rubric=rubric,
        enabled=enabled,
        created_at=existing.created_at,
        updated_at=now,
    )


def get_eval_criterion(
    engine: Engine,
    *,
    criterion_id: UUID,
) -> EvalCriterionResponse | None:
    """Fetch one criterion by id."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT id, slug, label, description, scorer_type, rubric,
                           enabled, created_at, updated_at
                    FROM eval_criteria WHERE id = :id
                    """
                ),
                {"id": criterion_id},
            )
            .mappings()
            .first()
        )
    if row is None:
        return None
    return _criterion_from_row(mapping_row(row))


def list_enabled_criteria(engine: Engine) -> list[EvalCriterionResponse]:
    """Return enabled criteria for the eval runner."""
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                    SELECT id, slug, label, description, scorer_type, rubric,
                           enabled, created_at, updated_at
                    FROM eval_criteria
                    WHERE enabled = true
                    ORDER BY slug ASC
                    """
                )
            )
            .mappings()
            .all()
        )
    return [_criterion_from_row(mapping_row(row)) for row in rows]


def _criterion_from_row(row: Mapping[str, object]) -> EvalCriterionResponse:
    scorer = row_str(row, "scorer_type")
    if scorer != "llm_rubric":
        msg = f"unsupported scorer_type: {scorer!r}"
        raise ValueError(msg)
    created = row.get("created_at")
    updated = row.get("updated_at")
    if not isinstance(created, datetime):
        created = datetime.now(UTC)
    if not isinstance(updated, datetime):
        updated = created
    return EvalCriterionResponse(
        criterion_id=row_uuid(row, "id"),
        slug=row_str(row, "slug"),
        label=row_str(row, "label"),
        description=row_str_optional(row, "description"),
        scorer_type="llm_rubric",
        rubric=row_str(row, "rubric"),
        enabled=bool(row.get("enabled")),
        created_at=created,
        updated_at=updated,
    )
