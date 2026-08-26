# Engineering Memory — workspace install

**Installed:** 2026-08-26

| Item | Path |
|------|------|
| Plugin (workspaceOpen) | `$EM_ROOT/cursor-plugin` (default `~/Documents/GitHub/spec-dev-knowledge-graph/cursor-plugin`) |
| MCP | `.cursor/mcp.json` (gitignored; copy from `.cursor/mcp.json.example`) |
| Pack symlink | `.cursor/pack` → plugin pack (gitignored; created by install script) |
| CLI | `.cursor/bin/` (verify, session-store, memory-hook) |
| CLI symlinks | `.cursor/skills/bin/` → `../../bin/` |
| Hook templates | `.cursor/hooks/pack/` (scope_check, feature_drift + lib) |
| Bootstrap (F71) | `.cursor/hooks/pack/bootstrap-engineering-memory.sh` |
| Cursor session hooks (F71) | `sessionStart` / `sessionEnd` → `.cursor/hooks/pack/cursor-session-*.sh` |
| Hook config examples | `.cursor/hooks/config/examples/` |
| Plugin rules | Loaded via `workspaceOpen` plugin — not copied to `.cursor/rules/` |
| EM root (Neo4j venv) | `$EM_ROOT` (default `~/Documents/GitHub/spec-dev-knowledge-graph`) |

Re-run:

```bash
EM_ROOT="${EM_ROOT:-$HOME/Documents/GitHub/spec-dev-knowledge-graph}"
"$EM_ROOT/cursor-plugin/scripts/install-workspace.sh" "$PWD"
```

Reload Cursor after pack/plugin updates.
