# Required GitHub checks inventory (016)

**Purpose**: Baseline and post-change merge-blocking check names for **FR-004** / **SC-003**.

## Baseline and post-change inventory

This inventory tracks workflow job check names for `.github/workflows/test.yml` before and after US1/US2.

| scope | check_name (GitHub UI) | source_workflow | baseline_present | post_change_present | status |
|------|-------------------------|-----------------|------------------|---------------------|--------|
| tests | `Tests / workflow-context` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / secret-scan` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / backend-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / frontend-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / data-management-api-structure` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / data-management-frontend-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / data-management-frontend-ci` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / embedding-modal-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / embedding-modal-ci` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / model-modal-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / model-modal-ci` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / scraper-quality` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / scraper-ci` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / backend-ci` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / backend-integration` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / backend-schema` | `test.yml` | yes | no | replaced under FR-004 |
| tests | `Tests / backend-schema-gateway` | `test.yml` | no | yes | added (replacement set) |
| tests | `Tests / backend-schema-agent` | `test.yml` | no | yes | added (replacement set) |
| tests | `Tests / backend-schema-data-management` | `test.yml` | no | yes | added (replacement set) |
| tests | `Tests / frontend-unit` | `test.yml` | yes | yes | unchanged |
| tests | `Tests / backend-integration-pgvector` | `test.yml` | yes | yes | unchanged |

## EquivalenceRecord (T022 — schema job split)

| baseline_check_id | replacement_summary | same_intent_note | approver | approval_date | rationale |
|-------------------|---------------------|------------------|----------|---------------|-----------|
| `Tests / backend-schema` (single job on workflow `Tests`) | Three parallel checks: `Tests / backend-schema-gateway`, `Tests / backend-schema-agent`, `Tests / backend-schema-data-management`; gateway leg retains `dm_openapi_diff.py` | Same pytest modules, same TraceCov floor (`--tracecov-fail-under=100`), same secrets/env usage, same SC-002 drift coverage; no defect/security class removal | *(merge PR author + reviewer)* | 2026-04-29 | Reduce wall-clock for schema stage without reducing merge safety. **PR link:** fill when merged. |

**Action required:** Update branch protection/rulesets to require all three `backend-schema-*` checks (or equivalent aggregate) and remove obsolete `Tests / backend-schema` if configured.
