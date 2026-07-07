"""Typed accessors for SQLAlchemy row mappings (reportAny-safe)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar, cast
from uuid import UUID

T = TypeVar("T")


def mapping_row(row: object) -> Mapping[str, object]:
    """Narrow a SQLAlchemy RowMapping to Mapping[str, object] for keyed access."""
    if isinstance(row, Mapping):
        return cast("Mapping[str, object]", row)
    msg = f"Expected mapping row, got {type(row).__name__}"
    raise TypeError(msg)


def row_value(row: Mapping[str, object], key: str) -> object:
    """Return the raw value for ``key`` from a database row mapping."""
    return row[key]


def row_str(row: Mapping[str, object], key: str) -> str:
    """Return ``key`` from a row mapping coerced to ``str``."""
    return str(row[key])


def row_str_optional(row: Mapping[str, object], key: str) -> str | None:
    """Return ``key`` as ``str`` or ``None`` when the column value is null."""
    value = row[key]
    if value is None:
        return None
    return str(value)


def row_int(row: Mapping[str, object], key: str) -> int:
    """Return ``key`` from a row mapping coerced to ``int``."""
    value = row[key]
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def row_uuid(row: Mapping[str, object], key: str) -> UUID:
    """Return ``key`` from a row mapping as a ``UUID``."""
    value = row[key]
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def row_uuid_optional(row: Mapping[str, object], key: str) -> UUID | None:
    """Return ``key`` as ``UUID`` or ``None`` when the column value is null."""
    value = row[key]
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def scalar_int(value: object) -> int:
    """Coerce a scalar database value to ``int``."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return int(str(value))


def scalar_float(value: object) -> float:
    """Coerce a scalar database value to ``float``."""
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    return float(str(value))


def scalar_uuid(value: object) -> UUID:
    """Coerce a scalar database value to ``UUID``."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def sqlalchemy_scalar_one(result: object) -> object:
    """Narrow SQLAlchemy Result.scalar_one() (typed Any upstream) to object."""
    scalar_one = getattr(result, "scalar_one", None)
    if not callable(scalar_one):
        msg = f"Expected SQLAlchemy result with scalar_one(), got {type(result).__name__}"
        raise TypeError(msg)
    return scalar_one()
