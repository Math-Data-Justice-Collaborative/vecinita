"""Unit coverage for anonymous feedback helpers (F68 / ADR-046)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Self, cast
from uuid import uuid4

import pytest
from vecinita_internal_write_api.feedback import (
    cleanup_feedback,
    insert_feedback,
    list_feedback,
)
from vecinita_shared_schemas.chat_rag import FeedbackRequest

pytestmark = pytest.mark.unit

_DELETED_COUNT = 2


class _FakeMappingResult:
    def __init__(
        self,
        *,
        row: dict[str, object] | None = None,
        rows: list[dict[str, object]] | None = None,
        rowcount: int = 0,
    ) -> None:
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def mappings(self) -> Self:
        return self

    def one(self) -> dict[str, object]:
        assert self._row is not None
        return self._row

    def all(self) -> list[dict[str, object]]:
        return self._rows


class _FakeScalarResult:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        return self._value


class _FakeConn:
    def __init__(self, result: _FakeMappingResult) -> None:
        self._result = result

    def execute(self, *_args: object, **_kwargs: object) -> _FakeMappingResult:
        return self._result


class _ListEngine:
    def __init__(self, *, count: int, rows: list[dict[str, object]]) -> None:
        self.count = count
        self.rows = rows
        self.call_n = 0

    def connect(self) -> _ListConn:
        return _ListConn(self)


class _ListConn:
    def __init__(self, engine: _ListEngine) -> None:
        self.engine = engine

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return

    def execute(self, *_args: object, **_kwargs: object) -> object:
        self.engine.call_n += 1
        if self.engine.call_n == 1:
            return _FakeScalarResult(self.engine.count)
        return _FakeMappingResult(rows=self.engine.rows)


class _CleanupEngine:
    def begin(self) -> _CleanupBegin:
        return _CleanupBegin()


class _CleanupBegin:
    def __enter__(self) -> _FakeConn:
        return _FakeConn(_FakeMappingResult(rowcount=_DELETED_COUNT))

    def __exit__(self, *_args: object) -> None:
        return


def test_insert_feedback_formats_datetime_created_at() -> None:
    """insert_feedback returns ISO created_at from datetime column."""
    feedback_id = uuid4()
    created = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    conn = _FakeConn(
        _FakeMappingResult(row={"id": feedback_id, "created_at": created}),
    )
    body = FeedbackRequest(category="suggestion", message="hello", locale="en")
    result = insert_feedback(cast("object", conn), body)  # type: ignore[arg-type]
    assert result.id == feedback_id
    assert "2026-08-04" in result.created_at


def test_insert_feedback_stringifies_non_datetime_created_at() -> None:
    """Non-datetime created_at values are stringified."""
    feedback_id = uuid4()
    conn = _FakeConn(
        _FakeMappingResult(
            row={"id": feedback_id, "created_at": "2026-08-04T12:00:00Z"},
        ),
    )
    body = FeedbackRequest(category="bug", message="hello", locale=None)
    result = insert_feedback(cast("object", conn), body)  # type: ignore[arg-type]
    assert result.created_at == "2026-08-04T12:00:00Z"


def test_list_feedback_without_category_filter() -> None:
    """list_feedback returns paginated items."""
    feedback_id = uuid4()
    created = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    engine = _ListEngine(
        count=1,
        rows=[
            {
                "id": feedback_id,
                "created_at": created,
                "category": "other",
                "message": "msg",
                "locale": "en",
            }
        ],
    )
    page = list_feedback(cast("object", engine), page=1, page_size=20)  # type: ignore[arg-type]
    assert page.total_count == 1
    assert page.items[0].id == feedback_id
    assert page.items[0].locale == "en"


def test_list_feedback_with_category_filter() -> None:
    """Category filter path returns matching rows."""
    feedback_id = uuid4()
    created = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    engine = _ListEngine(
        count=1,
        rows=[
            {
                "id": feedback_id,
                "created_at": created,
                "category": "bug",
                "message": "msg",
                "locale": None,
            }
        ],
    )
    page = list_feedback(
        cast("object", engine),  # type: ignore[arg-type]
        page=1,
        page_size=10,
        category="bug",
    )
    assert page.items[0].category == "bug"
    assert page.items[0].locale is None


def test_list_feedback_rejects_non_datetime_created_at() -> None:
    """list_feedback raises when created_at is not datetime."""
    engine = _ListEngine(
        count=1,
        rows=[
            {
                "id": uuid4(),
                "created_at": "not-a-datetime",
                "category": "bug",
                "message": "msg",
                "locale": "en",
            }
        ],
    )
    with pytest.raises(TypeError, match="created_at"):
        list_feedback(cast("object", engine), page=1, page_size=20)  # type: ignore[arg-type]


def test_cleanup_feedback_returns_rowcount() -> None:
    """cleanup_feedback returns deleted rowcount from DELETE."""
    deleted = cleanup_feedback(cast("object", _CleanupEngine()), retention_days=90)  # type: ignore[arg-type]
    assert deleted == _DELETED_COUNT
