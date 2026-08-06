# Deploy Checklist — S027 / EV-025 Multilingual embeddings (F70–F71)

> **Generated**: 2026-08-05  
> **Status**: **ready**  
> **Deployment plan**: [deployment-integration.md](../../../deployment-integration.md) §EV-025  
> **Stage**: 12-verify-deploy (S027 delta — F70/F71 / #159)  
> **Branch**: `evolve/EV-025-multilingual-embeddings` · **main tip**: `de1355c`  
> **Session**: S027-multilingual-embeddings  
> **Runbooks**: [staging-runbook.md](../../../staging-runbook.md) §EV-025 · [t120_4_staging_f36_checklist.md](t120_4_staging_f36_checklist.md)  
> **Decisions**: S027-D21 · S027-D35 · S027-D47 · S027-D48 · **S027-D49** (mitigations + rollback approved)

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]  
[Spec: docs/deployment-integration.md §EV-025]

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete | **PASS** | §EV-025 redeploy order + pin env documented; no `⚠️ Needs human input` |
| All secrets configured | **PASS** (ops) | No new secret *names*; pin via existing Modal/DO env (`VECINITA_EMBEDDING_MODEL_ID`, tokenizer, embed URL). Local `prod.env` **absent** this workspace — source at 13 |
| Data assets staged | **PASS** (ops pending) | Alembic `chunk_tokenizer_id` / `20260805_0013` in repo; staging apply = 13 |
| Resource allocation verified | **PASS** | Modal embed CPU (ST memory/timeout per ADR-048); DM rebuild existing timeout |
| Rollback plan reviewed | **APPROVED** (S027-D49) | E0 via F41 + `LEGACY_E0` (AC-ME9 / staging-runbook) |
| H0c CORS unit tests | **PASS** | `pytest tests/unit/test_cors_policy.py` exit 0 (2026-08-05) |
| Frontend `VITE_*` ↔ API matrix | **PASS** | **No UI change** (S027-D16); existing Admin/ChatRAG origins |
| `VECINITA_CORS_ORIGINS` documented | **PASS** | `infra/do/chat-rag-backend.yaml` + `internal-write-api.yaml` |
| Post-deploy H4–H5 documented | **PASS** | `scripts/deploy/verify_connectivity.sh` + live EN/ES ask @ 13 |

## Staging drift (must clear at 13)

| Field | Value |
|-------|-------|
| `origin/main` | `de1355c` (PR #213 F70–F71) |
| Last accepted staging smoke | `c942971` (S026) |
| Drift for EV-025 | **YES** — redeploy Modal embed + DM + DO write/chat-rag from `main` before cutover |

## S027-specific deploy surfaces

| Surface | Change | Deploy / apply |
|---------|--------|----------------|
| Modal `vecinita-embedding` | F70 pin + runtime + prefixes | `modal deploy` embed app **first** |
| Modal data-management | F71 rechunk/re-embed stamps | After embed |
| DO internal-write-api | Embed-promote report + stamps | DO CD / `do_apps.py` |
| DO chat-rag-backend | Shared client prefixes | DO CD |
| DO Managed Postgres | Tokenizer stamp columns | `alembic upgrade head` before cutover ops |
| Frontends | None (S027-D16) | Redeploy not required for UI |

### Redeploy order (staging → prod)

1. Modal `vecinita-embedding` (E1 pin + runtime)
2. Modal data-management (rebuild worker)
3. DO internal-write-api
4. DO chat-rag-backend
5. Staging cutover: shadow rechunk → F36 EN/ES → operator promote ([t120_4](t120_4_staging_f36_checklist.md))
6. Prod cutover only after staging (TC-240); **H4–H5 at 13**

### Post-Modal secret sync (before smokes)

```text
set -a && source prod.env && set +a
uv run python scripts/deploy/modal_url_validate.py
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
bash scripts/deploy/sync_github_secrets.sh --apply
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/verify_connectivity.sh   # H4–H5
```

## Agent results (Phase 1)

### Configuration (Agent 1) — PASS

| Item | Status |
|------|--------|
| Modal embed pin default | OK — `intfloat/multilingual-e5-small` |
| embedding-client pins/prefixes | OK |
| Write API promote report | OK |
| ChatRAG shared client | OK |
| Cutover / E0 runbook | OK — staging-runbook §EV-025 |

### Secrets (Agent 2) — PASS (ops)

| Category | Status |
|----------|--------|
| New secret names | None |
| Pin / tokenizer / runtime env | Documented; set on Modal + DO at 13 |
| Modal URL shape | Unchanged; validate before smokes |
| Live `modal secret list` / `prod.env` | SKIPPED locally (`prod.env` absent) |

### Data & volumes (Agent 3) — PASS (ops)

| Asset | Status |
|-------|--------|
| Alembic tokenizer columns | In repo — apply on staging @ 13 |
| Corpus | DO Postgres — no Modal corpus volume |
| Embed weights | Modal volume / FastEmbed — pin on deploy |

### Resources (Agent 4) — PASS

| Check | Status |
|-------|--------|
| New GPU | N/A — CPU embed preferred |
| ST memory/timeout | Per ADR-048 / Phase 28 |

### CI / CD (Agent 5) — PASS

| Check | Status |
|-------|--------|
| `ci.yml` → preflight → Modal → DO | PASS on main @ `de1355c` |
| Hybrid api+worker (not Cognichem job template) | N/A |

### Browser connectivity (Agent 6) — PASS

| Check | Status |
|-------|--------|
| H0c `test_cors_policy.py` | PASS |
| `verify_connectivity.sh` | Present |
| `tests/smoke/test_staging_connectivity.py` | Present |
| New FE origins | N/A (S027-D16) |

### Modal / DO secret parity (Agent 7) — PASS

| Check | Status |
|-------|--------|
| `infra/do/*` Modal embed/LLM URLs | Declared |
| Sync / validate scripts | Present |

## Failure Mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Staging still on pre-EV-025 commit | Redeploy embed → DM → write → chat-rag from `de1355c` before cutover | **approved** S027-D49 |
| 2 | Wrong / stale Modal embed URL after redeploy | `modal_url_validate` + sync-all-secrets + GitHub sync + verify | **approved** S027-D49 |
| 3 | Pin/tokenizer mismatch (AC-ME11) | Stamp both on rebuild; TC-241 gate; refuse dim≠384 | **approved** S027-D49 |
| 4 | Promote harms EN/ES retrieval | Staging-first shadow→F36→promote (S027-D21); operator judgment (S027-D11) | **approved** S027-D49 |
| 5 | Cannot restore E0 | Keep prior revision; F41 + `LEGACY_E0` runbook (AC-ME9) | **approved** S027-D49 |
| 6 | CORS / browser after backend redeploy | Existing origins; H0c PASS; H4–H5 @ 13 | **approved** S027-D49 |
| 7 | Local compose e2e unavailable | Accept S027-D35; rely on CI + staging ops | **approved** S027-D49 |

## Rollback

- **Before promote:** Abandon shadow / leave `rebuild_run_id`; live corpus unchanged.
- **After promote:** Restore prior E0 revision via F41 rebuild+promote with `LEGACY_E0` pin ([staging-runbook](../../../staging-runbook.md) §E0 rollback).
- **Code:** Redeploy prior Modal embed / DM / DO images from last-known-good pre-`de1355c` if needed.
- **Never** TRUNCATE corpus (corpus-db-safety).
- **Last known good (pre-EV-025 cutover):** staging smoke accepted @ `c942971` (S026); code tip for this cycle `de1355c`.
- **User approval:** S027-D49 (option 1) — 2026-08-05

## Sign-Off

- [x] User approved implementation (11-verify-impl S027-D47)
- [x] Failure mitigations approved (S027-D49)
- [x] Rollback plan approved (S027-D49)
- [x] Deploy strategy verified — **ready for 13-deploy-smoke**

## Next step

`13-deploy-smoke` — clear staging drift → redeploy order → secret sync → staging cutover → H4–H5 → prod cutover (TC-240).
