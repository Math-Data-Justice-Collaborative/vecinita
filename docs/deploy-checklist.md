# Deploy Checklist

> **Generated**: 2026-05-19  
> **Status**: **not ready** (blocking items below; strategy verified 2026-05-19)  
> **Deployment plan**: [deployment-integration.md](deployment-integration.md)  
> **Stage**: 12-verify-deploy

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete (no gaps) | **PARTIAL** | DO YAML + Modal apps + runbooks present; see gaps §Gaps |
| All secrets configured | **FAIL** | Modal secret `vecinita-data-management` missing; DO secrets unverified (no `doctl`) |
| Data assets staged | **PARTIAL** | D1–D5 verified; D6 verified; D7 `staged_procedure` (LLM deployed, run `stage_llm_weights`) |
| Resource allocation verified | **PASS** | T4 + `scaledown_window=300`; DO `basic-xxs` + `nyc`; pool 5/5 per deployment-integration |
| Rollback plan reviewed | **APPROVED** | User sign-off 2026-05-19 |

### Gaps (blocking first staging deploy)

1. **Create Modal secret `vecinita-data-management`** with keys from [staging-secrets-matrix.md](staging-secrets-matrix.md) §Modal — Data management. Workspace currently has `vecinita-secrets` and `vecinita-scraper-env` only (2026-05-19 `modal secret list`).
2. **Redeploy / start `vecinita-data-management`** — app state `stopped` on vecinita workspace.
3. **DigitalOcean apps** — not verified in this environment (`doctl` unavailable). Operator must create four App Platform apps per [infra/do/README.md](../infra/do/README.md) and set SECRET env vars before H1–H3.
4. **D7 weights** — run `./scripts/stage_modal_weights.sh` (or `modal run …::stage_llm_weights`) and set D7 to `verified` in [data-staging-state.md](data-staging-state.md).
5. **Staging URLs** — set `VECINITA_STAGING_CHAT_URL` / `VECINITA_STAGING_WRITE_URL` for T3 smoke (documented waiver for 11-verify-impl).

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| `infra/do/*.yaml` (4 deployables) | OK |
| `scripts/deploy/modal.sh` | OK |
| `docs/staging-runbook.md` deploy order | OK |
| `docs/staging-secrets-matrix.md` | OK |
| App names: `vecinita-embedding`, `vecinita-data-management`, `vecinita-llm` | OK (Modal app list) |
| `⚠️ Needs human input` in deployment-integration | None |
| Open: budget alerts 80%/100% | Deferred to T14.4 / 13-deploy-smoke |

## Secrets check (Agent 2)

| Secret / env | Platform | Status |
|--------------|----------|--------|
| `vecinita-data-management` | Modal | **MISSING** (required by `data_management_app.py`) |
| `vecinita-secrets` | Modal | Present (legacy; not wired in code) |
| `vecinita-scraper-env` | Modal | Present |
| `DATABASE_URL` | DO | **Unverified** |
| `VECINITA_INTERNAL_API_KEY` | DO + Modal | **Unverified** |
| `VECINITA_MODAL_*` URLs | DO ChatRAG | **Unverified** (embed/LLM deployed on Modal) |
| `VITE_*` build vars | DO static | **Unverified** |
| GitHub `MODAL_TOKEN_*` for CI deploy | N/A | Not used — manual/operator deploy (hybrid template) |

## Data & volumes (Agent 3)

| Asset | Status | Notes |
|-------|--------|-------|
| D1–D5 corpus/migrations | verified | `data/fixtures/`, Alembic revision |
| D6 FastEmbed | verified | Volume `embedding-models`; `vecinita-embedding` deployed |
| D7 Qwen weights | staged_procedure | Volume `llm-models`; `vecinita-llm` deployed; confirm staging job |
| pgvector 384-dim | OK | Schema + deployment-integration |

## Resource allocation (Agent 4)

| Resource | Plan | Actual (code/config) |
|----------|------|----------------------|
| LLM GPU | T4, scale-to-zero | `gpu="T4"`, `scaledown_window=300` in `llm_app.py` |
| Embed | CPU Modal | `embedding_app.py` — no GPU |
| ChatRAG DO | basic-xxs, nyc | `chat-rag-backend.yaml` |
| Internal write API | minimal tier | `internal-write-api.yaml` |
| Cost pilot | ≤ $50/mo | [cost-monitoring.md](cost-monitoring.md) documented |
| Regions | US only nyc/sfo3 | DO `nyc`; Modal US workspace `vecinita` |

## Template deploy validation (Agent 5 — `api+worker` hybrid)

| Check | Status | Notes |
|-------|--------|-------|
| Template ID `api+worker` | OK | Not Modal job template — no `deploy_to_modal.yml` required |
| Modal deploy command | OK | `modal deploy infra/modal/*.py` via `scripts/deploy/modal.sh` |
| Workspace | OK | `modal profile current` → `vecinita` |
| Volume naming | OK | `embedding-models`, `llm-models` (per Vecinita ADR-008/009, not cognichem job cache) |
| CI | OK | `ci.yml` — lint/test only; deploy is operator-driven per staging-runbook |

## Failure Mitigations

| # | Risk | Mitigation (planned) | Status |
|---|------|----------------------|--------|
| 1 | Modal/DO image build failure | `.github/workflows/deploy-preflight.yml` + `scripts/deploy/verify_build.sh` (import smoke; no Modal dry-run) | **approved** |
| 2 | Secret missing at runtime | `scripts/deploy/verify_secrets.sh` + create `vecinita-data-management` | **blocking** |
| 3 | Volume / model cold start | `stage_modal_weights.sh`; cold start allowance | **approved** |
| 4 | GPU T4 unavailable | Scale-to-zero; Ollama fallback per ADR-009 | **approved** (with #3) |
| 5 | DO ↔ Modal network / wrong URLs | `staging_smoke.sh` H1–H3; `vecinita--` prefix | **approved** |
| 6 | vLLM cold start / timeout | `timeout=600`; AC-C6 → T3 post-deploy | **approved** (T3 waiver) |
| 7 | Memory / OOM on DO basic-xxs | Monitor DO metrics; tier upgrade if needed | advisory |
| 8 | Admin auth / proxy key mismatch | Key parity matrix; UJ-008 T0 | **approved** (with #5) |

## Rollback

**Procedure (hybrid Vecinita v1):**

1. **Stop serving new traffic**
   - DO: `doctl apps list` → note app IDs → `doctl apps create-deployment <id> --spec <previous-spec>` or disable app in dashboard.
   - Modal: `modal app stop vecinita-data-management` (and optionally embed/llm if isolating).
2. **Database**
   - Forward-only Alembic preferred. Emergency: `alembic downgrade -1` only if revision is reversible — test on staging clone first.
3. **Verify rollback**
   - `curl` DO `/health` on previous deployment URL or local docker-compose.
   - Re-run `bash scripts/check_secrets.sh` (no secrets in tree).
4. **Communicate**
   - Record incident in deploy retrospective (13-deploy-smoke).

| Field | Value |
|-------|-------|
| **Last known good (code)** | `324bb50` — `chore: record Phase 4 gate check (partial pass)` |
| **Modal stop (per app)** | `modal app stop vecinita-embedding` / `vecinita-data-management` / `vecinita-llm` |
| **DO redeploy previous** | `doctl apps create-deployment <app-id> --spec infra/do/<service>.yaml` (after reverting git spec) |

## Deploy gate (upstream stages)

| Gate | Status |
|------|--------|
| QA (09) | PASS — [qa-report.md](qa-report.md) |
| E2E T0 (10) | PASS — 8/8 journeys |
| E2E T3 live | **PENDING** — no staging URLs |
| Implementation (11) | **Approved** (journeys F1–F18); T3 waiver documented |
| Deploy strategy (12) | **This checklist** |

## Connectivity Gates (H4/H5) — 2026-05-21

| Gate | Status | Detail |
|------|--------|--------|
| H0c CORS policy (local) | PASS | `pytest tests/unit/test_cors_policy.py` |
| H4 ChatRAG CORS | PASS | Preflight returns 200 + correct `ACAO` |
| H4 Write API CORS | PASS | Preflight returns 200 + correct `ACAO` |
| H4 Write API DELETE preflight | PASS | OPTIONS with `Access-Control-Request-Method: DELETE` → 200, `DELETE` in allow-methods (BUG-2026-05-22) |
| H4 Modal data-mgmt CORS | **WAIVER** | `requires_proxy_auth` blocks OPTIONS at proxy (401); user-approved waiver |
| H5 Chat frontend bundle | PASS | Bundle contains ChatRAG backend host |
| H5 Admin frontend bundle | PASS | Bundle contains write API + Modal hosts |

**Modal H4 waiver:** Modal's proxy auth operates before ASGI app; browsers never send auth on OPTIONS preflight per CORS spec. Deferred to post-v1 (app-level auth or DO proxy).

## Sign-Off

- [x] User approved implementation (11-verify-impl) — journeys + features 2026-05-19
- [x] Deploy strategy verified (failure modes + rollback acknowledged 2026-05-19)
- [x] Connectivity gates (H4/H5) — 4/5 pass, 1 waiver (Modal proxy auth) 2026-05-21
- [ ] Ready to deploy (resolve blocking gaps §Gaps)

### Operator commands (added 12-verify-deploy)

```bash
bash scripts/deploy/verify_build.sh    # local / CI build smoke
bash scripts/deploy/verify_secrets.sh  # Modal secret + volumes (fails until vecinita-data-management exists)
```

GitHub: add repo secrets `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` for `deploy-preflight` workflow on `main`.

## Next step

**13-deploy-smoke** after blocking gaps cleared and user approves failure mitigations + rollback.
