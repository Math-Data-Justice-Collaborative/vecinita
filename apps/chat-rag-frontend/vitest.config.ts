import react from "@vitejs/plugin-react";
import { filterExpectedVitestConsoleLog } from "../../packages/frontend-ui/src/test/vitestConsoleFilter";
import { defineConfig } from "vitest/config";

/** Node ≥25 ships a stub Web Storage that blocks jsdom's localStorage (vitest#8757). */
const nodeMajor = Number.parseInt(
  process.versions.node.split(".")[0] ?? "0",
  10,
);
const disableNodeWebstorage = nodeMajor >= 25;

export default defineConfig({
  plugins: [react()],
  define: {
    "import.meta.env.VITE_VECINITA_CHAT_API_URL": JSON.stringify(
      "http://localhost:8000",
    ),
  },
  test: {
    environment: "jsdom",
    ...(disableNodeWebstorage
      ? { execArgv: ["--no-experimental-webstorage"] }
      : {}),
    onConsoleLog: filterExpectedVitestConsoleLog,
    silent: "passed-only",
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.test.{ts,tsx}", "src/test/**"],
      reporter: ["json-summary", "html"],
      reportsDirectory: "../../coverage/chat-rag-frontend",
      thresholds: {
        lines: 95,
        branches: 95,
      },
    },
  },
});
