# `apis/`

**Canonical home** for Render-deployed **HTTP API** services (one child folder per API).

Rules: [`specs/018-strict-monorepo-layout/contracts/monorepo-layout-boundary.md`](../specs/018-strict-monorepo-layout/contracts/monorepo-layout-boundary.md) · Path map: [`specs/018-strict-monorepo-layout/artifacts/path-mapping.md`](../specs/018-strict-monorepo-layout/artifacts/path-mapping.md).

**Current**: `apis/data-management-api/` (submodule), **`apis/gateway/`** (gateway + shared Python `src/`, tests, lockfile), **`apis/agent/`** (agent `Dockerfile` + canonical `src/agent/`; gateway `src/agent` is a symlink here). See each folder’s `README.md` where present.
