# ADR-036: EV-010 playground model download (F38)

**Status:** Accepted (backend superseded by [ADR-037](ADR-037-unified-vecinita-llm-modal-app.md))  
**Stage:** 04-tech-plan (S009, EV-010)  
**Date:** 2026-07-05  
**Feature:** **F38** — Playground model download (super-admin)  
**Builds on:** [ADR-035](ADR-035-ev009-eval-playground-production-config.md), RD-146–RD-153, api-contract §EV-010

> **ADR-037 note (2026-07-08):** F38 UI and API paths unchanged. Modal backend moved from
> `vecinita-ollama` + `vecinita-models` to **`vecinita-llm`** + **`llm-models`** with HF Hub
> downloads (not `ollama pull`). See ADR-037 §Decision items 4–5.

## Context

F37 (EV-009) delivered the Evaluation Playground with an Ollama model picker and Modal background
pull infrastructure (`GET/POST /models/ollama*` on `vecinita-ollama`, proxied through
`internal-write-api`). Pull was wired with `WriteActorDep` (any admin) and **no download UI** —
operators could not trigger pulls from the browser.

S009 / EV-010 adds **super-admin-only** model download: tighten pull auth, expose a Playground
download panel, poll the model list until `available=true`, and cover the flow with a full-stack
test matrix (TC-134–TC-138, UJ-048, AC-E27–AC-E29).

01-requirements (RD-146–RD-153) locked product scope. F38 **targets Modal Volume storage** for all
playground Ollama model weights (see §3 below). The Modal Ollama app implements pull + manifest;
F38 v1 adds super-admin UI and auth on top of that pipeline without changing storage location.

## Decision

### 1. Build order (TP-S009-01)

Implement milestones **M71 → M72 → M73** on branch `feat/S009-playground-model-download`
(branched from `main` at 07-build — TP-S009-02). API auth ships before UI; UI before cross-layer
E2E/Playwright.

### 2. Pull auth tightening (M71, TP-S009-03)

Change `POST /internal/v1/models/ollama/pull` dependency from `WriteActorDep` to
`SuperAdminActorDep` — mirror the existing promote route pattern (ADR-035 §9).

| Route | Auth |
|-------|------|
| `GET /internal/v1/models/ollama` | `WriteActorDep` (admin + super-admin) — unchanged |
| `POST /internal/v1/models/ollama/pull` | `SuperAdminActorDep` only; admin → `403` |

No new middleware or role tables. Super-admin continues to be seeded via
`VECINITA_SUPER_ADMIN_EMAIL` (ADR-035 §9).

### 3. Model storage — Modal Volume only (TP-S009-17)

**Canonical storage target:** all playground Ollama model weights live on the Modal Volume
**`vecinita-models`**, mounted at **`/models`** in `vecinita-ollama` containers (`OLLAMA_MODELS=/models`).

| Artifact | Location | Notes |
|----------|----------|-------|
| Ollama model blobs | `/models` on `vecinita-models` | Written by `ollama pull` inside `pull_model_job` |
| Availability manifest | `/models/manifest.json` | `{ models: [{ model_id, available }] }`; `model_volume.commit()` after writes |
| Pull job status (v1) | Modal Dict `vecinita-ollama-pull-jobs` | Ephemeral; UI polls manifest via list API, not Dict |
| Playground config / presets | DO Postgres | **Not** model weights — eval config only (ADR-035) |

**Download data path (F38):**

```text
Playground UI → internal-write-api POST /models/ollama/pull
  → Modal ASGI vecinita-ollama POST /models/ollama/pull
  → pull_model_job.spawn → ollama pull → manifest update → volume commit
```

**Explicit non-targets (v1):** DO App Platform ephemeral disk, Postgres BYTEA/object columns, S3/Spaces,
browser `localStorage`, or external Ollama hosts. Eval runs and ChatRAG production LLM (vLLM) remain
separate from playground Ollama storage (RD-140).

**F38 code changes:** `infra/modal/ollama_app.py` — **no functional changes** in v1; storage pipeline
already implemented in F37 (`pull_model_job`, `_write_manifest`, volume mount). F38 verifies and
documents this contract; optional unit tests on manifest helpers (T73.6).

### 4. Frontend API client (M72, TP-S009-05)

Add `pullOllamaModel(client, modelId)` to `apps/data-management-frontend/src/api/admin.ts`:

- `POST /internal/v1/models/ollama/pull` with `{ model_id }`
- Expect `202`; throw on non-2xx with status in message (match `fetchOllamaModels` error style)
- Unit tests in `admin.test.ts`

### 5. Playground download UI (M72, TP-S009-06, TP-S009-07)

In `EvaluationPlaygroundTab`:

- Render a **Download model** `Card` in the config column (below the model picker) **only when**
  `authCtx?.role === "super-admin"` (RD-151 — hidden for admin/viewer, not disabled).
- Fields: text input for Ollama tag, **Download** button, status line (`idle` | `pulling` | `success` | `timeout` | `error`).
- On Download: call `pullOllamaModel`, then start poll loop.
- **Poll contract** (RD-150, api-contract §EV-010): re-fetch `fetchOllamaModels` every **10s**;
  stop when matching `model_id` has `available: true` or **30 min** elapsed (show timeout + allow retry).
- On success: refresh picker options and select the new model if not already selected.
- Allow parallel duplicate pulls (RD-149) — no client-side dedup.

Reuse existing `isSuperAdmin` guard pattern from promote button (ADR-035 §10).

### 6. i18n (TP-S009-08)

Add EN/ES keys under `admin.evaluation.playground.download*` in `packages/frontend-i18n`.

### 7. Test strategy (TP-S009-14, TP-S009-15)

| Layer | Module | Cases |
|-------|--------|-------|
| Integration | `tests/integration/test_ollama_models_list.py` | TC-134 — split admin list vs super-admin pull vs admin pull 403 |
| Unit | `tests/unit/internal_write_api/test_app_eval_routes.py` | Pull route auth matrix |
| Unit (Modal storage) | `tests/unit/modal/test_ollama_volume_manifest.py` | TC-139 — manifest read/write contract for `vecinita-models` |
| Vitest | `test_evaluation_playground.test.tsx` | TC-135, TC-136 — fake timers for 10s poll |
| API E2E | `tests/e2e/test_uj048_playground_model_download.py` | TC-138 |
| Playwright T0-ui | `tests/ui/admin/uj048-playground-model-download.spec.ts` | TC-137 |
| Unit (client) | `admin.test.ts` | `pullOllamaModel` |

**Playwright helper (TP-S009-09):** Add `mockAuthenticatedSuperAdmin` in
`tests/ui/helpers/mock-admin-auth.ts` (parallel to `seedAdminSession` with
`app_metadata.role: "super-admin"`).

Revise existing integration test `test_admin_lists_models_and_triggers_pull` — admin pull must
expect `403`; add `test_super_admin_triggers_pull`.

### 8. Connectivity / CORS (TP-S009-12)

No new routes or HTTP verbs. Existing CORS preflight for `POST` on pull path (Phase 15 / EV-009)
remains valid. M71 includes a regression assertion in `test_cors_policy.py` only if route
signature changes surface new preflight requirements.

### 9. OpenAPI (TP-S009-13)

Update `openapi/internal-write.yaml` — document `SuperAdminActorDep` on pull route (EV-010 section).

### 10. Deploy (TP-S009-11, TP-S009-16)

Evolve-lite single PR (**PR-52**) to `main`:

1. `internal-write-api` (auth change only)
2. `data-management-frontend` (download UI)

No DB migration. **`vecinita-ollama` Modal app + `vecinita-models` volume** must be deployed;
`VECINITA_MODAL_OLLAMA_URL` on internal-write-api must point at the Modal ASGI URL for pulls to
reach Modal storage (deploy checklist — not an F38 code blocker). Optional T3 smoke: super-admin
pull in staging confirms manifest `available=true` on volume.

### 11. Dependencies (TP-S009-10)

No new Python or Node runtime dependencies.

## Consequences

**Positive**

- Clear auth boundary: only super-admins can enqueue volume pulls; admins retain list/select.
- **Single storage location:** all playground model weights on Modal `vecinita-models` — no split-brain across DO/Modal.
- Reuses proven Modal pull + manifest pipeline from F37.
- Full-stack test matrix satisfies user emphasis on testing (RD-152).

**Negative / trade-offs**

- Large model downloads may exceed 30 min — operator must retry manually (no job-status endpoint v1).
- Free-text tags allow oversized models — no allow-list v1 (RD-148); operational risk accepted.
- Duplicate parallel pulls may waste Modal compute (RD-149).

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Keep admin pull (F37 TC-134) | User decision RD-147 / R78 — super-admin only |
| Disabled download UI for admin with tooltip | RD-151 — hidden entirely |
| Dedicated `GET /models/ollama/pull/{job_id}` status | RD-150 — poll model list only in v1 |
| Auto-pull on eval run when model missing | Out of scope v1 (RD-77) |
| Ollama library catalog browser | Out of scope v1 |
| DO disk / Postgres / S3 for model weights | TP-S009-17 — Modal Volume only |
| External self-hosted Ollama host | RD-140 — Modal Ollama on `vecinita-models` |

## References

- `docs/api-contract.md` §EV-010
- `docs/user-journeys.md` UJ-048
- `docs/test-plan.md` TC-134–TC-138
- `docs/sessions/S000-internal-docs-archive/context/playground-model-download.md`
- Execution plan Phase 16 (M71–M73)
