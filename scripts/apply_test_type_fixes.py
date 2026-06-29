#!/usr/bin/env python3
"""Apply hand-verified basedpyright/ruff fixes to scoped test dirs."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Files with async write_client fixture
ASYNC_CLIENT_FILES = [
    "tests/integration/test_write_api.py",
    "tests/integration/test_corpus_delete.py",
    "tests/integration/test_admin_tag_caps.py",
    "tests/integration/test_admin_chunks.py",
    "tests/e2e/test_uj003_corpus_delete.py",
]

DOC_IDS_FILES = [
    "tests/integration/test_serving_stats.py",
    "tests/e2e/test_uj016_bulk_tag.py",
    "tests/e2e/test_uj015_bulk_delete.py",
    "tests/e2e/test_bulk_retag.py",
    "tests/e2e/test_bulk_metadata.py",
]

RUNNER_FILES = [
    "tests/e2e/test_uj002_ingest_tagging.py",
    "tests/e2e/test_uj002_ingest_tag_resilience.py",
    "tests/e2e/test_uj006_job_failure.py",
    "tests/e2e/test_uj023_job_management.py",
]


def patch_async_clients() -> None:
    for rel in ASYNC_CLIENT_FILES:
        p = ROOT / rel
        text = p.read_text()
        if "AsyncIterator[AsyncClient]" in text:
            continue
        text = text.replace(
            "from fastapi.testclient import TestClient\n",
            "",
        )
        if "from typing import TYPE_CHECKING" not in text:
            text = text.replace(
                "from __future__ import annotations\n\n",
                "from __future__ import annotations\n\nfrom typing import TYPE_CHECKING\n\n",
            )
        if "from collections.abc import AsyncIterator" not in text:
            text = text.replace(
                "if TYPE_CHECKING:\n",
                "if TYPE_CHECKING:\n    from collections.abc import AsyncIterator\n",
                1,
            )
        text = text.replace(
            "async def write_client(internal_api_key: None) -> TestClient:",
            "async def write_client(internal_api_key: None) -> AsyncIterator[AsyncClient]:",
        )
        p.write_text(text)


def patch_doc_ids() -> None:
    for rel in DOC_IDS_FILES:
        p = ROOT / rel
        p.write_text(p.read_text().replace("    doc_ids = []", "    doc_ids: list[UUID] = []"))


def patch_runners() -> None:
    for rel in RUNNER_FILES:
        p = ROOT / rel
        text = p.read_text()
        if "from uuid import UUID" not in text and "def runner(job_id: UUID)" in text:
            pass
        text = text.replace(
            "def runner(job_id) -> None:  # type: ignore[no-untyped-def]",
            "def runner(job_id: UUID) -> None:",
        )
        if "from uuid import UUID" not in text:
            text = re.sub(
                r"(from http import HTTPStatus\n)",
                r"\1from uuid import UUID\n",
                text,
                count=1,
            )
        p.write_text(text)


def main() -> None:
    patch_async_clients()
    patch_doc_ids()
    patch_runners()
    print("Applied batch patches")


if __name__ == "__main__":
    main()
