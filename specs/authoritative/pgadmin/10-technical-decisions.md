# pgadmin — Technical Decisions

> Auto-generated: 2026-05-12

## Overview

Technical decisions for pgAdmin are minimal since it is an off-the-shelf Docker image with no custom code.

## Decided

| ID | Decision | Chosen | Alternatives Rejected | Date | Reversibility |
|----|----------|--------|----------------------|------|---------------|
| TD-001 | Database admin tool | pgAdmin 4 (Docker) | Adminer, DBeaver, raw psql CLI | 2026-05-12 | Easy |
| TD-002 | Deployment scope | Local/private only | Deploy to Render as private service | 2026-05-12 | Easy |
| TD-003 | Image version pinning | `latest` tag | Pinned version tag | 2026-05-12 | Easy |

### TD-001: Database Admin Tool

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Developer needs a visual database management tool for inspecting and debugging the Vecinita PostgreSQL database |
| Decision | Use pgAdmin 4 via the official `dpage/pgadmin4` Docker image |
| Rationale | pgAdmin is the most widely-used PostgreSQL GUI, well-maintained, and available as a ready-to-use Docker image. No additional setup or licensing required |
| Alternatives considered | **Adminer** — lighter weight but less PostgreSQL-specific. **DBeaver** — desktop app, not containerized. **psql CLI** — powerful but lacks visual schema navigation |
| Consequences | Adds a container to docker-compose but no custom code to maintain |
| Reversibility | Easy — swap Docker image or remove service entirely |

### TD-002: Deployment Scope

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Whether pgAdmin should be accessible in production/staging or local only |
| Decision | Local Docker Compose only — not deployed to Render |
| Rationale | Direct database admin access in production is a security risk. Render provides its own database dashboard. Solo developer can access production data via Render's psql shell or local tunneling if needed |
| Alternatives considered | **Render private service** — adds cost and security surface for rarely-used functionality |
| Consequences | No remote pgAdmin access; developer must use local Docker or Render dashboard for production database inspection |
| Reversibility | Easy — can add a Render private service definition later if needed |

### TD-003: Image Version Pinning

| Property | Value |
|----------|-------|
| Status | Accepted |
| Date | 2026-05-12 |
| Context | Whether to pin the pgAdmin Docker image to a specific version |
| Decision | Use `latest` tag for simplicity |
| Rationale | pgAdmin is a dev tool, not a production service. Breaking changes are rare and acceptable risk |
| Alternatives considered | **Pinned version** — more reproducible but requires manual updates |
| Consequences | May get unexpected UI changes on `docker-compose pull` |
| Reversibility | Easy — pin to a specific version at any time |

## Pending (Requiring Decision)

| ID | Decision | Options | Impact | Risk of Deferral | Recommendation |
|----|----------|---------|--------|------------------|----------------|
| PTD-001 | Volume persistence strategy | Named volume, bind mount | Data loss on container recreation | Low — dev tool only | Named volume |

### PTD-001: Volume Persistence Strategy

| Property | Value |
|----------|-------|
| Status | Pending |
| Identified | 2026-05-12 |
| Evidence | docker-compose.yml may or may not define a named volume for pgAdmin data |
| Impact | Saved queries and server configs lost on container recreation without persistent volume |
| Decision deadline | Before next major docker-compose refactor |

**Options researched:**

**Option A: Named Docker volume**
- How it works: Define a named volume in docker-compose.yml mounted at `/var/lib/pgadmin`
- Pros: Survives `docker-compose down`, easy backup
- Cons: Slightly more docker-compose config
- Effort: S
- Reversibility: Easy
- Ecosystem fit: Standard Docker practice

**Option B: Bind mount to host directory**
- How it works: Mount a host directory (e.g., `./data/pgadmin`) into the container
- Pros: Easy to inspect, backup, and version-control saved queries
- Cons: Permission issues on some host OSes
- Effort: S
- Reversibility: Easy
- Ecosystem fit: Common but can cause permission headaches

**Recommendation:** Named volume — simpler and avoids permission issues.
**Risk of continued deferral:** Low. Worst case is losing saved queries and server configs on container recreation.

## Related Documents

- [Architecture](07-architecture.md)
- [Dependencies](09-dependencies.md)
