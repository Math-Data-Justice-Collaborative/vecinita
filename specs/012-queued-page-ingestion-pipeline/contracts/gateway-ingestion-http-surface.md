# Contract: Gateway HTTP surface for ingestion-related consumers

## Purpose

Anchor **FR-011–FR-015** for **browser and declared HTTP consumers**: published **OpenAPI** is canonical; **Pact** files (`frontend/pacts/`, provider tests under `backend/tests/pact/`) and **Schemathesis** enforce drift detection per `TESTING_DOCUMENTATION.md`. Normative product wording for the same obligations lives under **[spec.md](../spec.md) § Clarifications (2026-04-24)** and **Requirements FR-011–FR-015**—this contract file must stay in lockstep when either side changes.

## Scope

Routes used for:

- Submitting or observing **page ingestion** / **scrape jobs** that feed the pipeline (e.g. `/api/v1/modal-jobs/scraper`, related GETs), and  
- Any **additional** ingestion-status routes this feature adds under `/api/v1/...` that the **frontend** is allowed to call.

**Out of scope for this contract file**: **DM API** scraper job JSON (`apps/data-management-frontend` → data-management-api) — separate consumer; do not conflate origins (**FR-012**).

## Correlation identifier (**FR-015**)

| Requirement | Rule |
|-------------|------|
| Presence | **Every** `2xx` and `4xx`/`5xx` response on in-scope routes includes a correlation id. |
| Location | Documented in OpenAPI: e.g. header **`X-Request-Id`** and/or JSON field on success bodies. |
| Format | Opaque string; stable charset (UUID v4 or ULID recommended). |
| Propagation | Gateway structured logs **must** include the same value; Modal worker logs **should** include it when processing that job. |

## Stable error envelope (**FR-014**)

Errors returned to browsers for in-scope routes **must** use:

- A **documented HTTP status** (including **504** for upstream timeout, **503** for overload/unavailable, **422** for validation).  
- A **JSON object** with **stable top-level keys** (names and types listed in OpenAPI). Suggested minimum:

| Key | Type | Meaning |
|-----|------|---------|
| `error` | string | Short stable code (e.g. `upstream_timeout`). |
| `message` | string | Human-safe description (no stack traces). |
| `request_id` | string | Same as correlation id if body carries it. |

**Forbidden as sole client signal**: raw Modal / scraper stack traces, internal hostnames, secret values.

## Versioning

- **Minor** additive JSON fields: allowed without major bump if OpenAPI updated and Pact relaxed or extended.  
- **Breaking** renames/removals/types: **contract version bump** (path prefix or `Accept` version policy — pick one in tasks) + consumer updates + **SC-005** green.

## Acceptance checks

1. OpenAPI snapshot for gateway includes correlation + error schema for new/changed routes.  
2. `npm run test:pact` passes for **vecinita-chat-frontend** when gateway provider verifies.  
3. Schemathesis runs for affected tags per `backend/schemathesis.toml`.  
4. Drillbook: random `request_id` from responses locates gateway log line (**SC-007**).
