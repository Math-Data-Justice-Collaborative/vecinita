# Vecinita Changelog

> Spec-driven changelog generated from `specs/` task completion state.
> Last updated: 2026-05-11.

## [Unreleased] -- 2026-05-11

> Spec-driven changelog generated from `specs/` task completion state.

### Added

- **[004] Startup Model Pre-Pull for Modal LLM Service** -- Add startup command that pre-pulls models so deployments do not fail with default-model-missing behavior
  - Status: Complete (46/46 tasks)
  - Branch: `004-modal-model-prepull`
  - Spec: `specs/004-modal-model-prepull/spec.md`

- **[005] Wire chat frontend to gateway/agent and align data-management stack** -- Wire main chat frontend to gateway/agent and connect data-management frontend to its API
  - Status: Complete (36/36 tasks)
  - Branch: `005-wire-services-dm-front`
  - Spec: `specs/005-wire-services-dm-front/spec.md`

- **[007] Route scraper access through data management backend** -- Move scraper interface from Modal endpoint to data-management-api with function-first invocation
  - Status: Complete (40/40 tasks)
  - Branch: `007-scraper-via-dm-api`
  - Spec: `specs/007-scraper-via-dm-api/spec.md`

- **[008] Make CLI web crawler** -- Build a CLI-accessible web crawler capability
  - Status: Complete (31/31 tasks)
  - Branch: `008-make-cli-web-crawler`
  - Spec: `specs/008-make-cli-web-crawler/spec.md`

- **[012] Queued page ingestion pipeline** -- Queue-based scraping pipeline with Modal workers and bounded concurrency
  - Status: Complete (40/40 tasks)
  - Branch: `012-queued-page-ingestion-pipeline`
  - Spec: `specs/012-queued-page-ingestion-pipeline/spec.md`

- **[015] OpenAPI SDK clients and standardized service URLs** -- Generate typed SDK clients from OpenAPI specs; eliminate all HTTP calls to Modal
  - Status: In Progress (20/47 tasks)
  - Branch: `015-openapi-sdk-clients`
  - Spec: `specs/015-openapi-sdk-clients/spec.md`

- **[017] Canonical Postgres Corpus Sync** -- Ensure both frontends connected to DATABASE_URL Postgres as canonical source with full test coverage
  - Status: Complete (49/49 tasks)
  - Branch: `017-canonical-postgres-sync`
  - Spec: `specs/017-canonical-postgres-sync/spec.md`

### Changed

- **[006] Chat Message Presentation** -- Improve visual presentation of agent-returned chat messages from raw payloads to rich markdown
  - Status: Complete (30/30 tasks)
  - Branch: `006-chat-message-presentation`
  - Spec: `specs/006-chat-message-presentation/spec.md`

### Fixed

- **[001] Gateway live reliability and contract coverage** -- Fix backend API errors on Render and achieve 100% schema coverage
  - Status: In Progress (18/19 tasks)
  - Branch: `001-gateway-live-schema`
  - Spec: `specs/001-gateway-live-schema/spec.md`

- **[009] Modal scraper gateway env wiring** -- Fix Modal-gateway environment variable wiring for scraper invocation
  - Status: Complete (14/14 tasks)
  - Branch: `009-modal-scraper-gateway-env`
  - Spec: `specs/009-modal-scraper-gateway-env/spec.md`

- **[011] Fix scraper success** -- Fix scraping job failures to achieve reliable end-to-end scrape completion
  - Status: Complete (23/23 tasks)
  - Branch: `011-fix-scraper-success`
  - Spec: `specs/011-fix-scraper-success/spec.md`

### Infrastructure

- **[002] Faster Docker packaging for Data Management API V1** -- Decrease build time for DM API Docker image
  - Status: Complete (16/16 tasks)
  - Branch: `002-dm-api-docker-build`
  - Spec: `specs/002-dm-api-docker-build/spec.md`

- **[003] Consolidate scraper and stabilize job APIs** -- Remove duplicate scraper implementations and fix persistence connectivity
  - Status: In Progress (39/41 tasks)
  - Branch: `003-consolidate-scraper-dm`
  - Spec: `specs/003-consolidate-scraper-dm/spec.md`

- **[010] Minimal env config** -- Reduce environment variable surface to the minimum required set
  - Status: In Progress (26/27 tasks)
  - Branch: `010-minimal-env-config`
  - Spec: `specs/010-minimal-env-config/spec.md`

- **[016] Faster deployment and CI feedback** -- Reduce Render build times and GitHub Actions CI completion times
  - Status: In Progress (23/24 tasks)
  - Branch: `016-faster-render-ci-builds`
  - Spec: `specs/016-faster-render-ci-builds/spec.md`

- **[018] Strict Canonical Monorepo Layout** -- Refactor repo to strict structure (apis/, modal-apps/, frontends/, packages/)
  - Status: In Progress (16/26 tasks)
  - Branch: `018-strict-monorepo-layout`
  - Spec: `specs/018-strict-monorepo-layout/spec.md`

- **[019] Contract-based CI via local test attestation** -- Replace hosted CI testing with JSON attestation from local runs
  - Status: Complete (19/19 tasks)
  - Branch: `019-contract-ci-json-gate`
  - Spec: `specs/019-contract-ci-json-gate/spec.md`

---

### Spec Completion Summary

| # | Spec | Status | Tasks | Branch |
|---|------|--------|-------|--------|
| 001 | Gateway live reliability | In Progress | 18/19 | `001-gateway-live-schema` |
| 002 | DM API Docker build | Complete | 16/16 | `002-dm-api-docker-build` |
| 003 | Consolidate scraper/DM | In Progress | 39/41 | `003-consolidate-scraper-dm` |
| 004 | Modal model pre-pull | Complete | 46/46 | `004-modal-model-prepull` |
| 005 | Wire services DM front | Complete | 36/36 | `005-wire-services-dm-front` |
| 006 | Chat message presentation | Complete | 30/30 | `006-chat-message-presentation` |
| 007 | Scraper via DM API | Complete | 40/40 | `007-scraper-via-dm-api` |
| 008 | Make CLI web crawler | Complete | 31/31 | `008-make-cli-web-crawler` |
| 009 | Modal scraper gateway env | Complete | 14/14 | `009-modal-scraper-gateway-env` |
| 010 | Minimal env config | In Progress | 26/27 | `010-minimal-env-config` |
| 011 | Fix scraper success | Complete | 23/23 | `011-fix-scraper-success` |
| 012 | Queued page ingestion | Complete | 40/40 | `012-queued-page-ingestion-pipeline` |
| 015 | OpenAPI SDK clients | In Progress | 20/47 | `015-openapi-sdk-clients` |
| 016 | Faster Render CI builds | In Progress | 23/24 | `016-faster-render-ci-builds` |
| 017 | Canonical Postgres sync | Complete | 49/49 | `017-canonical-postgres-sync` |
| 018 | Strict monorepo layout | In Progress | 16/26 | `018-strict-monorepo-layout` |
| 019 | Contract CI JSON gate | Complete | 19/19 | `019-contract-ci-json-gate` |

### Stats

- Total specs: 17
- Complete: 11
- In Progress: 6
- Not Started: 0
- Total tasks: 447 completed / 475 total (94%)
