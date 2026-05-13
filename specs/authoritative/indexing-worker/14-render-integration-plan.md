# Render Integration Plan: Indexing Worker
> Auto-generated: 2026-05-12

## Status: Not Applicable

The indexing-worker is deployed **exclusively on Modal** and has no Render deployment. This document exists for completeness and cross-reference consistency within the documentation suite.

## Why Not Render

| Concern | Reason |
|---------|--------|
| GPU requirement | Render does not offer GPU instances; Modal provides on-demand T4/A10G/A100 GPUs |
| Cost model | Indexing is bursty — serverless pay-per-invocation is more cost-effective than a persistent worker |
| Scale-to-zero | Modal containers scale to zero automatically; a Render worker would incur idle costs |
| Consistency | Embedding-worker and scraper-worker are already on Modal; indexing-worker follows the same pattern |

## Render Touchpoints (Indirect)

While the indexing-worker does not run on Render, it interacts with Render-hosted infrastructure:

| Resource | Hosted On | Connection |
|----------|-----------|------------|
| PostgreSQL | Render Managed | `DATABASE_URL` via Modal secret |
| Gateway (caller) | Render Web Service | Invokes indexing functions via Modal SDK |

## render.yaml

No entry in `render.yaml`. The indexing-worker is not part of the Render Blueprint.

## Cross-References

- Modal deployment: [13-modal-integration-plan.md](13-modal-integration-plan.md)
- Infrastructure: [12-infrastructure-plan.md](12-infrastructure-plan.md)
- Render landscape: [Render current-landscape](../render/current-landscape.md)
