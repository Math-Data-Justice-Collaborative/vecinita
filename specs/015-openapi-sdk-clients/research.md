# Research: OpenAPI SDK clients and standardized service URLs

Phase 0 decisions for feature **015-openapi-sdk-clients**. Resolves technical unknowns for planning without leaving `NEEDS CLARIFICATION` markers in [plan.md](./plan.md).

---

## Decision 1 — OpenAPI Generator delivery shape

**Decision**: Use the **official OpenAPI Generator CLI** (Docker image or `npx @openapitools/openapi-generator-cli` with **pinned version**) invoked from **`Makefile`** targets plus a **non-secret** `openapi-generator-config.yaml` (or per-service config fragments) checked into the repo. **CI** runs `openapi-generator-cli validate` + generate + **diff check** (or deterministic regen commit) so drift fails the build.

**Rationale**: Matches spec Assumptions and [OpenAPI Generator configuration](https://openapi-generator.tech/docs/configuration) practices; pin avoids silent template churn; `Makefile` matches existing vecinita merge gate (`make ci`).

**Alternatives considered**:

- **Only** `openapi-typescript` for TS — **Rejected** for this feature: spec mandates OpenAPI Generator with `typescript-node` and `typescript-axios` (may coexist briefly during migration—see Decision 4).
- **Gradle / Maven** plugins — **Rejected**: Python-first repo; adds JVM baseline for all contributors.

---

## Decision 2 — Python client package (`python-pydantic-v1`) vs runtime Pydantic v2

**Decision**: Generate into an **isolated package directory** (e.g. `packages/openapi-clients-python/` or `backend/generated/openapi_clients/`) with **clear import boundaries**; treat generated models as **v1-style** per generator while app code stays on **Pydantic v2**—use thin adapters (`.model_dump()` / dict bridge) at boundaries if needed.

**Rationale**: [python-pydantic-v1 generator](https://openapi-generator.tech/docs/generators/python-pydantic-v1) targets pydantic v1 APIs; mixing into existing `backend/src/api/models` would collide with v2 `ConfigDict` patterns documented in gateway models.

**Alternatives considered**:

- **Switch app to pydantic v1** — **Rejected**: large breaking change unrelated to client transport.
- **`python` generator without pydantic** — **Rejected**: weaker typing vs spec requirement.

---

## Decision 3 — TypeScript: `typescript-node` vs `typescript-axios`

**Decision**: **`typescript-axios`** for **browser-oriented** packages (`frontend/`, DM SPA) where Axios is already idiomatic; **`typescript-node`** for **Node-only** tooling (if any) or server-side TS scripts. Both consume the **same** three OpenAPI documents; **base URL** and **interceptors** (auth) configured from `VITE_*` / build-time env without introducing forbidden Modal URL vars.

**Rationale**: Aligns with spec Assumptions and [Axios API](https://axios-http.com/docs/api_intro) for request config; avoids forcing `fetch` wrapper where Axios is standard.

**Alternatives considered**:

- **Axios only everywhere** — **Deferred**: acceptable simplification if `typescript-node` adds little value—tasks may collapse to one TS stack after inventory.

---

## Decision 4 — Data Management frontend `codegen:api` today

**Decision**: **Migrate** `apps/data-management-frontend` from **`openapi-typescript`** on a **checked-in snapshot** toward **OpenAPI Generator `typescript-axios`** sourced from **`DATA_MANAGEMENT_SCHEMA_URL`** in CI (with **offline** fallback to committed schema only if spec’s offline mode is explicitly designed—default per spec edge case: **fail loud** unless `ALLOW_STALE_OPENAPI=1` documented for emergencies).

**Rationale**: Spec FR-003 / Assumptions require OpenAPI Generator for the three APIs; DM front is a first-class consumer.

**Alternatives considered**:

- **Keep openapi-typescript indefinitely** — **Rejected** as end state; optional **intermediate** dual codegen behind feature flag only if migration risk requires one release overlap.

---

## Decision 5 — SC-005 / FR-001 enforcement (Modal HTTP ban)

**Decision**: Maintain **`scripts/ci/modal_http_ban.py`** (or `make check-modal-http`) that:

1. Runs **`rg`** (or Python `pathlib` walk) with a **committed allowlist file** of glob paths to skip (`node_modules`, `.venv`, known vendored trees per **SC-001** quarantine rules).
2. Matches **host substrings** at minimum: `modal.run`, and any additional Modal deployment domains documented in [contracts/modal-http-ban-sc005.md](./contracts/modal-http-ban-sc005.md).
3. Ignores matches inside **comments-only** lines only if parser-safe; otherwise prefer **AST-based** check for Python `httpx`/`requests.get` with string literal URLs (tasks pick implementation depth).

**Rationale**: Spec requires zero violations in CI; `rg` is fast and auditable; pattern list versioned in git.

**Alternatives considered**:

- **Semgrep-only** — **Optional** add-on; may still add `rg` for simplicity.
- **Manual review** — **Rejected**: not scalable for SC-005.

---

## Decision 6 — Modal SDK for model/embedding vs Render HTTP

**Decision**: **Render-hosted** gateway/agent/DM expose HTTP OpenAPI; **Modal** hosts heavy inference. Callers on Render use **generated clients** to `RENDER_GATEWAY_URL` / `RENDER_AGENT_URL` / `DATA_MANAGEMENT_API_URL`. Code **on Modal** calls other Modal functions **only** via **`modal.Function.from_name`** / `.remote()` / `.spawn`—never `httpx` to `https://…modal.run`.

**Rationale**: Matches clarification **B** and existing `modal_invoker` direction in `packages/service-clients`; aligns with `RENDER_SHARED_ENV_CONTRACT.md` themes (function invocation vs raw HTTP).

**Alternatives considered**:

- **Allow httpx inside Modal to sibling Modal web endpoints** — **Rejected** by product clarification B.
