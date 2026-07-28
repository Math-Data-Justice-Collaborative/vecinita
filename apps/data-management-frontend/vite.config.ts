import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Case-insensitive FS: keep AuthContext.tsx distinct from auth-context.ts
      "@/auth/AuthContext": path.resolve(
        __dirname,
        "./src/auth/AuthContext.tsx",
      ),
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
  server: {
    port: 5174,
  },
});
