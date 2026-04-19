# Phase 0 research: Render-owned persistence vs Modal compute

## 1. Boundary decision

**Decision**: **Postgres (and any durable queue backed by Postgres) is accessed only from processes
running on Render** (gateway FastAPI app, agent FastAPI app, or other explicitly Render-hosted
workers). **Modal** functions for **model**, **embedding**, and **scraper** roles perform
**compute only** and return **serializable payloads**; **no** Modal container opens a Postgres DSN.

**Rationale**:

- Aligns with product directive and eliminates **internal Render hostname** (`dpg-*-a`) resolution
  failures from Modal regions.
- Centralizes audit, retries, and connection pooling on infrastructure already wired to the
  database VPC/network.

**Alternatives considered**:

| Alternative | Why not chosen |
|-------------|----------------|
| Modal VPC / private link to Postgres | High ops cost; not implied by directive; still couples DB
  to Modal. |
| Read-only replica URL on Modal | Still a DB client on Modal; violates “only Render” rule. |
| Gateway proxies raw SQL strings to Modal | Security and stewardship failure; rejected. |

## 2. Caller ownership (gateway vs agent)

**Decision**: **Gateway** remains the public `/api/v1` orchestrator for scrape and modal-job
routes today; **persistence for ingestion batches** should default to **gateway** (or shared
`backend` libraries invoked by gateway) unless a flow already routes through the **agent** for RAG
writes. **Agent** keeps DB for **retrieval / LangGraph tools** because the agent service is
Render-hosted—this does **not** violate the directive. Modal **model** and **embedding** endpoints
used for inference return tensors/text only; gateway/agent applies results without Modal touching
PG.

**Rationale**: Minimizes duplicate write paths; matches existing `invoke_modal_*` patterns.

## 3. Scraper / ingestion shape

**Decision**: Modal scraper functions return **chunk batches + job metadata** as JSON; **gateway**
(or a dedicated Render background task triggered by gateway) performs **upsert** into document
tables using existing SQL helpers. Job status rows, if any, are updated on Render only.

**Rationale**: Schemathesis failures showed scraper **job** paths hitting DB from Modal-side code;
moving writes closes the failure mode.

## 4. OpenAPI / TraceCov (spec track)

**Decision**: Implement **FR-006** by enumerating **documented** `responses` per included operation
(FastAPI `responses=` or shared schema components) until TraceCov **responses** dimension is **100%**
for the live pass selection, matching clarification **A**.

## 5. Risks

- **Payload size**: Large scrape batches need pagination or multipart strategy from Modal→Render.  
- **Latency**: Extra hop may impact UX; measure and consider async job + polling (already partly
  present).  
- **Dual maintenance**: Short-term feature flag may be needed during migration.

All items above are **resolved**; no `NEEDS CLARIFICATION` remains for planning.
