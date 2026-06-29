"""Unit tests for vecinita_shared_schemas.db_mapping."""

from __future__ import annotations

from uuid import uuid4

import pytest
from vecinita_shared_schemas.db_mapping import (
    mapping_row,
    row_int,
    row_str,
    row_str_optional,
    row_uuid,
    row_value,
    scalar_float,
    scalar_int,
    scalar_uuid,
    sqlalchemy_scalar_one,
)

_ROW_COUNT = 2
_COERCED_INT_FROM_FLOAT = 3
_COERCED_INT_FROM_STRING = 7
_SCALAR_INT_FROM_FLOAT = 4
_SCALAR_INT_FROM_STRING = 9
_SCALAR_FLOAT_FROM_INT = 2.0
_SCALAR_FLOAT_FROM_STRING = 1.5
_SCALAR_ONE_RESULT = 42
_RAW_COUNT = 5
_SCALAR_INT_RAW = 5
_SCALAR_FLOAT_RAW = 1.25


def test_mapping_row_accepts_mapping() -> None:
    """Test mapping row accepts mapping."""
    row = {"slug": "housing", "count": _ROW_COUNT}

    assert mapping_row(row)["slug"] == "housing"


def test_mapping_row_rejects_non_mapping() -> None:
    """Test mapping row rejects non mapping."""
    with pytest.raises(TypeError, match="mapping"):
        mapping_row(["not", "a", "mapping"])


def test_row_str_optional_returns_none_for_null() -> None:
    """Test row str optional returns none for null."""
    assert row_str_optional({"title": None}, "title") is None


def test_row_int_coerces_float_and_string() -> None:
    """Test row int coerces float and string."""
    assert row_int({"count": 3.0}, "count") == _COERCED_INT_FROM_FLOAT
    assert row_int({"count": "7"}, "count") == _COERCED_INT_FROM_STRING


def test_row_uuid_accepts_uuid_and_string() -> None:
    """Test row uuid accepts uuid and string."""
    value = uuid4()

    assert row_uuid({"id": value}, "id") == value
    assert row_uuid({"id": str(value)}, "id") == value


def test_scalar_int_coerces_numeric_types() -> None:
    """Test scalar int coerces numeric types."""
    assert scalar_int(4.0) == _SCALAR_INT_FROM_FLOAT
    assert scalar_int("9") == _SCALAR_INT_FROM_STRING


def test_scalar_float_coerces_numeric_types() -> None:
    """Test scalar float coerces numeric types."""
    assert scalar_float(2) == _SCALAR_FLOAT_FROM_INT
    assert scalar_float("1.5") == _SCALAR_FLOAT_FROM_STRING


def test_scalar_uuid_accepts_uuid_and_string() -> None:
    """Test scalar uuid accepts uuid and string."""
    value = uuid4()

    assert scalar_uuid(value) == value
    assert scalar_uuid(str(value)) == value


def test_sqlalchemy_scalar_one_returns_value() -> None:
    """Test sqlalchemy scalar one returns value."""

    class _Result:
        """Result."""

        def scalar_one(self) -> object:
            """Scalar one."""
            return _SCALAR_ONE_RESULT

    assert sqlalchemy_scalar_one(_Result()) == _SCALAR_ONE_RESULT


def test_sqlalchemy_scalar_one_rejects_invalid_result() -> None:
    """Test sqlalchemy scalar one rejects invalid result."""
    with pytest.raises(TypeError, match="scalar_one"):
        sqlalchemy_scalar_one(object())


def test_row_str_returns_string_value() -> None:
    """Test row str returns string value."""
    assert row_str({"language": "en"}, "language") == "en"


def test_row_value_returns_raw_object() -> None:
    """Test row value returns raw object."""
    assert row_value({"count": _RAW_COUNT}, "count") == _RAW_COUNT


def test_row_int_returns_int_without_coercion() -> None:
    """Test row int returns int without coercion."""
    assert row_int({"count": _RAW_COUNT}, "count") == _RAW_COUNT


def test_scalar_int_returns_int_without_coercion() -> None:
    """Test scalar int returns int without coercion."""
    assert scalar_int(_SCALAR_INT_RAW) == _SCALAR_INT_RAW


def test_scalar_float_returns_float_without_coercion() -> None:
    """Test scalar float returns float without coercion."""
    assert scalar_float(_SCALAR_FLOAT_RAW) == _SCALAR_FLOAT_RAW
