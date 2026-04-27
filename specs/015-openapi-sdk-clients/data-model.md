# Data model: connection profile and generated clients

Design artifacts for **015-openapi-sdk-clients** derived from [spec.md](./spec.md) Key Entities and FR-004.

## Entity: Connection profile

Represents everything an environment needs to reach **Postgres**, **Render HTTP APIs**, and **OpenAPI documents** used for codegen and contract tests.

| Field | Source env var | Required | Notes |
|-------|----------------|----------|--------|
| database_dsn | `DATABASE_URL` | Yes | Internal or external DSN per deployment; never log full value. |
| gateway_base | `RENDER_GATEWAY_URL` | Yes for HTTP clients to gateway | Origin only; no path suffix required if clients use `servers` from OpenAPI. |
| agent_base | `RENDER_AGENT_URL` | Yes when agent HTTP used | Same as above. |
| data_management_base | `DATA_MANAGEMENT_API_URL` | Yes when DM HTTP used | Public DM API origin. |
| gateway_openapi | `GATEWAY_SCHEMA_URL` | Yes for codegen + Schemathesis | Must resolve to **OpenAPI JSON** (gateway exports under `/api/v1/docs/openapi.json` per existing docs). |
| dm_openapi | `DATA_MANAGEMENT_SCHEMA_URL` | Yes | DM `openapi.json` URL. |
| agent_openapi | `AGENT_SCHEMA_URL` | Yes for agent consumer builds + optional third Schemathesis pass | Same pattern as gateway. |

**Forbidden keys** (must not appear in app manifests, committed examples, or runtime reads after migration):

- `MODAL_OLLAMA_ENDPOINT`, `MODAL_EMBEDDING_ENDPOINT`, `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `EMBEDDING_SERVICE_URL`

**Out of scope for FR-004** but still allowed when unrelated to “same logical destination”:

- Modal **auth** secrets (`MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, workspace tokens) — not HTTP route configuration.
- Frontend build-time vars (`VITE_*`) — must not reintroduce Modal `*.modal.run` bases for chat/ingestion per prior specs; planning references **005** / **012** contracts.

## Entity: Generated API client package

One **logical package** per **(language, service)** pair, produced from the canonical OpenAPI URL for that service.

| Attribute | Description |
|-----------|-------------|
| service | `gateway` \| `data_management` \| `agent` |
| language_runtime | `python` \| `typescript_node` \| `typescript_axios` |
| openapi_source | Resolved URL from connection profile |
| output_root | Filesystem directory under repo root (see [contracts/openapi-codegen-layout.md](./contracts/openapi-codegen-layout.md)) |
| version_pin | OpenAPI Generator CLI version + generator name |

**Validation rules**:

- Generated trees are either **committed** (preferred for simpler CI) or **gitignored** with **CI regen** + diff—pick one per language in tasks; default recommendation: **commit** Python + TS for reproducible `make ci` without network in unit phase, **optional** network job for “fresh schema” verification.

## Entity: Modal invocation

| Attribute | Description |
|-----------|-------------|
| entry_kind | `modal_function` (SDK reference + `.remote()` / `.spawn` / `.map`) |
| forbidden | HTTP(S) client to Modal-assigned hostname from any checked-in path |
| allowed_tokens | Modal API tokens / secrets for SDK auth only |

## Relationships

- **Connection profile** configures **runtime** instances of **Generated API client package** (base URL + auth interceptors).
- **Modal invocation** is used only from **Modal-deployed modules** and **Render services** that hold Modal SDK credentials—not from browser code.
