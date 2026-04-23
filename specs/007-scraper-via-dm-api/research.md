# Research: Modal function invocation for DM API and agent policy

## Decision 1 — DM API uses Modal SDK function calls for scraper, embedding, and model ingest

**Rationale**: The product already standardizes on `modal.Function.from_name` + `.remote()` / `.spawn()` in `backend/src/services/modal/invoker.py` for gateway-adjacent flows. Extending the same pattern to **data-management-api** keeps one mental model, avoids brittle `*.modal.run` HTTP coupling, and matches the feature addendum (function calls, not web endpoints). Modal’s documented pattern for calling deployed code from Python is function handles ([Modal: trigger deployed functions](https://modal.com/docs/guide/trigger-deployed-functions)).

**Alternatives considered**:

- **Keep httpx to Modal FastAPI URLs** — Rejected for this feature: explicit goal is to stop using Modal **web** endpoints for these integrations; HTTP remains a possible dev fallback only if guarded and not used for production Modal targets.
- **gRPC / custom wire** — Rejected: scraper and sibling Modal apps already expose Modal functions (`modal_scrape_job_submit`, etc.); duplicating wire format adds maintenance.

## Decision 2 — Gateway stays HTTP to agent; agent enforces Modal functions only

**Rationale**: The gateway is the public edge; the agent is an internal service. Keeping **HTTP** gateway→agent preserves existing `AGENT_SERVICE_URL` deployment topology. The constraint “agent only invokes Modal function calls” is enforced by **startup policy** (`enforce_modal_function_policy_for_urls`) plus ensuring LLM/embedding clients in the agent use `invoke_modal_*` when `OLLAMA_BASE_URL` / `EMBEDDING_SERVICE_URL` point at `modal.run`.

**Alternatives considered**:

- **Gateway calls Modal directly for chat** — Rejected: splits orchestration and breaks the agent as the RAG/LLM composition root; out of scope.

## Decision 3 — Testing: layered mocks + OpenAPI contracts

**Rationale**: Modal SDK calls are side-effectful and need credentials; **unit tests** must patch `modal.Function.from_name` or the adapter’s lookup. **Contract tests** validate stable JSON envelopes for scraper RPC (already used in scraper tests). **Schemathesis** continues to apply to HTTP OpenAPI surfaces (DM API, gateway) per repo norms.

**Alternatives considered**:

- **Live-only tests** — Rejected as PR gate; optional nightly with secrets.

## Decision 4 — Code layout: minimal duplication first

**Rationale**: Introduce `services/data-management-api/.../modal_invoker.py` (name TBD in tasks) mirroring the subset of `backend/src/services/modal/invoker.py` needed for DM (scrape job lifecycle, embed single/batch, model chat if required for ingest). **Extract a shared package** only if a second consumer needs identical code in the same release; otherwise YAGNI to avoid packaging cycles between `backend/` and `services/data-management-api/`.

**Alternatives considered**:

- **Shared `packages/modal-invoker` in monorepo** — Deferred until duplication pain is proven (constitution prefers small reversible steps).
