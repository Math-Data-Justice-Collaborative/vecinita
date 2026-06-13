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
  define: {
    "import.meta.env.VITE_VECINITA_ADMIN_API_URL": JSON.stringify(
      "http://localhost:8001",
    ),
    "import.meta.env.VITE_VECINITA_MODAL_PROXY_KEY":
      JSON.stringify("test-proxy-key"),
    "import.meta.env.VITE_VECINITA_CORPUS_API_URL": JSON.stringify(
      "http://localhost:8002",
    ),
    "import.meta.env.VITE_VECINITA_CORPUS_API_KEY":
      JSON.stringify("test-corpus-key"),
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**"],
      reporter: ["json-summary", "html"],
      reportsDirectory: "../../coverage/data-management-frontend",
    },
  },
});
