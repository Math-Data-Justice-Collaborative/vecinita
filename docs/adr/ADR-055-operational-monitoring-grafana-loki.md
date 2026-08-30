# ADR-055: Operational monitoring metrics + staging Grafana/Loki

**Status:** Accepted (spec)  
**Stage:** 01-requirements / draft-docs (EV-036)  
**Date:** 2026-08-29  
**Issue:** [#114](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/114)

## Context

Operators need historical success rates for ingest, chat, and embed without violating
ADR-004 / F3 (no chat content on the server). Existing F25/F26/F32 cover corpus analytics,
point-in-time health, and per-job lists — not SLO trends. Full APM (P5) remains deferred;
operators also asked for Grafana + Loki + alerts around Modal and DigitalOcean.

ADR-004’s **≤ $50/mo hard cap** makes always-on prod Grafana risky.

## Decision

### Product metrics (in-app)

1. New feature **F84**: dedicated admin route `/monitoring` (not an extension of F25).
2. **Storage** on DO Postgres (via **internal-write-api** only — Modal never holds
   `DATABASE_URL`):
   - Raw allow-listed events table (e.g. `operation_metrics`) — retention default **7 days**
   - Hourly rollups (e.g. `metrics_hourly`) — retention default **90 days**
3. **Workloads**:
   - **ingest**: aggregate from existing `jobs` (`status`, `error_code`, timestamps;
     include retag where useful)
   - **chat**: fire-and-forget `POST /internal/v1/metrics/events` after ChatRAG `/ask`
     with `{ outcome, latency_ms, error_code?, locale? }` only
   - **embed**: pipeline-stage events correlated to ingest `job_id` (+ optional Modal
     invoke counters); not a separate first-class `jobs` type in v1
4. **APIs**: `GET /internal/v1/metrics/summary`, `GET …/timeseries`; service
   `POST …/metrics/events`. Reject `question`/`answer`/`prompt`/`message`.
5. Privacy: extend `privacy.py` allow-list; privacy + contract tests mandatory.

### Infra observability (staging-only this cycle)

1. Compose stack under **`infra/observability/`** (Grafana + Loki + Alloy/Promtail +
   Alertmanager) on a **small staging Droplet**.
2. Alerts: Alertmanager → **generic webhook** URL from staging secret
   (`VECINITA_ALERTMANAGER_WEBHOOK_URL`).
3. **Prod always-on Grafana/Loki deferred** until explicit cost AskQuestion (EV-036-D11).
4. Logs: F17 structured fields only; no raw prompts at INFO+ with long retention.

## Consequences

- Admin Monitoring ships independently of Grafana; Grafana does not replace #114 AC.
- Cost: staging micro stack only; review before prod.
- Does **not** close P5 (full OpenTelemetry APM).
- OpenAPI + Alembic migration required before Build.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Grafana-only (no admin tab) | Fails #114 embedded admin AC |
| Admin-only (no Grafana) | Rejected — operator chose hybrid |
| Grafana Cloud | Vendor analytics / sovereignty tension with ADR-004 |
| Prod Grafana now | Exceeds or threatens ≤$50 cap without AskQuestion |

## References

- [Corpus: feature-list.md §F84]
- [Corpus: ADR-004]
- ADR-007 (Modal → write API boundary)
- F17, F25, F26, F32
