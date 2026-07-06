# Scoped context — Playground model download (S009)

**Session:** S009-playground-model-download  
**Stage:** 00-context (scoped delta)  
**Date:** 2026-07-05  
**Prior session:** S008-eval-ux-playground (EV-009 / F37) — **parked** at 09-qa (coverage gate open)  
**Evolve cycle:** EV-010 (proposed)  
**Feature ID:** **F38** (proposed — super-admin playground model download)

---

## Executive summary

Super-admins need a **playground UI** to download additional Ollama models onto the Modal
`vecinita-models` volume so eval experiments can use tags beyond the default
`qwen2.5:1.5b-instruct`. Backend pull infrastructure from EV-009 (F37) already exists; the gap
is **super-admin-only authorization**, a **frontend download flow**, and **full-stack tests**.
Admins retain **list + select** for playground runs; only super-admins trigger pulls. Pull
progress is shown by **polling** `GET /internal/v1/models/ollama` until the model entry shows
`available: true` — no new status endpoint in v1.

User approved **evolve-lite** session **S009** (park S008, open new session), not a hotfix.

---

## User request (2026-07-05)

> Create a new feature that will allow super-admins (only) to download additional models for
> the playground to run. Testing to make sure this works is an important part.

Interview resolutions:

| Topic | Decision |
|-------|----------|
| Session | Close/park S008 → open **S009-playground-model-download** |
| Download scope | **Pull UI only** — enter tag, trigger Modal background pull, show status |
| Auth | **Super-admin: pull** · **Admin: list + select** (not pull) |
| Pull progress | **Poll model list** until `available=true` |
| Testing | **Full stack** — unit, integration, Vitest, pytest e2e, Playwright |
| S008 handoff | **Park** — coverage gate remains open follow-up on `feat/S008-eval-ux-playground` |

---

## Current state (repo evidence)

### Modal Ollama app — pull infrastructure exists

[`infra/modal/ollama_app.py`](../../../infra/modal/ollama_app.py):

- Volume `vecinita-models`; manifest at `/models/manifest.json`
- `pull_model_job` — background `ollama pull`, updates manifest, tracks status in Modal Dict
- ASGI routes: `GET /models/ollama`, `POST /models/ollama/pull` (returns `202` + `job_id`)
- Proxy auth via `X-Vecinita-Proxy-Key`

### Internal write API — routes exist, wrong auth for pull

[`apps/internal-write-api/vecinita_internal_write_api/app.py`](../../../apps/internal-write-api/vecinita_internal_write_api/app.py):

- `GET /internal/v1/models/ollama` — `WriteActorDep` (admin+) ✓ matches desired admin list
- `POST /internal/v1/models/ollama/pull` — `WriteActorDep` (admin+) ✗ should be `SuperAdminActorDep`

[`packages/shared-schemas/vecinita_shared_schemas/ollama_models.py`](../../../packages/shared-schemas/vecinita_shared_schemas/ollama_models.py) — request/response models defined.

### Admin frontend — list only, no download UI

[`apps/data-management-frontend/src/api/admin.ts`](../../../apps/data-management-frontend/src/api/admin.ts):

- `fetchOllamaModels()` — implemented
- **No** `pullOllamaModel()` client function

[`EvaluationPlaygroundTab.tsx`](../../../apps/data-management-frontend/src/evaluation/EvaluationPlaygroundTab.tsx):

- Loads models into picker; `isSuperAdmin` already computed for promote button
- **No** download form / pull trigger / polling UX

### Tests — admin pull assumed; needs auth matrix update

| Test | Current behavior | Required change |
|------|------------------|-----------------|
| `tests/integration/test_ollama_models_list.py` | Admin can pull (`202`) | Super-admin pull OK; **admin pull → 403** |
| `tests/unit/internal_write_api/test_app_eval_routes.py` | Pull route tests | Add super-admin vs admin matrix |
| `tests/unit/test_cors_policy.py` | CORS on pull route | Keep (no change expected) |
| Vitest playground tests | Model list load | Add super-admin download UI tests |
| Playwright `uj045-eval-playground.spec.ts` | Playground journey | Extend or add UJ for download |

**TC-134** ([`docs/test-plan.md`](../../../test-plan.md)): currently expects admin pull — **spec drift** vs user decision.

### Spec / ADR baseline

- **F37** ([`docs/feature-list.md`](../../../feature-list.md)): mentions background pull for missing models (RD-141); does not define super-admin-only download UI
- **ADR-035**: Ollama model picker + background pull; promote is super-admin; pull auth not restricted to super-admin in implementation
- **api-contract.md** §EV-009: documents eval/promote routes; **does not document** `/models/ollama*` — gap for F38 delta

---

## Multi-app topology (connectivity)

| Consumer | API | Change |
|----------|-----|--------|
| Admin FE Playground | `internal-write-api` | New download UI → `POST …/models/ollama/pull` (super-admin JWT); poll `GET …/models/ollama` |
| Modal `vecinita-ollama` | Proxy from internal-write-api | Unchanged — existing pull spawn |
| Eval runner | Uses selected `model_id` | Unchanged — models must be `available` before run |

**Browser integration risk:** Low — same-origin admin FE → internal-write-api pattern as F37.
Ensure CORS preflight still covers `POST` on pull route (existing H0c coverage).

**Auth expansion:** Tighten pull to `super-admin` only; `admin` receives `403` on pull (mirror promote pattern).

---

## Cross-reference matrix

| Source | List models | Pull model | Download UI | Super-admin pull |
|--------|-------------|------------|---------------|------------------|
| User request (2026-07-05) | admin | super-admin only | yes | yes |
| F37 / TC-134 | admin | **admin** | no | no |
| Current code | admin (`WriteActorDep`) | admin | no | no |
| ADR-035 RD-141 | implied admin | background job | no | no |

**Classification:** Implementation drift + **spec delta** (TC-134, F38, api-contract).

---

## Resolution log (S009 00-context)

| # | Category | Resolution |
|---|----------|------------|
| R76 | Decision | Session: park S008; open **S009-playground-model-download** / **EV-010** |
| R77 | Decision | Scope: **pull UI only** (no catalog browser, no auto-pull on eval run v1) |
| R78 | Decision | Auth: **super-admin pull** · **admin list+select** |
| R79 | Decision | Progress UX: **poll model list** (no new job-status endpoint v1) |
| R80 | Decision | Testing: **full stack** (unit + integration + Vitest + e2e + Playwright) |
| R81 | Decision | Routing: **evolve-lite** 00→01→04→07→08→09→10→11→12→13 |
| R82 | Decision | Feature ID: **F38** (new — playground model download) |

---

## Unresolved gaps (for 01-requirements / 04-tech-plan)

1. **Allowed model tags** — free-text Ollama tag only, or allow-list / block-list for size/licensing?
2. **Concurrent pulls** — allow multiple in-flight pulls or reject if same tag already `pulling`?
3. **Failed pull UX** — manifest stays `available: false`; how long to poll / error message shape?
4. **Branch base** — S009 branch from `main` vs `feat/S008-eval-ux-playground` if S008 not merged
5. **Production Ollama wiring** — BUG-2026-07-05 showed `VECINITA_MODAL_OLLAMA_URL` may be unset in DO; download UI useless until Ollama URL configured (document in deploy checklist, not F38 blocker)

---

## Proposed F38 summary (for 01-requirements)

**F38: Playground model download (super-admin)**

- Super-admin enters Ollama model tag on Evaluation Playground
- Triggers background pull to `vecinita-models` volume
- UI polls model list until `available=true` or timeout/error
- Admin sees downloaded models in picker but cannot pull
- Viewer → `403` on all model routes (unchanged)
