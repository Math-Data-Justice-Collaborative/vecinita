# Render Integration Plan: Embedding Worker
> Auto-generated: 2026-05-12

## Status

**N/A — The embedding worker runs on Modal, not deployed on Render.**

## Rationale

The embedding worker is a serverless function application deployed exclusively on Modal. It uses Modal-specific primitives (functions, Volumes, images) that have no Render equivalent. The service is invoked via `modal.Function.from_name().remote()` — not via HTTP — so there is no web service to host.

## Why Not Render

| Factor | Modal (current) | Render (hypothetical) |
|--------|----------------|----------------------|
| Invocation model | Function call (`.remote()`) | HTTP request |
| Scaling | Auto per invocation | Container-based |
| Cold start | ~5-10s (model from Volume) | ~30-60s (image pull + model download) |
| Model caching | Modal Volume (persistent) | No equivalent (ephemeral disk) |
| Cost for 50-500/day | Minimal (pay-per-invocation) | Always-on instance required |
| GPU access | Available (not currently used) | Limited |

## Related Services on Render

| Service | Platform | Notes |
|---------|----------|-------|
| Gateway | Render | Calls embedding worker via Modal SDK |
| Data Management API | Render | Not related to embedding |
| Frontend | Render | Not related to embedding |

## Future Considerations

If the embedding worker were migrated to Render, it would require:
- A Dockerfile with fastembed + model download at build time
- Persistent disk or external storage for model cache
- HTTP endpoints replacing Modal function signatures
- Gateway changes to use HTTP instead of Modal SDK

No such migration is planned.

See: [Infrastructure Plan](12-infrastructure-plan.md) | [Modal Integration Plan](13-modal-integration-plan.md)
