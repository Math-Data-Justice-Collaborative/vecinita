# Research: Queued page ingestion pipeline (Modal, Render, TDD)

## Decision 1 — Modal: function invocation, timeouts, and secrets

**Decision**: Keep **Modal Python SDK** invocation (`Function.from_name`, `.remote()` / `.spawn()`) from **gateway and co-released scraper workers** only; store **Modal tokens and app/function names** in **Render/Modal secrets** (never in frontend env). Set explicit **`timeout`** (and container/resource hints where applicable) on Modal function stubs to avoid hung pipeline steps; prefer **`spawn`** for fire-and-forget drain kicks when completion is tracked asynchronously (aligned with existing `_kick_scraper_pipeline_after_submit` patterns).

**Rationale**: Modal’s documented model is **serverless functions** with **usage-based** scaling; explicit timeouts and secrets injection match [Modal product positioning](https://modal.com/) (iterate on Python workloads without hand-rolling infra). Matches existing repo patterns in `backend/src/services/modal/invoker.py` and specs **007**/**009**.

**Alternatives considered**:

- **Public `*.modal.run` HTTP from gateway for scrape/embed** — Rejected for this pipeline when **function invocation** is enabled: duplicates auth surfaces and complicates **FR-011** single contract story.
- **Long-running always-`remote()` blocking HTTP** — Rejected as default for large pages: risks gateway worker timeouts; use async job model + status polling already present on modal-jobs routes where appropriate.

## Decision 2 — Modal: observability and cold starts

**Decision**: Use **structured logging** on Modal workers with the same **correlation id** value the gateway issued (propagate from internal ingest callbacks or job metadata). Accept **cold start** latency as operational reality; mitigate with **keep-warm** only if cost-approved in tasks—not spec-blocking.

**Rationale**: **FR-015** / **SC-007** require join-up between browser-visible ids and backend logs; Modal logs are the tail for worker-side failures.

**Alternatives considered**:

- **Correlation id only on gateway** — Rejected: insufficient for Modal-only failures after internal handoff.

## Decision 3 — Render: blueprint, deploy safety, and env discipline

**Decision**: Continue **`render.yaml`** with **`autoDeployTrigger: checksPass`**, **health checks**, **`fromDatabase`** for `DATABASE_URL`, and **env group** ownership per **`docs/deployment/RENDER_SHARED_ENV_CONTRACT.md`**. Modal workers that persist via gateway use **`SCRAPER_GATEWAY_BASE_URL`** + matching **`SCRAPER_API_KEYS`** / pipeline ingest token as documented.

**Rationale**: Render’s own guidance emphasizes **Git-based deploys**, **health check gating**, and **preview/rollback** patterns ([Render: developer-friendly hosting](https://render.com/articles/developer-friendly-hosting-platforms)); repo already encodes **checksPass** in `render.yaml`.

**Alternatives considered**:

- **Manual deploys without CI gate** — Rejected: violates constitution **local CI / merge-ready** spirit and risks contract drift.

## Decision 4 — TDD and contract layering

**Decision**: **Red–green–refactor** per slice: (1) **OpenAPI** or contract doc change, (2) **pytest** or **Pact** consumer expectation failing, (3) implementation, (4) **`make ci`**. Order: **domain/unit** (pipeline state machine) → **HTTP contract** (`backend/tests/test_api/`, Schemathesis markers) → **Pact** (frontend provider verify when gateway response shapes change).

**Rationale**: User-requested **TDD**; repo already defines merge-blocking **Pact** + **Schemathesis** matrix in **`TESTING_DOCUMENTATION.md`**.

**Alternatives considered**:

- **E2E-only before unit** — Rejected: slow/flaky for pipeline; use informational **`real-stack-wiring`** workflow for smoke.

## Decision 5 — Queue durability shape

**Decision**: Treat **Postgres-backed job rows** (`scraping_jobs` / related) plus explicit **status** transitions as the **durable queue** for v1; avoid purely in-memory queues for FR-001. Modal **Queues** or external brokers are **out of scope** unless tasks discover load requirements.

**Rationale**: Spec assumption: “durable or operationally acceptable”; existing persistence path already centralizes truth in Postgres via gateway.

**Alternatives considered**:

- **Redis/SQS new dependency** — Deferred: higher operational burden unless scale testing demands it.
