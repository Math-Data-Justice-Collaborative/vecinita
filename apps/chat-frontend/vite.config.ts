import { defineConfig } from 'vite';
import path from 'path';
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';

// Default matches `frontend/.env.example` and root `.env.local.example` (gateway dev port 8004).
const gatewayProxyTarget = process.env.VITE_GATEWAY_PROXY_TARGET || 'http://127.0.0.1:8004';

export default defineConfig({
  // Load VITE_* vars from repository root env files (e.g. .env, .env.prod.render).
  envDir: path.resolve(__dirname, '..'),
  plugins: [
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // Proxy `/api` → `VITE_GATEWAY_PROXY_TARGET` (see `.env.example`); Vite rewrites bare `/api` paths to `/api/v1` for gateway compatibility.
      '/api': {
        target: gatewayProxyTarget,
        changeOrigin: true,
        rewrite: (path) => (path.startsWith('/api/v1/') ? path : path.replace(/^\/api/, '/api/v1')),
      },
    },
  },
});
