# User Personas: Indexing Worker
> Auto-generated: 2026-05-12

## Overview

The indexing-worker is a **backend service** with no direct human user interface. Its "users" are automated systems and technical operators. All interactions are programmatic via Modal SDK function invocations.

See: [User Personas Diagram](diagrams/user-personas.md)

## Personas

### P1: Gateway Service (Automated Caller)

| Property | Value |
|----------|-------|
| Type | Automated system |
| Identity | `vecinita-gateway` (Render web service) |
| Protocol | Modal SDK `Function.from_name().remote()` |
| Frequency | On-demand (user-initiated from data management UI) |

**Goals:**
- Trigger single-document indexing after user requests it
- Submit batch indexing jobs for multiple documents
- Request selective re-indexing when content changes are detected
- Initiate full vector rebuilds when embedding model changes

**Pain points (planned mitigations):**
- Long-running indexing blocks the gateway response → use `.spawn()` for rebuild operations
- Unclear indexing status → `IndexingResult` returns detailed progress
- Batch size limits → enforced at schema validation level with clear error messages

### P2: Scraper Worker (Automated Trigger)

| Property | Value |
|----------|-------|
| Type | Automated system |
| Identity | `vecinita-scraper` (Modal app) |
| Protocol | Modal SDK cross-app function call |
| Frequency | After every successful scrape completion |

**Goals:**
- Immediately index newly scraped documents so they become searchable
- Fire-and-forget: scraper should not block on indexing completion

**Pain points (planned mitigations):**
- Indexing failure should not fail the scrape pipeline → independent error handling, scraper logs warning and continues
- Scraper does not know if indexing succeeded → optional callback or status query

### P3: Platform Operator (Human)

| Property | Value |
|----------|-------|
| Type | Human (developer / DevOps) |
| Identity | Team member with Modal dashboard access |
| Frequency | Ad-hoc (deployments, incident response, model changes) |

**Goals:**
- Monitor indexing job health via Modal dashboard
- Trigger full vector rebuilds when changing the embedding model
- Debug failed indexing jobs using structured logs
- Understand GPU utilization and cost

**Pain points (planned mitigations):**
- No visibility into indexing pipeline stages → structured logging with `structlog`
- Unclear cost implications of rebuild → job duration tracking in `indexing_jobs` table
- Model change requires coordinated rebuild → `rebuild_all` with `reason` parameter

### P4: Developer (Human)

| Property | Value |
|----------|-------|
| Type | Human (software engineer) |
| Identity | Team member developing or testing the service |
| Frequency | During development and testing cycles |

**Goals:**
- Run indexing functions locally with `modal run`
- Test chunking and embedding logic in isolation
- Validate vector output against expected dimensions and quality
- Iterate on chunk size and overlap parameters

**Pain points (planned mitigations):**
- GPU not available locally → Modal handles GPU provisioning transparently
- Large test datasets slow iteration → `force` flag to bypass hash checks during development
- Hard to test change detection logic → unit tests with mocked content hashes

## Persona Interaction Frequency

| Persona | Trigger | Estimated Frequency |
|---------|---------|-------------------|
| Gateway (single) | User clicks "Index" in data management UI | 10-50/day |
| Gateway (batch) | User submits bulk index from data management UI | 1-5/day |
| Gateway (re-index) | Scheduled or manual re-index check | 1-2/day |
| Gateway (rebuild) | Embedding model change | Rare (~monthly) |
| Scraper Worker | After each scrape completion | Matches scrape volume |
| Platform Operator | Deployments, incidents, model changes | Weekly |
| Developer | Local development and testing | During development sprints |
