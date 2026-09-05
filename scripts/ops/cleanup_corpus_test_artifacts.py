#!/usr/bin/env python3
r"""Audit or delete synthetic test-artifact documents from a corpus Postgres URL.

Deletes documents whose URL matches example.com / fixture:// / localhost patterns
(cascades chunks/embeddings/tags via FK). Requires the same operator override as
corpus reset helpers when targeting Managed Postgres.

Usage (dry-run audit):
  uv run python scripts/ops/cleanup_corpus_test_artifacts.py --database-url "$DATABASE_URL"

Apply deletes (local or with override):
  export VECINITA_ALLOW_CORPUS_RESET=1
  export VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed
  uv run python scripts/ops/cleanup_corpus_test_artifacts.py \
    --database-url "$DATABASE_URL" --apply

[Corpus: corpus-db-safety] [Corpus: no-live-prod-corpus-push]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corpus_db_guard import (  # noqa: E402
    assert_corpus_reset_allowed,
    corpus_database_host,
)
from tests.helpers.corpus_test_artifacts import (  # noqa: E402
    LIST_TEST_ARTIFACT_DOCUMENTS_SQL,
    is_corpus_test_artifact_url,
)

_CLEAR_PAIR_SQL = (
    "UPDATE documents SET paired_document_id = NULL WHERE paired_document_id = CAST(:id AS uuid)"
)
_CLEAR_RUNS_SQL = "DELETE FROM automation_runs WHERE document_id = CAST(:id AS uuid)"
_CLEAR_AUDIT_SQL = (
    "DELETE FROM audit_log WHERE entity_type = 'document' AND entity_id = CAST(:id AS uuid)"
)
_DELETE_DOC_SQL = "DELETE FROM documents WHERE id = CAST(:id AS uuid)"


class ArtifactRow(TypedDict):
    id: str
    url: str
    title: str | None


@dataclass(frozen=True)
class CleanupArgs:
    """Typed CLI options for the cleanup operator script."""

    database_url: str
    apply: bool
    as_json: bool


def list_test_artifact_documents(*, database_url: str) -> list[ArtifactRow]:
    """Return documents matching the test-artifact URL classifier (read-only)."""
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(LIST_TEST_ARTIFACT_DOCUMENTS_SQL)).mappings().all()
    finally:
        engine.dispose()
    artifacts: list[ArtifactRow] = []
    for row in rows:
        url = str(row["url"])
        if not is_corpus_test_artifact_url(url):
            continue
        title_raw = row["title"]
        artifacts.append(
            {
                "id": str(row["id"]),
                "url": url,
                "title": None if title_raw is None else str(title_raw),
            }
        )
    return artifacts


def delete_test_artifact_documents(*, database_url: str) -> list[ArtifactRow]:
    """Delete matching documents after assert_corpus_reset_allowed. Returns deleted rows."""
    assert_corpus_reset_allowed(database_url)
    to_delete = list_test_artifact_documents(database_url=database_url)
    if not to_delete:
        return []
    engine = create_engine(database_url)
    try:
        with engine.begin() as conn:
            for row in to_delete:
                doc_id = row["id"]
                _ = conn.execute(text(_CLEAR_PAIR_SQL), {"id": doc_id})
                _ = conn.execute(text(_CLEAR_RUNS_SQL), {"id": doc_id})
                _ = conn.execute(text(_CLEAR_AUDIT_SQL), {"id": doc_id})
                _ = conn.execute(text(_DELETE_DOC_SQL), {"id": doc_id})
    finally:
        engine.dispose()
    return to_delete


def parse_cleanup_args(argv: list[str] | None = None) -> CleanupArgs:
    """Parse CLI argv into typed CleanupArgs."""
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Postgres URL (default: DATABASE_URL env)",
    )
    _ = parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete matching rows (default: dry-run list only)",
    )
    _ = parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print machine-readable JSON summary",
    )
    ns = parser.parse_args(argv)
    return CleanupArgs(
        database_url=str(ns.database_url),
        apply=bool(ns.apply),
        as_json=bool(ns.as_json),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry: audit (default) or --apply deletes."""
    args = parse_cleanup_args(argv)
    database_url = args.database_url.strip()
    if not database_url:
        print("ERROR: --database-url or DATABASE_URL required", file=sys.stderr)
        return 2
    host = corpus_database_host(database_url)
    artifacts = list_test_artifact_documents(database_url=database_url)
    deleted: list[ArtifactRow] = []
    if args.apply:
        deleted = delete_test_artifact_documents(database_url=database_url)
        remaining = list_test_artifact_documents(database_url=database_url)
    else:
        remaining = artifacts
    listed = deleted if args.apply else artifacts
    urls = [row["url"] for row in listed]
    summary: dict[str, object] = {
        "host": host,
        "mode": "apply" if args.apply else "dry-run",
        "matched": len(artifacts),
        "deleted": len(deleted),
        "remaining": len(remaining),
        "urls": urls,
    }
    if args.as_json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"host={host} mode={summary['mode']}")
        matched = summary["matched"]
        deleted_n = summary["deleted"]
        remaining_n = summary["remaining"]
        print(f"matched={matched} deleted={deleted_n} remaining={remaining_n}")
        for url in cast("list[str]", summary["urls"]):
            print(f"  {url}")
    if args.apply and remaining:
        print("ERROR: test artifacts still present after delete", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
