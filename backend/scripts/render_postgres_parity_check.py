#!/usr/bin/env python3
"""Check Render Postgres parity and optionally apply minimal vector schema.

Usage:
  uv run python backend/scripts/render_postgres_parity_check.py
  uv run python backend/scripts/render_postgres_parity_check.py --apply

Connection precedence:
1) DATABASE_URL (recommended)
2) DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD + sslmode=require

This script intentionally scopes parity to:
- extensions: vector, uuid-ossp, pgcrypto
- tables: document_chunks, processing_queue
- required indexes for retrieval/queue operations
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

import psycopg2
from dotenv import load_dotenv

EXPECTED_EXTENSIONS = ("vector", "uuid-ossp", "pgcrypto")
EXPECTED_TABLES = ("document_chunks", "processing_queue")


def _build_conn_kwargs() -> dict[str, object]:
    host = (os.getenv("DB_HOST") or "").strip()
    dbname = (os.getenv("DB_NAME") or "").strip()
    user = (os.getenv("DB_USER") or "").strip()
    password = os.getenv("DB_PASSWORD")
    port = int((os.getenv("DB_PORT") or "5432").strip())

    if host and dbname and user and password:
        return {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
            "sslmode": "require",
            "connect_timeout": 10,
        }

    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if database_url:
        return {"dsn": database_url, "connect_timeout": 10}

    if not (host and dbname and user and password):
        raise RuntimeError(
            "Missing database connection settings. Set DATABASE_URL or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD."
        )

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": "require",
        "connect_timeout": 10,
    }


def _fetch_set(cur, sql: str) -> set[str]:
    cur.execute(sql)
    return {str(row[0]) for row in cur.fetchall()}


def _print_missing(name: str, expected: Iterable[str], actual: set[str]) -> list[str]:
    missing = [item for item in expected if item not in actual]
    if missing:
        print(f"missing_{name}=", missing)
    else:
        print(f"missing_{name}= []")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Postgres parity checker")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply backend/scripts/render_postgres_parity.sql when parity gaps are detected",
    )
    args = parser.parse_args()

    load_dotenv()
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    conn_kwargs = _build_conn_kwargs()

    with psycopg2.connect(**conn_kwargs) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            exts = _fetch_set(
                cur,
                "SELECT extname FROM pg_extension WHERE extname IN ('vector','uuid-ossp','pgcrypto') ORDER BY extname",
            )
            tables = _fetch_set(
                cur,
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema='public'
                  AND table_name IN ('document_chunks','processing_queue')
                ORDER BY table_name
                """,
            )

            print("extensions=", sorted(exts))
            print("tables=", sorted(tables))

            missing_exts = _print_missing("extensions", EXPECTED_EXTENSIONS, exts)
            missing_tables = _print_missing("tables", EXPECTED_TABLES, tables)

            if args.apply and (missing_exts or missing_tables):
                sql_path = Path(__file__).resolve().with_name("render_postgres_parity.sql")
                sql = sql_path.read_text(encoding="utf-8")
                cur.execute(sql)
                print("applied_sql=", str(sql_path))

                exts = _fetch_set(
                    cur,
                    "SELECT extname FROM pg_extension WHERE extname IN ('vector','uuid-ossp','pgcrypto') ORDER BY extname",
                )
                tables = _fetch_set(
                    cur,
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema='public'
                      AND table_name IN ('document_chunks','processing_queue')
                    ORDER BY table_name
                    """,
                )
                print("post_apply_extensions=", sorted(exts))
                print("post_apply_tables=", sorted(tables))

            if missing_exts or missing_tables:
                print("parity_status=missing")
                return 2 if not args.apply else 0

            print("parity_status=ok")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
