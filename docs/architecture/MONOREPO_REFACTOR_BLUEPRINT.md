# Monorepo Refactor Blueprint (Chat + Data Management + Modal Services)

## Goal

Unify the Vecinita chat application and the data-management ecosystem into a single monorepo with clear boundaries between deployable apps, backend services, shared packages, and infrastructure.

This blueprint replaces the legacy in-repo scraper runtime path with the source-of-truth stack from:

- vecinita-data-management
- vecinita-data-management-frontend
- vecinita-scraper
- vecinita-direct-routing
- vecinita-embedding
- vecinita-model

## Core Architecture Decisions

1. One repository contains all source code domains.
2. Two frontends remain separate deployables:
   - Chat frontend
   - Data management frontend
3. Modal routing remains the required gateway for embedding/model production traffic.
4. Embedding and model services remain Modal deployment units, but deployment code and CI live in this monorepo.
5. Big-bang production cutover is used, with rollback toggles prepared in advance.
6. Branch orchestration workflow is mandatory for cross-component development.

## Target Repository Structure

```text
.
├── apps/
│   ├── chat-frontend/                  # existing vecinita frontend app
│   └── data-management-frontend/       # from vecinita-data-management-frontend
├── services/
│   ├── chat-api-gateway/               # existing backend API gateway and chat routes
│   ├── data-management-api/            # from vecinita-data-management
│   ├── scraper/                        # from vecinita-scraper (source of truth)
│   ├── direct-routing/                    # from vecinita-direct-routing
│   ├── embedding-modal/                # from vecinita-embedding
│   └── model-modal/                    # from vecinita-model
├── packages/
│   ├── shared-ts/                      # shared frontend clients/types/ui primitives
│   └── shared-py/                      # shared python utilities/contracts
├── infra/
│   ├── docker/                         # local multi-service compose and overrides
│   ├── render/                         # render blueprints and environment overlays
│   ├── modal/                          # modal deployment wrappers and docs
│   └── supabase/                       # migrations, seeds, and SQL ops
├── run/
│   ├── branch-orchestrator.sh          # branch workflow utility
│   └── branch-components.conf          # component branch mapping config
├── docs/
│   ├── architecture/
│   ├── guides/
│   └── adr/
└── Makefile
```

## Source Repo to Target Folder Mapping

| Source Repository | Target Path | Runtime Role |
|---|---|---|
| vecinita (current) | services/chat-api-gateway + apps/chat-frontend + infra/supabase | Chat API, existing frontend, DB baseline |
| vecinita-data-management | services/data-management-api | Source-of-truth data management backend |
| vecinita-data-management-frontend | apps/data-management-frontend | Source-of-truth data management UI |
| vecinita-scraper | services/scraper | Source-of-truth scraper pipeline |
| vecinita-direct-routing | services/direct-routing | Auth/routing layer for embedding/model |
| vecinita-embedding | services/embedding-modal | Modal embedding service |
| vecinita-model | services/model-modal | Modal model service |

## Import Strategy

Recommended import mode: git subtree (keeps provenance and allows future upstream syncs).

Example pattern:

```bash
git subtree add --prefix services/data-management-api <repo-url> main --squash
```

If full commit history is required, remove `--squash`.

Use one prefix per imported repo aligned to the target structure above.

## Phase-by-Phase Implementation Plan

## Phase 0: Baseline + Freeze

Deliverables:

- Contract snapshot for current chat ask flow and scraper admin endpoints.
- Test baseline for chat frontend and backend.
- Freeze notice for scraper-impacting changes during migration window.

Exit criteria:

- Baseline artifact set is committed under docs/reports or artifacts in CI.

## Phase 1: Scaffold Monorepo Domains

Deliverables:

- `apps/`, `services/`, `packages/`, `infra/` domain directories established.
- Root tooling conventions documented.
- Branch workflow utility available from Makefile.

Exit criteria:

- `make branch-status` works from root.

## Phase 2: Import External Repositories

Deliverables:

- All six target repos imported into mapped paths.
- Ownership map established (CODEOWNERS by domain).
- Build/test command matrix documented for each imported service.

Exit criteria:

- Each imported service can run its local tests from monorepo path.

## Phase 3: Contract Harmonization

Deliverables:

- Standardized service contracts:
  - Auth headers and trust boundaries
  - Timeouts and retry policies
  - Health and readiness endpoints
  - Error shape and status code conventions
- Compatibility adapter in chat gateway for transitional routing.

Exit criteria:

- Contract tests pass across gateway, data-management API, scraper, direct-routing, embedding, and model.

## Phase 4: Scraper Replacement

Deliverables:

- Legacy scraper runtime path removed from active flows.
- Gateway/admin wiring updated to source-of-truth data-management + scraper services.
- URL/config migration complete for managed scraping policies.

Exit criteria:

- Full scrape pipeline parity test passes on controlled fixture set.

## Phase 5: Frontend Split Integration

Deliverables:

- Two deployable frontends with clear route/session boundaries.
- Shared TS package initialized for common API clients and DTOs.

Exit criteria:

- Unit/E2E tests pass for both frontends.

## Phase 6: Environment Model + Secrets

Deliverables:

- Service-scoped env templates.
- Local/staging/prod env matrix docs.
- Routing rule codified: embedding/model production calls route through direct-routing.

Exit criteria:

- Environment drift checks pass in CI.

## Phase 7: Deploy Consolidation

Deliverables:

- Unified local compose under infra/docker.
- Consolidated CI with path filters for apps/services.
- Modal deploy workflows sourced from monorepo service paths.

Exit criteria:

- Staging deploy pipeline green for all target services.

## Phase 8: Big-Bang Cutover

Deliverables:

- Rehearsed cutover runbook.
- Production switch of service endpoints.
- Rollback toggles and known-good artifact references.

Exit criteria:

- Production SLOs stable during observation window.

## Phase 9: Legacy Cleanup

Deliverables:

- Deprecated scraper modules removed.
- Obsolete env vars and scripts removed.
- Finalized runbooks and ownership docs.

Exit criteria:

- No runtime path depends on retired scraper code.

## Development Workflow (Cross-Component Branching)

Use the root Make targets:

- `make branch-status`
- `make branch-save`
- `make branch-switch BRANCH=<feature-branch>`
- `make branch-restore`
- `make branch-sync-main`

Branch policy:

- Attempt same branch name in each configured component.
- Fallback to `main` if branch does not exist in a component.
- Skip dirty worktrees by default unless `FORCE=1` is set.

Config file:

- `run/branch-components.conf`

## Execution Backlog (First 2 Weeks)

1. Import external repos into target prefixes.
2. Add CODEOWNERS entries for new domains.
3. Move existing frontend from submodule path assumptions to `apps/chat-frontend` layout.
4. Stand up contract tests between chat gateway and data-management API.
5. Implement scraper route switch in gateway behind a feature flag.
6. Add staging cutover rehearsal checklist and traffic simulation script.

## Risks and Mitigations

1. Risk: hidden contract mismatches between existing chat routes and new data stack.
   - Mitigation: schema-level contract tests before cutover.
2. Risk: private repo divergence or unknown build assumptions.
   - Mitigation: repo reality-check pass immediately after import.
3. Risk: auth regression on routing path.
   - Mitigation: explicit end-to-end tests that validate routing-auth-only behavior.
4. Risk: big-bang blast radius.
   - Mitigation: precomputed rollback toggles and clear rollback time budget.

## Definition of Done

1. All target repos are in one monorepo with runnable build/test workflows.
2. Chat and data-management frontends deploy independently.
3. Scraper runtime path is fully sourced from data-management/scraper repos.
4. Embedding/model calls route through direct-routing in production path.
5. Staging rehearsal and production cutover runbooks are complete and validated.
