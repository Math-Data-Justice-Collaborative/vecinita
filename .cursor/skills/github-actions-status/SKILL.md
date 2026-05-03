---
name: github-actions-status
description: Checks GitHub Actions workflow run status for this repository using the GitHub CLI. Use when the user asks about CI status, workflow failures, latest runs on a branch, or monitoring in-progress checks.
disable-model-invocation: true
---

# GitHub Actions status (Vecinita)

## Preconditions

- `gh` installed and authenticated: `gh auth status` (needs `repo` scope for private repos).
- Run commands from the **repository root** (or pass `-R owner/repo` explicitly).

## Resolve the repository

Prefer the **current** git remote so forks match local work:

```bash
REPO="$(git remote get-url origin 2>/dev/null | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
# e.g. Math-Data-Justice-Collaborative/vecinita
```

If `origin` is missing, use the canonical upstream: `Math-Data-Justice-Collaborative/vecinita`.

## Commands

**Recent runs (default branch):**

```bash
gh run list -R "$REPO" --branch main --limit 10
```

**Recent runs (current branch):**

```bash
gh run list -R "$REPO" --branch "$(git branch --show-current)" --limit 10
```

**In-progress runs:**

```bash
gh run list -R "$REPO" --status in_progress --limit 20
```

**Failed runs (last day):**

```bash
gh run list -R "$REPO" --status failure --limit 10
```

**Open a run in the browser or stream logs:**

```bash
gh run view -R "$REPO" <run-id>
gh run watch -R "$REPO" <run-id>
```

**List workflows defined in the repo:**

```bash
gh workflow list -R "$REPO"
```

## Reporting to the user

Summarize: **conclusion** (success / failure / in_progress / skipped), **workflow name**, **branch**, **event** (push / pull_request), **elapsed** if completed, and **run URL** (`https://github.com/$REPO/actions/runs/<id>`). If several jobs belong to one PR, mention which are still running vs green.

## Limitations

- Does not fix failing jobs; use logs (`gh run view`) and local `make ci` to reproduce.
- Scheduled or `workflow_dispatch` runs appear like other events; filter with `--event` if needed.
