# Deploy Checklist — S021 / EV-018 Retrieval Follow-on (F46 + F45)

> **Generated**: 2026-08-02  
> **Status**: **approved** — Phase 2/3 signed (S021-D26); handoff to 13-deploy-smoke  
> **Mode**: DELTA — corpus guard + docs; Path B staging restore **already live**; CE metrics **PASS**  
> **Branch tip**: `evolve/EV-018-retrieval-follow-on` @ `8f9de98` (+ workflow-state dirty for D26)  
> **Staging now**: `main` (may lag tip until 13 merge/deploy)  
> **Deployment plan**: `docs/deployment-integration.md` §EV-017 (flags) + S021 Path A  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **approved** F46+F45 (S021-D25)  
> **Ship gate**: [ce-ship-gate.md](./ce-ship-gate.md) — **PASS** (`ship_gate_pass=true`)

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | No new secrets; CE default remains `false` |
| 2 | Secrets | **PASS** | Guard scripts OK; Modal no DATABASE_URL |
| 3 | Data / volumes | **PASS** | Path B E0 promote already on staging (`a0e8f32d-…`); no further corpus mutate at deploy |
| 4 | Resources | **PASS** | CE spike already run (ephemeral T4); no durable CE GPU for ship |
| 5 | Browser connectivity (Agent 6) | **N/A-delta** / carry-forward | No FE; H0c PASS; H4–H5 at 13 |
| 6 | Modal / DO secret parity | **PASS** | Existing embed/LLM URLs; no new knobs required |
| 7 | Ship-path CE flag | **PASS / hold** | AC-BB9 **PASS**; **do not** set `VECINITA_RAG_RERANK_CE=true` without explicit Path A CE approval |

### Flag defaults (must remain for this ship)

| Env | Default | Ship expectation |
|-----|---------|------------------|
| `VECINITA_RAG_RERANK_CE` | `false` | **OFF** on ChatRAG redeploy (AC-FO4 / S021-D24) even though AC-BB9 PASS |
| `VECINITA_RAG_CACHE` | `true` | Unchanged |
| `VECINITA_RAG_SOFT_LANGUAGE_FALLBACK` | `false` | Unchanged |

### Redeploy order (staging Path A)

1. Merge PR → `main` (or pin evolve for smoke then merge)  
2. Redeploy **`vecinita-chat-rag-backend`** (guarded helpers ship with tests; runtime ask path unchanged)  
3. Smokes: `do_verify` → `staging_smoke.sh` (H1) → `verify_connectivity.sh` (H4–H5)  
4. Confirm staging retrieve still non-empty (UJ-061 sample) — Path B already restored  
5. **Optional later:** enable `VECINITA_RAG_RERANK_CE=true` on staging only after separate Path A CE approval — **not** this default ship

## Failure mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Tip not on staging — guard only in git | Merge/deploy tip; pytest + CI prove guard | **approved** (S021-D26) |
| 2 | Accidental CE flag on | Keep DO env `false`; TC-183; no YAML enable in this cycle | **approved** (S021-D26) |
| 3 | Staging corpus re-wipe via pytest | Corpus DB guard + skill; never source staging URL into pytest shell | **approved** (S021-D26) |
| 4 | Empty pools regress after unrelated promote | Probe script; Path B runbook retained | **approved** (S021-D26) |
| 5 | Auth/CORS / browser connectivity | H0c green; H4–H5 at 13 | **approved** (S021-D26) |

## Rollback

| Item | Plan |
|------|------|
| Kill switches | Keep `VECINITA_RAG_RERANK_CE=false`; cache kill-switch unchanged |
| Code rollback | Redeploy prior ChatRAG DO image / `main` SHA before EV-018 merge |
| Corpus | Do **not** TRUNCATE; restore from DO backup only if embeddings wiped again |
| CE spike | Ephemeral app already finished; no durable CE deploy |

**User approved rollback** — S021-D26 option 1, 2026-08-02.

## Pre-Deploy checklist

- [x] Configuration complete (CE **OFF**)  
- [x] AC-BB9 evidence recorded (no empty-pool spike)  
- [x] Secrets / Modal / OpenAPI / operator-spec guards PASS  
- [x] H0c CORS unit tests PASS  
- [x] Connectivity scripts present (`verify_connectivity.sh`, staging smoke tests)  
- [x] Frontend `VITE_*` matrix — **N/A-delta**  
- [x] Post-deploy H4–H5 command documented  
- [x] Failure modes approved (Phase 2) — S021-D26  
- [x] Rollback plan approved (Phase 3) — S021-D26  

## Sign-Off

- [x] User approved implementation (11-verify-impl) — S021-D25, 2026-08-02  
- [x] User approved failure mitigations (12 Phase 2) — S021-D26, 2026-08-02  
- [x] User approved rollback plan (12 Phase 3) — S021-D26, 2026-08-02  
- [x] Ready for 13-deploy-smoke  

## Summary

```
Pre-deploy checks: PASS (CE flag hold)
AC-BB9: PASS (already run)
12 Phase 2+3: APPROVED (S021-D26)
Next: 13-deploy-smoke Path A — merge/redeploy ChatRAG; CE stays false
```
