# Engineering Memory — workspace install

**Installed:** 2026-08-31

| Item | Path |
|------|------|
| Plugin (workspaceOpen) | `$EM_ENGINEERING_MEMORY_ROOT/cursor-plugin` (or sibling / in-repo; resolved at runtime) |
| MCP | `.cursor/mcp.json` (prefer `${userHome}/...` when under $HOME) |
| Pack symlink | `.cursor/pack` → plugin pack (re-created by install per machine) |
| CLI | `.cursor/bin/` (verify, session-store, memory-hook) |
| CLI symlinks | `.cursor/skills/bin/` → `../../bin/` (memory-hook stack; skipped when skills/bin has real files) |
| Hook templates | `.cursor/hooks/pack/` (scope_check, feature_drift + lib) |
| Bootstrap (F71) | `.cursor/hooks/pack/bootstrap-engineering-memory.sh` |
| Cursor session hooks (F71) | `sessionStart` / `sessionEnd` → `.cursor/hooks/pack/cursor-session-*.sh` |
| Hook config examples | `.cursor/hooks/config/examples/` |
| Plugin rules | Loaded via `workspaceOpen` plugin — not copied to `.cursor/rules/` |
| EM root (Neo4j venv) | `$EM_ENGINEERING_MEMORY_ROOT` (default sibling or `~/Documents/GitHub/spec-dev-knowledge-graph`) |

Re-run (set `EM_ENGINEERING_MEMORY_ROOT` if the clone is not at the default layout):

```bash
EM_ENGINEERING_MEMORY_ROOT="${EM_ENGINEERING_MEMORY_ROOT:-$HOME/Documents/GitHub/spec-dev-knowledge-graph}"
"$EM_ENGINEERING_MEMORY_ROOT/cursor-plugin/scripts/install-workspace.sh" "$PWD"
```

Reload Cursor after pack/plugin updates.
