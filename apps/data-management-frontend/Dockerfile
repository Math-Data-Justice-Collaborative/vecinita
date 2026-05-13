FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine AS runner

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "node -e \"const fs=require('fs'); const env={VITE_DM_API_BASE_URL:process.env.VITE_DM_API_BASE_URL||'',VITE_OLLAMA_BASE_URL:process.env.VITE_OLLAMA_BASE_URL||'',VITE_EMBEDDING_UPSTREAM_URL:process.env.VITE_EMBEDDING_UPSTREAM_URL||'',VITE_DEFAULT_SCRAPER_USER_ID:process.env.VITE_DEFAULT_SCRAPER_USER_ID||''}; fs.writeFileSync('dist/env.js', 'window.__VECINITA_ENV__ = ' + JSON.stringify(env) + ';\\n');\" && serve -s dist -l ${PORT:-10000}"]