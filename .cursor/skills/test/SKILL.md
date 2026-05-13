---
name: test
description: Orchestrate unit, integration, and E2E test suites across the Vecinita monorepo. Audits the branch for untested changes, delegates to the unit-test-runner, integration-test-runner, and e2e-test-runner subagents, and raises every failure to the user before taking any action. Use when the user asks to run tests, check tests, verify changes, triage failures, or validate the branch before merge.
disable-model-invocation: true
---

# Test Orchestrator

Single entry point for all testing in the Vecinita monorepo. Delegates execution to the three test-runner subagents, enforces a strict failure escalation protocol, and never applies edits without explicit user approval.

## Orchestration workflow

### Phase 1: Branch audit

Determine what needs testing by diffing the branch against main.

```bash
BASE=$(git merge-base main HEAD 2>/dev/null || git merge-base origin/main HEAD)
git diff --name-only "$BASE"...HEAD
git diff --name-only HEAD
```

Merge and deduplicate both lists. Map every changed file to the area table:

| Path pattern | Area | Subagent |
|---|---|---|
| `apps/gateway/`, `packages/` | Backend | unit-test-runner, integration-test-runner |
| `apps/chat-frontend/` | Chat frontend | unit-test-runner, e2e-test-runner |
| `apps/data-management-frontend/` | DM frontend | unit-test-runner, integration-test-runner, e2e-test-runner |
| `apps/scraper-worker/` | Scraper | unit-test-runner |
| `apps/embedding-worker/` | Embedding | unit-test-runner |
| `apps/vllm-inference/` | vLLM | unit-test-runner |
| `tests/` | Cross-stack | unit-test-runner, integration-test-runner, e2e-test-runner |
| `render.yaml`, env configs, deploy scripts | Render/env | integration-test-runner |
| `docker-compose.microservices.yml` | Microservices | integration-test-runner |
| OpenAPI specs, codegen | Schema | integration-test-runner |
| `apps/chat-frontend/e2e/`, `apps/*/tests/e2e/` | E2E specs | e2e-test-runner |

Present the audit to the user before running:

```
Branch audit (vs main):
  Areas with changes: gateway, chat-frontend, packages/, render.yaml
  Planned test passes:
    1. Unit tests — gateway, chat-frontend
    2. Integration tests — gateway (Tier 1-3), Pact (Tier 6), Render (Tier 9)
    3. E2E tests — chat-frontend Playwright
```

Ask the user to confirm or adjust scope:

```
Use AskQuestion:
  id: "test_scope"
  prompt: "These are the test passes I plan to run based on branch changes. Proceed?"
  options:
    - id: "proceed"   label: "Run all planned passes"
    - id: "unit_only" label: "Unit tests only"
    - id: "integ_only" label: "Integration tests only"
    - id: "e2e_only"  label: "E2E tests only"
    - id: "custom"    label: "I'll specify which to run"
```

### Phase 2: Execute in order

Run passes sequentially: **unit -> integration -> E2E**. This ordering ensures fast feedback first and avoids wasting time on slow E2E suites when unit tests are broken.

For each pass, delegate to the corresponding subagent:

1. **Unit pass** — delegate to `unit-test-runner` subagent
2. **Integration pass** — delegate to `integration-test-runner` subagent
3. **E2E pass** — delegate to `e2e-test-runner` subagent

Each subagent runs its tests and returns structured results. If a pass has zero relevant changed areas, skip it with a note.

**Between passes**: if the previous pass had failures and the user chose to apply fixes, re-run only the fixed tests before moving to the next pass.

### Phase 3: Failure escalation (MANDATORY)

This is the critical protocol. **Every failure must be raised to the user. No silent fixes. No autonomous edits.**

When a subagent reports failures:

1. **Present each failure** clearly:

```
FAILURE #<n> — <test tier> / <area>
  Test:    <file>::<test_name>
  Error:   <one-line summary>
  Detail:  <assertion values, traceback excerpt, or contract diff>
  Category: <classification from the subagent>
  Root cause: <hypothesis from the subagent>
  Suggested fix: <what the subagent recommends>
```

2. **Ask the user** how to proceed for EACH failure:

```
Use AskQuestion:
  id: "failure_<pass>_<n>"
  prompt: "Failure #<n>: <test_name>\n<root cause summary>\n\nSuggested fix: <description>"
  options:
    - id: "fix"         label: "Apply the suggested fix"
    - id: "alt_fix"     label: "I want a different fix (I'll describe)"
    - id: "skip"        label: "Skip — I'll handle this later"
    - id: "investigate" label: "Investigate more before I decide"
```

3. **If the user chooses "fix"**, present the exact edit as a question before applying:

```
Use AskQuestion:
  id: "confirm_edit_<pass>_<n>"
  prompt: "I will make this edit:\n\nFile: <path>\nChange: <old code> -> <new code>\n\nProceed?"
  options:
    - id: "apply"  label: "Apply this edit"
    - id: "modify" label: "Modify the edit (I'll describe)"
    - id: "cancel" label: "Cancel — don't edit"
```

4. **After applying a fix**, re-run ONLY the specific failing test to verify:
   - If it passes: mark resolved, continue.
   - If it still fails: report the new output and re-ask the user.

5. **If the user chooses "investigate"**: read the failing test file, the code under test, recent git changes (`git log -5 --oneline -- <file>`), and any relevant spec under `specs/`. Present findings, then re-ask.

### Phase 4: Summary report

After all passes complete, present:

```markdown
## Test Run Summary

| Pass | Area | Status | Passed | Failed | Skipped | Fixes |
|------|------|--------|--------|--------|---------|-------|
| Unit | gateway | PASS | 42 | 0 | 1 | 0 |
| Unit | chat-frontend | PASS | 87 | 0 | 3 | 0 |
| Integration | Tier 1 gateway | FAIL | 12 | 1 | 0 | 1 |
| E2E | chat-frontend | PASS | 10 | 0 | 0 | 0 |

Branch coverage: 4/4 areas tested

### Unresolved failures
- <list with file paths>

### Fixes applied
- <list with file paths and descriptions>
```

If there are unresolved failures:

```
Use AskQuestion:
  id: "next_steps"
  prompt: "There are <N> unresolved failures. What next?"
  options:
    - id: "rerun_failed" label: "Re-run only failed passes"
    - id: "commit"       label: "Commit the fixes applied so far"
    - id: "done"         label: "Done for now"
```

## Hard rules

1. **Never edit code without asking the user first.** Every proposed edit must be presented as a structured question with apply/modify/cancel options.
2. **Never silently skip a failure.** Every failure is reported and the user decides.
3. **Never commit without explicit user request.**
4. **Re-run only the specific failing test after a fix**, not the entire suite.
5. **Follow root-cause-analysis-first**: fix underlying causes, not symptoms.
6. **Follow spec-feature-alignment-check**: verify fixes align with specs under `specs/`.
7. **If a test requires unavailable infrastructure** (Docker, secrets, running services), report it as skipped with the reason — do not attempt it.

## Quick-reference: Makefile targets

| Target | What it runs |
|--------|-------------|
| `make test-unit` | All backend + frontend unit tests |
| `make test-integration` | All backend + cross-stack integration |
| `make test-e2e` | Cross-stack + frontend E2E |
| `make test-all-integration` | Gateway integration (no LLM) |
| `make test-cross-integration` | Root tests/ integration |
| `make test-frontend-e2e` | Chat frontend Playwright |
| `make test-cross-e2e` | Root tests/ E2E |
| `make test-schemathesis-parallel` | All OpenAPI schema suites |
| `make pact-verify-providers` | Pact provider verification |
| `make test-microservices` | Docker compose contract tests |
| `make render-workflow-ci` | Render env + service suite |
| `make ci` | Full CI gate (required before merge) |

## Key references

- Testing targets: `Makefile` (repo root)
- Testing documentation: `TESTING_DOCUMENTATION.md`
- Test ownership: gateway in `apps/gateway/tests/`, frontends in `apps/*/tests/` and `apps/*/e2e/`
- Environment requirements: `.env` for Modal/Render secrets
