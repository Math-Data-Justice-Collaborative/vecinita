# Deploy Smoke — EV-027 / S030 (F75–F77)

> Date: 2026-08-13  
> Status: **baseline smoke in progress** (H2 disposition pending AskQuestion)  
> Path: **S030-D60** `baseline_only_flags_off`  
> `env_role`: **`staging_as_live`** = **live/prod** [ADR-049]

[Corpus: feature-list.md §F75–F77]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/adr/ADR-050-ci-cd-blocks-live-deploy.md]  
[Spec: docs/sessions/S030-corpus-automations/reports/deploy-checklist.md]

## Scope (approved)

| Do | Do not |
|----|--------|
| Push tip → tip CI green | EV-027 live cutover |
| H0c + H1–H5 on **current live** stack | Flip `*_ENABLED` / kill-switch off |
| Keep F75–F77 **off** | Live FT promote / prod corpus mutation |

## Tip / CI (RA-009)

| Field | Value |
|-------|--------|
| Tip | `588dab6` |
| Branch | `evolve/EV-027-corpus-automations` |
| CI | **PASS** — [run 31709704821](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31709704821) |
| Live commit | Pre-EV-027 (EV-027 **not** on live stack) |

## Live URLs (production traffic)

| Service | URL |
|---------|-----|
| ChatRAG | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| Chat FE | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin FE | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |
| Modal DM API | https://vecinita--vecinita-data-management-fastapi-app.modal.run |

## Smoke results

| Tier | Result | Notes |
|------|--------|-------|
| H0c CORS unit | **PASS** | `pytest tests/unit/test_cors_policy.py` |
| H1 ChatRAG `/health` | **PASS** | `status=ok`; `postgres` / `modal_embed` / `modal_llm` = `ok` |
| H1 Write `/health` | **PASS** | `status=ok` |
| H2 DB pool | **PASS** | DO Postgres connect `SELECT 1` |
| H2 Alembic head | **FAIL (expected)** | live `20260806_0014` ≠ tip head `20260812_0016` — tip migrations not cut over |
| H3 `POST /api/v1/ask` | **PASS** | answer returned (`en`, 303 chars); latency ~85.9s (cold LLM) |
| H3b browse | **PASS** | docs 5/61; tags 12 facets |
| H4–H5 connectivity | **PASS** | `scripts/deploy/verify_connectivity.sh` |
| Automations status probe | **404** | route absent on live — consistent with no EV-027 cutover |

## Flags / enable

| Flag / action | Status |
|---------------|--------|
| `VECINITA_AUTOMATIONS_ENABLED` | **unchanged / off path** (no enable) |
| Freshness enable | **unchanged** |
| FT train / promote | **not run** |

## Rollback (unused this path)

No live cutover — no rollback required. Prior plan remains in `deploy-checklist.md` (S030-D59).

## Disposition pending

**[Decision] S030-D61** — treat H2 alembic mismatch as **expected** for baseline-only (pool OK), or hard-fail stage.

## Next

Await S030-D61; then close baseline 13 or choose ship path (separate AskQuestion).
