# Data model: scraping jobs, gateway registry, and remote service integration

This feature extends **logical** configuration and error shapes; it may not add new Postgres tables
beyond what already exists for `scraping_jobs` / gateway registry (see gateway inventory specs).
New concepts support **remote-only** DM API integration and **safe** client errors.

## Entity: ScrapingJob (logical)

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|-------|
| `job_id` | UUID | yes | Stable identifier across gateway and Modal |
| `url` | string (URL) | yes | Target crawl root |
| `user_id` | string | yes | Owner / tenant key for listing filters |
| `status` | enum | yes | e.g. `pending`, `running`, `completed`, `failed`, `cancelled` |
| `metadata` | object | no | Opaque client metadata |
| `correlation_id` | string | no | Propagated for **FR-006** tracing |
| `created_at` / `updated_at` | timestamp | yes | Server-generated |

**State transitions**: `pending` → `running` → (`completed` \| `failed` \| `cancelled`). Invalid
transitions return **4xx**, not **5xx**, when job does not exist or action is illegal.

**Validation**: `url` must be absolute HTTP(S); `user_id` non-empty per API rules.

## Entity: GatewayJobRegistryEntry (logical)

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|-------|
| `gateway_job_id` | UUID | yes | Returned by registry APIs |
| `kind` | string | yes | Discriminator for job type |
| `status` | string | yes | For Schemathesis bootstrap hooks |

Links scraping and other async work under gateway control (see `modal-jobs/registry`).

## Entity: RemoteServiceEndpoint (configuration)

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|-------|
| `name` | enum | yes | `scraper` \| `embedding` \| `model` |
| `base_url` | string (URL) | yes | HTTPS origin, no trailing path garbage |
| `request_timeout_seconds` | number | yes | Client-side; must align with upstream SLAs |
| `auth_scheme` | enum | yes | e.g. `bearer`, `api_key_header`, `mtls_future` |
| `health_path` | string | no | Optional readiness probe path |

**Validation**: `base_url` must be parseable; timeouts > 0 and ≤ platform max (documented per env).

## Entity: SafeClientError (API envelope)

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|-------|
| `error` | string | yes | Human-safe message (**FR-002**) |
| `timestamp` | string (RFC 3339) | yes | Existing gateway pattern |
| `correlation_id` | string | no | Echo or generate for support |

**Validation**: Must **not** embed raw `dpg-*` hostnames or stack traces in **production** responses.

## Relationships

- **ScrapingJob** rows are created either on the **gateway** (persist-via-gateway mode) or legacy
  Modal path—exact DB ownership is deployment-configured; DM API does **not** embed scraper DB logic
  after refactor.  
- **RemoteServiceEndpoint** triple is required for DM API runtime once submodules are removed.  
- **GatewayJobRegistryEntry** is used by contract tests for **404** elimination when hooks supply
  valid IDs.
