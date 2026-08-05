# T118.3 — Phase 27 gate + issue closeout notes

> **Session:** S026 · **Cycle:** EV-024 · **Date:** 2026-08-04  
> **Status:** completed  
> **Branch tip (pre-PR):** evolve `4a151d0`+ (T118.1–T118.3) · main M117 merge `eb65837`

## OpenAPI + infra mirror check (TP3 / T118.2)

| Spec | Surface | Status |
|------|---------|--------|
| `openapi/chat-rag.yaml` | `energy_estimate` on ask/stream `done`; `POST /feedback` + body (no email) | **PASS** |
| `openapi/internal-write.yaml` | `POST /feedback`, `POST /feedback/cleanup`; anonymous body | **PASS** |
| `openapi/data-management.yaml` | `GET /admin/feedback`; audit `actor_email` enrich | **PASS** |
| `infra/vecinita.yaml` | `energy_*` knobs + `feedback:` retention block | **PASS** |
| `docs/staging-secrets-matrix.md` | EV-024 energy/feedback + F69 `SUPABASE_SECRET_KEY` (write-api) | **PASS** |
| `infra/do/.env.example` + `Brewfile` | `SUPABASE_SECRET_KEY` documented; `brew "supabase"` | **PASS** |

Live secret sync deferred (no local `prod.env`) — operator advisory only; not a gate blocker.

## Phase 27 gate (build-complete slice)

| Criterion | Result |
|-----------|--------|
| All M112–M118 tasks completed (T112.1–T118.3) | **PASS** (this task completes the set) |
| ADR-046 feedback; ADR-047 energy | **PASS** |
| OpenAPI + infra yaml keys (T118.2) | **PASS** (above) |
| Playwright UJ-069/070/073; optional 071/072/074 | **PASS** — see [t118-1-uj-suite.md](./t118-1-uj-suite.md) |
| No new CORS origins; no visitor email; no live Modal power | **PASS** (scope held) |
| AC-UX1–UX15, UX17 at T2; AC-UX16 scope held | Deferred to **08-verify-build** / 09–11 phase verify |
| ruff / basedpyright / Vitest / pytest e2e | Deferred to **08-verify-build** (M112–M117 CI green; M118 docs/config) |

## Milestone → PR → issue map

| Milestone | Feature | Issue | PR | Merge SHA | Code landed |
|-----------|---------|-------|-----|-----------|-------------|
| M112 | F66 ActionIcon | #104 | [#200](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/200) | (merged 2026-08-04) | yes |
| M113 | F67 Tooltip | #106 | [#202](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/202) | `9eaedb0` area | yes |
| M114 | F64 wait tips | #87 | [#203](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/203) | `f3f7dec` | yes (**issue CLOSED**) |
| M115+M116 | F65+F68 | #93 / #186 | [#205](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/205) | `0c1d838` | yes |
| M117 | F69 actor email | #170 | [#206](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/206) | `eb65837` | yes |
| M118 | OpenAPI + UJ + gate | #193 (epic) | M118 PR (this tip) | pending | docs/config |

## Issue closeout prep

Do **not** close child issues solely at T118.3 unless product owner confirms. Recommended timing:

| Issue | Close when | Notes |
|-------|------------|-------|
| #104 | After M112 merge + optional smoke | Code on main via #200; still OPEN |
| #106 | After M113 merge + optional smoke | Code on main via #202; still OPEN |
| #87 | Done | Already CLOSED (2026-08-04) |
| #93 | After M115 merge + energy visible in staging | Code on main via #205; still OPEN |
| #186 | After M116 merge + feedback write path live | Code on main via #205; still OPEN |
| #170 | After M117 merge + `SUPABASE_SECRET_KEY` synced | Code on main via #206; still OPEN |
| #193 | After all children closed + **13-deploy-smoke** H1–H5 | epic |

**Operator follow-ups (non-blocking for build gate):**

```bash
set -a && source prod.env && set +a
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-secrets
bash scripts/deploy/sync_modal_secret.sh --merge --apply
```

## Next

1. Commit T118.3 + open **[M118]** PR (OpenAPI / secrets / gate docs).
2. **08-verify-build** for M118 docs/config tip (or fold into Gate C→D digest).
3. **Gate C→D / phase_c** AskQuestion → then 09-qa → 10-e2e → …
