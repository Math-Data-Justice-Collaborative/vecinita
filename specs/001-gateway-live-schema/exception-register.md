# TraceCov / OpenAPI waiver register (FR-004)

Use this file to record **signed waivers** when an operation included in the live Schemathesis pass cannot reach **100%** TraceCov on a dimension (e.g. `responses`) without a deliberate exception.

| Operation ID / path | Dimension | Rationale | Owner | Date |
|---------------------|------------|-----------|-------|------|
| *(none signed)* | — | — | — | — |

**Note (2026-04-19):** `make test-schemathesis-gateway` runs TraceCov with `--tracecov-fail-under=100` over the **full** loaded OpenAPI; many operations stay below 100% until each router gains explicit `responses=` (FR-006) **and** the pytest selection exercises them. Waive here only with owner + date when an operation is intentionally excluded.

**Template (copy row):**

| `POST /api/v1/...` | `responses` | Why full matrix is unsafe or misleading | `@github-handle` | YYYY-MM-DD |
