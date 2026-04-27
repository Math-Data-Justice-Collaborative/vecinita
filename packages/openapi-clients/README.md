# OpenAPI-generated HTTP clients

Typed clients for **Gateway**, **Data Management**, and **Agent** are generated from each service’s canonical OpenAPI document into this tree. Application code **outside** these directories must not duplicate path strings for those APIs (**FR-002**).

## Layout

| Path | Generator (`-g`) | Consumers (planned) |
|------|-------------------|------------------------|
| `python/gateway/` | `python-pydantic-v1` | `backend/`, shared Python services |
| `python/data_management/` | `python-pydantic-v1` | `services/data-management-api/` |
| `python/agent/` | `python-pydantic-v1` | `backend/` |
| `typescript-axios/gateway/` | `typescript-axios` | `frontend/` |
| `typescript-axios/data_management/` | `typescript-axios` | `apps/data-management-frontend/` |
| `typescript-axios/agent/` | `typescript-axios` | `frontend/` |
| `typescript-node/` | `typescript-node` | Optional Node-only tooling |

Authoritative paths and CI drift rules: `specs/015-openapi-sdk-clients/contracts/openapi-codegen-layout.md`.

## Regeneration

From repo root (requires `GATEWAY_SCHEMA_URL`, `DATA_MANAGEMENT_SCHEMA_URL`, `AGENT_SCHEMA_URL`):

```bash
make openapi-codegen
```

Pinned CLI version: `scripts/openapi-generator-version.txt`.
