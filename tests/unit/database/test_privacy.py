"""Unit tests for privacy schema guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import patch

from vecinita_database.privacy import (
    _normalize_database_url,  # pyright: ignore[reportPrivateUsage]
    find_forbidden_tables,
    find_identity_columns_on_ev002_tables,
    find_identity_columns_on_tag_tables,
    find_missing_ev002_tables,
    find_missing_tag_tables,
)


@dataclass
class FakeInspector:
    """FakeInspector."""

    tables: list[str]
    columns: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def get_table_names(self, schema: str = "public") -> list[str]:
        """Get table names."""
        _ = schema
        return self.tables

    def get_columns(self, table: str, schema: str = "public") -> list[dict[str, str]]:
        """Get columns."""
        _ = schema
        return self.columns.get(table, [])


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    """Test normalize database url upgrades postgresql scheme."""
    assert (
        _normalize_database_url("postgresql://user:pass@host/db")
        == "postgresql+psycopg://user:pass@host/db"
    )


def test_find_forbidden_tables_detects_blocked_names() -> None:
    """Test find forbidden tables detects blocked names."""
    inspector = FakeInspector(tables=["documents", "users", "auth_tokens"])

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        found = find_forbidden_tables("postgresql+psycopg://localhost/db")

    assert found == {"users", "auth_tokens"}


def test_find_missing_tag_tables_reports_absent_tables() -> None:
    """Test find missing tag tables reports absent tables."""
    inspector = FakeInspector(tables=["documents"])

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        missing = find_missing_tag_tables("postgresql+psycopg://localhost/db")

    assert missing == {"tags", "document_tags", "chunk_tags"}


def test_find_identity_columns_on_tag_tables_reports_violations() -> None:
    """Test find identity columns on tag tables reports violations."""
    inspector = FakeInspector(
        tables=["tags", "document_tags"],
        columns={
            "tags": [{"name": "slug"}, {"name": "user_id"}],
            "document_tags": [{"name": "document_id"}, {"name": "auth_subject"}],
        },
    )

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        violations = find_identity_columns_on_tag_tables("postgresql+psycopg://localhost/db")

    assert violations["tags"] == ["user_id"]
    assert violations["document_tags"] == ["auth_subject"]


def test_find_missing_ev002_tables_reports_absent_tables() -> None:
    """Test find missing ev002 tables reports absent tables."""
    inspector = FakeInspector(tables=["documents", "audit_log"])

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        missing = find_missing_ev002_tables("postgresql+psycopg://localhost/db")

    assert missing == {"document_versions", "document_serving_stats"}


def test_find_identity_columns_on_ev002_tables_reports_violations() -> None:
    """Test find identity columns on ev002 tables reports violations."""
    inspector = FakeInspector(
        tables=["audit_log"],
        columns={"audit_log": [{"name": "event_type"}, {"name": "email"}]},
    )

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        violations = find_identity_columns_on_ev002_tables("postgresql+psycopg://localhost/db")

    assert violations == {"audit_log": ["email"]}


def test_find_identity_columns_on_tag_tables_returns_empty_when_compliant() -> None:
    """Test find identity columns on tag tables returns empty when compliant."""
    inspector = FakeInspector(
        tables=["tags"],
        columns={"tags": [{"name": "slug"}, {"name": "label"}]},
    )

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        violations = find_identity_columns_on_tag_tables("postgresql+psycopg://localhost/db")

    assert violations == {}


def test_find_identity_columns_on_ev002_tables_returns_empty_when_compliant() -> None:
    """Test find identity columns on ev002 tables returns empty when compliant."""
    inspector = FakeInspector(
        tables=["audit_log"],
        columns={"audit_log": [{"name": "event_type"}, {"name": "payload"}]},
    )

    with (
        patch("vecinita_database.privacy.create_engine"),
        patch(
            "vecinita_database.privacy.inspect",
            return_value=inspector,
        ),
    ):
        violations = find_identity_columns_on_ev002_tables("postgresql+psycopg://localhost/db")

    assert violations == {}
