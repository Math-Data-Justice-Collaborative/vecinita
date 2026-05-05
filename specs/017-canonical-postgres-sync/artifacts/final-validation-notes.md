# Final Validation Notes

## Regression checks tied to FR-008 / FR-009

- Confirmed bidirectional pact coverage exists for:
  - DM frontend consumer + DM API provider verification
  - Chat frontend consumer + gateway provider verification
- Confirmed contract drift enforcement step is present in `.github/workflows/test.yml`.
- Confirmed impacted-suite classifier and gate script exist in `scripts/ci/impacted_corpus_test_suites.py`.

## Known-risk checklist

- Risk: live provider verification depends on deployment URLs (`PACT_PROVIDER_DM_API_URL`, `PACT_PROVIDER_GATEWAY_URL`).
- Risk: full coverage thresholds are configured at workflow level and require CI reporters to remain aligned.
- Risk: cross-repo submodule availability gates some jobs on `CROSS_REPO_WORKFLOW_TOKEN`.
