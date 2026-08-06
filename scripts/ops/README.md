# scripts/ops — approved live operations (RET-002 RA-010 / RA-011)

Thin wrappers for deploy/hotfix skills. **Default is dry-run.** Mutating actions require
`--approve` after an explicit AskQuestion in the current turn.

| Script | Purpose |
|--------|---------|
| `require_ci_green.sh` | Block until tip CI (+ deploy-preflight on `main`) is green |
| `modal_redeploy_embed.sh` | Print or run Modal embed app deploy |
| `stage_embed_runtime.sh` | Print or apply Modal embed secret runtime/pin (dangerous) |

See [docs/staging-runbook.md](../../docs/staging-runbook.md) §CI/CD before promote and ADR-049/050.
