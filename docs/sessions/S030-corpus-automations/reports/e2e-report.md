# E2E Behavior Report — EV-027 / S030 (F75–F77)

> Generated: 2026-09-05  
> Mechanism: API/local TestClient (`T0`) with carried integration evidence (`T1`)  
> Journeys tested: `UJ-082`, `UJ-083`, `UJ-084`  
> Branch: `evolve/EV-027-corpus-automations`  
> Mode: evolve / delta · report-only `10-e2e`

[Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76] [Corpus: feature-list.md §F77]  
[Spec: docs/user-journeys.md §UJ-082] [Spec: docs/user-journeys.md §UJ-083] [Spec: docs/user-journeys.md §UJ-084]  
[Spec: docs/test-plan.md §TC-266–279]  
[Spec: docs/sessions/S030-corpus-automations/reports/qa-report.md]

## Summary

| # | Journey | Mechanism | Tier | Steps | Status | Notes |
|---|---------|-----------|------|-------|--------|-------|
| 1 | `UJ-082` Automations enable + history | pytest `TestClient` | T0 | 2 | PASS | `tests/e2e/test_uj082_automations.py` |
| 2 | `UJ-083` Freshness refresh / stale | pytest `TestClient` | T0 | 2 | PASS | `tests/e2e/test_uj083_freshness.py` |
| 3 | `UJ-084` FT approve + human promote | pytest `TestClient` | T0 | 4 | PASS | `tests/e2e/test_uj084_finetune.py` |
| 4 | Integration carry-forward | full compose-backed Python suite from fresh `make ci-push` | T1 | — | PASS | No blocking integration failure remains |
| 5 | Staging deploy smoke | env-gated | T2 | — | DEFERRED | staging URLs unset |
| 6 | Live browser / live Modal | env-gated | T3 | — | DEFERRED | out of scope for this local-only pass |

**Overall:** **PASS** for local EV-027 end-to-end evidence. The current docs map EV-027 to
`UJ-082`/`UJ-083`/`UJ-084`; this report corrects the stale historical numbering in the older S030 artifact.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| `T0` | PASS | `2 + 2 + 4 = 8` tests passed across `test_uj082_automations.py`, `test_uj083_freshness.py`, `test_uj084_finetune.py` |
| `T1` | PASS | Fresh `make ci-push` Python suite passed (`2413 passed, 40 skipped`) |
| `T2 connectivity` | DEFERRED | `VECINITA_STAGING_*` URLs unset locally |
| `T3 browser` | DEFERRED | live/browser tiers intentionally not exercised in this pass |

## Journey → test matrix

| Journey | Feature | Module | TCs | Result |
|---------|---------|--------|-----|--------|
| `UJ-082` | F75 | `tests/e2e/test_uj082_automations.py` | TC-266, TC-267, TC-268, TC-269, TC-270 | PASS |
| `UJ-083` | F76 | `tests/e2e/test_uj083_freshness.py` | TC-271, TC-272, TC-273, TC-274, TC-270 | PASS |
| `UJ-084` | F77 | `tests/e2e/test_uj084_finetune.py` | TC-275, TC-276, TC-277, TC-278, TC-279 | PASS |

## Journey details

### `UJ-082`: Enable automations + view run history

- Toggle automations state through the write-API-backed route: PASS
- Confirm run history is returned for automation runs: PASS

```text
bash scripts/ci/with_local_postgres.sh uv run pytest tests/e2e/test_uj082_automations.py -q
.. [100%]
```

### `UJ-083`: Refresh stale sources / schedule freshness

- Exercise stale-source listing and enable/disable freshness state: PASS
- Trigger refresh-now flow and assert expected freshness behavior: PASS

```text
bash scripts/ci/with_local_postgres.sh uv run pytest tests/e2e/test_uj083_freshness.py -q
.. [100%]
```

### `UJ-084`: Approve FT train + human promote

- Create and approve fine-tune flow: PASS
- Evaluate base vs adapter and promote/rollback behavior: PASS
- Guard kill-switch / limits behavior: PASS
- Confirm non-approved runs do not start train work: PASS

```text
bash scripts/ci/with_local_postgres.sh uv run pytest tests/e2e/test_uj084_finetune.py -q
.... [100%]
```

## Commands run

```bash
# first direct run failed because local Postgres was not started
uv run pytest tests/e2e/test_uj082_automations.py \
  tests/e2e/test_uj083_freshness.py \
  tests/e2e/test_uj084_finetune.py -q

# canonical local E2E path
bash scripts/ci/with_local_postgres.sh uv run pytest \
  tests/e2e/test_uj082_automations.py \
  tests/e2e/test_uj083_freshness.py \
  tests/e2e/test_uj084_finetune.py -q

# per-journey breakdown
bash scripts/ci/with_local_postgres.sh bash -lc '
  uv run pytest tests/e2e/test_uj082_automations.py -q &&
  uv run pytest tests/e2e/test_uj083_freshness.py -q &&
  uv run pytest tests/e2e/test_uj084_finetune.py -q
'
```

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| E2E-S030-001 | advisory | Older S030 E2E report used stale EV-027 journey numbering. Current docs map EV-027 to `UJ-082`/`UJ-083`/`UJ-084`. | Use this refreshed report as the authoritative E2E artifact. |
| E2E-S030-002 | advisory | Direct local pytest invocation fails without the repo’s Postgres wrapper. | Keep using `bash scripts/ci/with_local_postgres.sh` or `make test-e2e` for local T0 runs. |
| E2E-S030-003 | advisory | T2/T3 connectivity and live-browser evidence remain deferred because staging env URLs are unset. | Cover them later in `13-deploy-smoke` / `15-service-health` when env is available. |

## Next

Proceed to `11-verify-impl` using this E2E report plus the `09-qa` advisory set.
