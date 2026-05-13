#!/usr/bin/env python3
"""Canonicalize metadata tags across sources and chunks.

Reads the Render Postgres database (via DATABASE_URL) and normalises tag
fields in the metadata JSONB columns of both the ``sources`` and
``document_chunks`` tables.

Usage:
  uv run python scripts/canonicalize_tags.py --dry-run
  uv run python scripts/canonicalize_tags.py --apply
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

from src.utils.tags import normalize_tag_fields

TAG_FIELDS = (
    "tags",
    "location_tags",
    "subject_tags",
    "service_tags",
    "content_type_tags",
    "organization_tags",
    "audience_tags",
)


def _normalize_metadata(metadata: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    return normalize_tag_fields(metadata, TAG_FIELDS)


def _get_conn() -> "psycopg2.connection":
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Export it before running this script:\n"
            "  export DATABASE_URL=postgresql://<user>:<pass>@<host>:<port>/<db>"
        )
    return psycopg2.connect(database_url, connect_timeout=10)


def run(*, apply: bool, batch_size: int) -> dict[str, Any]:
    sources_scanned = 0
    sources_changed = 0
    chunks_scanned = 0
    chunks_changed = 0

    conn = _get_conn()
    try:
        conn.autocommit = False

        # ── Sources ──────────────────────────────────────────────────────────
        offset = 0
        while True:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, url, title, is_active, metadata"
                    " FROM sources"
                    " ORDER BY created_at"
                    " LIMIT %s OFFSET %s",
                    (batch_size, offset),
                )
                rows = cur.fetchall()

            if not rows:
                break

            for row in rows:
                sources_scanned += 1
                metadata = dict(row.get("metadata") or {})
                normalized, changed = _normalize_metadata(metadata)
                if not changed:
                    continue
                sources_changed += 1
                if apply:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE sources SET metadata = %s, updated_at = NOW() WHERE id = %s",
                            (json.dumps(normalized), row["id"]),
                        )

            offset += len(rows)
            if len(rows) < batch_size:
                break

        # ── document_chunks ───────────────────────────────────────────────────
        offset = 0
        while True:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, metadata"
                    " FROM document_chunks"
                    " ORDER BY created_at"
                    " LIMIT %s OFFSET %s",
                    (batch_size, offset),
                )
                rows = cur.fetchall()

            if not rows:
                break

            for row in rows:
                chunks_scanned += 1
                metadata = dict(row.get("metadata") or {})
                normalized, changed = _normalize_metadata(metadata)
                if not changed:
                    continue
                chunks_changed += 1
                if apply:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE document_chunks SET metadata = %s, updated_at = NOW() WHERE id = %s",
                            (json.dumps(normalized), row["id"]),
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
        "tag_fields": list(TAG_FIELDS),
        "sources_scanned": sources_scanned,
        "sources_changed": sources_changed,
        "chunks_scanned": chunks_scanned,
        "chunks_changed": chunks_changed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize bilingual metadata tags")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Apply updates")
    mode.add_argument("--dry-run", action="store_true", help="Preview updates without writing")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    apply = bool(args.apply)
    if not args.apply and not args.dry_run:
        apply = False

    try:
        summary = run(apply=apply, batch_size=max(1, int(args.batch_size)))
        print(json.dumps(summary, indent=2))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": "Ensure DATABASE_URL is set and points to the Render Postgres instance.",
                },
                indent=2,
            )
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
