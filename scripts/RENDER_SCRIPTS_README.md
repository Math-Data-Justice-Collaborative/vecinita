# Render environment scripts

Helpers for syncing environment variables to Render using the **Render REST API** and, where needed, the **Render CLI** for service discovery.

## `scripts/env_sync.py` (recommended)

Python entrypoint used by the shell wrappers. It parses dotenv files safely (handles `=` in values, quotes) and can read **`RENDER_API_KEY` from a merged `--file`** so you do not have to export it in the shell.

### List services (requires `render login`)

```bash
python3 scripts/env_sync.py render-list
```

### Push Modal runtime tokens (gateway / agent)

Preset **`render-runtime-modal`** sends:

- `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` (from `MODAL_TOKEN_*`, or `MODAL_API_TOKEN_*`, or `MODAL_AUTH_*`)
- `MODAL_FUNCTION_INVOCATION` when set in the file
- `EMBEDDING_SERVICE_AUTH_TOKEN` when set in the file

Resolve the service id with the CLI (requires `render login`):

```bash
python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  --file .env \
  --service-name vecinita-gateway \
  --dry-run
```

Or pass a known id (no CLI lookup):

```bash
python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  --file .env \
  --service-id srv-xxxxxxxx \
  --yes
```

`RENDER_API_KEY` may live in `.env` (merged) or in the environment.

### Other modes

See the module docstring in `scripts/env_sync.py` for `gh` (GitHub Actions secrets) and ad-hoc `render-api` with `--prefix` / `--key` / `--all-keys`.

---

## `setup-render-env.sh`

Thin wrapper around `env_sync.py render-api --preset render-runtime-modal`.

- **Default**: `--file .env`, `--service-name vecinita-gateway` (override with `RENDER_SERVICE_NAME` or `RENDER_SERVICE_ID`).
- **Dry-run** unless you pass **`--yes`**.

```bash
./scripts/setup-render-env.sh --dry-run
./scripts/setup-render-env.sh --yes
RENDER_SERVICE_NAME=vecinita-agent ./scripts/setup-render-env.sh --yes
```

---

## `apply-render-env-api.sh`

Same as `setup-render-env.sh` but **requires `--yes`** (non-interactive automation).

```bash
./scripts/apply-render-env-api.sh --yes
```

---

## `sync_scraper_auth_render_modal.sh`

Syncs scraper Bearer auth to Render and Modal. For Render, it calls `env_sync.py render-api` with `--key` filters. **`RENDER_API_KEY` may be only in the dotenv file** (merged by `env_sync`).

```bash
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --dry-run
./scripts/sync_scraper_auth_render_modal.sh render --dotenv .env.prod.render --yes
```

---

## Troubleshooting

### `render login`

Required for `--service-name` resolution and for `render-list`.

### `exec: "xdg-open": executable file not found in $PATH`

Headless Linux often lacks `xdg-open`. Install **`xdg-utils`** (`sudo apt-get install -y xdg-utils`) or copy the **device authorization URL** from the terminal into a browser on another machine. To avoid CLI login for env pushes, use **`--service-id`** plus **`RENDER_API_KEY`** (see `RENDER_LOGIN_INSTRUCTIONS.md` in the repo root).

### `error: set RENDER_API_KEY...`

For `--yes` PATCH calls, provide `RENDER_API_KEY` in the environment **or** in a merged `--file` (e.g. `.env`).

### Service not found

Run `python3 scripts/env_sync.py render-list` and confirm the **service name** matches your Render dashboard (e.g. `vecinita-gateway`, `vecinita-agent`).
