# Service Health — EV-027 / S030 (post-baseline 13)

> Date: 2026-08-13  
> Status: **PASS**  
> Trigger: post **13-deploy-smoke** baseline (`passed_baseline_only`)  
> Decisions: **S030-D62** → 15 · **S030-D63** recommended package  
> `env_role`: **`staging_as_live`** = **live/prod** [ADR-049]

[Corpus: feature-list.md §F75–F77]  
[Spec: docs/adr/ADR-049-single-env-staging-as-live.md]  
[Spec: docs/sessions/S030-corpus-automations/reports/deploy-smoke.md]

## Interview (S030-D63)

| Item | Choice |
|------|--------|
| Depth | Post-baseline: H0ci (advisory) + H1 + H2 pool + H3 + H4–H5 |
| H2 alembic | Known advisory (live ≠ tip head; no migrate) |
| Budget | Lean — one H3 ask; no H6; no corpus write |
| Proceed | Live URLs from `.env`; tip push not required |
| Flags | F75–F77 remain **off**; no enable / FT promote |

## Target (live)

| Service | URL |
|---------|-----|
| ChatRAG | https://vecinita-chat-rag-backend-jvqso.ondigitalocean.app |
| Write API | https://vecinita-internal-write-api-icze4.ondigitalocean.app |
| Chat FE | https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app |
| Admin FE | https://vecinita-admin-frontend-ef4ob.ondigitalocean.app |

## Results

| Layer / tier | Result | Evidence |
|--------------|--------|----------|
| **H0ci** (`main`) | **PASS** (advisory) | [run 31178547214](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31178547214) @ `8ae9d17` |
| **H1** ChatRAG | **PASS** | `status=ok`; `postgres` / `modal_embed` / `modal_llm` = `ok` |
| **H1** Write | **PASS** | `status=ok` |
| **H2** pool | **PASS** | `SELECT 1` on DO Postgres |
| **H2** alembic | **ADVISORY** | live `20260806_0014` ≠ tip head `20260812_0016` (S030-D61) |
| **H3** ask | **PASS** | answer `en` len=455; ~74.2s; `cache_hit=none` |
| **H4–H5** | **PASS** | `verify_connectivity.sh` |

### Summaries

| Summary | Result |
|---------|--------|
| Infra overall | **PASS** (alembic tip-drift advisory only) |
| Behavior overall | **PASS** |
| **Overall** | **PASS** |

## Drift / scope honesty

| Item | Status |
|------|--------|
| EV-027 on live stack | **false** |
| Live vs evolve tip | Tip ahead (migrations / F75–F77 code not cut over) |
| Enable / FT promote | **not run** |

## Remediation

**none** — live stack healthy for current (pre-EV-027) deploy. Cutover / enable remain separate AskQuestions.

## Next

Cycle may close, open ship-path AskQuestion, or return to evolve summary.
