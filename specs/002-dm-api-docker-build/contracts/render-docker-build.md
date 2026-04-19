# Contract: Render Docker build for `vecinita-data-management-api-v1`

**Audience**: Implementers changing `services/scraper` packaging.  
**Normative references**: Render documentation for [Docker on Render](https://render.com/docs/docker)
(image builds, BuildKit, `.dockerignore`, env → `ARG` translation, secrets).

## Blueprint binding (non-negotiable unless coordinated)

From root `render.yaml` (excerpt—verify line numbers in repo):

- **Service**: `vecinita-data-management-api-v1`
- **runtime**: `docker`
- **dockerfilePath**: `./services/scraper/Dockerfile`
- **dockerContext**: `./services/scraper`
- **healthCheckPath**: `/health`
- **PORT**: `10000` at runtime (Render sets `PORT`; Dockerfile already exposes `10000`)

Any optimization MUST preserve this **context + Dockerfile** pairing unless a separate blueprint PR
updates both and operators approve.

## Security obligations

1. **No secret `ARG`s**: Do not declare or use build `ARG` values that can contain passwords, API
   keys, or tokens. Render may map service env vars to `ARG`; only **non-sensitive** build-time
   values may be consumed in the Dockerfile.
2. **Secrets at runtime**: Continue to inject secrets via Render env / secret groups—not baked into
   layers during build.
3. **Provenance / scanning**: If the repository adds image scanning or signing steps, they MUST NOT
   be removed to gain speed (**FR-007**); replace with equivalent or stronger controls only.

## Build behavior obligations

1. **CMD / entrypoint**: The running process MUST remain the same **application factory** and host
   binding pattern (`uvicorn … --host 0.0.0.0 --port ${PORT:-10000}`) unless a defect fix is
   documented with equivalence proof (**FR-005** / **FR-006**).
2. **Python level**: Stay on **Python 3.11** line unless a deliberate upgrade is approved outside
   this performance-only feature.
3. **Base image pinning**: Prefer **immutable** base references when changing `FROM` to avoid
   Render’s **mutable-tag cache** pitfalls for public bases.
4. **Context size**: Maintain a **`.dockerignore`** (or equivalent) so caches, virtualenvs, and test
   artifacts are excluded from the Render build context.

## Verification hooks

- **Local parity**: `docker build` MUST use the same context path Render uses (see
  [quickstart.md](../quickstart.md)).
- **CI**: Existing scraper test/lint jobs remain green; optional future job may time `docker build`
  using the same context.

## Change process

1. Update Dockerfile / `.dockerignore` / install strategy.  
2. Record baselines and post-change medians (**FR-002**, **FR-008**).  
3. Attach evidence: timing table + `make ci` (or PR checks) green.
