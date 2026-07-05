# BUG-2026-07-05 — Publish Wiki CI push auth failure

**Status:** fixing  
**Severity:** medium  
**Remediation path:** local-first → PR → operator adds `WIKI_PUSH_TOKEN`

## Error description

Publish Wiki GitHub Actions workflow passes dry-run but fails on **Push to GitHub Wiki**
with `remote: Repository not found` when using `GITHUB_TOKEN` against `*.wiki.git`.

## Error logs

```
remote: Repository not found.
fatal: repository 'https://github.com/Math-Data-Justice-Collaborative/vecinita.wiki.git/' not found
subprocess.CalledProcessError: Command '['git', 'push', '--force', 'origin', 'HEAD:master']' returned non-zero exit status 128.
```

CI run: https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28750906126/job/85249740592

## Symptoms & reproduction

- **Where:** CI — Publish Wiki workflow on `main` (post PR #132 argparse fix)
- **When:** 2026-07-05 after merge of fix/wiki-ci-argparse
- **Frequency:** Every push-triggered run
- **Dry-run:** Passes (94 pages built)
- **Push:** Fails — wiki git remote rejects `GITHUB_TOKEN`

## Investigation

- Wiki is enabled (`has_wiki: true`) and `vecinita.wiki.git` exists (public `git ls-remote` succeeds).
- GitHub returns "Repository not found" (not 403) when `GITHUB_TOKEN` lacks wiki push scope.
- `WIKI_PUSH_TOKEN` repo secret is **not** configured yet (2026-07-05).

## Root cause

**Classification:** Config / infra — workflow uses `GITHUB_TOKEN` for wiki git push; GitHub
blocks wiki repo access for the default Actions token on this org/repo.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Remote URL + workflow token wiring | `tests/bugs/test_bug_2026_07_05_wiki_ci_push_token.py` | red → green after fix |

## TDD iteration log

| # | Change | Result |
|---|--------|--------|
| 1 | Repro: workflow must prefer `WIKI_PUSH_TOKEN` + `build_wiki_remote_url` | red on main |
| 2 | Add helper + workflow env wiring | green (local) |
| 3 | Operator adds `WIKI_PUSH_TOKEN` PAT secret | pending post-merge |

## Fix

1. Add `build_wiki_remote_url()` in `scripts/docs/sync_github_wiki.py` (PAT vs GITHUB_TOKEN auth).
2. Update `.github/workflows/publish-wiki.yml` to use `secrets.WIKI_PUSH_TOKEN || secrets.GITHUB_TOKEN`.
3. Operator creates fine-grained PAT (Contents: Read and write on `vecinita`) → repo secret `WIKI_PUSH_TOKEN`.

## Verification plan

- **Success criterion:** Publish Wiki workflow completes push step on main
- **Checks:** Regression tests + CI Publish Wiki green after merge + secret set
- **Monitoring:** Next docs push to main

## Verification

### Layer 1 — Automated

- [ ] Repro tests red before fix, green after
- [ ] `pytest tests/bugs/test_bug_2026_07_05_wiki_ci_push_token.py`

### Layer 2 — Reproduction

- [ ] CI Publish Wiki push step passes after merge + `WIKI_PUSH_TOKEN` set

## Spec conformance

No product spec drift — CI/workflow config only.
