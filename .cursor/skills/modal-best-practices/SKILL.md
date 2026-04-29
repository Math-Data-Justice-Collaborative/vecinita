---
name: modal-best-practices
description: Defines Modal.com implementation standards for this repository, including repo-specific rules for modal-repos-scraper, embedding-model, model-modal, and any calls to the project Modal instance. Use when adding, updating, reviewing, or debugging Modal-related code, deployments, env vars, or service-to-Modal integrations.
---

# Modal Best Practices (Vecinita)

Use this skill for any task that touches Modal codepaths, Modal deploy/config, or code that calls a Modal-backed capability.

The following requirement from the user is mandatory and preserved verbatim:
"we use best practices from @Modal.com and we define those specifically for the modal repos scraper, embedding-model, model-modal and for any calls to that modal instance"

## Core policy

1. Use official Modal SDK patterns and naming from Modal docs.
2. Keep compute orchestration inside Modal codepaths, and keep non-Modal services thin and contract-driven.
3. Prefer typed contracts and explicit interfaces between services.
4. Avoid ad-hoc environment variables and undocumented endpoints.
5. Treat reliability, idempotency, and observability as required, not optional.

## Repository-specific standards

### 1) `modal-repos-scraper`

- Keep scraper jobs deterministic and idempotent so retries do not duplicate records.
- Separate scraping, normalization, and persistence stages so each stage can be retried independently.
- Use bounded parallelism and explicit timeouts for external IO.
- Emit structured logs with correlation ids for each scrape job/run.
- Validate and sanitize raw upstream data before writing to shared stores.

### 2) `embedding-model`

- Pin model identity/version and embedding dimensions in one canonical config location.
- Enforce stable input preprocessing (chunking, normalization, truncation) across all embedding calls.
- Validate embedding vector shape/dtype before returning or persisting.
- Capture latency and failure metrics for each embedding batch/request.
- Keep backward compatibility when rotating model versions (migration plan for stored vectors).

### 3) `model-modal`

- Keep inference entrypoints typed and explicit about accepted payload and response shape.
- Use explicit resource sizing and concurrency settings rather than implicit defaults.
- Handle cold-start and transient failures with retries/backoff where appropriate.
- Log request metadata and model version without leaking secrets or user-sensitive payloads.
- Document all externally callable methods and their expected contracts.

## Any call to the Modal instance

For any code that calls this project Modal instance:

- Use a single shared client/wrapper pattern per service boundary; do not scatter inline call logic.
- Enforce request/response schema validation at the boundary.
- Set explicit timeout, retry, and error classification behavior.
- Include tracing context and structured logging fields (service, operation, request_id, model/version).
- Fail fast on auth/config issues; do not silently degrade behavior.
- Keep secret material in environment/secret managers only; never hardcode tokens or endpoints.

## Implementation checklist

Before finalizing a Modal-related change:

- [ ] Call path uses documented Modal SDK or approved wrapper pattern.
- [ ] Contract types/schemas are updated and validated.
- [ ] Timeout/retry behavior is explicit and tested.
- [ ] Logging/metrics are present for success and failure paths.
- [ ] Env vars and docs are updated for any config changes.
- [ ] CI/tests cover new behavior and regressions.

## Review checklist

When reviewing PRs that touch Modal:

- [ ] No ad-hoc one-off Modal call paths.
- [ ] No unbounded concurrency or missing timeouts.
- [ ] No schema drift between caller and Modal handler.
- [ ] No secret leakage in code or logs.
- [ ] Operational runbook/docs remain accurate.
