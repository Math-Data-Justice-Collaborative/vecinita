# Engineering Memory — workspace install

**Installed:** 2026-08-24

| Item | Path |
|------|------|
| Plugin (workspaceOpen) | `$EM_ROOT/cursor-plugin` (default `~/Documents/GitHub/spec-dev-knowledge-graph/cursor-plugin`) |
| MCP | `.cursor/mcp.json` (gitignored; copy from `.cursor/mcp.json.example`) |
| Pack symlink | `.cursor/pack` → plugin pack (gitignored; created by install script) |
| CLI | `.cursor/bin/` (verify, session-store, memory-hook) |
| CLI symlinks | `.cursor/skills/bin/` → `../../bin/` |
| Hook templates | `.cursor/hooks/pack/` (scope_check, feature_drift + lib) |
| Hook config examples | `.cursor/hooks/config/examples/` |
| Plugin rules | Loaded via `workspaceOpen` plugin — not copied to `.cursor/rules/` |

Re-run:

```bash
EM_ROOT="${EM_ROOT:-$HOME/Documents/GitHub/spec-dev-knowledge-graph}"
"$EM_ROOT/cursor-plugin/scripts/install-workspace.sh" "$PWD"
```

Reload Cursor after pack/plugin updates.
