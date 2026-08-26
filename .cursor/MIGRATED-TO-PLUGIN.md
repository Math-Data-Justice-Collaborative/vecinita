# Vecinita — engineering-memory (workspace-scoped)

**Status:** workspace install (2026-08-24). No global `~/.cursor/plugins/local/` copy.

## This workspace

| Item | Location |
|------|----------|
| Plugin load | `workspaceOpen` → `spec-dev-knowledge-graph/cursor-plugin` |
| MCP | `.cursor/mcp.json` |
| Pack / verify | `.cursor/pack`, `.cursor/bin/` |
| Notes | `.cursor/ENGINEERING-MEMORY.md` |

## Re-install

```bash
EM_ROOT="$HOME/Documents/GitHub/spec-dev-knowledge-graph"
"$EM_ROOT/cursor-plugin/scripts/install-workspace.sh" "$PWD"
```

Reload Cursor after updates.

Pack skills: plugin Customize (`evolve`, `spec-context`, `build-build`, …). Project skills: `.cursor/skills/` (corpus-*, etc.).

[docs/decisions/ev-023-plugin-migration.md](docs/decisions/ev-023-plugin-migration.md)
