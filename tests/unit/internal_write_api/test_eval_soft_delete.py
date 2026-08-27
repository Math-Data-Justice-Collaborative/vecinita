"""T83.2 / TP-S013-03/05 — soft-delete eval_runs hides from default list/detail."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import text
from vecinita_internal_write_api import eval_service

from tests.helpers.eval_runs import create_test_eval_run

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Engine
    from vecinita_shared_schemas.internal_write import EvalRunDetailResponse, EvalRunListResponse


def _soft_delete_fn() -> Callable[..., None]:
    """Resolve soft_delete_eval_run (missing until T83.5 — intentional red)."""
    fn = getattr(eval_service, "soft_delete_eval_run", None)
    assert fn is not None, "soft_delete_eval_run must be defined on eval_service"
    return cast("Callable[..., None]", fn)


def test_soft_delete_hides_from_default_list(engine: Engine) -> None:
    """Soft-deleted runs are omitted from list_eval_runs (TP-S013-05)."""
    soft_delete_eval_run = _soft_delete_fn()
    list_eval_runs = cast(
        "Callable[..., EvalRunListResponse]",
        eval_service.list_eval_runs,
    )
    created = create_test_eval_run(engine)
    run_id = created.response.run_id
    try:
        soft_delete_eval_run(engine, run_id=run_id)
        listed = list_eval_runs(engine, page=1, page_size=50)
        assert all(item.run_id != run_id for item in listed.items)
    finally:
        with engine.begin() as conn:
            _ = conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_soft_delete_hides_from_default_detail(engine: Engine) -> None:
    """Soft-deleted runs return None from get_eval_run (TP-S013-05)."""
    soft_delete_eval_run = _soft_delete_fn()
    get_eval_run = cast(
        "Callable[..., EvalRunDetailResponse | None]",
        eval_service.get_eval_run,
    )
    created = create_test_eval_run(engine)
    run_id = created.response.run_id
    try:
        soft_delete_eval_run(engine, run_id=run_id)
        assert get_eval_run(engine, run_id=run_id) is None
    finally:
        with engine.begin() as conn:
            _ = conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})


def test_soft_delete_sets_deleted_at(engine: Engine) -> None:
    """soft_delete_eval_run stamps deleted_at timestamptz (TP-S013-05)."""
    soft_delete_eval_run = _soft_delete_fn()
    created = create_test_eval_run(engine)
    run_id = created.response.run_id
    try:
        soft_delete_eval_run(engine, run_id=run_id)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT deleted_at FROM eval_runs WHERE id = :id"),
                {"id": run_id},
            ).one()
        assert row[0] is not None
    finally:
        with engine.begin() as conn:
            _ = conn.execute(text("DELETE FROM eval_runs WHERE id = :id"), {"id": run_id})
