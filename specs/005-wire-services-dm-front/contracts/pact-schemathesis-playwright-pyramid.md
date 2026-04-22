# Contract: Testing pyramid — Pact, Schemathesis, Playwright, typed DTOs

## Purpose

Define how **chatbot** (`frontend/` ↔ gateway ↔ agent) and **data-management** (`apps/data-management-frontend/` ↔ DM API ↔ optional gateway modal-jobs) stay **compatible and aligned** using four cooperating mechanisms: **consumer-driven contracts (Pact)**, **OpenAPI property testing (Schemathesis)**, **typed TypeScript DTOs** (shared by clients and Pact), and **Playwright E2E**.

## Roles (no duplication of purpose)

| Mechanism | Primary question it answers | Typical owner |
|-----------|------------------------------|---------------|
| **Typed DTOs** | Do client code and tests agree on **field names, optionality, and enums**? | Feature devs in each frontend |
| **Pact (consumer)** | Does the **consumer’s expected** HTTP usage match what we promise? | Frontend devs ([Pact FAQ — consumer implements tests](https://docs.pact.io/faq)) |
| **Pact (provider)** | Does the **running provider** honor published pacts (incl. provider states)? | Backend devs for gateway, agent, DM API |
| **Schemathesis** | Does the provider reject bad input and **respond within OpenAPI** for generated cases? | Backend / QA automation ([Schemathesis overview](https://schemathesis.readthedocs.io/en/stable/)) |
| **Playwright** | Do **real browsers** complete journeys against wired env without silent misconfiguration? | Full-stack / release gate |

Pact’s own guidance: **contract tests are not a substitute** for good communication between consumer and provider teams ([Pact FAQ](https://docs.pact.io/faq)).

## Product-line split

### Chatbot

- **Consumer Pact**: `frontend/` against gateway-facing paths (versioned `/api/v1/...` as used by `agentService`).
- **Provider verify**: gateway and/or agent as configured in CI.
- **Schemathesis**: `GATEWAY_SCHEMA_URL`, `AGENT_SCHEMA_URL` (existing).
- **Playwright**: login/config/chat message flow; use `page.route` only for **third-party** deps, not to fake the gateway under test when the goal is wiring validation ([Playwright best practices](https://playwright.dev/docs/best-practices)).

### Data-management

- **Consumer Pact**: `apps/data-management-frontend/` against DM API `/health`, `/jobs`, cancel routes, and **separate** interactions for gateway modal-jobs when flag-enabled.
- **Provider verify**: DM API process; gateway for modal-jobs if in production use.
- **Schemathesis**: DM `openapi.json` + gateway operations for modal-jobs if enabled.
- **Playwright**: diagnostics strip, scrape job list, optional create flow in non-prod data.

## CI placement (aligns with spec FR-006 / SC-003–SC-005)

- **Pull request**: Pact **consumer** tests (mock provider or Pact mock server), **Vitest** with typed fixtures, **optional** Playwright subset (Chromium, parallel/shard per [Playwright docs](https://playwright.dev/docs/best-practices)).
- **Default branch / schedule / manual**: Pact **provider** verification, **Schemathesis** full runs, **Playwright** against real or Compose stack, **real-stack** integration.

## Typed DTO rule

Any JSON shape asserted in a **Pact** interaction MUST reference the same **TypeScript type or Zod schema** used by production fetch code (or generated from OpenAPI consumed by both).

## Two Pact consumers

Chat and DM **must** use distinct **consumer names** and/or **provider tags** in the broker, or isolated pactfile directories, so verification jobs select the correct provider version matrix—per spec **Edge Cases** clarifications.

| Product line | Pact `consumer` value (this repo) |
|--------------|-------------------------------------|
| Chat (`frontend/`) | `vecinita-chat-frontend` |
| DM (`apps/data-management-frontend/`) | `vecinita-dm-frontend` |

See `TESTING_DOCUMENTATION.md` (**Contract & schema testing matrix**) for merge-blocking vs manual commands.
