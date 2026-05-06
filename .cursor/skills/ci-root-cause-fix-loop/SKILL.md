---
name: ci-root-cause-fix-loop
description: Runs the repository CI gate and drives a root-cause fix loop until tests pass. Use when the user asks to run CI, make tests pass, fix failing checks, debug regressions, or resolve CI failures before merge.
---

# CI Root-Cause Fix Loop

Run the CI test and make sure that the tests are passing; if not, fix the root cause of the problem.

## Default gate

- Use `make ci` from repository root as the default verification command.
- If the user requests a narrower command first, run it, but finish with `make ci`.

## Workflow

1. Reproduce
   - Run `make ci`.
   - Capture the first failing target, file, and error.

2. Diagnose
   - Identify the underlying cause, not just the symptom.
   - Prefer source-of-truth fixes over adding bypasses or silencing checks.

3. Fix
   - Apply the smallest durable code change that removes the failure cause.
   - Keep changes scoped to the failing behavior; avoid unrelated refactors.

4. Verify
   - Re-run the most relevant focused test(s) first.
   - Re-run `make ci` from repo root.

5. Close
   - Stop only when `make ci` exits successfully.
   - Report what failed, root cause, fix, and final verification command results.

## Guardrails

- Do not use workaround-only patches unless explicitly requested.
- Do not skip tests or checks with bypass flags unless explicitly requested.
- If contract/API behavior changes, update corresponding contract tests in the same task.
- If a failure cannot be reproduced locally, state the blocker and request missing context (exact job/log/commit).

## Output format

- Failing check(s): `<target/test>`
- Root cause: `<why it failed>`
- Fix applied: `<what changed>`
- Verification: `<focused tests>` and `make ci` result
