# Starting All Vecinita Services - Quick Reference

## 🚀 Three Ways to Start Everything

### Option 1: Background Processes (Recommended for Development)
**Pros:** Simple, logs to files, easy to debug  
**Cons:** No visual split-screen monitoring

```bash
cd backend
./start-services-bg.sh
```

**View logs:**
```bash
# All logs
tail -f logs/*.log

# Individual service
tail -f logs/agent.log
tail -f logs/embedding.log
tail -f logs/gateway.log
```

**Stop services:**
```bash
pkill -f 'uvicorn src'
# Or
kill $(cat .pids/*.pid)
```

---

### Option 2: Tmux Session (Best for Monitoring)
**Pros:** Visual monitoring in split panes, easy pane switching  
**Cons:** Requires tmux installation

```bash
cd backend
./start-all-services.sh
```

This opens a tmux session with 3 panes showing all service logs.

**Tmux commands:**
- **Switch panes:** `Ctrl+b` then arrow keys
- **Detach session:** `Ctrl+b` then `d`
- **Reattach:** `tmux attach -t vecinita`
- **Kill all:** `tmux kill-session -t vecinita`

---

### Option 3: Docker Compose (Production-like)
**Pros:** Isolated containers, closest to production  
**Cons:** Slower startup, requires Docker

```bash
# From project root
docker-compose up

# Or in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🎯 Service Endpoints

After starting with any method:

| Service | URL | Purpose |
|---------|-----|---------|
| **API Gateway** | http://localhost:8004 | Main entry point |
| **Swagger Docs** | http://localhost:8004/api/v1/docs | Interactive API docs |
| **OpenAPI JSON** | http://localhost:8004/api/v1/openapi.json | OpenAPI schema |
| **Agent Service** | http://localhost:8000 | Q&A backend (internal) |
| **Embedding Service** | http://localhost:8001 | Text embeddings (internal) |
| **Health Check** | http://localhost:8004/health | Service health status |

---

## 🔧 Troubleshooting

### "Demo mode" response
If you get demo responses, the gateway can't reach the agent service:

1. **Check agent is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check environment variables:**
   ```bash
   echo $AGENT_SERVICE_URL  # Should be http://localhost:8000
   echo $DEMO_MODE          # Should be false or empty
   ```

3. **Restart gateway with explicit vars:**
   ```bash
   export AGENT_SERVICE_URL=http://localhost:8000
   export DEMO_MODE=false
   uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload
   ```

### Port already in use
```bash
# Find what's using the port
lsof -i :8000
lsof -i :8001
lsof -i :8004

# Kill specific process
kill <PID>

# Or kill all uvicorn processes
pkill -f uvicorn
```

### Service won't start
1. **Check logs** (Option 1):
   ```bash
   tail -f backend/logs/*.log
   ```

2. **Check Python environment:**
   ```bash
   cd backend
   uv sync
   ```

3. **Check dependencies:**
   ```bash
   cd backend
   uv pip list | grep -E "fastapi|uvicorn|langchain"
   ```

---

## 📝 Development Workflow

### Quick Start (Recommended)
```bash
cd backend
./start-services-bg.sh    # Start all services
curl http://localhost:8004/health  # Verify
```

Open http://localhost:8004/api/v1/docs in browser and test!

### Update Code and Reload
The gateway runs with `--reload` flag, so code changes auto-reload. For agent/embedding services, restart them manually or use the startup scripts.

### Stop Everything
```bash
# If using background processes
pkill -f 'uvicorn src'

# If using tmux
tmux kill-session -t vecinita

# If using Docker
docker-compose down
```

---

## 🏃 Running Tests

```bash
cd backend

# All tests
uv run pytest

# API tests only
uv run pytest tests/test_api/ -v

# Specific test file
uv run pytest tests/test_api/test_gateway_main.py -v

# With coverage
uv run pytest --cov
```

---

## 📦 Environment Variables

Key variables to set:

```bash
# Required for Q&A to work
export AGENT_SERVICE_URL=http://localhost:8000
export EMBEDDING_SERVICE_URL=http://localhost:8001
export DEMO_MODE=false

# Database (optional for local dev)
export SUPABASE_URL=your_supabase_url
export SUPABASE_KEY=your_supabase_key

# LLM API Keys (at least one required)
export GROQ_API_KEY=your_groq_key
export DEEPSEEK_API_KEY=your_deepseek_key
export GEMINI_API_KEY=your_gemini_key

# Optional
export DEFAULT_PROVIDER=groq
export MAX_URLS_PER_REQUEST=100
export JOB_RETENTION_HOURS=24
```

Create a `.env` file in `backend/` with these values, and source it:
```bash
cd backend
cp .env.example .env  # Edit with your values
source .env
```
