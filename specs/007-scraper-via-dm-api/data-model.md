# Data model — Modal orchestration & DM ingest (feature 007)

## Overview

Logical entities for **routing**, **invocation**, and **job lifecycle** when the data-management API calls Modal-deployed functions instead of exposing Modal HTTP URLs to browsers.

## Entities

### ScrapingWorkflow (logical)

| Field | Description |
|--------|-------------|
| `job_id` | Stable identifier for the scrape job (UUID or string per existing schema). |
| `initiator` | Operator or system principal (for audit FR-006). |
| `status` | Coarse lifecycle: pending, running, completed, failed, cancelled. |
| `correlation_id` | Trace id propagated across DM API → Modal → persistence (gateway HTTP from worker if applicable). |

**Relationships**: Created and queried only through **DM API** from the operator UI; execution runs on **Modal scraper** deployment.

### ModalInvocationRef

| Field | Description |
|--------|-------------|
| `app_name` | Modal app name (e.g. `vecinita-scraper`). |
| `function_name` | Deployed function name (e.g. `modal_scrape_job_submit`). |
| `function_call_id` | Present when work was `spawn`’d; used for poll/get semantics. |

**Validation**: When `MODAL_FUNCTION_INVOCATION` is enabled, HTTP base URLs pointing at `*.modal.run` for the same capability must be **absent** or **unused** in server code paths.

### IngestOperation (embedding / model)

| Field | Description |
|--------|-------------|
| `operation_id` | Idempotent client or server id for batch ingest steps. |
| `texts` or `document_ref` | Inputs per existing shared-schemas types. |
| `embedding_vector` | Output side for embedding calls. |
| `model_output` | Output side for model calls used in ingest pipelines. |

**Relationships**: DM API orchestrates; Modal **embedding** and **model** apps satisfy requests via `.remote()`.

### GatewayAgentRequest (logical, unchanged)

| Field | Description |
|--------|-------------|
| `route` | e.g. `/ask` proxy from gateway to agent. |
| `session_context` | Existing chat/session payloads. |

**Note**: No schema migration required for this feature; entity documents **runtime** boundaries for tests and logs.

## State transitions (ScrapingWorkflow)

```
pending → running → completed
                 ↘ failed
                 ↘ cancelled
```

Cancel and status refresh go through **DM API**, which calls Modal functions (`modal_scrape_job_cancel`, `modal_scrape_job_get`, etc.) per deploy naming in settings.
