# BUG-2026-08-31 — workspaceOpen plugin path is machine-local

## Error description

The `workspaceOpen` hook `.cursor/hooks/register-workspace-plugins.sh` returns
`pluginPaths` pointing at a developer-machine absolute path under
`~/Documents/GitHub/spec-dev-knowledge-graph/cursor-plugin` (observed as
`/Users/bigme/Documents/GitHub/...`). That path does not exist on other
developers' machines or CI, so the engineering-memory Cursor plugin fails to
load for everyone except the original installer.

Upstream: `install-workspace.sh` historically baked `$PLUGIN_DIR` into the
generated hook via an unquoted heredoc.

## Error logs

```text
$ bash .cursor/hooks/register-workspace-plugins.sh
{"pluginPaths": ["/Users/bigme/Documents/GitHub/spec-dev-knowledge-graph/cursor-plugin"]}
```

Older installs (other workspaces) baked the literal into the script source:

```bash
python3 -c 'import json; print(json.dumps({"pluginPaths": ["/Users/bigme/Documents/GitHub/spec-dev-knowledge-graph/cursor-plugin"]}))'
```

## Investigation

| When | Note |
|------|------|
| 2026-08-31 | Confirmed output on vecinita contains `/Users/bigme/...`. |
| 2026-08-31 | Same baked form found in EMPIRIC2-planning, ams-knowledge-graph-1, empiricdownscale, vecinita-hotfix-embed-e1. |
| 2026-08-31 | Root cause: `cursor-plugin/scripts/install-workspace.sh` wrote `pluginPaths: ["$PLUGIN_DIR"]` into the hook at install time. |
| 2026-08-31 | Related: some `.cursor/mcp.json` files also store absolute `/Users/...` MCP commands. |
| 2026-08-31 | Fix: runtime resolver + empty `pluginPaths` when missing; `${userHome}` for MCP under `$HOME`. |

## GitHub issues

- Vecinita: https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/301
- Upstream plugin: https://github.com/joseph-c-mcguire/spec-dev-knowledge-graph/issues/106
  (duplicate https://github.com/joseph-c-mcguire/spec-dev-knowledge-graph/issues/107 closed)

## Repro test

`tests/bugs/test_bug_2026_08_31_workspace_plugin_hardcoded_path.py` — asserts the
tracked register hook does not embed a literal `/Users/` path and resolves via
runtime logic.

## Fix

1. Upstream `install-workspace.sh` copies `scripts/templates/register-workspace-plugins.sh`
   (runtime resolver; no bake-in) — joseph-c-mcguire/spec-dev-knowledge-graph#106.
2. Vecinita `.cursor/hooks/register-workspace-plugins.sh` replaced with the resolver.
3. Re-ran install on: vecinita, EMPIRIC2-planning, ams-knowledge-graph-1,
   empiricdownscale, vecinita-hotfix-embed-e1, spec-dev-knowledge-graph.
4. MCP commands now prefer `${userHome}/...` when under `$HOME`.
5. Regression: `cursor-plugin/scripts/tests/test_install_workspace_portable.sh` +
   `tests/bugs/test_bug_2026_08_31_workspace_plugin_hardcoded_path.py`.
