"""Contract: corpus data must resolve from canonical Postgres DATABASE_URL."""

from __future__ import annotations

import pytest

from src.utils.corpus_db_guard import validate_canonical_database_url

pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_strict_mode_rejects_non_postgres_database_url() -> None:
    with pytest.raises(RuntimeError, match="canonical postgres"):
        validate_canonical_database_url(
            service_name="gateway",
            strict=True,
            database_url="sqlite:///tmp/dev.db",
        )


def test_strict_mode_rejects_placeholder_markers() -> None:
    with pytest.raises(RuntimeError, match="mock/placeholder/example"):
        validate_canonical_database_url(
            service_name="gateway",
            strict=True,
            database_url="postgresql://user:pass@localhost:5432/placeholder_db",
        )


@pytest.mark.parametrize(
    "database_url",
    [
        "postgresql://user:pass@localhost:5432/mock_db",
        "postgresql://user:pass@localhost:5432/example_db",
        "postgresql://user:pass@localhost:5432/changeme_db",
    ],
)
def test_production_profile_rejects_non_canonical_markers(database_url: str) -> None:
    with pytest.raises(RuntimeError, match="mock/placeholder/example"):
        validate_canonical_database_url(
            service_name="gateway",
            strict=True,
            database_url=database_url,
        )


def test_non_strict_mode_allows_empty_database_url_for_local_bootstrap() -> None:
    result = validate_canonical_database_url(
        service_name="gateway",
        strict=False,
        database_url="",
    )
    assert result.database_url == ""
    assert result.strict is False


def test_strict_mode_accepts_valid_postgres_url() -> None:
    result = validate_canonical_database_url(
        service_name="gateway",
        strict=True,
        database_url="postgresql://user:pass@db.internal:5432/vecinita",
    )
    assert result.database_url.startswith("postgresql://")
    assert result.strict is True
