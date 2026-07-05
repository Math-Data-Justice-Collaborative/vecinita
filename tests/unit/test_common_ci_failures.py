"""Unit tests for common CI failure hook heuristics."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".cursor" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from common_ci_failures import (  # noqa: E402
    check_eval_runtime_factory_guard,
    check_migration_head_drift,
    check_test_inline_imports,
    migration_revision_from_path,
)


def _repo() -> Path:
    return Path(__file__).resolve().parents[2]


def test_migration_revision_from_path_parses_prefix() -> None:
    """Alembic revision prefix is parsed from the migration filename."""
    assert (
        migration_revision_from_path(Path("20260702_0007_ev009_eval_config.py")) == "20260702_0007"
    )


def test_check_migration_head_drift_warns_when_head_missing_from_schema_test() -> None:
    """A new migration warns when the EV-002 schema test does not mention the revision."""
    repo = _repo()
    migration = repo / "apps/database/alembic/versions/20990101_0099_future.sql.py"
    note = check_migration_head_drift(repo, migration)
    assert note is not None
    assert "20990101_0099" in note
    assert "test_ev002_schema.py" in note


def test_check_test_inline_imports_flags_indented_imports() -> None:
    """Indented imports inside test functions trigger PLC0415 guidance."""
    path = Path("tests/unit/foo/test_example.py")
    content = (
        "def test_something() -> None:\n"
        "    from vecinita_eval.modal_llm import ModalHttpLLM\n"
        "    assert True\n"
    )
    note = check_test_inline_imports(path, content)
    assert note is not None
    assert "PLC0415" in note


def test_check_test_inline_imports_ignores_top_level_imports() -> None:
    """Top-level imports in test modules are allowed."""
    path = Path("tests/unit/foo/test_example.py")
    content = (
        "from vecinita_eval.modal_llm import ModalHttpLLM\n\n"
        "def test_something() -> None:\n"
        "    assert True\n"
    )
    assert check_test_inline_imports(path, content) is None


def test_check_eval_runtime_factory_guard_flags_or_condition() -> None:
    """The injected-judge regression uses `or` instead of `and`."""
    path = Path("eval_service.py")
    content = (
        "def _resolve_eval_runtime(judge, llm):\n"
        "    if judge is None or llm is None:\n"
        "        return eval_runtime_for_config(config)\n"
    )
    note = check_eval_runtime_factory_guard(path, content)
    assert note is not None
    assert "UJ-039" in note


def test_check_eval_runtime_factory_guard_allows_and_condition() -> None:
    """The corrected guard using `and` does not warn."""
    path = Path("eval_service.py")
    content = (
        "def _resolve_eval_runtime(judge, llm):\n"
        "    if judge is None and llm is None:\n"
        "        return eval_runtime_for_config(config)\n"
    )
    assert check_eval_runtime_factory_guard(path, content) is None
