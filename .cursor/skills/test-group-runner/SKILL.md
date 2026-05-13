---
name: test-group-runner
description: Run integration and unit tests group-by-group across the Vecinita monorepo, summarize failures, research fixes, and ask the user how to proceed with each failure via structured questions. Use when the user asks to run tests, triage test failures, fix failing tests, or iterate through test groups.
disable-model-invocation: true
---

# Test Group Runner

Iterate through every testing group in the Vecinita monorepo, run each group, summarize failures, research root causes, recommend fixes, and ask the user how to proceed per failure.

## Testing groups (ordered by dependency, cheapest first)

| # | Group | Make target | Working dir | Description |
|---|-------|-------------|-------------|-------------|
| 1 | Backend Unit | `test-backend-unit` | repo root | Gateway + DM API unit tests (pytest, `-m "unit and not llm"`) |
| 2 | Frontend Unit | `test-frontend-unit` | repo root | Chat frontend Vitest unit suite |
| 3 | Imported Services | `test-imported` | repo root | DM frontend, embedding-modal, model-modal, scraper tests |
| 4 | Integration (all) | `test-all-integration` | repo root | Gateway integration tests (pytest, `-m "integration and not llm"`) |
| 5 | Cross Integration | `test-cross-integration` | repo root | Cross-service integration tests (`tests/`) |
| 6 | Corpus Sync | `test-corpus-sync-full` | repo root | Feature 017 corpus synchronization suites |
| 7 | Pact Providers | `pact-verify-providers` | repo root | Consumer-driven contract replay (chat, DM, agent, Modal SDK) |
| 8 | Schemathesis Gateway | `test-schemathesis-gateway` | repo root | OpenAPI property testing — gateway (TraceCov 100%) |
| 9 | Schemathesis Agent | `test-schemathesis-agent` | repo root | OpenAPI property testing — agent |
| 10 | Schemathesis DM | `test-schemathesis-data-management` | repo root | OpenAPI property testing — data-management API (needs `SCRAPER_API_KEYS`) |
| 11 | Microservices Contracts | `test-microservices-contracts` | repo root | Proxy chain contracts (requires Docker compose) |
| 12 | Frontend E2E | `test-frontend-e2e` | repo root | Playwright chat frontend end-to-end |
| 13 | Cross E2E | `test-cross-e2e` | repo root | Cross-service Playwright end-to-end |

## Workflow

### Phase 1: Pre-flight

1. Run `make --version` and `uv --version` to confirm tooling.
2. Read the current `TESTING_DOCUMENTATION.md` for known skips and environment requirements.
3. Present the full group table to the user and ask which groups to include:

```
Use AskQuestion with:
  id: "groups_to_run"
  prompt: "Which testing groups should I run? (all selected by default)"
  options: one per group from the table above
  allow_multiple: true
```

### Phase 2: Execute groups sequentially

For each selected group, in table order:

1. **Announce** the group: print its name, make target, and a one-line description.
2. **Run** `make <target>` from the repo root. Use Shell with a generous `block_until_ms` (120000 for unit, 180000 for integration/schemathesis, 300000 for e2e). Background long-running groups and monitor with AwaitShell.
3. **Capture** the full output.
4. **Parse** the result:
   - If all tests pass: print a one-line summary (e.g., "Backend Unit: 463 passed, 24 skipped") and move to the next group.
   - If any tests fail: proceed to Phase 3 for this group before continuing.

### Phase 3: Failure triage (per group)

For each group with failures:

1. **Summarize failures** in a table:

| # | Test | File | Error summary |
|---|------|------|---------------|
| 1 | `test_name` | `path/to/test.py::TestClass` | KeyError: 'missing_field' |
| 2 | ... | ... | ... |

2. **Research each failure**: read the failing test file, the code under test, recent git changes to those files, and any relevant spec under `specs/`. Identify the root cause (not just the symptom).

3. **Recommend a fix** for each failure: explain the root cause and propose a specific code change.

4. **Ask the user** how to proceed with EACH failure using AskQuestion:

```
Use AskQuestion with:
  id: "failure_<group>_<n>"
  prompt: "Failure #<n> in <Group Name>:\n\n<test_name> — <root cause summary>\n\nRecommended fix: <one-line fix description>"
  options:
    - id: "fix"      label: "Apply the recommended fix"
    - id: "skip"     label: "Skip this failure for now"
    - id: "investigate" label: "Investigate further before deciding"
    - id: "custom"   label: "I'll describe what I want"
```

5. **Act on the user's choice**:
   - **fix**: Apply the fix, re-run ONLY the failing test to confirm, then mark resolved.
   - **skip**: Log it and move on.
   - **investigate**: Read additional context (git blame, related tests, specs), present findings, then re-ask.
   - **custom**: Wait for the user's free-text instruction and follow it.

### Phase 4: Summary

After all groups complete, present a final report:

```markdown
## Test Run Summary

| Group | Status | Passed | Failed | Skipped | Fixes Applied |
|-------|--------|--------|--------|---------|---------------|
| Backend Unit | PASS | 463 | 0 | 24 | 0 |
| Frontend Unit | FAIL | 370 | 5 | 1 | 3 |
| ... | ... | ... | ... | ... | ... |

### Unresolved failures
- <list of skipped/deferred failures with file paths>

### Fixes applied
- <list of changes made, with file paths>
```

If there are unresolved failures, ask:

```
Use AskQuestion with:
  id: "next_steps"
  prompt: "There are <N> unresolved failures. What would you like to do?"
  options:
    - id: "rerun"    label: "Re-run only failed groups"
    - id: "commit"   label: "Commit the fixes applied so far"
    - id: "done"     label: "Done for now"
```

## Key references

- Test targets and commands: `Makefile` (repo root)
- Testing documentation: `TESTING_DOCUMENTATION.md`
- Testing gates matrix: `specs/017-canonical-postgres-sync/contracts/testing-gates-matrix.md`
- Testing contracts matrix: `specs/007-scraper-via-dm-api/contracts/testing-contracts-matrix.md`
- Testing pyramid: `specs/005-wire-services-dm-front/contracts/pact-schemathesis-playwright-pyramid.md`
- Test ownership: DM API tests in `apis/data-management-api/tests/`, gateway/agent in `apis/gateway/tests/`
- Environment requirements: `.env` for Modal/Render secrets; some groups skip cleanly without them

## Important constraints

- Follow the `root-cause-analysis-first` rule: fix underlying causes, not symptoms.
- Follow the `spec-feature-alignment-check` rule: verify fixes align with relevant specs.
- Never commit fixes without user approval.
- Re-run only the specific failing test after applying a fix, not the entire group.
- If a group requires secrets not present in the environment (e.g., `SCRAPER_API_KEYS`), note the skip reason and move on.
