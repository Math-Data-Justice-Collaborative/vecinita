# Deploy Checklist — S026 / EV-024 ChatRAG + Admin UX polish (F64–F69)

> **Generated**: 2026-08-04  
> **Status**: **pending user sign-off** (checklist drafted after S026-D55)  
> **Mode**: DELTA — DO ChatRAG + Admin FE + write API + ChatRAG API; Alembic feedback; F69 `SUPABASE_SECRET_KEY`  
> **Main tip**: `c942971` (#207); Phase D reports on evolve `ffc66b1`  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **approved** F64–F69 (S026-D55)

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | `infra/vecinita.yaml` energy_* + feedback retention; no new `VITE_*` / CORS |
| 2 | Secrets | **ADVISORY** | F69 needs `SUPABASE_SECRET_KEY` on DO write-api (+ Modal DM if used); **live sync blocked** (no local `prod.env`) |
| 3 | Data / migration | **PASS** (ship-path) | `feedback` table + 90d purge — confirm Alembic head on DO Postgres |
| 4 | Resources | **PASS** | No new GPU class; heuristic energy only (ADR-047) |
| 5 | Template / CI deploy | **PASS** | Existing Modal + DO CD; main CI + deploy-preflight green @ `c942971` |
| 6 | Browser connectivity | **PASS** (ready) | H0c unchanged; H4–H5 at 13 |
| 7 | Modal / DO secret parity | **PARTIAL** | Documented in staging-secrets-matrix; apply when `prod.env` available |

### New / changed ship surfaces

| Surface | Change |
|---------|--------|
| DO ChatRAG FE | wait tips, energy chip, ActionIcon, Tooltip, Feedback page |
| DO ChatRAG API | `energy_estimate` on ask/stream; `POST /api/v1/feedback` |
| DO Admin FE | ActionIcon/Tooltip MVP; Feedback page; Audit `actor_email` |
| DO internal-write | feedback write/cleanup; audit enrich (Supabase) |
| DO Postgres | `feedback` migration + purge job |
| OpenAPI / infra yaml | ask/feedback/audit fields; energy/feedback knobs |

### Env / secrets

| Key | Where | Ship expectation |
|-----|-------|------------------|
| `SUPABASE_SECRET_KEY` | DO write-api (F69) | **Must sync** for live actor email; UUID fallback without it |
| energy_* / feedback retention | `infra/vecinita.yaml` / env | Defaults OK; not secrets |
| `VECINITA_CORS_ORIGINS` / `VITE_*` | Existing | **Unchanged** |

### Redeploy order (staging)

1. Ensure `main` @ `c942971` (+ optional PR for Phase D docs `ffc66b1`)  
2. `source prod.env` → `do_apps.py sync-secrets` (+ `sync_modal_secret.sh --merge --apply` if needed)  
3. DO CD: Alembic → force deploy write API + ChatRAG API/FE + Admin FE  
4. Smokes at 13: H1–H3 → ChatRAG wait/energy/feedback → Admin Feedback/Audit → H4–H5  

## Failure mitigations (proposed)

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Missing `SUPABASE_SECRET_KEY` | Audit shows truncated UUID; sync secret then redeploy write-api | **proposed** |
| 2 | Feedback migration not applied | DO CD Alembic; confirm table before Feedback smokes | **proposed** |
| 3 | Auth/CORS / browser | H0c PASS; H4–H5 via `verify_connectivity.sh` at 13 | **proposed** |
| 4 | Energy heuristic misread as live power | Advisory copy + ADR-047; AC-UX16 holds live Modal power OOS | **proposed** |

## Rollback (proposed)

| Item | Plan |
|------|------|
| DO apps | Redeploy prior revisions / revert merge on `main` |
| Alembic feedback | Prefer leave forward (anonymous rows); purge job can stay |
| Last known good | `main` before #207 / prior milestone merges as needed |

## Connectivity readiness

| Gate | Status |
|------|--------|
| H0c CORS unit | **PASS** |
| VITE / CORS matrix | **PASS** — no new origins |
| H4–H5 | Planned at **13** |
| Live F69 email enrich | Needs secret sync |

## Sign-Off (pending)

- [x] User approved implementation (11-verify-impl — S026-D55)
- [ ] User approved failure mitigations + rollback
- [ ] Deploy strategy verified → ready for 13
- [ ] Operator: `SUPABASE_SECRET_KEY` sync when `prod.env` available

## AC ship notes

| AC | At 12 | At 13 |
|----|-------|-------|
| UX1–15,17 | T0 met | Live UI smokes |
| UX16 | held | confirm no OOS ship |
| UX14 live email | UUID fallback OK | enrich after secret sync |
