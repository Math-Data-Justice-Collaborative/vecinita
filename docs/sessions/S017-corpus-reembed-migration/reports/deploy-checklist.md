# Deploy Checklist — S017 / EV-015 Corpus rebuild (F41)

> **Generated**: 2026-07-30  
> **Status**: **ready**  
> **Deployment plan**: [deployment-integration.md](../../../deployment-integration.md) §EV-015  
> **Stage**: 12-verify-deploy (S017 delta — F41 / #167)  
> **Branch**: `evolve/EV-015-corpus-reembed-migration` @ `1c2e46e`  
> **Session**: S017-corpus-reembed-migration  
> **Runbook**: [runbook-corpus-rebuild-outline.md](runbook-corpus-rebuild-outline.md)

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete | **PASS** (advisories) | Redeploy order + entry points verified; TP-S017-12-A/B |
| All secrets configured | **PASS** | No new secret names; existing Modal/DO/Admin matrix |
| Data assets staged | **PASS** (ops pending) | Alembic `20260730_0010` in repo; staging apply = 13 step 1 |
| Resource allocation verified | **PASS** | Existing Modal DM CPU worker `timeout=600`; no new GPU |
| Rollback plan reviewed | **APPROVED** | User option 1 — 2026-07-30 |
| H0c CORS unit tests | **PASS** | `pytest tests/unit/test_cors_policy.py` exit 0; T90.4 promote case |
| Frontend `VITE_*` ↔ API matrix | **PASS** | Existing Admin `VITE_VECINITA_*` + corpus API; no new origins |
| `VECINITA_CORS_ORIGINS` documented | **PASS** | Write API + Modal DM; Admin origin already authorized |
| Post-deploy H4–H5 documented | **PASS** | `scripts/deploy/verify_connectivity.sh` |

## S017-specific deploy surfaces

| Surface | Change | Deploy / apply |
|---------|--------|----------------|
| DO Managed Postgres | Store + shadow + `rebuild_runs` | `alembic upgrade head` **first** |
| DO internal-write-api | Promote + store upsert + shadow batch | DO CD / `do_apps.py` |
| Modal data-management | `job_type=rebuild` + backfill worker | `modal deploy -m infra.modal.data_management_app` |
| Admin frontend (DO) | RebuildForm + RebuildPromoteForm + BackfillForm | DO static / FE build env |
| ChatRAG | No schema change | Redeploy not required for F41 schema |

### Redeploy order (staging)

1. `alembic upgrade head`
2. internal-write-api
3. Modal data-management
4. Admin frontend
5. Ops smokes (TP-S017-01 / TP-S017-07):
   - Live same-settings equivalence rebuild
   - Shadow `dry_run=true` → F36 with `rebuild_run_id` → promote
6. Prod live rebuild **out of scope** — runbook only

### Post-Modal secret sync (before smokes)

```text
set -a && source prod.env && set +a
uv run python scripts/deploy/modal_url_validate.py
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
bash scripts/deploy/sync_github_secrets.sh --apply
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/verify_connectivity.sh   # H4–H5
```

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| Modal DM rebuild / backfill entry | OK |
| Write API promote + shadow routes | OK (implemented) |
| Admin Corpus rebuild / promote UI | OK |
| Alembic `20260730_0010_ev015_*` | OK |
| `⚠️ Needs human input` in F41 deploy docs | None |
| `VECINITA_REBUILD_SHADOW_ENABLED` | **Clarified** — planned/unused; `dry_run` always on (TP-S017-12-A) |
| OpenAPI create/patch/shadow rebuild | **Advisory** — promote + DM Jobs documented; sync follow-on (TP-S017-12-B) |

## Secrets (Agent 2)

| Category | Status |
|----------|--------|
| Modal DM | PASS — existing secrets |
| DO write-api + Modal URLs | PASS |
| Admin FE Vite | PASS |
| Postgres `DATABASE_URL` | PASS — write API only |
| New F41 secret names | PASS — none |
| Live `modal secret list` | SKIPPED (CLI unavailable locally) |

## Data & volumes (Agent 3)

| Asset | Status |
|-------|--------|
| Alembic F41 migration | PASS (code) |
| Corpus storage | DO Managed Postgres — no Modal corpus volume |
| Modal DM | `modal.Dict` jobs only |
| Staging migration apply | OPS — 13 step 1 |
| Backfill precondition | OPS — before live equivalence / scoped rebuild |

## Resources (Agent 4)

| Check | Status |
|-------|--------|
| New GPU tier | N/A — none |
| Timeout | Same DM ASGI `timeout=600` |
| `min_containers` | None new |

## CI / CD (Agent 5)

| Check | Status |
|-------|--------|
| `ci.yml` → preflight → Modal → DO | PASS |
| Cognichem job template cache naming | N/A (hybrid) |
| `MODAL_TOKEN_*` docs | PASS (`staging-runbook.md`) |

## Browser connectivity (Agent 6)

| Check | Status |
|-------|--------|
| `tests/unit/test_cors_policy.py` | PASS |
| Promote CORS (T90.4) | Present (DB-gated in some envs) |
| `verify_connectivity.sh` | Present |
| `tests/smoke/test_staging_connectivity.py` | Present |

## Modal / DO secret parity (Agent 7)

| Check | Status |
|-------|--------|
| `infra/do/internal-write-api.yaml` Modal URLs | PASS |
| `infra/do/chat-rag-backend.yaml` Modal URLs | PASS |
| Sync scripts | PASS |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Alembic migration failure | Upgrade head before services; verify head; corpus-db-safety | **approved** |
| 2 | Stale Modal URLs after DM redeploy | `modal_url_validate` + sync-all-secrets + GitHub sync + verify | **approved** |
| 3 | Promote corrupts live retrieval | Staging shadow→F36→promote; transactional promote; no prod live rebuild | **approved** |
| 4 | Admin CORS / promote browser failure | Existing CORS origins; H0c + T90.4; H4–H5 | **approved** |
| 5 | Secret missing at runtime | No new secrets; pre-deploy DO secret checks | **approved** |
| 6 | Long rebuild / cold-start timeout | Scope `document_ids`; monitor Jobs; same 600s worker | **approved** |

## Decisions (12-verify-deploy)

| ID | Decision |
|----|----------|
| TP-S017-12-A | Always-on shadow `dry_run`; env flag planned/unused (clarify docs) |
| TP-S017-12-B | OpenAPI create/patch/shadow sync deferred; promote + DM Jobs sufficient this cycle |

## Rollback

- **Before promote:** Live chunks/embeddings unchanged; abandon or leave shadow `rebuild_run_id`.
- **After promote:** Re-promote prior `rebuild_run_id` if retained, or restore from `document_revisions` checklist (runbook).
- **Never** TRUNCATE corpus without corpus-db-safety guards.
- **Code rollback:** Redeploy prior Modal DM / write-api / Admin FE images; schema rollback only if migration unused.
- **Prod live rebuild:** Out of scope for EV-015 (runbook outline only).
- **Last known good (pre-merge):** `main` prior to EV-015 merge; branch tip `1c2e46e` for this checklist.

## Sign-Off

- [x] User approved implementation (11-verify-impl)
- [x] Config drift decisions TP-S017-12-A/B
- [x] Failure mitigations approved (all option 1)
- [x] Rollback plan approved
- [x] Deploy strategy verified — **ready for 13-deploy-smoke**

## Next step

`13-deploy-smoke` — staging: Alembic → services → secret sync → H4–H5 → live equivalence + shadow→F36→promote (TP-S017-07). Single PR at phase end (TP-S017-05).
