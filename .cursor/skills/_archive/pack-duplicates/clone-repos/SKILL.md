---
name: clone-repos
description: Batch-clone multiple GitHub repositories into a local directory. Parses messy copy-pasted repo names, confirms the cleaned list with the user, and clones in batches. Use when the user wants to clone many repos at once, bulk clone, or mentions cloning from an organization.
disable-model-invocation: true
---

# Batch Clone Repos

Clone multiple GitHub repos from a single organization into a local directory.

**Cross-cutting:** [considerations.md](../considerations.md) (usually N/A for this skill).

## State management

Optional: update repo-root [`workflow-state.yaml`](../../workflow-state.yaml) §`stages.clone-repos`
with `repos_cloned`, `status`, and `completed_at` when a batch finishes.
Rules: [workflow-state-reference.md](../workflow-state-reference.md).

## Inputs

Collect three things from the user (ask for any that are missing):

1. **Local path** — absolute directory where repos will be cloned (create it if it doesn't exist)
2. **Org base URL** — e.g. `https://github.com/my-org`
3. **Repo names** — a raw list of short names / stubs (may be messy copy-paste)

## Step 1: Ask Clone Protocol

Use AskQuestion to ask the user:

```
"Which clone protocol?" → ["HTTPS", "SSH"]
```

- HTTPS → `https://github.com/{org}/{repo}.git`
- SSH → `git@github.com:{org}/{repo}.git`

## Step 2: Parse and Clean Repo Names

The raw input is often a messy paste from a web page. Clean it:

1. Split on whitespace, commas, semicolons, or newlines.
2. Strip leading/trailing punctuation, bullets, numbering (`1.`, `-`, `*`).
3. Remove fragments that are clearly not repo names (empty strings, pure URLs, descriptive text longer than 100 chars, strings containing spaces after trimming).
4. Deduplicate (case-sensitive).
5. Sort alphabetically.

## Step 3: Confirm with the User

Present the cleaned list as a numbered table and ask the user to confirm or edit:

```
Org:      https://github.com/my-org
Target:   /path/to/local/dir
Protocol: HTTPS
Repos (14):
  1. repo-alpha
  2. repo-beta
  ...

Does this look correct? You can:
  - Remove repos by number (e.g. "remove 3, 7")
  - Add repos (e.g. "add repo-gamma")
  - Confirm to start cloning
```

Wait for user confirmation before proceeding. If the user modifies the list, show the updated list and confirm again.

## Step 4: Clone in Batches

Once confirmed:

1. Create the target directory if it doesn't exist: `mkdir -p <path>`
2. Clone repos in **parallel batches of 4** using background shell calls.
3. After each batch completes, report results before starting the next batch.
4. Track successes and failures.

For each repo run:

```bash
git clone <url> "<target_path>/<repo_name>"
```

Skip repos whose target directory already exists — report them as "already exists".

## Step 5: Summary

After all batches finish, print a summary:

```
Cloning complete.
  Cloned:         10
  Already existed:  2
  Failed:           1  ← repo-bad (exit code 128)
```

If any clones failed, show the repo name and error. Offer to retry failures.
