---
name: github-actions-poll-until-complete
description: Polls GitHub Actions until every workflow run for a given commit reaches a terminal status, then builds a compact error summary for failed runs. Use after a root push when multiple workflows must finish before declaring CI done, when push-deploy-debug-workflow completes Phase C or PR creation, when the user asks to wait for all checks on a SHA, or when a single latest run is insufficient because sibling workflows are still queued or in progress.
disable-model-invocation: true
---

# GitHub Actions — poll until all runs complete (Vecinita)

## Preconditions

- `gh` installed and authenticated (`gh auth status`; `repo` scope for private repos).
- Work from the **repository root** unless passing `-R owner/repo`.

## Resolve `REPO`

Same as [github-actions-status](../github-actions-status/SKILL.md):

```bash
REPO="$(git remote get-url origin 2>/dev/null | sed -E 's#.*github\.com[:/]##; s#\.git$##')"
```

If `origin` is missing, use `Math-Data-Justice-Collaborative/vecinita`.

## Identify the commit

After a successful **root** push, use the commit GitHub Actions will attribute runs to:

```bash
SHA="$(git rev-parse HEAD)"
```

If you pushed a different ref, resolve that ref’s SHA explicitly (must match the pushed commit on GitHub).

## Wait for runs to appear

`gh run list --commit` can be empty for a short window right after `git push`.

- Poll `gh run list -R "$REPO" --commit "$SHA" --limit 50 --json databaseId` every **10–20s** for up to **~3 minutes** until the list is non-empty **or** you have strong evidence no workflows trigger on push for this repo (then document that in the ledger instead of spinning forever).

## Terminal run states

Treat a workflow **run** as finished when `status` is **`completed`**, or the API exposes a non-active terminal state GitHub uses for that run (e.g. run-level **`cancelled`** in listings).

**Keep polling** while **any** run for `--commit "$SHA"` has:

`queued`, `in_progress`, `waiting`, `pending`, or `requested`

**Stop polling** when **every** listed run for that SHA is no longer in those states (typically all show `status: completed` with a `conclusion`).

Use a sensible interval (**30–90s**) between polls; optionally `gh run watch -R "$REPO" <id>` on the **last still-active** run if it helps, but **re-list by commit** afterward so sibling workflows are not missed.

## Practical cap

If polling exceeds **~90 minutes**, stop, record **cap hit** in the ledger, print the current table of in-progress vs completed runs with URLs, and suggest manual follow-up—do not loop silently.

## After all runs are terminal

1. **Table** (ledger-friendly): `workflowName` (or `name`), `databaseId`, `conclusion`, `url` for each run for `$SHA`.
2. **`## CI error summary`** (mandatory section in the agent reply when **any** run has `conclusion` in `failure`, `cancelled`, `timed_out`, `startup_failure`, or `action_required`):
   - One bullet per failed/problem run: **workflow name**, **run id**, **URL**.
   - Under each bullet, paste a **short excerpt** (roughly **5–15 lines**) from:

     ```bash
     gh run view -R "$REPO" <run-id> --log-failed
     ```

     Prefer the **first actionable error** (assertion, traceback head, npm/pytest failure line). If `--log-failed` is empty, use `gh run view -R "$REPO" <run-id>` for job names, then `gh run view -R "$REPO" <run-id> --job "<job>" --log` for the failing job.
3. If **every** run `conclusion` is **`success`** (or only allowed green outcomes like **`skipped`** where acceptable), state explicitly: **All workflow runs for this commit succeeded** (still list the table for audit).

Deeper triage: [github-actions-debug](../github-actions-debug/SKILL.md).

## Submodule remotes

If you also pushed a submodule with its own GitHub Actions, repeat this flow with that repo’s `origin` URL as `-R` and that submodule’s post-push `HEAD` SHA.

## Commands reference

**List runs for commit (JSON):**

```bash
gh run list -R "$REPO" --commit "$SHA" --limit 50 \
  --json databaseId,workflowName,name,status,conclusion,url,displayTitle,event
```

**Optional: restrict to push-triggered runs** (if PR noise appears on the same SHA):

```bash
gh run list -R "$REPO" --commit "$SHA" --event push --limit 50 \
  --json databaseId,workflowName,name,status,conclusion,url,displayTitle
```

## Limitations

- Organization ruleset runs may omit `workflowName` in the API; still poll by `status`/`conclusion`.
- Does not replace local **`make ci`** for fixing failures; use it after you understand what broke.
