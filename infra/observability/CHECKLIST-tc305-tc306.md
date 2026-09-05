# TC-305 / TC-306 staging observability checklist (F84)

Run after `docker compose up -d` on the **staging** Droplet.
Record date, operator, and PASS/FAIL in the session HANDOFF or deploy notes.

[Spec: docs/test-plan.md §TC-305 §TC-306]
[Spec: docs/acceptance-criteria.md §AC-MON6–AC-MON8]

## TC-305 — Loki / log allow-list (AC-MON6)

| # | Step | Pass? |
|---|------|-------|
| 1 | Confirm Loki up: `curl -sf http://127.0.0.1:3100/ready` | |
| 2 | Retention is ≤7d: `limits_config.retention_period` = `168h` in `loki-config.yaml` | |
| 3 | Push or ship a sample JSON log **without** forbidden keys via Alloy | |
| 4 | Query Loki for last 1h: `{job=~".+"}` — sample lines have no `question`/`answer`/`prompt` payload fields | |
| 5 | Intentionally ship a line containing `"question":"..."` — Alloy redact/drop removes or redacts it before durable store | |

Automated guard: `tests/unit/observability/test_staging_obs_stack.py` (+ F17
`tests/unit/shared_schemas/test_observability.py`).

## TC-306 — Alertmanager webhook (AC-MON7–AC-MON8)

| # | Step | Pass? |
|---|------|-------|
| 1 | Alertmanager up: `curl -sf http://127.0.0.1:9093/-/ready` | |
| 2 | `alertmanager.yml` receiver uses `VECINITA_ALERTMANAGER_WEBHOOK_URL` (rendered) | |
| 3 | Fire test alert (see below) — webhook receives POST | |
| 4 | Inspect webhook body: no chat `question`/`answer`/`prompt` fields | |
| 5 | Open Grafana dashboard **Vecinita staging — Modal + DO overview** (AC-MON7 panels) | |

### Fire a test alert

```bash
# From the Droplet (Alertmanager API)
curl -sS -XPOST http://127.0.0.1:9093/api/v2/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {"alertname":"VecinitaStagingWebhookTest","severity":"warning","workload":"health"},
    "annotations": {"summary":"staging webhook drill","description":"TC-306 synthetic"}
  }]'
```

## Sign-off

| Field | Value |
|-------|-------|
| Date | |
| Operator | |
| Droplet | |
| Result | PASS / FAIL |
| Notes | |
