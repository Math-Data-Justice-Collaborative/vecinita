---
name: git-push-plan-main-submodules
description: Plans and executes ordered git pushes for the superrepository and every submodule path declared in `.gitmodules`, including when the root records submodule pointer or `.gitmodules` edits. Use when syncing local commits to remotes, pushing after submodule changes, publishing submodule SHAs from the root, or when the user asks to push the main module together with submodules.
disable-model-invocation: true
---

# Push plan: root + `.gitmodules`

## Relationship to other skills

- For **staging and committing only** (no push), use [git-commit-series-submodules](../git-commit-series-submodules/SKILL.md) first; this skill covers **pushing** what those commits recorded.
- If the user has not committed yet, prepare commits there (or equivalent) before applying this push workflow.

## Goals

1. Produce a short, explicit **push plan** (repos, branches, order) the user can skim or paste into a PR.
2. **Push in a safe order**: submodule repositories that have new commits **before** the superproject commit that updates submodule pointers (if any).

## Non‑negotiables

- **Do not** `git push --force` (or rewrite published history) unless the user explicitly requests it and understands the risk.
- Confirm **remote** and **upstream branch** exist for each push target (`git rev-parse --abbrev-ref @{u}` or `git branch -vv`); if missing, set upstream with the user’s chosen remote/branch name rather than guessing destructive defaults.

## Discovery (from repository root)

1. Read `.gitmodules` and collect every `path = …` entry (submodule working trees relative to root).
2. For each path: `git -C <path> rev-parse --is-inside-work-tree` and note `branch =` from `.gitmodules` as the **intended** tracking branch when present.
3. Root: `git status -sb`, `git submodule status`, and whether `.gitmodules` or any `gitlink` entries are staged/committed but not yet pushed.

## Push plan template

Copy and fill before pushing (adjust rows if some submodules need no push):

```markdown
## Push plan (root + submodules)

| Repo | Path | Branch | Has local commits to push? | Push after |
|------|------|--------|------------------------------|------------|
| Root | `.` | … | yes/no | last |
| Submodule | … | … | yes/no | before root if pointer bump |

Order: [list submodule paths that push first] → root.

Risks / notes: [detached HEAD, diverged upstream, CI expectations]
```

## Preconditions (fix before pushing)

For **each submodule** that will receive a push:

- Working tree clean for the paths being published (or the user explicitly accepts pushing with known extra local changes—discourage this).
- Not stuck on an unintended detached `HEAD` when the team expects a named branch; align with `.gitmodules` `branch =` when that is the contract.
- New commits are intended to be **public** (review message and scope once more).

For the **root**:

- If the root commit only updates **submodule gitlinks** or `.gitmodules`, submodule pushes for those SHAs **must succeed first**; otherwise the root will point at commits the remote cannot fetch.

## Execution order

1. **Submodules with outgoing commits** (each dirty submodule in dependency order if one submodule depends on another—rare; default is arbitrary but consistent, e.g. order of appearance in `.gitmodules`): `git -C <path> push` (or `git push` inside that directory).
2. **Superproject last**: `git push` from root so remote consumers see consistent submodule targets.

If a submodule has **nothing** to push but the root still changes its recorded SHA (e.g. after a reset), push only the root after confirming that SHA already exists on the submodule remote.

## Verification after push

- Root: `git status -sb` clean ahead/behind expectations; `git submodule status` without unexpected `+` for published work.
- Each pushed submodule: `git status -sb` matches expectation vs its remote.

## Optional roll-up

From root:

```bash
git submodule foreach --recursive 'git status -sb'
```

Interpret per-submodule ahead/behind before and after the push sequence.

## Out of scope

- Choosing commit messages or splitting commits (use commit-series skill).
- Opening PRs, CI babysitting, or release tagging unless the user explicitly expands the task.
