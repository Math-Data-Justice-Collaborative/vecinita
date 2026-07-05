# BUG-2026-07-05 — Publish Wiki CI argparse failure

**Status:** fixing  
**Severity:** medium  
**Remediation path:** local-first → PR → CI green

## Error description

Publish Wiki GitHub Actions workflow fails on the dry-run step with exit code 2.
`sync_github_wiki.py` rejects `--include-operator="false"` because
`BooleanOptionalAction` expects `--include-operator` or `--no-include-operator`, not
`=false`.

## Error logs

```
sync_github_wiki.py: error: argument --include-operator/--no-include-operator: ignored explicit argument 'false'
##[error]Process completed with exit code 2.
```

CI run: https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28749720275/job/85246600097

## Symptoms & reproduction

- **Where:** CI — Publish Wiki workflow on `main`
- **When:** After merge of PR #131 (wiki publish pipeline)
- **Frequency:** Every run (push and workflow_dispatch paths)
- **Local repro:** `uv run python scripts/docs/sync_github_wiki.py --dry-run --include-operator=false` → exit 2
- **Local pass:** `uv run python scripts/docs/sync_github_wiki.py --dry-run --no-include-operator` → builds 93 pages

## Investigation

Root cause: `.github/workflows/publish-wiki.yml` sets `INCLUDE_OP=false` and passes
`--include-operator="$INCLUDE_OP"`. Python 3.11 `argparse.BooleanOptionalAction` does not
accept explicit boolean string values.

## Root cause

**Classification:** Config / infra — workflow passes invalid CLI flag syntax.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Workflow flag regression | `tests/bugs/test_bug_2026_07_05_wiki_ci_argparse.py` | red → green after fix |

## TDD iteration log

| # | Change | Result |
|---|--------|--------|
| 1 | Repro: assert workflow must not use `--include-operator="$INCLUDE_OP"` | red on main |
| 2 | Fix publish-wiki.yml to use `--no-include-operator` / `--include-operator` | green |

## Fix

Update `.github/workflows/publish-wiki.yml` dry-run and push steps to pass
`--no-include-operator` by default and `--include-operator` only when
`workflow_dispatch` input `include_operator` is true.

## Verification plan

- **Success criterion:** Publish Wiki workflow dry-run step passes on main after merge
- **Checks:** Unit/regression tests + local dry-run + CI green after merge
- **Monitoring:** Next Publish Wiki run on main

## Verification

### Layer 1 — Automated

- [ ] Repro test red before fix, green after
- [ ] `pytest tests/bugs/test_bug_2026_07_05_wiki_ci_argparse.py`
- [ ] Local dry-run with workflow-equivalent flags

### Layer 2 — Reproduction

- [ ] CI Publish Wiki dry-run passes after merge

## Spec conformance

No product spec drift — CI/workflow config only.
