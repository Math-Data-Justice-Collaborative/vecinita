# Contract: Monorepo layout boundaries

**Audience**: Humans + reviewers (not an HTTP contract).  
**Normative spec**: `specs/018-strict-monorepo-layout/spec.md` (FR-001–FR-013).

## Rules

1. **Deployable ownership**  
   Runtime entrypoints, Dockerfiles used for that service’s Render or Modal deploy, and service-local tests **primary** to that service MUST live under **one** folder: `apis/<name>/`, `modal-apps/<name>/`, or `frontends/<name>/`.

2. **Shared libraries**  
   Code imported by **more than one** deployable (or by both an API and a client generator) MUST live under `packages/python/*` or `packages/ts/*` with a clear name. **Forbidden**: copying the same module into two deploy folders as the long-term state.

2a. **Temporary duplication (migration-only)**  
   During an approved split (e.g. `backend/` → `apis/agent` + `apis/gateway`), the same logical module MAY exist in two paths **only** for the smallest number of PRs needed to land `make ci` green, with **both** paths listed in `artifacts/path-mapping.md` (`notes` + `status`) and a **follow-up row or task** that removes the duplicate. **Not allowed** as an indefinite steady state.

3. **Database access**  
   SQLAlchemy session helpers, migration glue, and DB URL handling shared by HTTP APIs MUST converge on `packages/python/db/` (FR-004). Modal apps MUST NOT silently depend on API-only DB helpers without an explicit row in the path map and a documented need.

4. **HTTP consumer surfaces**  
   Generated or hand-maintained typed clients for first-party APIs MUST live under `clients/apis/<api-name>/` (FR-005). Changing an API contract MUST update the matching client subtree in the **same change set** per repository policy.

5. **Contract snapshots**  
   HTTP OpenAPI snapshots, Pact JSON, and similar **review artifacts** belong in one of two places, **without contradiction**: (a) **Repository-level** `contracts/` for snapshots and artifacts that gate **production** or cross-feature reviews; (b) **`specs/<feature>/contracts/`** for **feature-local** design and acceptance notes tied to that spec’s lifecycle. The same bytes SHOULD NOT be canonically duplicated in both—pick one primary home and link from the other. Deployable `src/` SHOULD NOT host long-lived snapshot trees unless a path-map **notes** exception exists.

6. **Automation**  
   Repo-wide scripts (not shipped in a container image as the main app) SHOULD live under `scripts/` (FR-010).

7. **Path map authority**  
   Any PR that moves directories or updates Render/Modal paths MUST update **`specs/018-strict-monorepo-layout/artifacts/path-mapping.md`** in lockstep (FR-013).

## Render alignment (informative)

Today, `vecinita-data-management-api-v1` builds from `modal-apps/scraper` per `render.yaml`. Boundary rule **does not** bless that as the final layout—it documents **current production wiring** to be reconciled when `apis/data-management-api` owns its image.
