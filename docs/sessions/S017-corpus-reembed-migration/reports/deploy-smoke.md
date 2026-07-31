# Deploy & Smoke Report — EV-015 Corpus rebuild (S017 / F41)

> **Date:** 2026-07-30  
> **Session:** S017-corpus-reembed-migration  
> **Cycle:** EV-015  
> **Stage:** 13-deploy-smoke  
> **Status:** **PASS** — Path A deploy checkpoint **approved** 2026-07-30 (option 1: prepare PR; DO pins stay on evolve until merge)  
> **Branch:** `evolve/EV-015-corpus-reembed-migration` @ `180ad14`  
> **Operator env:** `.env` (no `prod.env` on this machine)

## Pre-Deploy

| Check | Status | Evidence |
|-------|--------|----------|
| 12-verify-deploy | **READY** | checklist @ `180ad14` |
| H0c CORS | **PASS** | `pytest tests/unit/test_cors_policy.py` + `verify_connectivity.sh` |
| Alembic head (repo) | **PASS** | `20260730_0010` |

## Deployment (Path A — staging)

| Step | Action | Result |
|------|--------|--------|
| 1 | `alembic upgrade head` on staging Postgres | **PASS** `20260728_0009` → `20260730_0010` |
| 2 | Push evolve branch | **SUCCESS** `origin/evolve/EV-015-corpus-reembed-migration` |
| 3 | Pin + deploy `vecinita-internal-write-api` | **ACTIVE** (`ae2822e4-…`) branch=evolve |
| 4 | `modal deploy infra/modal/data_management_app.py` | **SUCCESS** URL unchanged |
| 5 | Pin + deploy `vecinita-admin-frontend` | **ACTIVE** (`7bcd1307-…`) branch=evolve |
| 6 | Secret sync (DO + GitHub) + `do_verify_required_secrets.sh` | **PASS** |
| 7 | H1–H3 `staging_smoke.sh` | **PASS** (H2 head match; macOS `%3N` latency noise) |
| 8 | H0c + H4–H5 `verify_connectivity.sh` | **PASS** |

ChatRAG FE/BE left on `main` (no F41 schema change).

## Ops smokes (TP-S017-01 / TP-S017-07)

Scoped to 2 docs (store was empty: 40/40 `missing_body` before backfill).

| Drill | IDs / result |
|-------|----------------|
| Backfill `from_chunks` + ack | job `bb69b3a1-…` **completed**; body_text populated |
| Live same-settings `reembed` `force` | job `bc432d0f-…` **completed**; chunk text hashes unchanged (**LIVE_EQUIV PASS**) |
| Shadow `dry_run=true` | job `b0af7b1b-…` **completed**; `rebuild_run_id=e3a78965-448f-4246-ab6f-d29f36feceaa`; 60 shadow chunks; live unchanged |
| F36 with `rebuild_run_id` | eval `01ca4019-…` **completed** (operator-local `execute_eval_run`; see advisories); metrics: retrieval_relevance=0.0, faithfulness≈0.08 (scoped corpus / top_k=2) |
| Promote | **PASS** `{promoted:true, chunks_promoted:60, documents_promoted:2}` |
| Post-promote H1–H3 | **PASS** |

### Document IDs (scoped)

- `8b78a43f-5afc-43b8-8cbd-2bd93ba00878`
- `dee0a4b3-7f2a-4767-a6d4-c9685c0002ad`

## URLs

| Service | URL | Pin |
|---------|-----|-----|
| Internal write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app | evolve |
| Admin frontend | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app | evolve |
| Modal data-mgmt | https://vecinita--vecinita-data-management-fastapi-app.modal.run | redeployed |
| ChatRAG BE/FE | unchanged staging URLs | `main` |

## Advisories (non-blocking for Path A promote path; follow-ups)

1. **Modal `job_type=eval` dispatch gap:** `run_job` falls through to ingest → `BatchUpsertRequest(documents=[])` ValidationError. F36 was completed via operator-local `execute_eval_run` against staging DB. Needs hotfix / Modal eval worker before relying on Admin Evaluation enqueue alone.
2. **Prompt length:** default `top_k=5` + 256-token chunks exceeded vLLM `max_model_len=2048` (500). Staging F36 used `config.top_k=2`.
3. **Full-corpus backfill** still pending (38 docs without `body_text`); only scoped store backfill done for the drill.
4. **DO pins** still on evolve — reset to `main` after merge (S013/S014 pattern).
5. Do **not** commit `scripts/deploy/_tmp_proxy_key_check.py`.

## Rollback

1. Reset DO `github.branch` → `main` for write-api + admin FE; force redeploy.  
2. Modal: redeploy prior data-management revision if needed.  
3. After promote: re-promote prior `rebuild_run_id` if retained, or revision checklist (runbook).  
4. Schema: forward-only; do not TRUNCATE without corpus-db-safety.

## Gate / next

- **13-deploy-smoke Path A:** **COMPLETE** — user approved deploy checkpoint (option 1).  
- **PR:** prepare / open `evolve/EV-015-corpus-reembed-migration` → `main` (TP-S017-05 / #167).  
- **DO pins:** remain on evolve until merge; reset to `main` after merge.  
- Optional follow-ups: Modal eval dispatch hotfix; full store backfill (38 docs); 15-service-health.

> CI note: coverage gate green on `1928b62+`; security re-run after Supabase advisor 502.
