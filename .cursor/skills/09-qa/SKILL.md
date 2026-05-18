---
name: 09-qa
description: >
  Post-build quality assurance. Runs full lint, format, typecheck, security, and dependency
  checks against the complete codebase as a final QA pass. Also checks for cross-file
  consistency (unused imports, dead code, circular dependencies). Runs asynchronously in
  parallel with 10-e2e. Results collected by 11-verify-impl.
---

# 09 — QA Checks

Final quality assurance pass on the complete codebase after the build is done.

**Cross-cutting:** [considerations.md](../considerations.md).

## When to Use

- **After 07-build completes**: The "final exam" catching anything that slipped through
  milestone-level checks
- Runs **in parallel** with 10-e2e (async)
- Results collected by 11-verify-impl

## Difference from 08-verify-build

| Aspect | 08-verify-build | 09-qa |
|--------|----------------|-------|
| When | During build, at milestones | After build completes |
| Scope | Changed files in milestone | Entire codebase |
| Auto-correct | Yes (lint/format) | Report only |
| Blocking | Non-blocking for auto-fix | Async — results go to 11 |
| Extra checks | No | Cross-file analysis |

## Prerequisites

1. **Phase C gate must pass**: 07-build `completed`, all tasks done
2. `docs/execution-plan.md` for tool configuration
3. Complete codebase with all tests passing (per 08-verify-build)

## State Management

Track via `workflow-state.yaml` §stages.09-qa.

## Workflow

### Phase 1 — Configuration

Read `docs/execution-plan.md` §Tech Stack Summary for tool commands.

### Phase 2 — Run QA Checks (Parallel Agents)

Launch all agents in one message:

**Agent 1 — Linter** (full codebase):
- Run linter on all source files (not just changed)
- Parse findings by severity
- Return: total issues, by category

**Agent 2 — Formatter** (full codebase):
- Run formatter in check mode on all files
- Return: files needing format changes

**Agent 3 — Typechecker** (full codebase):
- Full typecheck pass
- Return: all type errors

**Agent 4 — Test Suite** (full):
- Run complete test suite
- Return: pass/fail counts, failure details

**Agent 5 — Security**:
- Dependency CVE scan (`pip-audit`)
- Committed secrets scan
- Vulnerability pattern scan
- Return: all findings by category

**Agent 6 — Cross-File Analysis** (new for QA):
- **Unused imports**: Scan for imports that are never used
- **Dead code**: Functions/classes defined but never called
- **Circular dependencies**: Detect import cycles
- **Inconsistent naming**: Functions/variables that don't follow project conventions
- **Missing docstrings**: Public functions without documentation
- Return: findings by category with file/line references

**Agent 7 — Dependency Analysis**:
- Outdated packages (compare installed vs latest)
- Unused dependencies (installed but not imported)
- Missing dependencies (imported but not in requirements)
- Return: dependency health report

**Agent 8 — Template Conformance** (if template selected): Read `workflow-state.yaml`
§template and [template-registry.md](../template-registry.md). Final conformance check:
- File layout preserved from template scaffold
- Modal patterns consistent with template type across all source files
- Core logic module (`service.py` / `utils.py`) has no Modal imports
- CI/CD workflow still matches template pattern
- Naming conventions followed (`cognichem-{service_name}`)
- For job: all GPU classes consistent (same volume, timeout, `i_am_running()`)
- Return: template conformance report

### Phase 3 — Compile Results

Produce a QA report (not written to disk — passed to 11-verify-impl):

```
QA Results:
  Lint:           [PASS/FAIL] — [N] issues
  Format:         [PASS/FAIL] — [N] files
  Typecheck:      [PASS/FAIL] — [N] errors
  Tests:          [PASS/FAIL] — [N] passed, [N] failed
  Security:       [PASS/FAIL] — [N] CVEs, [N] secrets, [N] patterns
  Cross-file:     [N] unused imports, [N] dead code, [N] circular deps
  Dependencies:   [N] outdated, [N] unused, [N] missing
```

### Phase 4 — Write Report

Write `docs/qa-report.md` with full details.

**State**: Set status to `completed`. Results available for 11-verify-impl.

## Output Rules

1. **Report only**: Do not auto-fix. This is an assessment, not a correction pass.
2. **Full codebase scope**: Check everything, not just changed files.
3. **Cross-file analysis**: Go beyond single-file checks.
4. **Async-safe**: Results are self-contained and can be consumed by 11-verify-impl
   whenever it runs.
5. **No user interaction**: This stage does not ask the user questions. All findings
   go to 11-verify-impl for user review.
