# Render CLI login (and when `xdg-open` is missing)

## `Error: exec: "xdg-open": executable file not found in $PATH`

The Render CLI tries to open your browser with **`xdg-open`** (standard on desktop Linux). Minimal images, SSH servers, and containers often omit it.

**Option A — install the helper (Debian/Ubuntu):**

```bash
sudo apt-get update && sudo apt-get install -y xdg-utils
```

Then run `render login` again. If you still have no graphical browser, use option B.

**Option B — device login without opening a browser:**

1. Run:

   ```bash
   render login
   ```

2. If the CLI prints a **device authorization URL** and a **code** but fails on `xdg-open`, copy the URL from the terminal and open it on any machine that has a browser (your laptop is enough).

3. Approve the device in the Render dashboard, then verify:

   ```bash
   render whoami -o text
   ```

**Option C — skip CLI login entirely (env sync only):**

For `scripts/env_sync.py render-api` you only need a **Render API key**, not an interactive CLI session, if you pass **`--service-id`** (from the dashboard URL or `render services -o json` on another machine).

Put **`RENDER_API_KEY`** in a gitignored `.env` (or export it), then:

```bash
python3 scripts/env_sync.py render-api \
  --preset render-runtime-modal \
  --file .env \
  --service-id srv-xxxxxxxx \
  --dry-run
```

See [Render CLI auth with an API key](https://render.com/docs/cli#2-log-in) — an API key in the environment can satisfy automated use cases without `render login`.

---

## After you are authenticated

```bash
render whoami -o text
./scripts/setup-render-env.sh --dry-run
```

---

## API key (dashboard)

1. Open https://dashboard.render.com/api-keys  
2. Create a key and add **`RENDER_API_KEY=...`** to your gitignored `.env` (or export it in the shell).

---

## Verify a deployed service

```bash
curl -fsS "https://<your-service>.onrender.com/health"
```
