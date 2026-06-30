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

**H4–H5 are required for UI sign-off** — see `.cursor/skills/connectivity-gates.md`.

## Pre-flight (before deploy)

```bash
bash scripts/deploy/verify_build.sh
bash scripts/deploy/verify_secrets.sh   # requires Modal auth + vecinita-data-management secret
```

CI on `main`: `.github/workflows/deploy-preflight.yml` (needs GitHub `MODAL_TOKEN_*` for secrets job).

**Modal CD on `main`:** `.github/workflows/deploy-modal.yml` auto-deploys the three Modal
apps after **CI** succeeds on `main` (re-runs build-smoke + secrets, then `scripts/deploy/modal.sh`).
Requires repo secrets `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`
([Modal continuous deployment](https://modal.com/docs/guide/continuous-deployment)).
**DigitalOcean CD on `main`:** `.github/workflows/deploy-digitalocean.yml` deploys the four
DO apps after **CI** succeeds on `main` (via `scripts/deploy/do_apps.py`). `deploy_on_push` is
**disabled** in `infra/do/*.yaml` so deploys are CI-gated (push-webhook deploys would bypass CI).
Requires repo secret `DIGITALOCEAN_TOKEN`.
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

Mark items in [execution-plan.md](execution-plan.md) Phase 4 Gate Check after evidence:

| Gate item | How to verify |
|-----------|----------------|
| CI pytest + vitest green | GitHub Actions `main` green |
| Staging H1–H3 | `staging_smoke.sh` or smoke pytest with URLs set |
| Cost ≤ $50 documented | [docs/reference.md#cost-monitoring-baseline-adr-004](reference.md#cost-monitoring-baseline-adr-004) |
| Data assets D1–D7 | [data-staging-state.md](data-staging-state.md) — D6/D7 after first Modal deploy |

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| H1 502/timeout | DO app not deployed; missing Modal URLs in ChatRAG secrets |
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

Public self-signup remains disabled (`enable_signup = false` in `config.toml`); offline guard:
`bash scripts/check_supabase_config.sh`.

### Secret rotation (TP-S005-16)

| Secret | Where | Rotation steps |
|--------|-------|----------------|
| `SUPABASE_SMTP_PASS` / `RESEND_API_KEY` | GitHub Actions + Supabase project env + Modal DM | 1) Create new Resend API key. 2) Update `prod.env`. 3) `bash scripts/deploy/sync_github_secrets.sh --apply`. 4) `supabase config push` (or CI sync-production on `main`). 5) `bash scripts/deploy/sync_modal_secret.sh --merge --apply`. 6) Revoke old Resend key. |
| `SUPABASE_SECRET_KEY` | Modal data-management only | 1) Rotate in Supabase dashboard (Settings → API). 2) Update `prod.env`. 3) `bash scripts/deploy/sync_modal_secret.sh --merge --apply`. 4) Smoke `GET /admin/users` as admin. 5) Revoke old secret key. |

Never commit secret values. Use `--merge` on Modal pushes so rotation does not drop unrelated keys.

## Related

- `scripts/deploy/staging_smoke.sh` — shell H1–H3  
- `tests/smoke/test_staging_health.py` — pytest H1–H3  
- `tests/smoke/test_staging_gate.py` — gate criteria + live skips  
- `tests/smoke/staging_h2.py` — shared H2 logic (pool + Alembic)
