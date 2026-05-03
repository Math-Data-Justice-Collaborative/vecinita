# Contract: OpenAPI Generator layout and CI

**Feature**: [015-openapi-sdk-clients](../spec.md)  
**Related**: [plan.md](../plan.md), [research.md](../research.md) Decision 1–4

## Canonical OpenAPI sources

| Service | Schema URL env | Typical JSON path (verify per deployment) |
|---------|------------------|-------------------------------------------|
| Gateway | `GATEWAY_SCHEMA_URL` | Often `…/api/v1/docs/openapi.json` |
| Data Management | `DATA_MANAGEMENT_SCHEMA_URL` | DM service `openapi.json` |
| Agent | `AGENT_SCHEMA_URL` | Agent `openapi.json` equivalent |

## Generators (per spec Assumptions)

| Language / runtime | OpenAPI Generator `-g` | Primary consumers |
|--------------------|----------------------|---------------------|
| Python | `python-pydantic-v1` | `backend/`, `apis/data-management-api/` packages |
| TypeScript (Node) | `typescript-node` | Node-only scripts or services (if any); else optional |
| TypeScript (Axios) | `typescript-axios` | `frontend/`, `apps/data-management-frontend/` |

**Additional properties** (examples—finalize in tasks):

- Python: `packageName=vecinita_gateway_client` (per service), `library=urllib3` or `asyncio` per call style in repo.
- TS: `npmName`, `supportsES6=true` as needed.

## Output directories (proposal — adjust only via PR that updates this contract)

> Exact paths are **proposals**; first implementation PR must either adopt them or edit this file in the same PR.

```text
packages/openapi-clients/
  python/
    gateway/                 # from GATEWAY_SCHEMA_URL
    data_management/
    agent/
  typescript-axios/
    gateway/
    data_management/
    agent/
  typescript-node/           # optional per consumer inventory
    ...
```

**Import rule**: Application code **outside** these trees **must not** define duplicate path strings for the three APIs—**FR-002**.

## CI / drift

1. **Fetch** or **validate** each schema URL (network job) OR compare pinned checksum of committed snapshot—**tasks** choose; spec default prefers **fail loud** if URL unreachable.
2. Run **openapi-generator-cli generate** for each (service × language) pair required by consumer inventory.
3. **`git diff --exit-code`** on generated trees if committed; if ignored, run **checksum manifest** instead.

## Docs workflow

- **`docs-gh-pages.yml`** (and related): must reference **schema URL env vars** for published “how to regen” docs; must not document deprecated Modal URL env vars as current (FR-008).

## Constitution

Cross-service coupling appears **only** through these generated surfaces + existing Pact/Schemathesis matrices (`TESTING_DOCUMENTATION.md`).
