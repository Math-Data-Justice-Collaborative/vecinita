import { defineConfig, devices } from "@playwright/test";

const chatPort = 5173;
const adminPort = 5174;
const chatBaseUrl = `http://127.0.0.1:${chatPort}`;
const adminBaseUrl = `http://127.0.0.1:${adminPort}`;

/**
 * Playwright UI E2E (T0-ui): production bundles via `vite preview`, API mocked in specs.
 * See tests/ui/README.md and docs/test-plan.md §UI E2E.
 */
export default defineConfig({
  testDir: "./tests/ui",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? "github" : "list",
  timeout: 30_000,
  use: {
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chat-rag",
      testMatch: /chat\/.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        baseURL: chatBaseUrl,
      },
    },
    {
      name: "data-management",
      testMatch: /admin\/.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
        baseURL: adminBaseUrl,
      },
    },
    {
      name: "staging",
      testMatch: /staging\/.*\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
      },
    },
  ],
  webServer: [
    {
      command: `npm run preview -w vecinita-chat-rag-frontend -- --host 127.0.0.1 --port ${chatPort} --strictPort`,
      url: chatBaseUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `npm run preview -w vecinita-data-management-frontend -- --host 127.0.0.1 --port ${adminPort} --strictPort`,
      url: adminBaseUrl,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
