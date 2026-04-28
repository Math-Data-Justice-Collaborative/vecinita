---
name: cross-service-playbooks
description: Runs safe cross-service workflows for API contract changes, environment variables, and deployment debugging in the Vecinita monorepo. Use when changing FastAPI routes or OpenAPI surfaces, adding or renaming env vars, regenerating typed clients, or triaging Render/multi-service failures.
---

# Cross-service playbooks (Vecinita)

Use these playbooks so backend, frontend, generated clients, and docs stay aligned. Pair with `.cursor/skills/fastapi-router-py/SKILL.md` for router implementation details.

## 1. Change an API route safely

**Goal:** Router change + committed generated clients + callers + tests in one logical change.

1. **Implement the contract** in the owning FastAPI app (gateway, agent, or data-management API). Keep `response_model` and status codes explicit so OpenAPI stays truthful.
2. **Regenerate clients** from repo root (requires all three URLs; see `scripts/openapi_codegen.sh`):

   ```bash
   export GATEWAY_SCHEMA_URL=…
   export DATA_MANAGEMENT_SCHEMA_URL=…
   export AGENT_SCHEMA_URL=…
   make openapi-codegen-verify
   ```

   That runs codegen and fails if `packages/openapi-clients/` is not committed in sync.

3. **Update every consumer** in the same task: TypeScript call sites under `frontend/`, Python callers, DM service-clients if applicable—no hand-rolled HTTP that bypasses generated types where the repo already uses generated clients.
4. **Extend tests:** backend route tests / Schemathesis-relevant cases, frontend Vitest for changed callers, contract tests under `tests/contracts/` or `frontend/.../contracts/` when the change crosses the wire.
5. **Verify:** `make ci` from repository root before calling the work done.

## 2. Add an environment variable safely

**Goal:** One canonical example file, wired runtime, no duplicate “shadow” keys.

1. **Add the key only** to `.env.local.example` at repo root (committed defaults/examples). Do not add parallel `.env.example` trees unless the task explicitly documents an exception.
2. **Read the variable** only through existing config helpers in the service that needs it; reuse an existing name if one already covers the same destination (see `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md` and FR-004 in `specs/015-openapi-sdk-clients/spec.md`).
3. **Update all references** in the same task: application code, CI/docs that list vars, Render or local run scripts that must pass the value through.
4. **Verify:** grep for the old name if this is a rename; run `make ci` (or at minimum the quality targets for touched services).

## 3. Deployment / debug loop

**Goal:** Narrow which tier failed, then reproduce with the smallest surface.

1. **Classify the failure:** gateway vs agent vs frontend vs data-management vs Modal worker vs DB/auth. Use logs and HTTP status from the edge the user hit first.
2. **Config sanity:** compare runtime env to `docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`; run `make render-env-validate` when validating Render-oriented env bundles.
3. **Contract sanity:** if the symptom is 4xx/5xx or wrong payloads, diff behavior against OpenAPI—regenerate clients if schemas moved (`make openapi-codegen-verify` when URLs are available).
4. **Tests:** reproduce with a focused test or `make test-schemathesis-cli` / live Schemathesis flows described in `TESTING_DOCUMENTATION.md` when the issue is HTTP contract drift.
5. **Exit criteria:** root cause fixed (not only symptoms), regression test where practical, `make ci` green.

## Quick checklist (copy into a PR comment)

- [ ] API change reflected in OpenAPI and regenerated `packages/openapi-clients/` if applicable  
- [ ] All callers updated (same PR)  
- [ ] Env-only changes confined to `.env.local.example` + wiring  
- [ ] `make ci` passed locally  
