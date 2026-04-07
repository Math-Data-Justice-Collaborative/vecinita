# Render Postgres DNS Troubleshooting (Documents 503)

Use this runbook when documents endpoints return 503 with errors like:

could not translate host name "dpg-..." to address: Temporary failure in name resolution

## Quick Diagnosis

This message usually means a Render-internal Postgres hostname is being used from outside Render private networking.

- Render-internal hostnames: `dpg-*`
- Local/dev machine cannot resolve `dpg-*`
- Render services in the same private network can resolve `dpg-*`

This is normally a hostname scope mismatch, not a confirmed database outage.

## Reproduction Steps

### Local failure reproduction (expected 503)

1. Set `DATABASE_URL` host to a Render-internal `dpg-*` host in your local env.
2. Start gateway and agent locally.
3. Call:
   - `GET /api/v1/documents/overview`
   - `GET /api/v1/documents/tags?limit=100`
4. Expected:
   - HTTP 503 from both endpoints
   - Gateway logs mention Postgres unavailable and host translation failure

### Local recovery confirmation (expected 200)

1. Replace DB host with either:
   - local Postgres host (`localhost` / compose service host), or
   - Render external hostname
2. Restart services.
3. Re-run the two requests above.
4. Expected: endpoints return 200.

## Render MCP Debug Steps

1. Workspace selection:
   - `mcp_render_mcp_get_selected_workspace`
   - If unset: `mcp_render_mcp_list_workspaces` then `mcp_render_mcp_select_workspace`
2. Database inventory:
   - `mcp_render_mcp_list_postgres_instances`
   - Confirm target DB ID (`dpg-d6or4g2a214c73f6hl20-a`) shows `status: available`
3. Service inventory:
   - `mcp_render_mcp_list_services`
   - Find active service IDs for `vecinita-agent` and gateway service (if present)
4. Service logs:
   - `mcp_render_mcp_list_logs` with service resource IDs
   - Filter for: `preflight|degraded|database_url|could not translate host name|render_internal_host_unresolvable`
5. Database logs:
   - `mcp_render_mcp_list_logs` with DB resource ID
   - Look for accepted/authenticated connections versus crash/FATAL patterns
6. Optional SQL liveness probe:
   - `mcp_render_mcp_query_render_postgres` with `SELECT 1;`

### MCP Interpretation Rules

- DB `available` + DB logs show accepted/authenticated connections + service health endpoints return 200:
  Treat as local host scope mismatch, not Render database outage.
- DB unavailable/suspended, repeated FATAL/restart patterns, or failed SQL liveness probe:
  Treat as Render-side DB incident and escalate with captured MCP evidence.

### Evidence Checklist for Escalation

- Postgres instance ID, status, region, and timestamp from MCP response
- Service IDs and current deploy status for agent/gateway
- Representative log snippets (service and DB)
- Result of optional SQL liveness probe
- Local reproduction note showing whether host was `dpg-*` or external/local hostname

## Automated Regression Test

Use this test to lock behavior:

- [backend/tests/test_api/test_gateway_router_documents.py](backend/tests/test_api/test_gateway_router_documents.py)
  - `test_documents_endpoints_consistent_503_for_render_internal_dns_error`
- [backend/tests/integration/test_startup_database_url_failure.py](backend/tests/integration/test_startup_database_url_failure.py)
   - `TestPreflightModeSelectionConsistency` suite (guards postgres backend selection)

What it protects:

- All documents endpoints degrade to 503 consistently for DNS translation failures.
- Response contract remains stable during DB-host resolution failures.

## Local Preflight Script

Use:

- [scripts/local-render-check.sh](scripts/local-render-check.sh)

The script now includes:

- Documents endpoint smoke checks
- DATABASE_URL host scope guard (fails if local run uses `dpg-*` host)

Example:

```bash
./scripts/local-render-check.sh
```
