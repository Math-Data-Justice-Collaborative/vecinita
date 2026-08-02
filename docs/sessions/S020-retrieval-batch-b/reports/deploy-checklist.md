# Deploy Checklist — S020 / EV-017 Retrieval Batch B (F43–F45)

> **Generated**: 2026-08-02  
> **Status**: **ready**  
> **Mode**: DELTA (API/backend + `packages/rag` + flags; no FE)  
> **Branch tip**: `evolve/EV-017-retrieval-batch-b` @ `e1e2899`  
> **Staging now**: `main` @ `b08ec30` — Batch B **not** deployed until 13  
> **PR**: [#173](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/173)  
> **Deployment plan**: `docs/deployment-integration.md` §EV-017  
> **Session**: S020-retrieval-batch-b  
> **Ship gate**: [ce-ship-gate.md](./ce-ship-gate.md) · [spike-f45-ce-runbook.md](./spike-f45-ce-runbook.md)  
> **11-verify-impl**: [verify-impl.md](./verify-impl.md) — **completed / approved**

## Phase 1 — Pre-Deploy Checks (summary)

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Configuration | **PASS** | §EV-017 added to `deployment-integration.md` |
| 2 | Secrets | **PASS** | Guard scripts present; **no new secrets** for F43–F45 |
| 3 | Data / volumes | **PASS** | In-process cache; existing `llm-models`; CE spike ephemeral only |
| 4 | Resources | **PASS** | No prod GPU for F43/F44; CE T4 only if UJ-060 run |
| 5 | Browser connectivity (Agent 6) | **N/A-delta** / carry-forward | No FE; H0c artifacts present; live H4–H5 at 13 |
| 6 | Modal / DO secret parity (Agent 7) | **PASS** | Embed/LLM declared; RAG knobs optional (defaults) |
| 7 | Ship-path carry-forward | **ADVISORY** (required) | UJ-060 / AC-BB9 on 13; prod CE **off** until gate |

### Flag defaults (must remain for T0 ship)

| Env | Default | Ship expectation |
|-----|---------|------------------|
| `VECINITA_RAG_CACHE` | `true` | On after ChatRAG redeploy |
| `VECINITA_RAG_SOFT_LANGUAGE_FALLBACK` | `false` | **OFF** unless ops enable for UJ-058 live |
| `VECINITA_RAG_RERANK_CE` | `false` | **OFF** until AC-BB9 / UJ-060 pass |

### Redeploy order (staging)

1. Optional: Modal URL secret sync (skip if unchanged)
2. **`vecinita-chat-rag-backend`** — tip with F43–F45 (primary)
3. Smokes: `do_verify` → `staging_smoke.sh` (H1) → `verify_connectivity.sh` (H4–H5) → live `openapi.json` has `cache_hit`
4. **UJ-060 / AC-BB9** CE spike per runbook — **do not** set `VECINITA_RAG_RERANK_CE=true` unless gate passes

## Failure mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Tip not on staging — no live `cache_hit` | Merge/deploy tip; verify live OpenAPI before claiming F43 | **approved** (2026-08-02) |
| 2 | Clients break on required `cache_hit` | Tip OpenAPI SoT; no FE delta; smoke `/ask` + stream `done` | **approved** |
| 3 | CE on before UJ-060 | Default off; no DO YAML enable; gate before toggle | **approved** |
| 4 | Soft language on unexpectedly | Default off; enable only for staged UJ-058 | **approved** |
| 5 | Multi-replica in-process cache miss | Expected ADR-042; not a deploy failure | **approved** (accept) |
| 6 | Stale Modal embed/LLM URL | `modal_url_validate` + `do_verify` | **approved** |
| 7 | Auth/CORS / browser connectivity | H0c green; H4–H5 via `verify_connectivity.sh` at 13 | **approved** |

## Rollback

| Item | Plan |
|------|------|
| Kill switches | `VECINITA_RAG_CACHE=false`; keep soft-language + CE **false** |
| Code rollback | Redeploy prior ChatRAG DO deployment / SHA **`b08ec30`** (pre-Batch B) |
| Procedure | 1) Confirm regression 2) Apply kill switch or redeploy prior 3) Re-run H1 + OpenAPI check |
| CE spike | Stop ephemeral `vecinita-spike-f45-rerank` if started |
| Volumes / corpus | None — in-process cache only |

**User approved rollback** — option 1, 2026-08-02.

## UJ-060 / AC-BB9 (carry into 13)

- [ ] Staging CE spike Path A (Modal T4) per runbook
- [ ] Fill `ce-ship-gate.md` / spike JSON — relevancy ≥ 0.28, faith ≥ 0.91
- [ ] Prod `VECINITA_RAG_RERANK_CE` remains **false** unless gate passes
- [ ] LLM for spike = prod URL only (never playground)

## Pre-Deploy checklist

- [x] Configuration complete (defaults OFF for soft language + CE; cache ON)
- [x] `deployment-integration.md` §EV-017 documented
- [x] All secrets configured (no new F43–F45 secrets)
- [x] Data assets / volumes OK
- [x] Resource allocation verified
- [x] Rollback plan reviewed
- [x] H0c CORS unit test artifact present
- [x] Frontend `VITE_*` matrix — **N/A-delta**
- [x] Post-deploy H4–H5 command documented (`verify_connectivity.sh`)
- [x] Failure modes approved (Phase 2)
- [x] UJ-060 / AC-BB9 carry documented; prod CE off until gate

## Sign-Off

- [x] User approved implementation (11-verify-impl) — 2026-08-02
- [x] User approved failure mitigations (12 Phase 2) — option 1, 2026-08-02
- [x] User approved rollback plan (12 Phase 3) — option 1, 2026-08-02
- [x] Deploy strategy verified — checklist **ready**
- [x] Ready for 13-deploy-smoke

## Summary

```
Deploy Strategy Verification Complete.

Pre-deploy checks:
  Configuration: PASS
  Secrets:       PASS — no new secrets
  Data/Volumes:  PASS
  Resources:     PASS

Failure mitigations: 7 risks addressed (all approved)
Rollback plan: reviewed / approved

Deploy gate:
  ✓ QA checks passed (09-qa)
  ✓ E2E behaviors passed (10-e2e)
  ✓ Implementation verified (11-verify-impl)
  ✓ Deploy strategy verified
  → Ready for deployment (API + browser connectivity plan verified)

Next step: 13-deploy-smoke
```
