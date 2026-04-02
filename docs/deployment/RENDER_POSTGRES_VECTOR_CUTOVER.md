# Render Postgres Vector Cutover

This runbook moves Vecinita vector/document data paths to Render Postgres while keeping Supabase for authentication.

## Target architecture

- Supabase: auth/session/role metadata.
- Render Postgres: vector/document retrieval and ingestion data.

## Required service env vars

Set these on agent/scraper services in Render:

- `DATABASE_URL` = internal Render Postgres URL
- `DB_DATA_MODE=postgres`
- `VECTOR_SYNC_TARGET=postgres`
- `VECTOR_SYNC_SUPABASE_FALLBACK_READS=false`
- `SUPABASE_URL` (still needed for auth-backed flows)
- `SUPABASE_KEY` (still needed for auth-backed flows)

Optional rollback toggles:

- `POSTGRES_DATA_READS_ENABLED=true`
- `SUPABASE_DATA_READS_ENABLED=true`

## Local `.env` procedure (untracked)

Use the internal Render coordinates in your local `.env` (file is ignored by git):

```env
DATABASE_URL=postgresql://vecinita_postgres_user:<password>@dpg-d6or4g2a214c73f6hl20-a:5432/vecinita_postgres?sslmode=require
DB_HOST=dpg-d6or4g2a214c73f6hl20-a
DB_PORT=5432
DB_NAME=vecinita_postgres
DB_USER=vecinita_postgres_user
DB_PASSWORD=<password>
DB_DATA_MODE=postgres
VECTOR_SYNC_SUPABASE_FALLBACK_READS=false
```

If your password includes reserved URL characters (`@`, `:`, `/`, `?`, `#`, `%`), URL-encode it in `DATABASE_URL`.

If you are running outside Render, use your external Render hostname and keep `sslmode=require`.

Example:

- raw password: `pa:ss@word#1`
- encoded password: `pa%3Ass%40word%231`

## Cutover sequence

1. Confirm pgvector/schema prerequisites exist in Render Postgres.
2. Set env vars above in staging first.
3. Deploy staging and verify startup preflight reports `data_mode=postgres`.
4. Run retrieval and ingestion smoke tests.
5. Promote identical env settings to production.

Parity check command:

```bash
uv run python backend/scripts/render_postgres_parity_check.py
uv run python backend/scripts/render_postgres_parity_check.py --apply
```

The `--apply` command executes [backend/scripts/render_postgres_parity.sql](backend/scripts/render_postgres_parity.sql).

## Validation checklist

- Startup log includes `data_mode=postgres`.
- `checks.data_backend.backend=postgres` in preflight payload.
- `ask` endpoint returns sourced answers from vector data.
- Auth login/session still works via Supabase.

## Security notes

- Never commit real credentials to tracked files.
- Rotate credentials if they were ever shared in plaintext.
- Prefer Render internal URL for same-region service-to-database traffic.
