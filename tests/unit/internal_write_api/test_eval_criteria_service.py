"""Unit tests for eval criteria CRUD service (ADR-034)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import text
from vecinita_internal_write_api.eval_criteria_service import (
    _criterion_from_row,  # pyright: ignore[reportPrivateUsage]
    create_eval_criterion,
    get_eval_criterion,
    list_enabled_criteria,
    list_eval_criteria,
    update_eval_criterion,
)
from vecinita_shared_schemas.internal_write import (
    EvalCriterionCreateRequest,
    EvalCriterionUpdateRequest,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine


@pytest.fixture
def criterion_id(engine: Engine) -> Iterator[object]:
    """Create one eval criterion and delete it after the test."""
    created = create_eval_criterion(
        engine,
        body=EvalCriterionCreateRequest(
            slug=f"unit-{uuid4().hex[:8]}",
            label="Unit criterion",
            rubric="Must cite sources",
            scorer_type="llm_rubric",
            enabled=True,
        ),
    )
    yield created.criterion_id
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM eval_criteria WHERE id = :id"),
            {"id": created.criterion_id},
        )


def test_list_create_and_get_eval_criterion(engine: Engine, criterion_id: object) -> None:
    """CRUD round-trip returns persisted criterion fields."""
    listed = list_eval_criteria(engine)
    assert any(item.criterion_id == criterion_id for item in listed.items)

    fetched = get_eval_criterion(engine, criterion_id=criterion_id)  # type: ignore[arg-type]
    assert fetched is not None
    assert fetched.enabled is True
    assert fetched.scorer_type == "llm_rubric"


def test_get_eval_criterion_returns_none_for_missing_id(engine: Engine) -> None:
    """Missing criterion ids return None."""
    assert get_eval_criterion(engine, criterion_id=uuid4()) is None


def test_update_eval_criterion_patches_fields(engine: Engine, criterion_id: object) -> None:
    """update_eval_criterion merges partial updates."""
    updated = update_eval_criterion(
        engine,
        criterion_id=criterion_id,  # type: ignore[arg-type]
        body=EvalCriterionUpdateRequest(
            label="Updated label",
            enabled=False,
        ),
    )
    assert updated is not None
    assert updated.label == "Updated label"
    assert updated.enabled is False

    enabled_only = list_enabled_criteria(engine)
    assert all(item.criterion_id != criterion_id for item in enabled_only)


def test_update_eval_criterion_returns_none_when_missing(engine: Engine) -> None:
    """update_eval_criterion returns None for unknown ids."""
    result = update_eval_criterion(
        engine,
        criterion_id=uuid4(),
        body=EvalCriterionUpdateRequest(enabled=False),
    )
    assert result is None


def test_criterion_from_row_rejects_unsupported_scorer() -> None:
    """_criterion_from_row validates scorer_type."""
    with pytest.raises(ValueError, match="unsupported scorer_type"):
        _criterion_from_row(
            {
                "id": uuid4(),
                "slug": "bad",
                "label": "Bad",
                "description": None,
                "scorer_type": "unknown",
                "rubric": "R",
                "enabled": True,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )


def test_criterion_from_row_defaults_non_datetime_timestamps() -> None:
    """_criterion_from_row substitutes timestamps when DB values are not datetimes."""
    parsed = _criterion_from_row(
        {
            "id": uuid4(),
            "slug": "ts-fallback",
            "label": "TS",
            "description": None,
            "scorer_type": "llm_rubric",
            "rubric": "Rubric",
            "enabled": True,
            "created_at": "not-a-datetime",
            "updated_at": None,
        }
    )
    assert isinstance(parsed.created_at, datetime)
    assert isinstance(parsed.updated_at, datetime)
