---
name: github-actions-debug
description: Triages failed GitHub Actions workflows using the GitHub CLI, run and job logs, and local reproduction. Use when a workflow or job failed, CI is red on a PR, the user asks to debug GitHub Actions, or after listing runs with github-actions-status.
disable-model-invocation: true
---

# GitHub Actions debug (Vecinita)

## How this fits GitHub Actions

Workflows run **jobs** on **runners**; each job has **steps** (actions or shell commands). A red check is usually one **failed step** in one **job**. Debug by narrowing **run → job → step**, then reproduce the same command locally when possible. See GitHub’s overview of workflows, jobs, and events in [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions) and CI concepts in [Continuous integration](https://docs.github.com/en/actions/get-started/continuous-integration).

## Preconditions

- `gh` installed and authenticated: `gh auth status` (`repo` scope for private repos).
- Work from the **repository root** unless passing `-R owner/repo`.

## Resolve the repository

Same as `github-actions-status`:

```bash
REPO="$(git remote get-url origin 2>/dev/null | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
```

If `origin` is missing: `Math-Data-Justice-Collaborative/vecinita`.

## Quick triage

1. **List failed runs** (or use [github-actions-status](../github-actions-status/SKILL.md) first):

   ```bash
   gh run list -R "$REPO" --status failure --limit 15
   ```

2. **Inspect the run** (summary, jobs, conclusion):

   ```bash
   gh run view -R "$REPO" <run-id>
   ```

3. **Logs for the failed parts** (fastest default):

   ```bash
   gh run view -R "$REPO" <run-id> --log-failed
   ```

4. **Full log** (when failure context is above the first error):

   ```bash
   gh run view -R "$REPO" <run-id> --log
   ```

5. **Matrix / multi-job**: pick the failing job name from `gh run view`, then:

   ```bash
   gh run view -R "$REPO" <run-id> --job "<job-name>" --log
   ```

6. **Watch a live run**:

   ```bash
   gh run watch -R "$REPO" <run-id>
   ```

Official guidance on finding and reading logs: [Using workflow run logs](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/using-workflow-run-logs).

## Reproduce locally (this repo)

- Prefer **`make ci`** from the repository root after you understand which job failed (tests, lint, contracts, etc.). Aligns with how CI should mirror local verification ([Building and testing your code](https://docs.github.com/en/actions/tutorials/build-and-test-code)).
- If the log shows a **specific target** (e.g. one pytest file, one package script), run that narrower command first for speed, then `make ci` before calling the fix done.

## Interpret failures (root cause first)

| Signal | Likely area |
|--------|-------------|
| First red step is `npm` / `pip` / `uv` install | Lockfiles, registry auth, Python/Node version mismatch vs workflow |
| Compiler / typecheck / linter step | Same commands locally; compare env vars and working directory |
| Test step only | Flaky test vs assertion; run the same test file repeatedly |
| Deploy / third-party (e.g. Render) | Secrets, tokens, API quotas, branch filters—not always reproducible without secrets |
| `skipped` entire workflow | `paths` / `paths-ignore`, `if:` conditions, or concurrency cancel |

Prefer fixing the **underlying** failure (wrong assumption, drift, missing env in workflow) over muting checks.

## Artifacts and deep dives

- Download run artifacts when the workflow uploads logs or reports:

  ```bash
  gh run download -R "$REPO" <run-id>
  ```

- Open the run in the UI when stack traces are long or log folding hides context:  
  `https://github.com/$REPO/actions/runs/<run-id>`

## Reporting to the user

Include: **workflow name**, **event** (e.g. `pull_request`), **branch**, **failed job name(s)**, **first actionable error line** (or step name), **run URL** `https://github.com/$REPO/actions/runs/<id>`, and whether **`make ci`** reproduces it locally.

## Related skills

- List and summarize status: [github-actions-status](../github-actions-status/SKILL.md)

## Limitations

- Cannot read secrets; only whether a step *failed* due to missing auth (infer from logs).
- Does not replace reading `.github/workflows/*.yml` for exact step commands and `if:` / matrix definitions.
