import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    env: {
      VITE_VECINITA_ADMIN_API_URL: "http://localhost:8001",
      VITE_VECINITA_MODAL_PROXY_KEY: "test-proxy-key",
      VITE_VECINITA_CORPUS_API_URL: "http://localhost:8002/",
      VITE_VECINITA_CORPUS_API_KEY: "test-corpus-key",
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**"],
      reporter: ["json-summary", "html"],
      reportsDirectory: "../../coverage/data-management-frontend",
      thresholds: {
        lines: 95,
        branches: 95,
      },
    },
  },
});
