# Deploy Checklist — S001 Modal cold-start / GPU snapshot

> **Generated**: 2026-06-25  
> **Status**: **ready**  
> **Session**: S001-modal-cold-start-snapshot  
> **Stage**: 12-verify-deploy (delta — user-invoked; not in session routing plan)  
> **Deployment plan**: [deployment-integration.md](../../../deployment-integration.md) + [ADR-022](../../../adr/ADR-022-gpu-memory-snapshot-cold-start.md)  
> **Branch verified**: `feat/S001-modal-cold-start-snapshot` @ `f766233`  
> **Previous checklist**: [deploy-checklist.md](../../../deploy-checklist.md) (EV-002 @ 2026-05-27)

## Scope (changed surfaces only)

| Surface | Platform | Change |
|---------|----------|--------|
| `vecinita-llm` | Modal (T4 GPU) | GPU memory snapshots, vLLM 0.7.x, split `@modal.enter`, `VECINITA_LLM_ENFORCE_EAGER` A/B |
| `vecinita-embedding` | Modal (CPU) | CPU memory snapshot + `scaledown_window=600` |
| `chat-rag-backend` | DO | `POST /api/v1/warm` → parallel Modal `/warm` |
| `chat-rag-frontend` | DO static | `prewarmChatServices()` on chat mount |

**No changes:** Postgres, internal-write-api, data-management apps, CORS secrets matrix, `VITE_*` vars.

## Pre-Deploy

| Check | Result | Evidence |
|-------|--------|----------|
| Configuration complete (no gaps) | **PASS** | `infra/modal/llm_app.py`, `embedding_app.py`; warm chain wired FE→BE→Modal |
| All secrets configured | **PASS** | No new Modal secrets; `VECINITA_LLM_ENFORCE_EAGER` defaults `true` (optional A/B) |
| Data assets staged | **PASS** | D6/D7 volumes unchanged; snapshots are Modal-managed state, not Volume assets |
| Resource allocation verified | **PASS** | T4 scale-to-zero preserved; `scaledown_window=300` (LLM), `600` (embed); no `min_containers` |
| Rollback plan reviewed | **APPROVED** | User sign-off 2026-06-25 |
| H0c CORS unit tests pass | **PASS** | `pytest tests/unit/test_cors_policy.py` — includes `POST /api/v1/warm` preflight |
| Frontend `VITE_*` ↔ API URL matrix | **PASS** | Pre-warm reuses `VITE_VECINITA_CHAT_API_URL`; no new rows |
| `VECINITA_CORS_ORIGINS` documented | **PASS** | Unchanged; existing chat frontend origin covers `/api/v1/warm` |
| Post-deploy H4–H5 command documented | **PASS** | `bash scripts/deploy/verify_connectivity.sh` (+ optional warm H4 extension) |
| Build verify (08) | **PASS** | [verification-report.md](verification-report.md) — milestone boundary PASS |

### S001-specific checks

| Check | Result | Evidence |
|-------|--------|----------|
| P1 instrumentation gate passed | **PASS** | [p1-cold-start-traces.md](p1-cold-start-traces.md) — compilation/init dominates |
| GPU snapshot deploy (T8) | **PASS** | [p2-snapshot-deploy.md](p2-snapshot-deploy.md) — snapshot created + restore log |
| Cold-start measurement (T9) | **PASS** | [p3-snapshot-deploy-traces.md](p3-snapshot-deploy-traces.md) — ~9s restore vs ~71s creation |
| Pre-warm client (T11) | **PASS** | `warm.ts` + `ChatPanel.tsx`; backend `POST /api/v1/warm` |
| `enforce_eager` A/B (T7) | **PASS** | Default `true`; unit tests green; Arm B deferred |
| T12 web-fn hop collapse | **PENDING** | Not blocking deploy; follow-up in 07-build |
| ADR-022 status reconciled | **ADVISORY** | Header Accepted; body still says "Proposed" — reconcile before merge |

## Configuration validation (Agent 1)

| Item | Status |
|------|--------|
| `infra/modal/llm_app.py` — `enable_memory_snapshot` + `enable_gpu_snapshot` | OK |
| Split `@modal.enter(snap=True/False)` + `sleep`/`wake_up` | OK |
| vLLM pin `>=0.7,<0.8` + sleep mode | OK |
| `scripts/deploy/modal.sh` covers `llm_app.py` + `embedding_app.py` | OK |
| `VECINITA_LLM_ENFORCE_EAGER` in secrets matrix | **Advisory gap** — document optional A/B lever |
| `⚠️ Needs human input` markers | None |

## Secrets check (Agent 2)

| Secret / env | Platform | Status |
|--------------|----------|--------|
| `VECINITA_LLM_ENFORCE_EAGER` | Modal runtime (optional) | **PASS** — default `true`; not a secret |
| `TORCHINDUCTOR_COMPILE_THREADS` / `XFORMERS_ENABLE_TRITON` | Image-baked | **PASS** |
| Existing `VECINITA_MODAL_*` URLs on DO ChatRAG | DO | **PASS** — unchanged |
| `VECINITA_CORS_ORIGINS` | DO chat-rag-backend | **PASS** — unchanged |
| Modal secret on `vecinita-llm` | — | **PASS** — none attached (by design) |

## Data & volumes (Agent 3)

| Asset | Status | Notes |
|-------|--------|-------|
| D6 `embedding-models` | **PASS** | Unchanged; CPU snapshot only |
| D7 `llm-models` | **PASS** | Unchanged; weights still on Volume |
| D1–D5, D8–D9 | **N/A** | No DB/corpus changes |
| New Modal volumes | **N/A** | Snapshots are Modal infra, not Volume assets |

## Resource allocation (Agent 4)

| Resource | Spec | Actual | Status |
|----------|------|--------|--------|
| LLM GPU | T4, scale-to-zero | `gpu="T4"`, `scaledown_window=300` | **PASS** |
| Embedding | CPU, scale-to-zero | CPU snapshot, `scaledown_window=600` | **PASS** |
| `min_containers` | 0 (ADR-004 budget) | Not set (defaults 0) | **PASS** |
| Pilot cost cap | ≤ $50/mo | No always-warm change | **PASS** |

## Template / deploy conformance (Agent 5)

| Item | Status |
|------|--------|
| Modal deploy command | `modal deploy infra/modal/llm_app.py` (via `scripts/deploy/modal.sh`) | OK |
| App name `vecinita-llm` | Matches `deployment-integration.md` | OK |
| DO apps for warm route | chat-rag-backend redeploy required | OK |
| CI import smoke | `.github/workflows/deploy-preflight.yml` | OK (on `main` post-merge) |

## Browser connectivity (Agent 6)

| Item | Status |
|------|--------|
| `tests/unit/test_cors_policy.py` | **PASS** — includes warm preflight |
| `configure_cors` on all FastAPI apps | **PASS** |
| `verify_connectivity.sh` + live smoke tests | **PASS** — present |
| New `VITE_*` rows | **N/A** |
| Live H4 on `/api/v1/warm` | **Advisory** — H0c covers; extend live smoke optional |

## Failure mitigations

| # | Risk | Mitigation | Status |
|---|------|-----------|--------|
| 1 | GPU snapshot alpha restore failure | Pre-warm (T11) hides cold path; rollback = redeploy pre-snapshot `llm_app.py` | **approved** |
| 2 | First-ever snapshot **creation** boot ~71s (504) | Pre-warm on chat mount fires before user asks; creation is one-time per deploy/GPU type | **approved** |
| 3 | Modal image build failure (vLLM 0.7.x) | `verify_build.sh` + deploy-preflight import smoke; pin `vllm>=0.7,<0.8` | **approved** |
| 4 | `enforce_eager=false` + snapshot interaction | Default `true`; Arm B deferred until measured | **approved** |
| 5 | Warm endpoint CORS blocked in browser | H0c `test_chat_rag_cors_preflight_on_warm`; existing `VECINITA_CORS_ORIGINS` | **approved** |
| 6 | Scale-to-zero cost regression | No `min_containers`; monitor Modal billing post-deploy | **approved** |
| 7 | T12 second cold start (ASGI web-fn hop) | Documented follow-up; pre-warm + snapshot restore still within DO budget | **approved** |

## Rollback

**Procedure (S001 delta — reverse deploy order):**

1. **chat-rag-frontend** — Redeploy previous build (removes client pre-warm) *optional if warm-only issue*
2. **chat-rag-backend** — Redeploy previous build (removes `POST /api/v1/warm`)
3. **vecinita-llm** — `git checkout <LKG> -- infra/modal/llm_app.py` then `modal deploy infra/modal/llm_app.py` (removes GPU snapshot)
4. **vecinita-embedding** — Redeploy previous build if embedding snapshot causes issues
5. **Emergency stop** — `modal app stop vecinita-llm` (blocks LLM until redeploy)
6. **Verify rollback** — H1–H3 staging smoke; confirm ask path works (may be slow cold start)

| Field | Value |
|-------|-------|
| **Last known good (staging main)** | `7f38c58` — EV-002 deployed 2026-05-27 |
| **Last known good (pre-S001 LLM)** | `ca77646` or parent of first S001 LLM snapshot commit |
| **Snapshot creation cost** | One-time ~71s boot per deploy/GPU worker type — not rolled back by code revert alone |

## Deploy order (S001)

1. **vecinita-llm** — `modal deploy infra/modal/llm_app.py` (triggers snapshot capture)
2. **vecinita-embedding** — `modal deploy infra/modal/embedding_app.py` (CPU snapshot; optional same window)
3. **chat-rag-backend** — redeploy with `POST /api/v1/warm` (DO)
4. **chat-rag-frontend** — redeploy with pre-warm on mount (DO)
5. **Post-deploy** — `bash scripts/deploy/verify_connectivity.sh` (H4–H5)
6. **Post-deploy** — `bash scripts/deploy/staging_smoke.sh` (H1–H3); measure cold vs warm ask
7. **15-service-health** — record DO-path cold ask latency (target < 60s with pre-warm + snapshot restore)

**Note:** Postgres, internal-write-api, data-management Modal/DO apps do **not** require redeploy.

## Deploy gate (upstream stages)

| Gate | Status |
|------|--------|
| Build verify (08) | **PASS** — S001 milestone boundary |
| QA (09) | **Skipped** — ops session; no new product surface |
| E2E (10) | **Skipped** — no new user journey |
| Implementation (11) | **Waived** — perf spike under ADR-009; 08-verify-build + P3 traces substitute |
| Deploy strategy (12) | **This checklist** |

## Sign-Off

- [x] User approved implementation (08-verify-build + P3 measurement)
- [x] Failure mitigations acknowledged (Phase 2) — 2026-06-25
- [x] Rollback plan approved (Phase 3) — 2026-06-25
- [x] Ready for **13-deploy-smoke** (staging DO path + cold-start measurement)

### Operator commands

```bash
# Pre-deploy: build smoke
bash scripts/deploy/verify_build.sh

# Deploy Modal (S001 primary)
bash scripts/deploy/modal.sh   # or: modal deploy infra/modal/llm_app.py

# Post-deploy: connectivity (blocking)
bash scripts/deploy/verify_connectivity.sh

# Post-deploy: API smoke (H1–H3)
bash scripts/deploy/staging_smoke.sh

# Measure cold ask (after container stop)
modal container stop vecinita-llm   # force cold
# then POST ask via DO chat backend URL
```

## Next step

**13-deploy-smoke** — deploy S001 to staging DO path; confirm end-to-end cold ask < 60s with pre-warm + snapshot restore; then **15-service-health**.
