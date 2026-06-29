#!/usr/bin/env python3
"""All verified manual fixes for scoped integration/e2e test typing."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FIXTURE_TYPES = '''"""Shared TypedDict shapes for pytest fixtures (strict typing)."""

from __future__ import annotations

from typing import TypedDict
from uuid import UUID


class DocumentFixtureData(TypedDict):
    """Document id and URL produced by audit/history E2E fixtures."""

    doc_id: UUID
'''


def write_fixture_types() -> None:
    (ROOT / "tests/helpers/fixture_types.py").write_text(FIXTURE_TYPES, encoding="utf-8")


def patch_file(rel: str, old: str, new: str) -> None:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if old not in text:
        return
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    write_fixture_types()

    # audit emission
    patch_file(
        "tests/integration/test_audit_emission.py",
        "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n    from sqlalchemy.engine import Engine",
        "from typing import TYPE_CHECKING, cast\n\nif TYPE_CHECKING:\n    from sqlalchemy.engine import Engine",
    )
    patch_file(
        "tests/integration/test_audit_emission.py",
        "def _clear_audit(engine, entity_id: uuid.UUID) -> None:",
        "def _clear_audit(engine: Engine, entity_id: uuid.UUID) -> None:",
    )
    patch_file(
        "tests/integration/test_audit_emission.py",
        "from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one",
        "from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one\n\nfrom tests.helpers.json_response import json_object_items, json_str",
    )
    patch_file(
        "tests/integration/test_audit_emission.py",
        '        assert any(t["slug"] == "housing" for t in version_row["tags_snapshot"])',
        '        tags_snapshot_raw: object = cast("object", version_row["tags_snapshot"])\n'
        "        tags_snapshot = json_object_items(tags_snapshot_raw)\n"
        '        assert any(json_str(tag, "slug") == "housing" for tag in tags_snapshot)',
    )

    # seed test - avoid private import
    patch_file(
        "tests/integration/test_seed.py",
        "import pytest\nfrom sqlalchemy import create_engine, text\nfrom vecinita_database.seeds.load import _database_url, load_corpus",
        "import os\n\nimport pytest\nfrom sqlalchemy import create_engine, text\nfrom vecinita_database.seeds.load import load_corpus",
    )
    patch_file(
        "tests/integration/test_seed.py",
        "pytestmark = pytest.mark.integration\n\n\n@pytest.fixture",
        "pytestmark = pytest.mark.integration\n\n\n"
        "def _database_url() -> str:\n"
        "    return os.environ.get(\n"
        '        "DATABASE_URL",\n'
        '        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",\n'
        "    )\n\n\n@pytest.fixture",
    )

    # uj007 mock llm
    patch_file(
        "tests/e2e/test_uj007_reject_identity.py",
        "from tests.integration.chat_rag.conftest import _MockLlmClient\nfrom tests.unit.rag.conftest import basis_vector",
        "from tests.unit.rag.conftest import basis_vector",
    )
    patch_file(
        "tests/e2e/test_uj007_reject_identity.py",
        "pytestmark = pytest.mark.e2e\n\n\n@pytest.fixture",
        "pytestmark = pytest.mark.e2e\n\n\n"
        "class _E2eMockLlmClient:\n"
        "    def generate(self, prompt: str, **kwargs: object) -> str:\n"
        "        _ = (prompt, kwargs)\n"
        '        return "ok"\n\n'
        "    def generate_stream(self, prompt: str, **kwargs: object):\n"
        "        _ = (prompt, kwargs)\n"
        '        yield "ok"\n\n'
        "    def close(self) -> None:\n"
        "        return None\n\n\n@pytest.fixture",
    )
    patch_file(
        "tests/e2e/test_uj007_reject_identity.py",
        "llm_client=_MockLlmClient())",
        "llm_client=_E2eMockLlmClient())",
    )

    # autouse fixture pyright ignores
    for rel, name in [
        ("tests/bugs/test_bug_2026_05_22_delete_document_failed_to_fetch.py", "_cors_and_db_env"),
        ("tests/bugs/test_bug_2026_05_22_modal_jobs_failed_to_fetch.py", "_cors_env"),
        ("tests/bugs/test_bug_2026_05_25_retag_503_not_configured.py", "_env"),
    ]:
        patch_file(
            rel,
            f"def {name}(monkeypatch: pytest.MonkeyPatch) -> None:",
            f"def {name}(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]",
        )

    # modal repo root
    (ROOT / "tests/bugs/test_bug_2026_05_22_modal_data_mgmt_repo_root.py").write_text(
        '''"""BUG-2026-05-22: Modal data-mgmt ASGI must import when mounted at /root/data_management_app.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Protocol, cast


class _MountedDataMgmtModule(Protocol):
    _REPO_ROOT: object


def test_data_management_app_imports_when_modal_mounts_at_root(tmp_path: Path) -> None:
    """Modal copies the deploy module to /root/data_management_app.py — parents[2] must not crash."""
    source = Path(__file__).resolve().parents[2] / "infra" / "modal" / "data_management_app.py"
    mounted = tmp_path / "data_management_app.py"
    mounted.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("data_management_app_mounted", mounted)
    assert spec
    assert spec.loader
    raw_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw_module)
    module = cast("_MountedDataMgmtModule", raw_module)

    repo_root: object = module._REPO_ROOT  # pyright: ignore[reportPrivateUsage]
    assert Path("/opt/vecinita") == Path(str(repo_root))
''',
        encoding="utf-8",
    )

    print("Manual fixes applied")


if __name__ == "__main__":
    main()
