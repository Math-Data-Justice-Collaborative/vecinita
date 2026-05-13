
  # Vecinita-Scraper-Dashboard

  This is a code bundle for Vecinita-Scraper-Dashboard. The original project is available at https://www.figma.com/design/N3vjflaaiytzI03BTzBCtc/Vecinita-Scraper-Dashboard.

  ## Running the code

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

  ## Docker deploy

  This frontend now supports Docker-based web-service deploys on Render.

  - The container listens on the runtime `PORT` provided by Render.
  - Runtime configuration is injected into `/env.js` when the container starts.
  - Set `VITE_DM_API_BASE_URL` and optional `VITE_DEFAULT_SCRAPER_USER_ID`
    in the Render service environment before starting the container.

  Local image build:

  ```bash
  docker build -t vecinita-data-management-frontend .
  docker run --rm -p 10000:10000 \
    -e PORT=10000 \
    -e VITE_DM_API_BASE_URL=http://host.docker.internal:8005 \
    vecinita-data-management-frontend
  ```

  ## Testing

  Run `npm run test` for unit and component tests.

  Run `npm run test:integration` for integration tests.

  Run `npm run e2e` for all Playwright end-to-end tests.

  ### E2E modes (dev vs live)

  The E2E suite now supports two scraper journey modes:

  - Mocked dev flow (stable for PR checks)
    - Command: `npm run test:e2e:journey:mocked`
    - Uses deterministic mocked scraper responses.

  - Live API flow (real data-management `/jobs` backend as configured on the target app)
    - Command: `npm run test:e2e:journey:live`
    - Set `PLAYWRIGHT_BASE_URL` to the hosted frontend; the deployed app must already have a valid `VITE_DM_API_BASE_URL` (or runtime `/env.js` equivalent). No separate scraper proxy env var is needed in the shell that runs Playwright.

  For PR pipelines, run:

  - `npm run test:e2e:pr`

  This executes login/auth baseline suites plus the mocked scraper journey.

  ### Environment variables for authenticated E2E

  Required for authenticated flows:

  - `E2E_ADMIN_EMAIL`
  - `E2E_ADMIN_PASSWORD`

  ### Targeting localhost vs production URL in Playwright

  By default, Playwright uses local dev server mode at `http://127.0.0.1:4173` and starts Vite automatically.

  To run against a hosted environment (for production-like validation), set:

  - `PLAYWRIGHT_BASE_URL=https://your-hosted-frontend-url`

  When `PLAYWRIGHT_BASE_URL` is set, Playwright does not start the local dev server.
  