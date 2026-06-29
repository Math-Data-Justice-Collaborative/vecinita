# Supabase — Vecinita admin auth (F34 / EV-005)

Identity for **admin surfaces only** (Data Management UI/API + internal-write API). Operator
PII lives in Supabase; the Vecinita corpus DB stays PII-free (ADR-026).

## Canonical project

| Field | Value |
|-------|-------|
| Project ref | `cfuvghdsuwactfeamtym` |
| URL | `https://cfuvghdsuwactfeamtym.supabase.co` |
| JWT signing | **ES256** (JWKS at `/auth/v1/.well-known/jwks.json`) — ADR-028 |

## Registration model

- **Public sign-up disabled** (`enable_signup = false` in `config.toml`).
- Operators are onboarded via **`inviteUserByEmail`** (admin API) or the first-admin seed script.
- Invitee accepts the email link and sets a password (UJ-027).

## Environment syncing (branching)

Per ADR-027 §6 — **Supabase Pro + ephemeral preview branches**:

1. **Link** the CLI to the canonical project (one-time per machine):
   ```bash
   supabase login
   supabase link --project-ref cfuvghdsuwactfeamtym
   ```
2. **Preview branch** for a PR / migration review (ephemeral — tear down after merge):
   ```bash
   supabase branches create preview-pr-47 --experimental
   supabase db push --db-url "$SUPABASE_URI"   # when schema migrations exist
   ```
3. **Delete** the branch when done (~$0.32/day if left running):
   ```bash
   supabase branches delete preview-pr-47 --experimental
   ```
4. **Production** config changes: merge `supabase/config.toml` to `main`, then
   `supabase config push` (or apply via Dashboard) during deploy smoke.

Auth settings (invite-only, SMTP) are versioned in **`supabase/config.toml`** in this repo.
Corpus schema remains on **DO Postgres** via Alembic (`apps/database/alembic/`).

## Operator secrets (never commit)

See `docs/staging-secrets-matrix.md` §Supabase (EV-005) and `docs/config-spec.md` §Admin auth.

## First admin bootstrap

```bash
# From repo root; reads prod.env / shell env
uv run python scripts/seed_first_admin.py
```

Requires `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_ADMIN_EMAIL`, `SUPABASE_ADMIN_PASSWORD`.

## Custom SMTP (production invites)

Enable and configure SMTP in the Supabase Dashboard (or `auth.email.smtp` via config push) before
live invite delivery. Staging may use Inbucket locally (`supabase start`).
