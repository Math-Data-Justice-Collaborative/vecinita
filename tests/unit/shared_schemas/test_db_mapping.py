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


def test_mapping_row_accepts_mapping() -> None:
    row = {"slug": "housing", "count": 2}

    assert mapping_row(row)["slug"] == "housing"


def test_mapping_row_rejects_non_mapping() -> None:
    with pytest.raises(TypeError, match="mapping"):
        mapping_row(["not", "a", "mapping"])


def test_row_str_optional_returns_none_for_null() -> None:
    assert row_str_optional({"title": None}, "title") is None


def test_row_int_coerces_float_and_string() -> None:
    assert row_int({"count": 3.0}, "count") == 3
    assert row_int({"count": "7"}, "count") == 7


def test_row_uuid_accepts_uuid_and_string() -> None:
    value = uuid4()

    assert row_uuid({"id": value}, "id") == value
    assert row_uuid({"id": str(value)}, "id") == value


def test_scalar_int_coerces_numeric_types() -> None:
    assert scalar_int(4.0) == 4
    assert scalar_int("9") == 9


def test_scalar_float_coerces_numeric_types() -> None:
    assert scalar_float(2) == 2.0
    assert scalar_float("1.5") == 1.5


def test_scalar_uuid_accepts_uuid_and_string() -> None:
    value = uuid4()

    assert scalar_uuid(value) == value
    assert scalar_uuid(str(value)) == value


def test_sqlalchemy_scalar_one_returns_value() -> None:
    class _Result:
        def scalar_one(self) -> object:
            return 42

    assert sqlalchemy_scalar_one(_Result()) == 42


def test_sqlalchemy_scalar_one_rejects_invalid_result() -> None:
    with pytest.raises(TypeError, match="scalar_one"):
        sqlalchemy_scalar_one(object())


def test_row_str_returns_string_value() -> None:
    assert row_str({"language": "en"}, "language") == "en"


def test_row_value_returns_raw_object() -> None:
    assert row_value({"count": 5}, "count") == 5


def test_row_int_returns_int_without_coercion() -> None:
    assert row_int({"count": 5}, "count") == 5


def test_scalar_int_returns_int_without_coercion() -> None:
    assert scalar_int(5) == 5


def test_scalar_float_returns_float_without_coercion() -> None:
    assert scalar_float(1.25) == 1.25
