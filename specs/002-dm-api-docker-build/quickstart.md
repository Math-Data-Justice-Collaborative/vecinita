# Quickstart: Baseline and compare Docker builds (Render parity)

Render builds **`vecinita-data-management-api-v1`** from:

- **Dockerfile**: `./services/scraper/Dockerfile`
- **Context**: `./services/scraper`

Local commands MUST use the **same context directory** as `dockerContext` so timings translate.

## Prerequisites

- Docker with BuildKit enabled (default on recent Docker Desktop / modern CLI).
- Submodule present: `git submodule update --init services/scraper`

## Repeat-edit scenario (warm cache)

From the **monorepo root**:

```bash
docker build \
  -f services/scraper/Dockerfile \
  -t vecinita-data-management-api-v1:local \
  services/scraper
```

Make a small **source-only** change under `services/scraper/src/`, then rebuild and compare
wall-clock times. Keep `pyproject.toml` unchanged between runs to match spec “repeat edit”.

## Cold / minimal-cache scenario

From the monorepo root (example—`docker builder prune` affects all builder cache; use on a throwaway machine or accept team coordination):

```bash
docker build --no-cache \
  -f services/scraper/Dockerfile \
  -t vecinita-data-management-api-v1:local-cold \
  services/scraper
```

Document machine profile, Docker version, and whether prune was used (**MeasurementProfile** in
[data-model.md](./data-model.md)).

## Smoke run (optional)

```bash
docker run --rm -p 10000:10000 \
  -e PORT=10000 \
  -e SCRAPER_API_KEYS=test-key \
  vecinita-data-management-api-v1:local
```

Then `curl -sf localhost:10000/health` (adjust env to match minimal local config). Full runtime
env is not required for timing work but helps prove **FR-005** / **FR-006** when combined with tests.

## Render notes

- Render uses **BuildKit** and caches **intermediate layers**; local warm builds approximate but may
  not match **exact** Render wall-clock—always record **profile** when publishing numbers.
- Follow Render guidance: **`.dockerignore`**, avoid **secret `ARG`s**, pin bases when practical.
