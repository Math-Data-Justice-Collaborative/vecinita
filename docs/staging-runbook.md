# Staging runbook (Phase 4)

> **Purpose:** Operator checklist for staging deploy and H1–H3 health tiers (QA-006).  
> **Health tiers:** `.cursor/skills/deployment-catalog.md`, `15-service-health`  
> **Secrets:** [staging-secrets-matrix.md](staging-secrets-matrix.md)

## Health tiers

| Tier | Check | Pass criteria |
|------|-------|---------------|
| **H1** | Liveness | `GET {CHAT_URL}/health` → 200, `{"status":"ok"}`; optional write API |
| **H2** | DB ready | `SELECT 1` via SQLAlchemy pool; `alembic current` revision == `alembic heads` |
| **H3** | RAG smoke | `POST {CHAT_URL}/api/v1/ask` with pantry question → `answer` + `language` in `en`/`es` |
| **H3b** | Browse smoke (EV-001) | `GET {CHAT_URL}/api/v1/documents` + `/api/v1/tags` → paginated items + tag facets |
| **H4** | Browser CORS | `OPTIONS` from frontend origin → API returns `Access-Control-Allow-Origin` |
| **H5** | Frontend bundle | Live JS contains staging API hosts (not `localhost`) |

Unset env vars **skip** that tier (exit 0). Set vars only for tiers you can reach from your shell.

Copy `infra/staging/.env.example` into `prod.env` (gitignored) or export vars before running
`make verify-connectivity` / `bash scripts/deploy/verify_connectivity.sh`.

**H4–H5 are required for UI sign-off** — see `.cursor/skills/connectivity-gates.md`.

## Pre-flight (before deploy)

```bash
bash scripts/deploy/verify_build.sh
bash scripts/deploy/verify_secrets.sh   # requires Modal auth + vecinita-data-management secret
```

CI on `main`: `.github/workflows/ci.yml` must pass first. Then
`.github/workflows/deploy-preflight.yml` runs via `workflow_run` (needs GitHub `MODAL_TOKEN_*`
for secrets job).

**CD chain on `main`:** CI → Deploy preflight → Deploy Modal → Deploy DigitalOcean. Each step
uses `workflow_run` and checks out the CI-tested commit (`head_sha`).

**Modal CD on `main`:** `.github/workflows/deploy-modal.yml` runs after **Deploy preflight**
succeeds on `main`. Job order inside that workflow: **Supabase sync** (`config push` + migrations,
Resend SMTP via `SUPABASE_SMTP_PASS`) → **Modal deploy** (embedding, data-management, llm).
Requires repo secrets `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` and `SUPABASE_ACCESS_TOKEN`
([Modal continuous deployment](https://modal.com/docs/guide/continuous-deployment)).

**DigitalOcean CD on `main`:** `.github/workflows/deploy-digitalocean.yml` deploys the four
DO apps after **Deploy Modal** succeeds on `main` (EV-007 order: Supabase → Modal → DO).
`deploy_on_push` is **disabled** in `infra/do/*.yaml` so deploys are CI-gated. Requires repo
secret `DIGITALOCEAN_TOKEN`.

**Supabase on `main`:** `.github/workflows/supabase.yml` path-filters on `supabase/**` for
offline validate on PRs and feature branches. Production auth config, email templates, and
migrations are pushed on every main deploy via the Modal workflow's `supabase-sync` job after
CI passes (idempotent). Use `workflow_dispatch` on `supabase.yml` for manual `sync-production`.

**Resend:** No standalone deploy workflow. SMTP delivery is configured through Supabase
`config push` (`SUPABASE_SMTP_PASS` GitHub secret). In-app test-send uses `RESEND_API_KEY` on
the Modal DM secret — operator sync via `bash scripts/deploy/sync_modal_secret.sh --merge --apply`.
Database migrations are **not** automated — run `alembic upgrade head` per the Deploy order below.

## Deploy order

1. **Managed Postgres** — create DO database, enable `pgvector`, note connection string.
2. **Migrations + seed** (once per database):

   ```bash
   export DATABASE_URL='postgresql://...'   # or VECINITA_STAGING_DATABASE_URL
   cd apps/database && uv run alembic upgrade head
   uv run python -c "from vecinita_database.seeds.load import load_corpus; load_corpus()"
   ```

3. **Modal** (US workspace) — embedding, data-management, LLM:

   ```bash
   bash scripts/deploy/modal.sh
   ```

   Record embed/LLM URLs for ChatRAG secrets (D6/D7 on first deploy).

4. **DigitalOcean App Platform** — per [infra/do/README.md](../infra/do/README.md):

   ```bash
   export DIGITALOCEAN_TOKEN='...'
   uv run --with pydo --with pyyaml scripts/deploy/do_apps.py create-all
   ```

   - Deploy order: `internal-write-api` → `chat-rag-backend` → frontends (specs in `create-all`)  
   - Set secrets from [staging-secrets-matrix.md](staging-secrets-matrix.md) before apps go healthy.

   **EV-001 redeploy order:** Deploy `chat-rag-backend` (browse GET routes + CORS) and
   `internal-write-api` (PATCH tag routes) **before** frontends. Browse uses existing
   `VITE_VECINITA_CHAT_API_URL` — no new chat frontend secret; rebuild chat frontend after
   backend is live so H5 bundle includes `/api/v1/documents` and `/api/v1/tags`.

   **EV-002 redeploy order (TP-029):** `alembic upgrade head` → `internal-write-api` →
   `chat-rag-backend` → `data-management-frontend`. Modal apps do not need redeploy.

5. **Smoke** — after DO apps report running:

   ```bash
   export VECINITA_STAGING_CHAT_URL=https://<chat-rag-backend>.ondigitalocean.app
   export VECINITA_STAGING_WRITE_URL=https://<internal-write-api>.ondigitalocean.app   # optional H1
   export VECINITA_STAGING_DATABASE_URL='postgresql://...'   # H2; or reuse DATABASE_URL
   bash scripts/deploy/staging_smoke.sh
   bash scripts/deploy/verify_connectivity.sh
   ```

   Print env hints (API + frontend URLs):

   ```bash
   uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend
   export VECINITA_STAGING_ADMIN_API_URL=https://vecinita--vecinita-data-management-fastapi-app.modal.run
   ```

   Equivalent pytest (skips unset tiers):

   ```bash
   uv run pytest tests/smoke/test_staging_health.py tests/smoke/test_staging_gate.py tests/smoke/test_staging_latency.py tests/smoke/test_staging_connectivity.py tests/smoke/test_staging_ev002_admin.py -m live
   ```

## Operator env vars

| Variable | Tier | Required |
|----------|------|----------|
| `VECINITA_STAGING_CHAT_URL` | H1, H3, H4 | No — skip if unset |
| `VECINITA_STAGING_WRITE_URL` | H1 (write API), H4, H5 | No |
| `VECINITA_STAGING_CHAT_FRONTEND_URL` | H4, H5 | No — skip H4/H5 chat wiring if unset |
| `VECINITA_STAGING_ADMIN_FRONTEND_URL` | H4, H5 | No — skip admin wiring if unset |
| `VECINITA_STAGING_ADMIN_API_URL` | H4 (Modal jobs CORS) | No |
| `VECINITA_STAGING_DATABASE_URL` | H2 | No — falls back to `DATABASE_URL` |
| `VECINITA_STAGING_INTERNAL_API_KEY` | T3 (EV-002 admin) | No — skip `test_staging_ev002_admin.py` if unset |
| `DATABASE_URL` | H2 | No — used when staging-specific URL unset |
| `VECINITA_CORS_ORIGINS` | H4 (on API containers) | **Yes** on each FastAPI deploy — comma-separated frontend origins |

Never commit connection strings or API keys.

## Phase 4 gate checklist

Mark items in [execution-plan.md](sessions/S000-internal-docs-archive/execution-plan.md) Phase 4 Gate Check after evidence:

| Gate item | How to verify |
|-----------|----------------|
| CI pytest + vitest green | GitHub Actions `main` green |
| Staging H1–H3 | `staging_smoke.sh` or smoke pytest with URLs set |
| Cost ≤ $50 documented | [docs/sessions/S000-internal-docs-archive/reference.md#cost-monitoring-baseline-adr-004](reference.md#cost-monitoring-baseline-adr-004) |
| Data assets D1–D7 | [data-staging-state.md](data-staging-state.md) — D6/D7 after first Modal deploy |

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| H1 502/timeout | DO app not deployed; missing Modal URLs in ChatRAG secrets |
| H1 `modal_embed` not ok | Wrong `VECINITA_MODAL_EMBED_URL` (e.g. `fontface--` prefix or `/health` suffix) — see §Modal embed URL |
| H2 `no alembic revision` | Run `alembic upgrade head` against staging DB |
| H2 revision != head | Deploy newer code; re-run migrations |
| H3 empty answer | Corpus not seeded; embed/LLM Modal URLs wrong |
| H3 wrong language | Expected `en` or `es` for fixture question — check corpus |
| UI “Failed to fetch”, H3 pass | Missing CORS | Set `VECINITA_CORS_ORIGINS` on APIs; redeploy backends |
| H5 shows `localhost` | Frontend built without `VITE_*` | Set DO BUILD_TIME secrets; redeploy frontends |

## EV-004 coverage gate (F31) — CI smoke only

**No staging deploy** for EV-004. The coverage gate is enforced in GitHub Actions only.

| Check | How to verify |
|-------|----------------|
| Dedicated CI `coverage` job | `.github/workflows/ci.yml` — runs `make test-unit-coverage` (`--enforce` on summary script) |
| Local parity | `make test-unit-coverage` exits 0 when all twelve components ≥95% line + branch |
| Staging H1–H5 | **Unchanged** — no new secrets, CORS, or `VITE_*`; existing smokes still apply |
| Post-merge health | `bash scripts/ci/watch_github_ci.sh main` — `coverage` job must be green on `main` |

If the `coverage` job fails while `python` / `frontend` jobs pass, inspect `scripts/test/print_unit_coverage_summary.py` output for the failing component row.

## EV-006 (F35) — Admin user management + Resend email (S005)

Operator checklist for live invite delivery and `/admin/users*` on the Modal DM backend.
Secrets matrix: [staging-secrets-matrix.md](staging-secrets-matrix.md) §EV-006.

### Resend domain verification (prerequisite)

1. In the [Resend dashboard](https://resend.com/domains), add the sending domain and complete
   **SPF**, **DKIM**, and **DMARC** records (see secrets matrix §Deliverability DNS checklist).
2. Set `[auth.email.smtp] admin_email` / `sender_name` in `supabase/config.toml` to the verified
   address (e.g. `noreply@<domain>`).
3. After deploy, use **Send test email** on the DM `/users` page (UJ-037) or Resend dashboard
   to confirm inbox delivery before inviting operators.

### Invite / resend workflow

1. Ensure `SUPABASE_SECRET_KEY` is on the **Modal data-management** secret
   (`bash scripts/deploy/sync_modal_secret.sh --merge --apply`).
2. Ensure `SUPABASE_SMTP_PASS` (Resend API key) is in GitHub secrets and pushed to Supabase via
   `bash scripts/supabase/ci_sync.sh sync-production` on `main` (or manual `supabase config push`).
3. **First operator:** `uv run python scripts/seed_first_admin.py` (idempotent).
4. **Additional operators:** Admin signs in → `/users` → **Invite** → enter email + role → submit.
   Supabase sends the repo-versioned bilingual invite template via Resend SMTP.
5. **Pending invitee:** Admin → row action **Resend invite** → `POST /admin/users/{id}/resend-invite`.
6. **Password recovery (admin-triggered):** Row action **Reset password** sends recovery email.
7. **Disable / revoke:** Use **Disable** to ban; **Delete** to remove the identity (confirmation).

## EV-007 (F35 ext) — Invite acceptance redirect chain (#109)

Closes the production onboarding gap: email links must land on the deployed admin frontend
`/accept-invite`, not `localhost:3000`. Secrets matrix:
[staging-secrets-matrix.md](staging-secrets-matrix.md) §EV-007.

### Redeploy order (critical)

1. **Supabase `config push`** — merge to `main` runs `.github/workflows/supabase.yml`, or run
   `bash scripts/supabase/ci_sync.sh sync-production` manually. Updates `site_url` (staging-first)
   and `additional_redirect_urls` with `/accept-invite` and `/reset-password` full paths.
2. **Operator verification** — Supabase Dashboard → **Authentication** → **URL Configuration**
   must match `supabase/config.toml` (TC-109). Confirm `site_url` is the staging admin frontend,
   not `http://localhost:3000`.
3. **Modal DM secret** — set `VECINITA_ADMIN_FRONTEND_URL` (origin only, no trailing slash):
   `bash scripts/deploy/sync_modal_secret.sh --merge --apply`
4. **Modal deploy** — `bash scripts/deploy/modal.sh` (backend passes `redirect_to` on invite/resend/recovery).
5. **Admin frontend redeploy** — callback handling on `/accept-invite` and `/reset-password` (no new `VITE_*`).
6. **Live invite smoke (T3)** — fresh invite link opens staging `/accept-invite`; password set + login (13-deploy-smoke).

### Invitation lifecycle (EV-007)

- **Retract invitation** — row action for `status=invited` only → `POST /admin/users/{id}/revoke-invite`
  (distinct from **Delete user**).
- **Resend invite** — re-issues OTP with `redirect_to={VECINITA_ADMIN_FRONTEND_URL}/accept-invite`.
- **Expired link UX** — invitee sees bilingual in-app error on `/accept-invite` when `#error=otp_expired`.

### Force sign-out RPC (one-time operator apply)

The admin **Force sign-out** row action calls `POST /admin/users/{id}/signout`, which invokes the
`admin_delete_user_sessions` RPC on the Supabase project database. Apply the committed migration
once before relying on force sign-out in production:

```bash
# From repo root — review supabase/migrations/*admin_delete_user_sessions*.sql first
supabase db push   # or apply via Supabase SQL editor per operator policy
```

Until the RPC exists, the route returns `503 mechanism_unavailable` and the UI advises using
**Disable** as the guaranteed lockout. Verify with an admin test on `/users` (UJ-036).

### Deliverability test-send workflow (UJ-037)

1. Set `RESEND_API_KEY` and `RESEND_SENDER_EMAIL` on the Modal data-management secret
   (`bash scripts/deploy/sync_modal_secret.sh --merge --apply`).
2. Complete SPF/DKIM/DMARC on the Resend-verified domain (secrets matrix §Deliverability DNS).
3. On `/users`, use **Send test email** → confirm `message_id` in the UI and receipt in the inbox.
4. If secrets are unset, the UI links to this runbook and the API returns `503 email_unconfigured`.

### AC-U10–U16 checklist (S005 / M53)

| Criterion | Verify |
|-----------|--------|
| AC-U10 Idle timeout | Vitest TC-096; warning at 60s, local sign-out at 30min |
| AC-U11 Log out everywhere | Vitest TC-097; global vs local `signOut` scopes |
| AC-U12 Force sign-out | Integration TC-098 + e2e UJ-036; audit `user.signed_out` |
| AC-U13 Test-send | Integration TC-099 + e2e UJ-037; Resend mocked |
| AC-U14 User search + pagination | Integration TC-100 + Vitest search/pagination |
| AC-U15 Audit viewer | Vitest TC-101; entity_type filter + view-activity link |
| AC-U16 Privacy + CORS | Vitest TC-102; CORS preflight TC-103 on new POST routes |

Public self-signup remains disabled (`enable_signup = false` in `config.toml`); offline guard:
`bash scripts/check_supabase_config.sh`.

### Secret rotation (TP-S005-16)

| Secret | Where | Rotation steps |
|--------|-------|----------------|
| `SUPABASE_SMTP_PASS` / `RESEND_API_KEY` | GitHub Actions + Supabase project env + Modal DM | 1) Create new Resend API key. 2) Update `prod.env`. 3) `bash scripts/deploy/sync_github_secrets.sh --apply`. 4) `supabase config push` (or CI sync-production on `main`). 5) `bash scripts/deploy/sync_modal_secret.sh --merge --apply`. 6) Revoke old Resend key. |
| `SUPABASE_SECRET_KEY` | Modal data-management only | 1) Rotate in Supabase dashboard (Settings → API). 2) Update `prod.env`. 3) `bash scripts/deploy/sync_modal_secret.sh --merge --apply`. 4) Smoke `GET /admin/users` as admin. 5) Revoke old secret key. |

Never commit secret values. Use `--merge` on Modal pushes so rotation does not drop unrelated keys.

## Corpus protection (DO Managed Postgres)

The **corpus lives only on DO Managed Postgres** (`vecinita-staging` via `DATABASE_URL`).
Supabase holds auth identity only — corpus documents were never stored there.

### Prevent accidental wipes

Test helpers that `TRUNCATE` corpus tables (`seed_eval_corpus`, `reset_corpus_tables`) **refuse
any `DATABASE_URL` whose host ends in `.ondigitalocean.com`**. They only run against
local/CI Postgres (`localhost`, `127.0.0.1`, `postgres`).

**Do not** run `pytest`, `seed_eval_corpus()`, or `make test-py` with `prod.env` sourced unless
`DATABASE_URL` points at localhost. A July 2026 incident wiped ~40 ingested staging documents
when eval seed ran against staging.

Operator override (intentional staging reset only — destroys live corpus):

```bash
export VECINITA_ALLOW_CORPUS_RESET=1
export VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed
# then run the maintenance command
```

CI guard: `bash scripts/check_corpus_reset_guard.sh` (also in `make ci-guards`).

### Recovery via DigitalOcean backups

DO Managed Postgres includes **daily backups** for `vecinita-staging`. Verify:

```bash
set -a && source prod.env && set +a
bash scripts/infra/do_verify_staging_backups.sh
```

To restore corpus after accidental data loss:

1. DO control panel → **Databases** → `vecinita-staging` → **Backups** → **Restore** / **Fork**
   (pick a timestamp **before** the wipe — e.g. daily backup at 16:41 UTC).
2. Confirm `SELECT COUNT(*) FROM documents` on the forked cluster.
3. Update `DATABASE_URL` on `vecinita-chat-rag-backend` and `vecinita-internal-write-api`
   (DO dashboard or `scripts/deploy/do_apps.py sync-secrets`).
4. Re-run H2/H3 smoke.

Reference: [DO PostgreSQL restore from backups](https://docs.digitalocean.com/products/databases/postgresql/how-to/restore-from-backups/).

## Modal embed / LLM URLs (DO + GitHub)

Both backend DO apps require **`VECINITA_MODAL_EMBED_URL`** and **`VECINITA_MODAL_LLM_URL`**
(base Modal ASGI URLs — no `/health` suffix). Wrong values (e.g. legacy `fontface--` workspace
prefix) cause eval ingest/embed 404s and `dependencies.modal_embed != ok` on ChatRAG `/health`.

### Sync to DigitalOcean

```bash
set -a && source prod.env && set +a
# prod.env must include:
#   VECINITA_MODAL_EMBED_URL=https://vecinita--vecinita-embedding-embedding-api.modal.run
#   VECINITA_MODAL_LLM_URL=https://vecinita--vecinita-llm-fastapi-app.modal.run
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-internal-write-api
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-chat-rag-backend
```

`do_apps.py` validates URL shape before push (rejects `fontface--`, `/health`, wrong app host).

### Sync to GitHub (CD parity)

```bash
bash scripts/deploy/sync_github_secrets.sh --apply
```

Ensures `deploy-digitalocean.yml` materializes the same URLs on every `main` deploy.

### Verify live

```bash
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/staging_smoke.sh   # H1 asserts modal_embed/modal_llm ok
```

CI guards: `bash scripts/check_do_required_secrets.sh` (YAML + sync helper parity),
`scripts/deploy/ci_materialize_env.sh` (DO deploy job — required keys + validator).

## Related

- `scripts/deploy/staging_smoke.sh` — shell H1–H3  
- `tests/smoke/test_staging_health.py` — pytest H1–H3  
- `tests/smoke/test_staging_gate.py` — gate criteria + live skips  
- `tests/smoke/staging_h2.py` — shared H2 logic (pool + Alembic)
