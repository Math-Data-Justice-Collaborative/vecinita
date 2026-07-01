import path from "node:path";
import react from "@vitejs/plugin-react";
import { filterExpectedVitestConsoleLog } from "../../packages/frontend-ui/src/test/vitestConsoleFilter";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "vecinita-frontend-i18n": path.resolve(
        __dirname,
        "../../packages/frontend-i18n/src/index.ts",
      ),
      "vecinita-frontend-ui": path.resolve(
        __dirname,
        "../../packages/frontend-ui/src/index.ts",
      ),
    },
  },
  test: {
    environment: "jsdom",
    onConsoleLog: filterExpectedVitestConsoleLog,
    silent: "passed-only",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    env: {
      VITE_VECINITA_ADMIN_API_URL: "http://localhost:8001",
      VITE_VECINITA_MODAL_PROXY_KEY: "test-proxy-key",
      VITE_VECINITA_CORPUS_API_URL: "http://localhost:8002/",
      VITE_VECINITA_CORPUS_API_KEY: "test-corpus-key",
      VITE_SUPABASE_URL: "https://test.supabase.co",
      VITE_SUPABASE_PUBLISHABLE_KEY: "test-publishable",
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**"],
      reporter: ["json-summary", "html"],
      reportsDirectory: "../../coverage/data-management-frontend",
      thresholds: {
        lines: 100,
        branches: 98,
      },
    },
  },
});
