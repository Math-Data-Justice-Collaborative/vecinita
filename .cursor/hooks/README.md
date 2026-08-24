# Cursor agent hooks

Hooks are **advisory** — they inject `additional_context` for the agent and always exit 0.
They must **not** block edits or shell when the uv workspace is temporarily invalid.

## Run hook scripts with `python3`, not `uv run python`

`.cursor/hooks.json` invokes every hook via:

```text
python3 .cursor/hooks/<script>.py
```

**Do not** use `uv run python .cursor/hooks/...` in `hooks.json`.

### Why

`uv run` resolves the whole workspace (`pyproject.toml` members, `[tool.uv.sources]`,
dev dependency group) **before** the hook script starts. A partial workspace edit — e.g.
adding `packages/rerank-client` to `[tool.uv.workspace].members` without a matching
`tool.uv.sources` entry — makes **every** `uv run` fail. Cursor then treats preToolUse
hook failure as a hard block on Write and Shell, so the agent cannot fix `pyproject.toml`.

Hook scripts themselves only need the stdlib (plus local `hook_paths.py`). When a hook needs
ruff, basedpyright, or make, it spawns `uv run …` inside `subprocess` and tolerates failure
(timeout / non-zero exit → no `additional_context`, still exit 0).

### If you add a new hook

1. Add `python3 .cursor/hooks/your_hook.py` to `hooks.json` (never `uv run python`).
2. Keep `main()` exiting 0 even when subprocess checks fail.
3. Optional: use `subprocess.run(["uv", "run", …])` inside the script for lint/typecheck.

## Hook inventory

| Script | Phase | Needs uv inside |
|--------|--------|-----------------|
| `scope_check.py` | preToolUse (Write) | No |
| `pre_task_check.py` | preToolUse (Write) | No |
| `pr_checklist.py` | preToolUse (Shell) | No |
| `common_ci_failures.py` | preToolUse / afterFileEdit | Yes (ruff) |
| `shell_deploy_guard.py` | preToolUse (Shell) | No |
| `make_format_lint_fix.py` | afterFileEdit | Yes (make → ruff) |
| `typecheck.py` | afterFileEdit | Yes (basedpyright) |
| `pydantic_field_check.py` | afterFileEdit | No |
| `feature_drift.py` | afterFileEdit | No |
| `type_suppression_check.py` | afterFileEdit | No |
| `make_ci_on_stop.py` | stop | Yes (make) |

[Corpus: ci-local-parity] [Corpus: architecture]
