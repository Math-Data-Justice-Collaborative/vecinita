# BUG-2026-08-28 — Alembic deploy fails: Postgres connection slots exhausted

## Error description

DigitalOcean deploy job **Alembic upgrade head** failed with:

```text
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

DO Managed Postgres (`max_connections=25`, `superuser_reserved=3` → ~22 usable) was full. ChatRAG created a **new SQLAlchemy engine on every** `/health` and browse request **without dispose**, so idle pool connections accumulated until Alembic could not connect.

## Error logs

GitHub Actions run `33188055386` (Deploy DigitalOcean, 2026-08-28):

```text
psycopg.OperationalError: connection failed: ... port 25060 failed: FATAL:  remaining connection slots are reserved for non-replication superuser connections
```

Live check (same day): `slots_used=22/25`, `free_non_super=0`.

## Investigation

1. Confirmed not App Platform HTTP port limits — Postgres backend slots.
2. Two App Platform egress IPs held most idle `doadmin` backends (`ROLLBACK` last query).
3. ChatRAG `app.py` called `create_engine(...)` inside `/health`, `/documents`, `/tags` with no shared engine and no `dispose()`.
4. Default SQLAlchemy pool (`pool_size=5`, `max_overflow=10`) per leaked engine exhausts a 25-slot DB quickly under DO health probes.
5. DO API token lacked `databases` read (403); inspected via `DATABASE_URL` + `pg_stat_activity`.
6. Terminated idle backends to free slots for immediate recovery; code fix required to stop refill.

## Repro test

- `tests/unit/chat_rag/test_app_engine_reuse.py` — red when each `/health` calls `create_engine`; green with shared `create_app_engine`.

## Fix

- Shared capped engine for ChatRAG health/browse (`pool_size=2`, `max_overflow=1`, `pool_pre_ping`, `application_name`).
- Same caps on write-API engine, ChatRAG RAG service engine (shared with retriever), and retriever fallback.
- Session: `HF-alembic-do-db-ports`.
