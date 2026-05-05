# Monorepo layout (canonical target)

**Feature**: [specs/018-strict-monorepo-layout/spec.md](../specs/018-strict-monorepo-layout/spec.md)  
**Plan**: [specs/018-strict-monorepo-layout/plan.md](../specs/018-strict-monorepo-layout/plan.md)  
**Tasks**: [specs/018-strict-monorepo-layout/tasks.md](../specs/018-strict-monorepo-layout/tasks.md)

## Resolve paths first (FR-013)

Before editing or reviewing a move:

1. Open the authoritative map: **[specs/018-strict-monorepo-layout/artifacts/path-mapping.md](../specs/018-strict-monorepo-layout/artifacts/path-mapping.md)** and find the **`row_id`** (e.g. `PM-003`) for the legacy or canonical path.
2. Then read **plan.md** / **tasks.md** for sequencing and acceptance tests.

Do not invent a second mapping document; one source of truth is required through the refactor.

## Target tree (end state)

```text
apis/
├── gateway/
├── agent/
└── data-management-api/

modal-apps/
├── scraper/
├── embedding-modal/
└── model-modal/

frontends/
├── chat/
└── data-management/

packages/
├── python/
│   └── db/              # shared API DB/session glue (FR-004)
└── ts/

clients/apis/
├── gateway/
├── agent/
└── data-management-api/

contracts/                 # optional — HTTP snapshots, Pact (FR-009)
infra/                     # optional — blueprint fragments (FR-008)
scripts/                   # repo-wide automation (FR-010)
specs/
Makefile
.env.local.example
render.yaml                  # primary blueprint today (FR-008)
```

Optional subtrees (`packages/python/shared-schemas/`, `modal-apps/…`, etc.) follow **plan.md** and the path map; they are not all required on day one.

## Where does X live?

Use **`row_id`** for status; **legacy** is current until the row is `done`.

| Concern | Legacy (today) | Canonical target | Path map |
|--------|----------------|-------------------|----------|
| Gateway HTTP API | `backend/` (gateway image) | `apis/gateway/` | PM-008 |
| Agent HTTP API | `backend/` (agent image) | `apis/agent/` | PM-007 |
| Data-management HTTP API (submodule) | `apis/data-management-api/` (moved from `services/data-management-api/`) | `apis/data-management-api/` | PM-006 |
| Scraper Modal / shared scraper image | `modal-apps/scraper/` (was `services/scraper/`) | `modal-apps/scraper/` | PM-003 |
| Embedding Modal | `modal-apps/embedding-modal/` (was `services/embedding-modal/`) | `modal-apps/embedding-modal/` | PM-004 |
| Model Modal | `modal-apps/model-modal/` (was `services/model-modal/`) | `modal-apps/model-modal/` | PM-005 |
| Chat frontend (Render) | `frontends/chat/` (moved from `frontend/`) | `frontends/chat/` | PM-001 |
| Data-management frontend (Render) | `frontends/data-management/` (moved from `apps/data-management-frontend/`) | `frontends/data-management/` | PM-002 |
| OpenAPI / typed HTTP clients | `packages/openapi-clients/` | `clients/apis/<api>/` (after client move) | PM-009 |
| Feature specs (Spec Kit) | `specs/` | `specs/` (unchanged) | PM-012 |
| Root Makefile / CI / compose | `Makefile`, `.github/workflows/`, root `docker-compose*.yml` | same roots; paths inside files update | PM-013–PM-015 |

For **Render** wiring vs folders, see the **T006** table in **artifacts/path-mapping.md**.
