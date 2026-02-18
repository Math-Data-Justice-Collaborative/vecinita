# 🚀 Vecinita API v1 Quick Reference

## Live Service Information

**Gateway Running:** ✅ `http://localhost:8004`  
**Port:** 8004 (development) - Change to 8002 for production  
**Status:** Demo mode enabled (`DEMO_MODE=true`)

---

## 📍 Access Points

### Frontend
```
Browser: http://localhost:8004/
Purpose: Web UI for Vecinita Q&A Assistant
Negotiation: Automatically serves HTML for browsers, JSON API info for API clients
```

### API Base
```
Base URL: http://localhost:8004/api/v1
All endpoints prefixed with /api/v1/
```

### Documentation
```
Swagger UI:     http://localhost:8004/api/v1/docs
OpenAPI Schema: http://localhost:8004/api/v1/openapi.json
```

### Health Checks
```
Backward compatible: http://localhost:8004/health
Modern endpoint:     http://localhost:8004/api/v1/admin/health
```

---

## 🔧 Common Endpoints

### Q&A
```bash
# Ask a question
curl "http://localhost:8004/api/v1/ask?question=What%20is%20Vecinita?"

# Stream response (for large answers)
curl "http://localhost:8004/api/v1/ask/stream?question=..."

# Get Q&A configuration
curl "http://localhost:8004/api/v1/ask/config"
```

### Scraping
```bash
# Start a scraping job
curl -X POST http://localhost:8004/api/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'

# Get job status
curl "http://localhost:8004/api/v1/scrape/{job_id}"

# Cancel job
curl -X POST "http://localhost:8004/api/v1/scrape/{job_id}/cancel"

# View job history
curl "http://localhost:8004/api/v1/scrape/history"
```

### Admin
```bash
# Health check
curl "http://localhost:8004/api/v1/admin/health"

# Get statistics
curl "http://localhost:8004/api/v1/admin/stats"

# List documents
curl "http://localhost:8004/api/v1/admin/documents"

# Delete a document
curl -X DELETE "http://localhost:8004/api/v1/admin/documents/{chunk_id}"
```

---

## 📊 Complete Endpoint List (22 Total)

### Root Endpoints
- `GET /` - Service info or frontend HTML
- `GET /health` - Health check (backward compatible)
- `GET /config` - Configuration

### Q&A Endpoints (`/api/v1/ask`)
- `GET /api/v1/ask` - Ask question
- `GET /api/v1/ask/stream` - Stream response
- `GET /api/v1/ask/config` - Get config

### Scraping Endpoints (`/api/v1/scrape`)
- `POST /api/v1/scrape` - Start job
- `GET /api/v1/scrape/{job_id}` - Get status
- `POST /api/v1/scrape/{job_id}/cancel` - Cancel job
- `GET /api/v1/scrape/history` - View history
- `GET /api/v1/scrape/stats` - Get stats
- `POST /api/v1/scrape/cleanup` - Clean up

### Embedding Endpoints (`/api/v1/embed`)
- `POST /api/v1/embed` - Single embedding
- `POST /api/v1/embed/batch` - Batch embedding
- `POST /api/v1/embed/similarity` - Similarity search
- `GET /api/v1/embed/config` - Get config
- `POST /api/v1/embed/config` - Update config

### Admin Endpoints (`/api/v1/admin`)
- `GET /api/v1/admin/health` - Health check
- `GET /api/v1/admin/stats` - Statistics
- `GET /api/v1/admin/documents` - List documents
- `DELETE /api/v1/admin/documents/{chunk_id}` - Delete document
- `POST /api/v1/admin/database/clean` - Clean database
- `GET /api/v1/admin/database/clean-request` - Request clean token
- `GET /api/v1/admin/sources` - List sources
- `POST /api/v1/admin/sources/validate` - Validate sources

---

## 🔑 Features

### Content Negotiation
The root endpoint intelligently responds based on client type:
- **Browser request** (Accept: text/html): Returns HTML frontend
- **API request** (Accept: application/json): Returns JSON service info

### Backward Compatibility
Legacy endpoints remain available:
- `/health` → redirects to `/api/v1/admin/health` (for scripts)
- `/config` → Gateway configuration info
- `/` → Service info (JSON) or frontend (HTML)

### Demo Mode
When `DEMO_MODE=true` (current):
- All endpoints return sample responses
- No agent service required
- Perfect for testing and documentation
- Disable with `DEMO_MODE=false` when agent service is running

---

## 🚀 Deployment

### Current Setup
```bash
# Running in development mode on port 8004
DEMO_MODE=true python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004
```

### Production Deployment
```bash
# Stop development gateway
pkill -f "uvicorn src.api.main:app"

# Start on production port (8002)
DEMO_MODE=false GATEWAY_PORT=8002 python -m uvicorn src.api.main:app --host 0.0.0.0
```

### Frontend Build (Optional)
```bash
# Build frontend for serving at /
cd frontend
npm install
npm run build
# Creates frontend/dist/ which gets served at http://localhost:8004/
```

---

## 📝 Client Integration

### JavaScript/Frontend
```javascript
// Use the versioned API
const response = await fetch('/api/v1/ask?question=What%20is%20Vecinita?');
const data = await response.json();
console.log(data.answer, data.sources);

// Access API docs
window.open('/api/v1/docs');
```

### Python
```python
import requests

# Ask a question
response = requests.get('http://localhost:8004/api/v1/ask', 
                       params={'question': 'What is Vecinita?'})
data = response.json()
print(data['answer'])
print(data['sources'])

# Health check
health = requests.get('http://localhost:8004/health').json()
print(f"Status: {health['status']}")
```

### cURL
```bash
# Ask a question
curl -s 'http://localhost:8004/api/v1/ask?question=Hello' | jq .

# Pretty print response
curl -s 'http://localhost:8004/api/v1/ask?question=Hello' | \
  python3 -m json.tool

# Health check with verbose output
curl -v 'http://localhost:8004/health'
```

---

## 🔍 Troubleshooting

### "Frontend not built" message
**Solution:** Build the frontend
```bash
cd frontend && npm install && npm run build
```

### Agent service not connected
**Current Status:** This is expected - DEMO_MODE=true provides responses  
**To enable real agent:** 
```bash
# 1. Start agent service on port 8000
cd backend && python -m uvicorn src.services.agent.server:app --port 8000

# 2. Disable demo mode
DEMO_MODE=false python -m uvicorn src.api.main:app --port 8004
```

### "Not Found" on `/api/v1/` endpoints
**Check:** 
- Gateway is running: `ps aux | grep uvicorn`
- Endpoint path is correct (no double slashes)
- Port is 8004 in development

### CORS errors
**Check:** 
- Frontend origin is in `ALLOWED_ORIGINS` environment variable
- Current value: `http://localhost:5173,http://localhost:5174,http://localhost:4173`

---

## 📚 Architecture Overview

```
┌────────────────────────────────────────────────┐
│           Client / Browser                      │
│        (http://localhost:8004)                 │
└────────────────┬─────────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │  Root Handler "/"       │
    │  (Content Negotiation)  │
    │                         │
    │ Accept: text/html  ──→  Frontend HTML
    │ Accept: app/json   ──→  API Info
    └────────────┬────────────┘
                 │
      ┌──────────┴──────────────────────┐
      │                                  │
      ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐
│   /api/v1/*          │  │   StaticFiles        │
│   (API Routers)      │  │   (Frontend Assets)  │
│                      │  │                      │
│ ├─ /ask              │  │ Frontend dist/       │
│ ├─ /scrape           │  │ serves on /          │
│ ├─ /embed            │  │                      │
│ └─ /admin            │  │ index.html ──┐       │
└──────────────────────┘  │              │       │
                          └──────┬───────┘
                                 │
                    ┌────────────▼────────────┐
                    │                         │
                    │   Agent Service (8000)  │
                    │   Embedding (8001)      │
                    │   Database (Supabase)   │
                    │                         │
                    └─────────────────────────┘
```

---

## ✨ Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| API v1 Routing | ✅ Active | `/api/v1/*` endpoints |
| Swagger UI | ✅ Active | `/api/v1/docs` |
| Frontend Serving | ✅ Ready | Serves at `/` when built |
| Demo Mode | ✅ Enabled | All endpoints return sample data |
| Agent Service | ⚠️ Not Running | Set `DEMO_MODE=false` when ready |
| Database | ⚠️ Optional | Not required for demo mode |
| Health Check | ✅ Active | `/health` endpoint |

---

**Last Updated:** 2024  
**API Version:** 1.0.0  
**Gateway Port:** 8004 (dev), 8002 (prod)  
**Files Modified:** `/root/GitHub/VECINA/vecinita/backend/src/api/main.py`
