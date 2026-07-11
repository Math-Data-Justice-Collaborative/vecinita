# Deploy — {{PROJECT_NAME}}

> **Merged standing doc**: checklist + integration + runbook.  
> **Last updated**: {{DATE}}

## Checklist

Pre-deploy gates (complete in order):

- [ ] CI green on release branch (`{{TEST_COMMAND}}`)
- [ ] Migrations applied (`{{MIGRATION_COMMAND}}`)
- [ ] Secrets configured in `{{DEPLOY_TARGET}}` (no plaintext in git)
- [ ] Staging smoke passed (see §Runbook)
- [ ] Rollback plan documented below

## Integration

### Topology

Describe services, databases, and external dependencies.

| Component | Platform | Notes |
|-----------|----------|-------|
| {{SERVICE_NAME}} | {{DEPLOY_TARGET}} | |

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `{{CONFIG_PREFIX}}_DATABASE_URL` | yes | |

### Cross-service wiring

- Frontend → API: `{{STAGING_URL}}`
- CORS / auth: {{CORS_NOTES}}

## Runbook

### Staging deploy

```bash
{{DEPLOY_COMMAND}}
```

### Post-deploy smoke

```bash
{{SMOKE_COMMAND}}
```

### Rollback

```bash
{{ROLLBACK_COMMAND}}
```

### Common failures

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Health check 503 | Missing env / migration | |
