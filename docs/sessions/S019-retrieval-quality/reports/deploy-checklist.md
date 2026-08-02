# Deploy Checklist — S019 / EV-016 Retrieval quality (F42)

> **Generated**: 2026-08-01  
> **Status**: **ready**  
> **Deployment plan**: [deployment-integration.md](../../../deployment-integration.md) §EV-016  
> **Stage**: 12-verify-deploy (S019 delta — F42 / Hy1 on E0)  
> **Branch**: `evolve/EV-016-retrieval-quality` @ `5530b46`  
> **Session**: S019-retrieval-quality  
> **Ship gate**: [hy1-ship-gate.md](hy1-ship-gate.md)

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete | **PASS** (after EV-016 section) | `deployment-integration.md` §EV-016; config-spec knobs; ADR-041 |
| All secrets configured | **PASS** (repo) / live ops at 13 | No new secrets; guard scripts green |
| Data assets staged | **PASS** (ISS-008 live = 13) | `qa_pairs_staging.json` in repo; write-api mapping on branch |
| Resource allocation verified | **PASS** | No GPU change; H7 ~3× embed/retrieve — monitor `basic-xxs` |
| Rollback plan reviewed | **APPROVED** | User option 1 — 2026-08-01 |
| H0c CORS unit tests | **PASS** | `pytest tests/unit/test_cors_policy.py` exit 0 (2026-08-01) |
| Frontend `VITE_*` ↔ API matrix | **PASS** | No F42 UI / CORS delta |
| `VECINITA_CORS_ORIGINS` documented | **PASS** | Existing ChatRAG + write-api rows |
| Post-deploy H4–H5 documented | **PASS** | `scripts/deploy/verify_connectivity.sh` |

## S019-specific deploy surfaces

| Surface | Change | Deploy / apply |
|---------|--------|----------------|
| `packages/rag` | H7 + P1 helpers | Library — ships with backends |
| DO internal-write-api | ISS-008 staging fixture + F36 H7/P1 | **First** DO redeploy |
| DO chat-rag-backend | Ask/stream H7+P1 defaults | **Second** DO redeploy |
| Modal embed / LLM / DM | None | Skip |
| Frontends | None | Skip |

### Redeploy order (staging)

1. Optional: `sync-all-secrets` if Modal URLs rotated
2. `vecinita-internal-write-api` (ISS-008 + eval sandbox)
3. `vecinita-chat-rag-backend` (F42 ask)
4. Ops smokes:
   - `bash scripts/infra/do_verify_required_secrets.sh`
   - `bash scripts/deploy/staging_smoke.sh` (H1)
   - `bash scripts/deploy/verify_connectivity.sh` (H4–H5)
   - Admin F36 Hy1 gate per `hy1-ship-gate.md` (AC-RQ6)

### Post-Modal secret sync (only if Modal redeployed)

```text
set -a && source prod.env && set +a
uv run python scripts/deploy/modal_url_validate.py
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
bash scripts/deploy/sync_github_secrets.sh --apply
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/verify_connectivity.sh
```

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| EV-016 in `deployment-integration.md` | OK (added 2026-08-01) |
| `VECINITA_RAG_*` in config-spec / ADR-041 | OK |
| ChatRAG / write-api entry points | OK |
| ISS-008 fixture mapping (code) | OK |
| ISS-008 live on staging | **OPS — 13** |
| `⚠️ Needs human input` markers | None |

## Secrets (Agent 2)

| Category | Status |
|----------|--------|
| New F42 secrets | PASS — none |
| DO ChatRAG / write-api matrix | PASS (repo) |
| Guard scripts | PASS |
| Live `do_verify` / `modal secret list` | SKIPPED locally — run at 13 |

## Data & volumes (Agent 3)

| Asset | Status |
|-------|--------|
| `qa_pairs_staging.json` | PASS |
| ISS-008 code | PASS |
| ISS-008 deployed | **FAIL until write-api redeploy** |
| New Modal volumes / re-embed | N/A — none; E0 pin retained |

## Resources (Agent 4)

| Check | Status |
|-------|--------|
| GPU tier change | N/A — none |
| DO instance size | Unchanged `basic-xxs` |
| H7 latency/cost | ACCEPT w/ monitoring — ~3× embed/retrieve; p95 << 15s in spikes |

## CI / CD (Agent 5)

| Check | Status |
|-------|--------|
| `ci.yml` → preflight → Modal → DO | PASS |
| Job template GPU/cache | N/A (hybrid api+worker) |
| F42 ships via DO backends | PASS |

## Browser connectivity (Agent 6)

| Check | Status |
|-------|--------|
| H0c / verify_connectivity / smoke tests | PASS (artifacts present) |
| New UI / CORS / VITE | N/A |
| Live H4–H5 | **13 after ChatRAG redeploy** |

## Modal / DO secret parity (Agent 7)

| Check | Status |
|-------|--------|
| Modal embed/LLM in DO YAML + sync | PASS |
| F42 knobs in `infra/do/` | Advisory gap — Hy1 defaults OK without YAML |
| Deploy order vs hy1-ship-gate | PASS — write-api → ChatRAG |

## Failure mitigations

| # | Risk | Mitigation | Status |
|---|------|------------|--------|
| 1 | Image / DO build failure | Existing CI + deploy-preflight; fix-forward on branch | **approved** |
| 2 | Secret / Modal URL stale | `modal_url_validate` + `do_verify_required_secrets` before smoke | **approved** |
| 3 | ISS-008 not live → wrong golden | Redeploy write-api **before** Hy1 gate | **approved** |
| 4 | H7 latency / embed load | Monitor p95; kill switch `VECINITA_RAG_MULTI_QUERY=false` | **approved** |
| 5 | Auth/CORS / browser connectivity | H0c green; H4–H5 via `verify_connectivity.sh` at 13 | **approved** |
| 6 | Hy1 floors miss (AC-RQ6) | Hold promote; investigate vs spike baseline; do not disable silently | **approved** |

## Rollback

| Item | Plan |
|------|------|
| Command / action | Set `VECINITA_RAG_MULTI_QUERY=false` on chat-rag-backend (and write-api if needed), **or** redeploy prior DO deployment / pre-F42 SHA |
| Procedure | 1) Confirm staging ask/eval regression 2) Apply kill switch or redeploy prior 3) Re-run H1 + optional F36 baseline |
| Last known good (staging pre-F42) | `a6c39e5` (2026-07-31) — lacks F42/ISS-008 |
| Embed / corpus | No change — E0 remains |

## Hy1 ship gate (carry into 13)

- [ ] ISS-008 deployed to staging write-api
- [ ] Staging Hy1 F36: relevancy ≥ 0.28, faithfulness ≥ 0.91
- [ ] Promote smoke uses staging golden path
- [ ] Prod embed pin unchanged (E0)

## Sign-Off

- [x] User approved implementation (11-verify-impl) — 2026-08-02
- [x] User approved failure mitigations (12 Phase 2) — option 1, 2026-08-01
- [x] User approved rollback plan (12 Phase 3) — option 1, 2026-08-01
- [x] Deploy strategy verified — checklist **ready**
- [x] Ready for 13-deploy-smoke
