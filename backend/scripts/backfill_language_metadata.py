#!/usr/bin/env python3
"""Backfill persisted resource language metadata for existing document chunks.

Usage:
  uv run python scripts/backfill_language_metadata.py --dry-run
  uv run python scripts/backfill_language_metadata.py --apply
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from typing import Any

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2  # type: ignore[import-not-found]
import psycopg2.extras  # type: ignore[import-not-found]

from src.utils.resource_metadata import infer_resource_language_metadata


def _get_conn() -> "psycopg2.connection":
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export it before running this script:\n"
            "  export DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>"
        )
    return psycopg2.connect(database_url, connect_timeout=10)


def _language_snapshot(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "language": metadata.get("language"),
        "primary_language": metadata.get("primary_language"),
        "primary_language_code": metadata.get("primary_language_code"),
        "available_languages": metadata.get("available_languages"),
        "available_language_codes": metadata.get("available_language_codes"),
        "is_bilingual": metadata.get("is_bilingual"),
    }


def run(*, apply: bool, batch_size: int) -> dict[str, Any]:
    scanned = 0
    changed = 0

    conn = _get_conn()
    try:
        conn.autocommit = False
        offset = 0
        while True:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, content, metadata FROM document_chunks ORDER BY created_at LIMIT %s OFFSET %s",
                    (batch_size, offset),
                )
                rows = cur.fetchall()

            if not rows:
                break

            for row in rows:
                scanned += 1
                metadata = dict(row.get("metadata") or {})
                before = _language_snapshot(metadata)
                metadata.update(
                    infer_resource_language_metadata(
                        [str(row.get("content") or "")],
                        existing_metadata=metadata,
                    )
                )
                if before == _language_snapshot(metadata):
                    continue

                changed += 1
                if apply:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE document_chunks SET metadata = %s, updated_at = NOW() WHERE id = %s",
                            (json.dumps(metadata), row["id"]),
                        )

            offset += len(rows)
            if len(rows) < batch_size:
                break

        if apply:
            conn.commit()
    finally:
        conn.close()

    return {
        "apply": apply,
        "batch_size": batch_size,
        "rows_scanned": scanned,
        "rows_changed": changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill language metadata on document chunks")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Apply updates")
    mode.add_argument("--dry-run", action="store_true", help="Preview updates without writing")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    try:
        summary = run(apply=bool(args.apply), batch_size=max(1, int(args.batch_size)))
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()