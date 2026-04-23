# Testing & contracts matrix — Feature 007

## Goals

- Prove **DM API** uses Modal **functions** for scraper / embedding / model ingest integrations under test configuration.
- Prove **gateway → agent** HTTP boundary remains intact.
- Prove **agent** respects Modal function policy (no silent `modal.run` HTTP without invocation).

## Automated tests (by layer)

| Layer | What to test | Tooling |
|-------|----------------|---------|
| DM API Modal adapter | `from_name` called with expected app/fn; `remote`/`spawn` receive expected dict args | `pytest` + `monkeypatch` / `unittest.mock` |
| DM API HTTP | Routers return documented status codes when Modal returns `_rpc_err` | `pytest` + httpx `ASGITransport` or TestClient |
| DM API OpenAPI | No undocumented 5xx on documented operations under Schemathesis | `schemathesis` (CI matrix) |
| Scraper RPC shapes | Request/response parity with fixtures | Reuse patterns from `services/data-management-api/tests/parity/test_remote_clients_parity.py`; extend for Modal envelopes |
| Gateway agent proxy | Forwarding headers, errors | Existing `backend/tests/test_api/test_gateway_main.py` |
| Agent policy | `enforce_modal_function_policy_for_urls` | Existing / extended unit tests |

## Live / optional

- Modal **smoke** with real tokens: gated (`workflow_dispatch`, labeled job, or `MODAL_LIVE_SMOKE=1`), not blocking PR.
- **Adding a GitHub Actions workflow:** only after operators approve secrets + cost; prefer extending
  existing `backend` contract jobs with a `workflow_dispatch` input rather than a new always-on job.
  Document the exact command (e.g. `cd services/scraper && modal run …`) beside the workflow when introduced.

## Ownership

- DM API tests: `services/data-management-api/tests/` (+ package tests).
- Gateway/agent: `backend/tests/`.
- Documentation: update `TESTING_DOCUMENTATION.md` when new Schemathesis scope is added for DM Modal routes.
