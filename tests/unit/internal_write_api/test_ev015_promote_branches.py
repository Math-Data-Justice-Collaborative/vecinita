"""EV-015 — promote conflict/idempotent branches without Postgres (coverage gate)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast
from uuid import uuid4

import pytest
from vecinita_internal_write_api import rebuild_promote as promote_mod
from vecinita_internal_write_api.rebuild_promote import (
    RebuildPromoteConflictError,
    RebuildPromoteNotFoundError,
)

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

_PROMOTE = promote_mod._promote_on_connection  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
_CHUNK_COUNT = 2
_DOC_COUNT = 1


class _Mappings:
    def __init__(self, row: dict[str, object] | None) -> None:
        self._row = row

    def first(self) -> dict[str, object] | None:
        return self._row

    def one(self) -> dict[str, object]:
        assert self._row is not None
        return self._row


class _Result:
    def __init__(self, row: dict[str, object] | None) -> None:
        self._row = row

    def mappings(self) -> _Mappings:
        return _Mappings(self._row)


class _Conn:
    def __init__(
        self,
        *,
        run_row: dict[str, object] | None,
        chunk_count: int = 0,
        doc_count: int = 0,
    ) -> None:
        self._run_row = run_row
        self._chunk_count = chunk_count
        self._doc_count = doc_count

    def execute(
        self,
        statement: object,
        params: dict[str, object] | None = None,
    ) -> _Result:
        _ = params
        sql = str(statement).lower()
        if "from rebuild_runs" in sql and "for update" in sql:
            return _Result(self._run_row)
        if "count(distinct document_id)" in sql:
            return _Result({"c": self._doc_count})
        if "count(*)" in sql and "shadow_chunks" in sql:
            return _Result({"c": self._chunk_count})
        return _Result({"c": 0})

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def test_promote_not_found() -> None:
    """Missing rebuild_run raises RebuildPromoteNotFoundError."""
    conn = cast("Connection", _Conn(run_row=None))
    with pytest.raises(RebuildPromoteNotFoundError, match="not found"):
        _ = _PROMOTE(conn, rebuild_run_id=uuid4())


def test_promote_already_promoted_is_idempotent() -> None:
    """status=promoted returns success without rewriting live tables."""
    run_id = uuid4()
    conn = cast(
        "Connection",
        _Conn(
            run_row={"id": run_id, "status": "promoted"},
            chunk_count=_CHUNK_COUNT,
            doc_count=_DOC_COUNT,
        ),
    )
    result = _PROMOTE(conn, rebuild_run_id=run_id)
    assert result.promoted is True
    assert result.chunks_promoted == _CHUNK_COUNT
    assert result.documents_promoted == _DOC_COUNT


def test_promote_rejects_non_completed_status() -> None:
    """running/failed rebuild runs cannot promote."""
    run_id = uuid4()
    conn = cast(
        "Connection",
        _Conn(
            run_row={"id": run_id, "status": "running"},
            chunk_count=_DOC_COUNT,
            doc_count=_DOC_COUNT,
        ),
    )
    with pytest.raises(RebuildPromoteConflictError, match="must be completed"):
        _ = _PROMOTE(conn, rebuild_run_id=run_id)


def test_promote_rejects_empty_shadow() -> None:
    """Completed run with zero shadow docs is a conflict."""
    run_id = uuid4()
    conn = cast(
        "Connection",
        _Conn(run_row={"id": run_id, "status": "completed"}, chunk_count=0, doc_count=0),
    )
    with pytest.raises(RebuildPromoteConflictError, match="no shadow chunks"):
        _ = _PROMOTE(conn, rebuild_run_id=run_id)
