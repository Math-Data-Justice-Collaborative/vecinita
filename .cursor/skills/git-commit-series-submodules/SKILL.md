---
name: git-commit-series-submodules
description: Reviews working trees and writes a logical series of commits across the superrepository and every path in `.gitmodules`, without pushing. Use when preparing commits for the root repo and submodules, updating submodule pointers, splitting changes into multiple commits, or when the user forbids push.
disable-model-invocation: true
---

# Git commit series (root + `.gitmodules`, no push)

## Scope (verbatim user intent)

To review and write a series of git commits for the main module and all the @.gitmodules but not to push

## Non‑negotiables

- **Do not `git push`** (to any remote) unless the user explicitly asks to push afterward.
- **Do not** force-push, rewrite published history, or run destructive git commands unless the user explicitly requests that and understands the risk.

## Discovery

1. From the repository root, read `.gitmodules` and collect every `path = …` entry (these are submodule working trees relative to the root).
2. For each path, confirm the directory exists and `git -C <path> rev-parse --is-inside-work-tree` is true.

## Review before committing

For the **root** and **each submodule path**:

1. `git status` (and `git submodule status` from root for a quick health view).
2. `git diff` / `git diff --staged` as needed; use `git log -5 --oneline` to match local commit message style (Conventional Commits, prefixes, etc.).
3. Group changes into **logical commits** (one concern per commit). Prefer `git add -p` / path-scoped staging when the working tree mixes unrelated edits.

## Submodule vs superproject order

1. **Commit inside each dirty submodule first** (each has its own history). Ensure the submodule is on the intended branch (not accidentally detached) before committing; align with the `branch =` entry in `.gitmodules` when the team tracks a default branch.
2. **Commit the superproject last** when it records submodule pointer changes, `.gitmodules` edits, or root-only files. A single superproject commit may update several submodule SHAs after submodule commits land.

## Writing commits

- Use clear, imperative subject lines; body text when context helps reviewers.
- One commit = one coherent story; split large diffs rather than one vague message.
- After each successful commit, re-check `git status` in that repo before moving on.

## Verification

- Root: `git status` clean for intended paths; `git submodule status` shows no unexpected `+` / `-` unless you intentionally left a submodule unpinned for follow-up.
- Each touched submodule: `git status` clean after its commits.

## Optional diagnostics

- From root: `git submodule foreach --recursive 'git status -sb'` for a quick roll-up (read output; fix failures per submodule).

## Out of scope

- History rewrite (interactive rebase, amend published commits), push, and PR workflows are **not** part of this skill unless the user explicitly expands the task after commits are written.
