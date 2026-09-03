"""Unit tests for cleanup_corpus_test_artifacts operator script helpers."""

from __future__ import annotations

import pytest
from scripts.ops.cleanup_corpus_test_artifacts import parse_cleanup_args

pytestmark = pytest.mark.unit


def test_parse_cleanup_args_defaults_to_dry_run() -> None:
    """Without --apply the CLI stays in audit/dry-run mode."""
    args = parse_cleanup_args(["--database-url", "postgresql://localhost/vecinita"])
    assert args.apply is False
    assert args.database_url.startswith("postgresql://")
    assert args.as_json is False


def test_parse_cleanup_args_apply_and_json_flags() -> None:
    """--apply and --json opt into deletes and machine-readable output."""
    args = parse_cleanup_args(
        ["--database-url", "postgresql://localhost/vecinita", "--apply", "--json"],
    )
    assert args.apply is True
    assert args.as_json is True
