# chat-rag-frontend

Bilingual ChatRAG web UI (React/Vite, F11). Streams answers from `POST /api/v1/ask/stream`; conversation history stays in the browser only (F3).

## Local dev

```bash
cp .env.example .env
npm install
npm run dev
```

Set `VITE_VECINITA_CHAT_API_URL` to the ChatRAG backend (default `http://localhost:8000`).

## Scripts

| Command         | Purpose                     |
| --------------- | --------------------------- |
| `npm run dev`   | Vite dev server (port 5173) |
| `npm run build` | Production build            |
| `npm test`      | Vitest component tests      |
