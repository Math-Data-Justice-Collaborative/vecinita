# Staging runbook (Phase 4)

> **Purpose:** Operator checklist for staging deploy and H1–H3 health tiers (QA-006).  
> **Health tiers:** `.cursor/skills/deployment-catalog.md`, `15-service-health`  
> **Secrets:** [staging-secrets-matrix.md](staging-secrets-matrix.md)

## Env role: staging vs prod (ADR-054 / F83)

**Target (after dual-env provision):** resolve `env_role` as `staging` or `prod` only.

| Role | Resources |
|------|-----------|
| **staging** | DO project **first-project** — apps `vecinita-staging-*` + Postgres **`vecinita-staging-db`** (nyc); Droplet `vecinita-staging-obs`; Supabase `vecinita-staging` (`camkatfbjguwvymfgdme`); Modal Environment **`staging`** |
| **prod** | DO project **vecinita** — apps without `vecinita-staging-` prefix; Postgres display name **`vecinita-staging-restored-20260701`** (operator alias **`vecinita-prod-db`** — DO cannot rename managed clusters; EV-323); Modal Environment **`main`**; Supabase ref `cfuvghdsuwactfeamtym` |

Cite [ADR-054](adr/ADR-054-distinct-staging-and-production.md). Staging corpus = migrations + seed;
live corpus mutate / promote still needs AskQuestion (`no-live-prod-corpus-push`).

### Idle cost posture (EV-354 / #354 / AC-ST9–14)

Default staging to **cheap when idle**, still effective for Stage→Main:

| Lever | Default |
|-------|---------|
| Modal Environment `staging` embed | `VECINITA_EMBED_MIN_CONTAINERS=0` (scale-to-zero) |
| Staging LLM / playground / FT / rerank | Deployed; scale-to-zero (not always-warm) |
| Obs droplet `vecinita-staging-obs` | **Powered off** until Grafana/Loki drill (EV-323-D13) |
| Promote smoke | **Warm** Modal services, then H1–H5 / `staging-smoke` (UJ-095) |

Soft target: maximize safe idle savings and document delta — no hard staging-only $ cap.
Do **not** destroy `vecinita-staging-restored-20260701` (prod DB display name — EV-323-D10).

**Warm-before-smoke (operator or CI):**

```bash
# Staging Modal URLs + proxy key from secrets matrix (never commit keys)
export MODAL_ENVIRONMENT=staging
uv run python scripts/ops/warm_staging_for_smoke.py
bash scripts/deploy/staging_smoke.sh
# or: uv run pytest tests/smoke/test_staging_health.py -m live -q
```

CI: `deploy-staging.yml` `staging-smoke` runs `scripts/ops/warm_staging_for_smoke.py`
before H1–H3 (TC-326 / UJ-095).

**Operational status (2026-08-28):** Distinct staging H1–H5 passed. Resolve `env_role` as
`staging` or `prod` — do **not** use `staging_as_live` for the new `vecinita-staging-*`
stack. Legacy DO app hostnames without the `vecinita-staging-` prefix remain **prod**.
[ADR-049](adr/ADR-049-single-env-staging-as-live.md) is historical for the single-env era.

## Branch protection / merge gate (F83 / ADR-050 / ADR-054 / EV-033)

`main` must use a GitHub **ruleset** (or classic branch protection) that requires:

1. Project CI green for the PR tip SHA (`CI success` from `ci.yml`)
2. **Staging deploy + H1–H5 smoke** green for that same SHA (`staging-smoke`, GitHub Environment `staging`)

Do not merge to `main` when either check is red/missing unless an explicit waiver AskQuestion.
Prefer Environments: `staging` (PR / pre-merge) and `production` (post-merge CD on `main`).

**Agent rule:** Always-applied `.cursor/rules/stage-before-main.mdc` (EV-033 / AC-ST8 /
EV-036-D15) — agents must (1) open feature/evolve PRs into **`stage` first** when that
branch exists, (2) not treat PRs as merge-ready or open/merge to `main` without CI +
`staging-smoke` (or a recorded waiver). Distinct from `.cursor/rules/ci-after-push.mdc`
(watch CI **after** push).

**Promotion model (EV-036-D15):** When `origin/stage` exists:
**feature branch → PR into `stage` (CI) → promote PR `stage`→`main` (CI + `staging-smoke`) → prod CD**.
`staging-smoke` runs on PRs targeting **`main`** (`deploy-staging.yml`), not on the
feature→`stage` hop. When `stage` does not exist yet: AskQuestion to create it from `main`
before the first integration PR (do not silently PR to `main`). Smoke on the tip SHA remains
required for any `main` merge (ADR-054 / #212).

**After promote (DO staging deploy branches):** Staging apps normally track **`main`**. If an
app was temporarily pointed at `stage` (e.g. `vecinita-staging-write-api` for pre-promote
smoke), flip its GitHub deploy `branch` back to **`main`** after the promote PR merges so
staging stays aligned with production CD. Do not leave staging permanently on `stage`
unless an AskQuestion records that exception.

## CI/CD before promote (RET-002 / ADR-050)

Tip SHA must be **green** before deploy-ready, promote, or cutover:

```bash
bash scripts/ops/require_ci_green.sh          # default: current branch
bash scripts/ops/require_ci_green.sh main     # live cutover
```

Wraps `scripts/ci/watch_github_ci.sh` (CI always; deploy-preflight on `main`). **Red /
cancelled = hard stop** unless an explicit waiver AskQuestion. Prefer enabling GitHub
**branch protection** required checks on `main` (ci.yml + deploy-preflight) when the org allows.

Cite [ADR-050](adr/ADR-050-ci-cd-blocks-live-deploy.md). Approved live ops: `scripts/ops/`
(`--dry-run` default; `--approve` only after AskQuestion).

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

**CD chain on `main`:** CI → Deploy preflight → Deploy Modal → Deploy DigitalOcean →
**Release** (semver tag + GitHub Release; F63 / #103). Each step
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

**Release on `main`:** `.github/workflows/release.yml` runs after **Deploy DigitalOcean**
succeeds. Creates the next strict `vX.Y.Z` patch tag + GitHub Release (skips on
`[skip release]` or if HEAD is already tagged).

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

3. **Modal** (workspace `vecinita`) — embedding, data-management, LLM:

   **One-time (staging Environment):**
   ```bash
   modal profile activate vecinita   # or existing MODAL_TOKEN_* for workspace vecinita
   modal environment create staging
   modal environment update staging --set-web-suffix staging
   ```

   **Deploy staging:**
   ```bash
   export VECINITA_MODAL_WORKSPACE=vecinita
   export MODAL_ENVIRONMENT=staging
   bash scripts/deploy/modal.sh
   ```

   **Deploy prod** (Environment `main`):
   ```bash
   export VECINITA_MODAL_WORKSPACE=vecinita
   unset MODAL_ENVIRONMENT   # or export MODAL_ENVIRONMENT=main
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

   **Audit actor index (20260707_0008):** Before deploy smoke for the user-activity hotfix,
   confirm `alembic current` includes revision `20260707_0008` on staging Postgres so
   `GET /internal/v1/audit?actor_id=…` uses `ix_audit_log_actor_id_created_at`.

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

## EV-036 (F84) — Staging observability (Grafana / Loki / Alertmanager)

**Status:** Compose shipped under [`infra/observability/`](../infra/observability/README.md)
([ADR-055](adr/ADR-055-operational-monitoring-grafana-loki.md)). Droplet bring-up is
operator-run (staging only).

| Piece | Intent |
|-------|--------|
| Compose | `infra/observability/` on a **small staging Droplet** (`s-1vcpu-1gb`, not App Platform) |
| Grafana | Modal + DO overview dashboard; optional `VECINITA_GRAFANA_URL` |
| Loki | Retention **168h**; Alloy drops/redacts prompt-like keys (ADR-004 / F17) |
| Alertmanager | ≥1 rule → `VECINITA_ALERTMANAGER_WEBHOOK_URL` (staging secret) |
| Checklist | [`infra/observability/CHECKLIST-tc305-tc306.md`](../infra/observability/CHECKLIST-tc305-tc306.md) (TC-305/306) |
| Prod | **Deferred** until cost AskQuestion (ADR-004 ≤$50) |

Do **not** point prod log shippers at staging Loki. Do not enable live prod corpus mutate
from monitoring tools.

### Bring-up (operator)

```bash
# Auth: DIGITALOCEAN_TOKEN in repo-root .env (gitignored), or doctl auth init
set -a && source .env && set +a
export DIGITALOCEAN_ACCESS_TOKEN="$DIGITALOCEAN_TOKEN"
bash scripts/deploy/create_staging_obs_droplet.sh

# On Droplet (after create):
# rsync infra/observability/ root@<ip>:/opt/vecinita-obs/
# cp .env.example .env  # set GRAFANA_ADMIN_PASSWORD
# docker compose up -d
# Complete CHECKLIST-tc305-tc306.md
```

**Live (2026-08-30 create; EV-323 power-off 2026-09-04):** Droplet `vecinita-staging-obs`
(id `596408528`) / `159.203.137.236` (nyc3), `s-1vcpu-1gb` (~**$6/mo** when on).
**Default cost posture (EV-323-D13):** keep droplet **powered off** until staging Grafana/Loki
is needed; power on via DO UI or
`doctl compute droplet-action power-on 596408528`. Services bind **loopback** — public curl
to :3000/:80 times out by design; tunnel Grafana after power-on:

```bash
ssh -L 3000:127.0.0.1:3000 root@159.203.137.236
# then open http://127.0.0.1:3000  (password in /opt/vecinita-obs/.env on host)
```

**EV-323 cost note:** Droplet still bills while powered on even if unused. Destroy only after
separate AskQuestion (recreate via `create_staging_obs_droplet.sh`).

TC-306 drill: Alertmanager → compose `webhook-sink` received synthetic alert with no
chat content fields (PASS). Replace sink URL with a real staging webhook when ready.

## EV-311 — Close cold-start umbrella on evidence (#311)

**Status:** Spec locked 2026-09-04 (close on evidence).  
**ADR:** [ADR-022 §Amendment EV-311](adr/ADR-022-gpu-memory-snapshot-cold-start.md).

### Procedure (staging only)

```bash
# Requires Modal CLI auth + staging LLM URL + proxy key (never commit secrets)
export MODAL_ENVIRONMENT=staging
# Optional: ensure snapshots stay on at next deploy (deploy-shell env, not Secret alone)
# export VECINITA_LLM_GPU_SNAPSHOT=true

# After LLM deploy: seed snapshots first (EV-315 / TC-315-02) — see §EV-315 below

# Restore smoke (TC-311-01 / TC-314-02) — synthetic prompts only
# --force-cold lists staging containers then stops vecinita-llm ids (Modal CLI 1.5+)
uv run python scripts/ops/cold_start_bench.py \
  --n 20 --force-cold --modal-env staging \
  --llm-url "$VECINITA_STAGING_MODAL_LLM_URL" \
  --proxy-key "$VECINITA_MODAL_PROXY_KEY" \
  --output ~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-311-infra-sub-second-chatrag-latency-on-cheap-server/evidence/cold-smoke.json

# Optional publishable p95
# uv run python scripts/ops/cold_start_bench.py --n 100 --force-cold --output …/cold-p95.json

# E2E ChatRAG ask path (TC-311-02) — staging ChatRAG URL
uv run python scripts/ops/cold_start_bench.py --mode chat-ask \
  --chat-url "$VECINITA_STAGING_CHAT_URL" --n 5 \
  --output …/chat-ask-smoke.json
# and/or: bash scripts/deploy/staging_smoke.sh (H3)
```

### Close rules

| Band | Action |
|------|--------|
| **Green** (restore p50 &lt;1s, p95 &lt;3s) | Fill ADR frontier table; close #311 |
| **Useful** (planning band ~1–2s / ~3–10s; no 504) | Fill frontier; close #311 with honest Useful cite |
| **Red** | Do **not** close; investigate / consider snapshot disable |

Do **not** `modal container stop` on prod Environment `main` without AskQuestion.  
Related ops: [§EV-315](#ev-315--seed-gpu-snapshots-after-deploy-315) seed · #317 thin ingress · #319 scaledown.

## EV-315 — Seed GPU snapshots after deploy (#315)

**Goal:** After staging LLM deploy (GPU snapshots on), prime authenticated `/warm` so the
first real user hits **restore**, not ~70s **create**.  
**ADR:** [ADR-022 §Amendment EV-315](adr/ADR-022-gpu-memory-snapshot-cold-start.md).  
**Prod:** AskQuestion before any prod prime (default Environment is staging).  
**CI:** Optional advisory only — not a hard CD gate.

### Procedure (staging)

```bash
source .env   # or export VECINITA_STAGING_MODAL_LLM_URL + VECINITA_MODAL_PROXY_KEY
export MODAL_ENVIRONMENT=staging

# 1) Trigger captures (side effect). Exit 1 without kinds is expected (fail-closed).
uv run python scripts/ops/seed_gpu_snapshots.py \
  --modal-env staging \
  --llm-url "$VECINITA_STAGING_MODAL_LLM_URL" \
  --proxy-key "$VECINITA_MODAL_PROXY_KEY" \
  --max-primes 3

# 2) Capture cold_kind stamps from Modal logs (create latency is separate from restore p50/p95)
modal app logs vecinita-llm -e staging --tail 500 --timestamps > /tmp/vecinita-llm-seed-logs.txt
# Evidence lines (either is enough for --kinds-file):
#   cold_start_stamp … 'cold_kind': 'snapshot_restore'
#   Restoring Function from memory snapshot.
#   Creating memory snapshot…  (create path — document latency separately)

# 3) Fail-closed evaluate (exit 0 only when snapshot_restore observed)
uv run python scripts/ops/seed_gpu_snapshots.py --kinds-file /tmp/vecinita-llm-seed-logs.txt
```

Document **create** wall time separately from restore percentiles (Layer E / #314 harness).
Do not conflate seed primes with FE mount `prewarm_to_ready` (#318).

### Pass / fail

| Result | Meaning |
|--------|---------|
| Exit 0 on `--kinds-file` / `--observed-kinds` | Restore-kind observed (TC-315-02) |
| Exit 1 after live `/warm` only | Expected until kinds supplied — not a silent PASS |
| Create-only kinds | Fail closed; re-prime / investigate snapshots |

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

The **corpus lives only on DO Managed Postgres**.

| Env | Cluster display name (DO) | Operator alias | Typical env |
|-----|---------------------------|----------------|-------------|
| Staging | `vecinita-staging-db` | staging corpus | `VECINITA_STAGING_DATABASE_URL` |
| Production | `vecinita-staging-restored-20260701` | **`vecinita-prod-db`** (cannot rename on DO) | `DATABASE_URL` on prod DO apps |

**EV-323:** Do **not** destroy the restored-named cluster — it is live prod (ChatRAG + write API).
Confirm hosts differ before any wipe/mirror ([corpus-db-safety](../.cursor/skills/corpus-db-safety/SKILL.md)).

`DATABASE_URL` / staging URLs whose host ends in `.ondigitalocean.com` are **Managed**.
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

### Prod → staging corpus mirror (EV-338 / #338)

Use when staging Managed Postgres was emptied (e.g. test-artifact cleanup) and staging
ChatRAG needs a **community corpus** that matches prod retrieval quality. Prefer this over
fixture-only `load_corpus()` when parity with live content matters.

[Corpus: staging] [Corpus: feature-list.md §F83] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md]
[Corpus: corpus-db-safety] [Corpus: no-live-prod-corpus-push]

**Hard rules**

| Rule | Detail |
|------|--------|
| Prod | **Read-only** — never `TRUNCATE` / restore / write against the prod corpus URL |
| Staging write | Only after AskQuestion Approve + `VECINITA_ALLOW_CORPUS_RESET=1` and `VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed` |
| Hosts | Confirm `VECINITA_STAGING_DATABASE_URL` host ≠ prod `DATABASE_URL` host before any dump target |
| Artifacts | After restore, zero `example.com` / `fixture://` / localhost document URLs |

**Include tables (ChatRAG retrieval)** — dump in FK-safe order; feasibility / execute may add
companion tables only if restore requires them:

1. `tags`
2. `documents`
3. `chunks`
4. `embeddings`
5. `document_tags`
6. `chunk_tags`

**Exclude (default):** `jobs`, eval_* , `rebuild_runs`, `shadow_chunks`, `shadow_embeddings`,
automation run tables, operation metrics, feedback. Do not wipe staging jobs history as part of
this mirror unless a separate AskQuestion says so.

**Procedure (dry-run first)**

1. Resolve hosts (print only hostnames, never paste passwords into docs/tickets):

   ```bash
   python3 - <<'PY'
   import os
   from urllib.parse import urlparse
   for key in ("VECINITA_STAGING_DATABASE_URL", "DATABASE_URL", "VECINITA_PROD_DATABASE_URL"):
       raw = os.environ.get(key) or ""
       if not raw:
           print(f"{key}: (unset)")
           continue
       print(f"{key}: {urlparse(raw).hostname}")
   PY
   ```

2. Confirm staging host is the emptied ChatRAG DB; prod host is the live corpus source.
3. `pg_dump` from **prod** (`--data-only` / table list above; no `--clean` against prod).
4. On staging: migrations current (`alembic upgrade head`), then restore dump with corpus-reset
   override set. Prefer truncate/replace of **include** tables only — not a full DB wipe.
5. Counts: `documents`, `chunks`, `embeddings` all `> 0`.
6. Test-artifact guard dry-run:

   ```bash
   uv run python scripts/ops/cleanup_corpus_test_artifacts.py \
     --database-url "$VECINITA_STAGING_DATABASE_URL"
   # expect zero matches (or apply cleanup only on staging after ack)
   ```

7. H2 / H3: `bash scripts/deploy/staging_smoke.sh` (or equivalent) with staging ChatRAG URL.
8. Record evidence in the active session `evidence/` folder (counts + smoke exit codes).

**Embed model alignment:** Mirrored vectors must match the embed model ChatRAG uses for
queries. Staging DO apps **and** GitHub Environment `staging` secret
`VECINITA_MODAL_EMBED_URL` must use the **`vecinita--`** embedding base (same model that
produced prod vectors) — not `vecinita-staging--` — or retrieval scores collapse (~0.02)
and H3 returns the no-context fallback. See [staging-secrets-matrix.md](staging-secrets-matrix.md).
Deploy Staging runs `scripts/deploy/check_staging_embed_mirror_align.sh` before secret sync
(BUG-2026-09-03-staging-embed-url-mirror-regress). After correcting the URL, redeploy
`vecinita-staging-chat-api` (and write-api if ingest uses embed). Waiver only when staging
intentionally re-embeds under the staging Modal Environment pin:
`VECINITA_ALLOW_STAGING_EMBED=1`.

**Alternatives:** DO backup restore (section above) when a pre-wipe staging snapshot exists;
fixture `load_corpus()` for empty/dev-shaped staging only.

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

## EV-025 (F70–F71) — Staging shadow rechunk before promote

Multilingual cutover (S027-D21): **staging first** — shadow rebuild → F36 EN/ES report →
operator promote — then repeat on prod. Do not promote prod until staging promote is accepted.

### Secrets / pins (staging DO + Modal)

| Variable | Expected (planned E1) | Notes |
|----------|----------------------|-------|
| `VECINITA_EMBEDDING_MODEL_ID` | `intfloat/multilingual-e5-small` | F70 pin; final after F36 review (S027-D14) |
| `VECINITA_CHUNK_TOKENIZER_ID` | **same as embed pin** | ADR-048 / S027-D15 — default in code matches E1 (T120.2) |
| `VECINITA_EMBED_RUNTIME` | `fastembed` (or `sentence_transformers` / `onnx`) | Modal embed app |
| `VECINITA_MODAL_EMBED_URL` | `https://vecinita--vecinita-embedding-…` | Must serve F70 pin before rebuild |

Sync with `do_apps.py sync-all-secrets` after pin changes (see §Modal embed / LLM URLs).

### Shadow rebuild checklist

1. Confirm Modal embed `/health` (or warm) serves the F70 pin at 384-d.
2. Enqueue F41 `job_type=rebuild` with `mode=rechunk`, `dry_run=true`, stamps
   `embedding_model_id` + `chunk_tokenizer_id` = pin (defaults match E1 after T120.2/T120.3).
3. Confirm Alembic head includes `20260805_0013` (`chunk_tokenizer_id` on `rebuild_runs` /
   `document_revisions`) before create/promote.
4. Run F36 against shadow (`rebuild_run_id` on eval config). Capture EN/ES Hy1
   answer relevancy + faithfulness vs E0, plus dense hit@k / mean_rank when the harness
   provides them (UJ-076 / TC-235–236 / S027-D18).
5. Open advisory report:
   `GET /internal/v1/rebuild/{rebuild_run_id}/embed-promote-report`
   — expect `candidate_embedding_model_id` = pin, `baseline_embedding_model_id` =
   `BAAI/bge-small-en-v1.5` (E0), `by_language.en|es` with `answer_relevancy`,
   `faithfulness`, nested `baseline_e0`, and `dense_available` + ranks when present.
6. Operator judgment promote (no hard numeric gate — S027-D11); retain E0 revision for
   rollback (TC-239 / S027-D22).
7. Only then repeat the sequence on prod (M121 / TC-240 staging-then-prod).

**Local verification:** `make test-py` (compose) covers rebuild stamps + promote + report
shape (`tests/e2e/test_uj076_embed_promote_report.py`). Remote CI is unit-only (S027-D34).

### Prod cutover (M121 / TC-240)

**Order is mandatory (S027-D21 / AC-ME6):** complete staging shadow → F36 → operator promote
**before** any prod rebuild promote. Do not start prod cutover until staging promote is
accepted and ChatRAG smoke (H4/H5) looks healthy on staging.

1. Sync the same F70 pin secrets on **prod** DO + Modal (`VECINITA_EMBEDDING_MODEL_ID` /
   `VECINITA_CHUNK_TOKENIZER_ID` = E1; embed URL serves the pin).
2. Repeat the staging checklist on prod: shadow `mode=rechunk` → F36 EN/ES report →
   **operator judgment** promote (no hard numeric abort — S027-D11).
3. Record prod `rebuild_run_id`, revision stamps, and eval links in the session deploy notes.
4. Live prod smoke remains **13-deploy-smoke** (H1–H5); this runbook is the operator
   procedure for 07–12.

### E0 rollback (M121 / TC-239 / AC-ME9)

If post-promote retrieval regresses, restore the prior **E0** corpus via F41 — do **not**
re-`POST …/promote` on an already-`promoted` run (idempotent; does not re-copy shadow).

1. Note prior live chunk text / revision stamps (or use retained E0 shadow artifacts).
2. Create a **new** rebuild run stamped with `LEGACY_E0` =
   `BAAI/bge-small-en-v1.5` for both `embedding_model_id` and `chunk_tokenizer_id`
   (`mode=rechunk`, `dry_run=true`, `force=true` as needed).
3. Shadow-batch the prior E0 chunk text + embeddings for affected documents.
4. Mark the run `completed`, then promote.
5. Confirm live chunks match the E0 restore text and latest `document_revisions` stamps
   are `BAAI/bge-small-en-v1.5` (unit/e2e: `test_f71_e0_rollback` / UJ-076 T121.1).

**E0 rollback** is runbook-proven in CI unit/schema + local compose e2e when Docker works
(S027-D35 waive otherwise); live staging/prod rollback drill is optional at 13.

## EV-027 (F75–F77) — Flags-off posture (in-tree; live enable deferred)

S030 closed with **cutover deferred** (S030-D64). Catch-up, freshness, and LoRA train/promote
are **implemented in-tree** and must stay **disabled** on the live stack until an explicit
AskQuestion approve. [Corpus: feature-list.md §F75–F77]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Corpus: staging]

**Do not** enable automations or promote an FT adapter on live/prod from this runbook alone.
See [no-live-prod-corpus-push.mdc](../.cursor/rules/no-live-prod-corpus-push.mdc).

### Safe-off defaults

| Knob | Safe value | Notes |
|------|------------|-------|
| `VECINITA_AUTOMATIONS_KILL_SWITCH` | on / true | Blocks F75 enqueue and F77 train start |
| Automations enable (DM UI / `automation_settings.enabled`) | **false** | Catch-up does not run |
| Per-source `refresh_enabled` | operator-controlled; treat live as **off** until approved | F76 |
| `VECINITA_FINETUNE_ADAPTER_ID` | unset / empty | Prod `vecinita-llm` stays base Qwen |
| FT train approve / promote | not invoked | Human promote only after eval evidence |

### Kill-switch and caps

- One shared Modal schedule on `vecinita-data-management` dispatches `job_type=automation_catchup`
  then `freshness_refresh` (ADR-052). Distinct enable flags still apply.
- FT caps: `VECINITA_FINETUNE_MAX_CONCURRENT` (default 1),
  `VECINITA_FINETUNE_MAX_RUNS_PER_DAY` (default 3).
- Secrets matrix: [staging-secrets-matrix.md](staging-secrets-matrix.md) §EV-027. Do not enable
  until DO/Modal secret sync lists include these keys.

### CD / deploy debt (document, do not invent)

- `vecinita-llm-finetune` may be omitted from CD / `modal.sh` (accepted S030-D59). Flags-off
  13-smoke is the standing posture; deploying FT CD is **not** implied by this section.
- Session checklist: [sessions/S030-corpus-automations/reports/deploy-checklist.md](sessions/S030-corpus-automations/reports/deploy-checklist.md).
- Live Alembic may lag tip (`20260806_0014` vs `20260812_0016`) — apply migrations only with
  corpus-safety gates; enabling F75/F76 without the schema is unsupported.

### Enable / promote (AskQuestion required)

1. Staging-first evidence (local compose + flags-off smoke already recorded in S030).
2. AskQuestion `[Decision]` for **live enable** of F78/F79 and/or **F80 promote** onto
   `vecinita-llm`. Recommended default: defer / runbook-only.
3. Proceed only after an explicit approve option — then follow operator steps in
   [runbooks/corpus-operator-guide.md](runbooks/corpus-operator-guide.md).

### EV-031 live enable sequence (F78 + F79 + F80 eval path)

**Cycle:** EV-031 · **Decision:** S035-D1–D3  
**Scope:** F78 catch-up + F79 freshness live; F80 playground eval only (no prod promote).

| Step | Action |
|------|--------|
| 1 | Ship secrets/CD parity (M131–M132) — flags still safe-off |
| 2 | CD deploy green on `main` |
| 3 | **AskQuestion** — approve live F78/F79 enable |
| 4 | Set `VECINITA_AUTOMATIONS_ENABLED=true`, `VECINITA_FRESHNESS_ENABLED=true`, `VECINITA_AUTOMATIONS_KILL_SWITCH=true` |
| 5 | `sync_github_secrets.sh --apply` + DO sync + redeploy |
| 6 | Post-enable smoke H1–H5 (kill-switch ON — no jobs yet) |
| 7 | Set `VECINITA_AUTOMATIONS_KILL_SWITCH=false`; observe bounded catch-up/freshness |
| 8 | Verify DM run history (TC-289); re-run H1–H3 |
| 9 | Enable F80 eval: deploy `vecinita-llm-finetune`; `VECINITA_FINETUNE_ENABLED=true`; **leave** `VECINITA_FINETUNE_ADAPTER_ID` empty |
| 10 | Confirm TC-292/293; record AC-AU7/FR7/FT10 |

**Rollback:** kill-switch ON → `*_ENABLED=false` → DO redeploy → H1–H5.

## Feedback operator notify — Resend (F68 / #214)

Code ships with EV-214. Email notify stays **off** until secrets are set on internal-write.

| Variable | Role |
|----------|------|
| `VECINITA_FEEDBACK_NOTIFY_EMAIL` | Operator **To** inbox |
| `RESEND_API_KEY` | Resend API key for **this environment** (same value as that env’s Modal DM / SMTP pass — EV-305) |
| `RESEND_SENDER_EMAIL` | Verified **From** for this env (staging e.g. `noreply+staging@josephcmcg.com`; prod e.g. `noreply@josephcmcg.com`) |
| `VECINITA_FEEDBACK_NOTIFY_WEBHOOK` | Optional; leave unset for email-only |

### Dual Resend path (EV-305 / #305)

Same Resend **account**; staging and prod use **different API keys** and From addresses.
Do **not** put the prod `re_` key on staging Modal, staging write-api, or staging Supabase SMTP.
See [staging-secrets-matrix.md](staging-secrets-matrix.md) §Dual Resend path.

**Provision staging key (#306):** Resend dashboard → API key labeled staging → add From
`noreply+staging@josephcmcg.com` on the verified domain → store in operator `.env` / GH Env
`staging` only.

**Wire stacks (#307):** sync staging Modal DM (`MODAL_ENVIRONMENT=staging`),
`vecinita-staging-write-api`, and staging Supabase `SUPABASE_SMTP_PASS` from the staging key.
Replace any prior staging `RESEND_*` that still matched prod (EV-feedback-notify-secrets).

> **Warning:** Root `supabase/config.toml` is **prod-oriented** (`site_url` / redirects /
> `admin_email`). Do **not** run `supabase config push --project-ref camkatfbjguwvymfgdme`
> from the repo root without a staging override workdir (staging admin FE URLs +
> `noreply+staging@…` From). A bare push overwrites staging Auth redirects with prod
> (caught and restored in EV-305).

### Staging enable

1. AskQuestion approve staging (EV-feedback-notify-secrets / EV-305).
2. Ensure **staging** `RESEND_*` + `VECINITA_FEEDBACK_NOTIFY_EMAIL` in operator `.env` (not prod key).
3. Sync **staging only**:

```bash
set -a && source .env && set +a
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py \
  sync-secrets --name vecinita-staging-write-api
```

4. Smoke (#308): after notify code is on the staging image (#212 promote or temp branch),
   `POST` anonymous feedback to staging write-api → Resend delivery to the To inbox.
   Confirm Resend dashboard traffic on the **staging** key. Notify failure must not roll back
   the store (ADR-046).

### Prod enable

**AskQuestion required** before syncing `vecinita-internal-write-api`. Do not copy staging
values to prod without an explicit approve.

[Corpus: feature-list.md §F68]
[Spec: docs/adr/ADR-046-anonymous-community-feedback.md]
[Corpus: staging-secrets-matrix]
[Corpus: ADR-054] #305 #306 #307 #308 #309

## Related

- `scripts/deploy/staging_smoke.sh` — shell H1–H3  
- `tests/smoke/test_staging_health.py` — pytest H1–H3  
- `tests/smoke/test_staging_gate.py` — gate criteria + live skips  
- `tests/smoke/staging_h2.py` — shared H2 logic (pool + Alembic)
