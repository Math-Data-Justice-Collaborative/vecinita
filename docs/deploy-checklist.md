# Deploy Checklist

> **Generated**: 2026-05-25 (EV-001 delta update)
> **Status**: **ready** (pending D7 formal verification — operator action)
> **Deployment plan**: [deployment-integration.md](deployment-integration.md)
> **Stage**: 12-verify-deploy (EV-001 delta)
> **Previous run**: 2026-05-19 (v1) → blockers resolved 2026-05-21 (13-deploy-smoke)

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete (no gaps) | **PASS** | DO YAMLs, Modal apps, runbook, deploy scripts present; no `⚠️ Needs human input` |
| All secrets configured | **PASS** (fixed) | Staging secrets matrix corrected (12-verify-deploy): name fix `VECINITA_INTERNAL_WRITE_URL`, 5 EV-001 optional vars added, 2 DO write API vars added for retag |
| Data assets staged | **PASS** (D7 advisory) | D1–D6, D8–D9 verified; D7 `staged_procedure` — LLM live, formal verify in 13 |
| Resource allocation verified | **PASS** | No new GPU; LLM tagging reuses T4; cost within ≤ $50/mo cap |
| Rollback plan reviewed | **APPROVED** | User sign-off 2026-05-25; option A (leave tag tables on rollback) |
| H0c CORS unit tests pass | **PASS** | TC-046 browse GET, TC-049 admin PATCH, DELETE preflight |
| Frontend `VITE_*` ↔ API URL matrix complete | **PASS** | Browse shares `VITE_VECINITA_CHAT_API_URL`; admin uses `VITE_VECINITA_CORPUS_API_URL` |
| `VECINITA_CORS_ORIGINS` documented per API service | **PASS** | chat-rag-backend + internal-write-api in staging-secrets-matrix |
| Post-deploy H4–H5 command documented | **PASS** | `verify_connectivity.sh` updated (T19.3, T19.5) |

### EV-001 specific checks

| Check | Result | Evidence |
|-------|--------|----------|
| Alembic tag migration exists | **PASS** | Revision `20260524_0002`: tags, document_tags, chunk_tags |
| Browse routes implemented | **PASS** | GET /api/v1/documents, /tags, /documents/{id} |
| Admin PATCH routes implemented | **PASS** | PATCH tag routes on internal-write-api |
| Retag worker defined | **PASS** | Modal retag worker + `job_type=retag` |
| Deploy order documented | **PASS** | Staging-runbook: DB → backends → Modal → frontends |
| D7 formally verified before deploy | **PENDING** | Operator: run `stage_llm_weights` + health check before EV-001 deploy |

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| `infra/do/*.yaml` (4 deployables) | OK |
| `scripts/deploy/modal.sh` | OK |
| `docs/staging-runbook.md` deploy order (EV-001) | OK |
| `docs/staging-secrets-matrix.md` (EV-001 update) | OK |
| App names: `vecinita-embedding`, `vecinita-data-management`, `vecinita-llm` | OK |
| `⚠️ Needs human input` in deployment-integration | None |
| Alembic revision `20260524_0002` (tag tables) | OK |
| Browse routes in chat-rag-backend | OK |
| Tag PATCH routes in internal-write-api | OK |

## Secrets check (Agent 2)

| Secret / env | Platform | Status |
|--------------|----------|--------|
| `DATABASE_URL` | DO (backends) | Configured (v1) |
| `VECINITA_INTERNAL_API_KEY` | DO + Modal | Configured (v1) |
| `VECINITA_MODAL_EMBED_URL` | DO ChatRAG + Modal | Configured (v1); **added to Modal section** in matrix |
| `VECINITA_MODAL_LLM_URL` | DO ChatRAG + Modal | Configured (v1); **added to Modal section** for EV-001 tagging |
| `VECINITA_INTERNAL_WRITE_URL` | Modal | Configured — **name corrected** from `VECINITA_DO_WRITE_API_URL` |
| `VECINITA_CORS_ORIGINS` | chat-rag-backend | Configured — includes chat frontend origin |
| `VECINITA_CORS_ORIGINS` | internal-write-api | Configured — includes admin frontend origin |
| `VECINITA_CORS_ORIGINS` | Modal data-mgmt | Configured — includes admin origin |
| `VECINITA_MODAL_DATA_MGMT_URL` | DO write API | **Added** — EV-001 retag job dispatch |
| `VECINITA_MODAL_PROXY_KEY` | DO write API | **Added** — EV-001 retag auth |
| `VECINITA_BROWSE_PAGE_SIZE` | DO ChatRAG | **Added** — optional, default 20 |
| `VECINITA_MAX_TAGS_PER_DOCUMENT` | DO write API | **Added** — optional, default 10 |
| `VECINITA_MAX_TAGS_PER_CHUNK` | DO write API | **Added** — optional, default 5 |
| `VECINITA_LLM_TAG_MAX_TOKENS` | Modal | **Added** — optional, default 128 |
| `VECINITA_TAG_SEED_PATH` | Modal | **Added** — optional, default `data/fixtures/tags/seed_tags.json` |
| `VITE_VECINITA_CHAT_API_URL` | chat-rag-frontend | Configured — covers ask + browse |
| `VITE_VECINITA_ADMIN_API_URL` | data-mgmt-frontend | Configured (v1) |
| `VITE_VECINITA_CORPUS_API_URL` | data-mgmt-frontend | Configured — admin tag PATCH |
| `VITE_VECINITA_CORPUS_API_KEY` | data-mgmt-frontend | Configured — Bearer for internal-write |
| `VITE_VECINITA_MODAL_PROXY_KEY` | data-mgmt-frontend | Configured (v1) |
| `DATABASE_URL` in Modal | Forbidden (ADR-007) | OK — not present |

### Corrections applied (12-verify-deploy)

1. **Name fix**: `VECINITA_DO_WRITE_API_URL` → `VECINITA_INTERNAL_WRITE_URL` (code is source of truth; staging secret already correct)
2. **Added to DO write API section**: `VECINITA_MODAL_DATA_MGMT_URL`, `VECINITA_MODAL_PROXY_KEY` (needed for retag dispatch)
3. **Added to Modal section**: `VECINITA_MODAL_EMBED_URL`, `VECINITA_MODAL_LLM_URL` (used by ingest/tagging workers)
4. **Added EV-001 optional vars**: `VECINITA_BROWSE_PAGE_SIZE`, `VECINITA_MAX_TAGS_PER_DOCUMENT`, `VECINITA_MAX_TAGS_PER_CHUNK`, `VECINITA_LLM_TAG_MAX_TOKENS`, `VECINITA_TAG_SEED_PATH`
5. **Removed phantom**: `VECINITA_CHUNK_SIZE_TOKENS` (never read from env; chunk size passed via job payload)
6. **Updated**: `config-spec.md` §Data Management to use correct name

## Data & volumes (Agent 3)

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5 corpus/migrations | verified | `data/fixtures/`, Alembic revisions |
| D6 FastEmbed | verified | Volume `embedding-models`; service deployed |
| D7 Qwen weights | staged_procedure | **Verify before EV-001 deploy** (user-requested mitigation) |
| D8 Seed tag vocabulary | verified | `data/fixtures/tags/seed_tags.json` |
| D9 Tagged corpus | verified | `data/fixtures/corpus/tagged/` |
| pgvector 384-dim | OK | Schema + deployment-integration |
| Tag migration | OK | Revision `20260524_0002` additive |

## Resource allocation (Agent 4)

| Resource | Plan | Actual (code/config) | Status |
|----------|------|----------------------|--------|
| LLM GPU | T4, scale-to-zero | `gpu="T4"`, `scaledown_window=300` | OK |
| Embed | CPU Modal | `embedding_app.py` — no GPU | OK |
| ChatRAG DO | basic-xxs, nyc | `chat-rag-backend.yaml` | OK |
| Internal write API | minimal tier | `internal-write-api.yaml` | OK |
| Retag worker | CPU Modal (no new GPU) | Shares data-mgmt app | OK |
| Cost pilot | ≤ $50/mo | [cost-monitoring.md](cost-monitoring.md) documented; EV-001 within cap | OK |
| Regions | US only nyc/sfo3 | DO `nyc`; Modal US workspace `vecinita` | OK |

## Template deploy validation (Agent 5 — `api+worker` hybrid)

| Check | Status | Notes |
|-------|--------|-------|
| Template ID `api+worker` | OK | Not Modal job template |
| Modal deploy command | OK | `modal deploy infra/modal/*.py` via `scripts/deploy/modal.sh` |
| Workspace | OK | `vecinita` |
| Volume naming | OK | `embedding-models`, `llm-models` |
| CI workflow | OK | `.github/workflows/ci.yml` (lint/test/typecheck) |
| Deploy workflow | N/A | Manual deploy per staging-runbook (operator-driven) |
| `DATABASE_URL` not in Modal | OK | ADR-007 enforced |

## Connectivity Gates (H4/H5) — EV-001 readiness

| Gate | Status | Detail |
|------|--------|--------|
| H0c browse GET CORS (TC-046) | **PASS** | `pytest tests/unit/test_cors_policy.py` — GET on `/api/v1/documents`, `/tags` |
| H0c admin PATCH CORS (TC-049) | **PASS** | PATCH preflight on tag routes |
| H0c DELETE preflight (BUG-2026-05-22) | **PASS** | Existing; unchanged |
| H4 ChatRAG CORS (live) | **PENDING** | Post-deploy: `verify_connectivity.sh` |
| H4 Write API CORS (live) | **PENDING** | Post-deploy: includes PATCH preflight |
| H4 Modal data-mgmt CORS | **WAIVER** | `requires_proxy_auth` blocks OPTIONS; user-approved waiver (v1) |
| H5 Chat frontend bundle | **PENDING** | Post-deploy: bundle contains ChatRAG backend host (browse + ask) |
| H5 Admin frontend bundle | **PENDING** | Post-deploy: bundle contains write API + Modal hosts |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|-----------|--------|
| 1 | Tag migration failure | Additive migration; `alembic upgrade head` on staging first | **approved** |
| 2 | CORS on browse GET routes | H0c TC-046 pass; existing CORS config covers browse (same origin) | **approved** |
| 3 | Admin PATCH CORS / auth | H0c TC-049 pass; PATCH in allow_methods; Bearer auth | **approved** |
| 4 | Retag worker LLM cold start | Async job; scaledown_window=300s; user polls status | **approved** |
| 5 | Incorrect deploy order | Staging runbook: DB → backends → Modal → frontends | **approved** |
| 6 | D7 LLM weights not verified | **Verify before EV-001 deploy** — run `stage_llm_weights` + health | **blocking** |
| 7 | Modal/DO image build failure | `verify_build.sh` + import smoke | **approved** (v1) |
| 8 | Secret missing at runtime | `verify_secrets.sh` + secrets matrix | **approved** (v1) |

## Rollback

**Procedure (EV-001 delta):**

1. **Stop serving new traffic**
   - DO: Redeploy previous app spec or disable in dashboard
   - Modal: `modal app stop vecinita-data-management` (retag worker)
2. **Database**
   - **Option A (preferred, approved):** Leave tag tables in place — unused if code reverted. No data loss.
   - Option B (clean): `alembic downgrade -1` only if no production tag data
3. **Frontend**
   - Redeploy previous frontend builds (removes /corpus browse page, tag chips)
4. **Verify rollback**
   - `curl` DO `/health` on previous deployment
   - Re-run H1–H3 staging smoke
   - Confirm no tag-related errors in logs

| Field | Value |
|-------|-------|
| **Last known good (code)** | `2317490` — `chore: auto-fix lint/format issues from 08-verify-build` |
| **Modal stop (per app)** | `modal app stop vecinita-data-management` / `vecinita-embedding` / `vecinita-llm` |
| **DO redeploy previous** | `doctl apps create-deployment <app-id> --spec infra/do/<service>.yaml` (after reverting git spec) |

## Deploy gate (upstream stages)

| Gate | Status |
|------|--------|
| QA (09) | **PASS** — [qa-report.md](qa-report.md) (2026-05-25) |
| E2E T0 (10) | **PASS** — 16/16 journeys [e2e-report.md](e2e-report.md) |
| E2E T3 live | **PENDING** — post-deploy |
| Implementation (11) | **Approved** — F1–F22 all journeys signed off (2026-05-25) |
| Deploy strategy (12) | **This checklist** |

## Deploy order (EV-001)

1. **Verify D7 LLM weights** — `./scripts/stage_modal_weights.sh` + health check
2. **Database** — `alembic upgrade head` (adds tag tables)
3. **chat-rag-backend** — new browse routes + CORS (deploy before frontend)
4. **internal-write-api** — tag PATCH + retag trigger routes
5. **Modal data-management** — retag worker
6. **chat-rag-frontend** — browse page + tag filter chips
7. **data-management-frontend** — chunk viewer + tag editor
8. **Run connectivity smoke** — `bash scripts/deploy/verify_connectivity.sh`

## Sign-Off

- [x] User approved implementation (11-verify-impl) — F1–F22 journeys 2026-05-25
- [x] Deploy strategy verified (failure modes + rollback acknowledged 2026-05-25)
- [x] Connectivity gates: H0c pass (TC-046, TC-049); H4/H5 pending post-deploy
- [x] Modal H4 waiver acknowledged (proxy auth blocks OPTIONS preflight)
- [ ] D7 LLM weights formally verified (operator action before deploy)
- [ ] Ready to deploy (after D7 verification)

### Operator commands

```bash
# Pre-deploy: verify D7 LLM weights
./scripts/stage_modal_weights.sh

# Pre-deploy: build smoke
bash scripts/deploy/verify_build.sh

# Pre-deploy: secrets check
bash scripts/deploy/verify_secrets.sh

# Post-deploy: connectivity smoke (blocking)
bash scripts/deploy/verify_connectivity.sh

# Post-deploy: staging health
bash scripts/deploy/staging_smoke.sh
```

## Next step

**13-deploy-smoke** after D7 verified and user approves deployment.
