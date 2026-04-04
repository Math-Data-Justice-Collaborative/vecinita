# Vecinita Quick Reference Guide

**Last Updated:** February 8, 2026  
**For:** Developers, DevOps, QA teams  
**Status:** Pre-Release (6 of 8 phases complete)

---

## 🚀 Quick Start (5 Minutes)

### Run Everything Locally

```bash
cd /root/GitHub/VECINA/vecinita

# 1. Create environment file
cat > .env.local << 'EOF'
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Optional (provides fallback models)
DEEPSEEK_API_KEY=sk_...      # Primary
GEMINI_API_KEY=...            # Fallback
GROK_API_KEY=...              # Fallback
GROQ_API_KEY=...              # Already configured
OPENAI_API_KEY=sk-...         # Fallback
EOF

# 2. Start services
docker-compose up

# 3. Test streaming (in another terminal)
curl -X GET "http://localhost:8002/ask-stream?question=What+is+Python%3F" \
  -H "Accept: text/event-stream"

# 4. Test frontend
open http://localhost:5173
```

**Expected Output:**
```
data: {"type": "thinking", "message": "Analyzing..."}
data: {"type": "token", "content": "Python", "cumulative": "Python"}
data: {"type": "token", "content": " is", "cumulative": "Python is"}
...
data: {"type": "complete", ...}
```

---

## 📋 Architecture at a Glance

```
Frontend (5173)
    ↓ HTTP + SSE
Gateway (8002)
    ├→ Auth Routing (8003) [NEW]
    └→ Agent (8000)
        ├→ LLM (DeepSeek → Gemini → Grok → Groq → OpenAI → Ollama) [UPDATED]
        └→ Tools
            ├→ Vector Search (DB)
            ├→ Web Search
            └→ Static Responses
```

---

## 🔑 Key Features Implemented

### 1. Token-Streaming Responses ✅
- Real-time tokens from `/ask-stream` endpoint
- 3-word batches for UI responsiveness
- SSE (Server-Sent Events) format
- Event types: thinking, token, source, complete, error

**Test It:**
```bash
# Should see tokens appear one by one
curl "http://localhost:8002/ask-stream?question=explain+Python"
```

### 2. Multi-Model Fallback Chain ✅
- Primary: DeepSeek (api.deepseek.com)
- Fallback 1: Gemini (Google)
- Fallback 2: Grok (xAI, api.x.ai)
- Fallback 3: Groq (Llama)
- Fallback 4: OpenAI
- Fallback 5: Ollama (local)

**Check Active Model:**
```bash
curl http://localhost:8000/config | jq '.providers'
```

### 3. Auth Routing & Rate Limiting ✅
- API key validation
- Per-key rate limits (1000 tokens/day default)
- Request limits (100 req/hour)
- Health check endpoint

**Test It:**
```bash
# Health
curl http://localhost:8003/health

# With API key
curl http://localhost:8002/ask \
  -H "Authorization: Bearer sk_test123" \
  -H "X-API-Key: sk_test123"

# Check usage
curl http://localhost:8003/usage \
  -H "X-API-Key: sk_test123"
```

### 4. Gateway with Middleware ✅
- Authentication: Validates API keys
- Rate Limiting: Enforces per-key limits
- Response Headers: X-API-Key-Masked, X-Request-Time
- Fail-Open: Continues if auth routing down

**Test It:**
```bash
# Without API key (once auth is enabled)
curl http://localhost:8002/ask?question=test
# Returns 401 Unauthorized

# With API key
curl http://localhost:8002/ask?question=test \
  -H "Authorization: Bearer your-key"
# Returns 200 OK
```

### 5. Frontend Event Streaming ✅
- Token accumulation in real-time
- Source discovery as executed
- Metadata logging (debugging)
- SSE EventSource handling

**Check Console:**
```javascript
// In browser console, you'll see:
Streaming complete. Metadata: {
  model_used: "deepseek:deepseek-chat",
  tokens: 245
}
```

---

## 🛠️ Common Tasks

### Check Service Status
```bash
# All containers
docker-compose ps

# Specific service
docker-compose logs auth-service
docker-compose logs gateway
docker-compose logs agent

# Health checks
curl http://localhost:8000/health    # Agent
curl http://localhost:8002/health    # Gateway
curl http://localhost:8003/health    # Auth routing
curl http://localhost:3001/swagger    # PostgREST
```

### Monitor Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth-service

# With grep
docker-compose logs agent | grep "model_used"
```

### Debug Streaming
```bash
# Test SSE format
curl -v "http://localhost:8002/ask-stream?question=test"

# Watch in real-time with jq
curl "http://localhost:8002/ask-stream?question=test" | \
  sed 's/^data: //' | jq .

# Count events
curl -s "http://localhost:8002/ask-stream?question=test" | \
  grep -c "^data:"
```

### Test Model Fallback
```bash
# With primary (DeepSeek) only
DEEPSEEK_API_KEY=sk_test docker-compose up

# Logs will show: "Trying provider: deepseek..."
# Check: docker-compose logs agent | grep "Trying provider"
```

### Check Rate Limiting
```bash
# Get current usage
curl http://localhost:8003/usage \
  -H "X-API-Key: sk_test123"

# Should return
{
  "tokens_today": 245,
  "tokens_limit": 1000,
  "requests_today": 5,
  "requests_limit": 100
}
```

### Run Tests
```bash
cd backend

# All tests
uv run pytest -v

# Just integration tests (newly added)
uv run pytest tests/integration/ -v

# With coverage
uv run pytest --cov=src tests/

# Watch mode
uv run pytest-watch tests/
```

---

## 🔧 Configuration Reference

### Environment Variables

**Backend Agent**
```bash
# Primary LLM provider (required for no fallback)
DEEPSEEK_API_KEY=sk_xxxxxxxxxxxx

# Fallback providers (optional)
GEMINI_API_KEY=AIzaSy...
GROK_API_KEY=xai_...
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434

# Supabase (existing)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

**Gateway**
```bash
# Auth routing integration
AUTH_SERVICE_URL=http://auth-service:8003
ENABLE_AUTH=false  # Set true to enforce auth

# Rate limiting
RATE_LIMIT_TOKENS_PER_DAY=1000
RATE_LIMIT_REQUESTS_PER_HOUR=100
```

**Auth Routing**
```bash
# Service config
PORT=8003
ENVIRONMENT=development

# Supabase (for key validation)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# Rate limits (in-memory)
RATE_LIMIT_TOKENS_PER_DAY=1000
RATE_LIMIT_REQUESTS_PER_HOUR=100
```

### Docker Compose Services

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| agent | 8000 | LLM + tools | postgres, supabase |
| embedding | 8001 | Vector embeddings | postgres |
| gateway | 8002 | API routing | agent, auth-service |
| auth-service | 8003 | Key validation | postgres |
| postgrest | 3001 | DB API | postgres |
| postgres | 5432 | Database | none |
| pgadmin | 5050 | DB UI | postgres |

---

## 📊 Request/Response Examples

### Streaming Request/Response

**Request:**
```bash
curl http://localhost:8002/ask-stream?question=Explain+Python \
  -H "Accept: text/event-stream"
```

**Response (SSE Stream):**
```
data: {"type":"thinking","message":"Analyzing question..."}

data: {"type":"token","content":"Python","cumulative":"Python"}

data: {"type":"token","content":" is","cumulative":"Python is"}

data: {"type":"token","content":" a","cumulative":"Python is a"}

data: {"type":"source","url":"https://python.org","title":"Python Official Docs","source_type":"document"}

data: {"type":"complete","answer":"Python is a high-level programming language...","sources":[{"url":"https://python.org","title":"Python Docs"}],"metadata":{"model_used":"deepseek:deepseek-chat","tokens":154}}
```

### Non-Streaming Request/Response

**Request:**
```bash
curl "http://localhost:8002/ask?question=What+is+Python%3F"
```

**Response (JSON):**
```json
{
  "answer": "Python is a high-level programming language...",
  "sources": [
    {
      "url": "https://python.org",
      "title": "Python Official Docs",
      "type": "document"
    }
  ],
  "metadata": {
    "model_used": "deepseek:deepseek-chat",
    "tokens": 154
  }
}
```

### Auth Routing Endpoints

**Validate Key:**
```bash
curl -X POST http://localhost:8003/validate-key \
  -H "Content-Type: application/json" \
  -d '{"api_key":"sk_test123"}'

# Response
{"valid": true, "metadata": {...}}
```

**Get Usage:**
```bash
curl http://localhost:8003/usage \
  -H "X-API-Key: sk_test123"

# Response
{
  "tokens_today": 245,
  "tokens_limit": 1000,
  "requests_today": 5,
  "requests_limit": 100
}
```

---

## 🐛 Troubleshooting

### "Connection refused" at port 8003
```bash
# Check if auth-service is running
docker-compose logs auth-service

# Restart it
docker-compose restart auth-service

# Or disable auth temporarily
ENABLE_AUTH=false docker-compose up
```

### Streaming returns empty or missing tokens
```bash
# Check endpoint is returning event-stream format
curl -i "http://localhost:8002/ask-stream?question=test"

# Should show:
# Content-Type: text/event-stream

# If not, check agent logs
docker-compose logs agent | grep "streaming\|SSE"
```

### Model keeps falling back to Ollama
```bash
# Check if API keys are set
docker-compose config | grep API_KEY

# Check specific provider
docker-compose logs agent | grep "Trying provider"

# Verify key is valid (for deepseek)
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer sk_xxxxx"
```

### Rate limit always triggered
```bash
# Check auth routing loading state
curl http://localhost:8003/config

# Reset usage (auth routing needs restart)
docker-compose restart auth-service

# Check rate limit config
docker-compose config | grep RATE_LIMIT
```

### Frontend not receiving tokens
```bash
# Check browser console for errors
# Open DevTools → Console

# Check SSE connection
# Network tab → look for /ask-stream request
# Should show "text/event-stream" responses

# Test endpoint directly
curl "http://localhost:8002/ask-stream?question=test" | head -50
```

---

## 📈 Performance Tips

### Optimizing Token Streaming
```javascript
// Frontend - Token batching is done server-side,
// but you can debounce UI updates:
const [displayedTokens, setDisplayedTokens] = useState("");
const debounceTimeout = useRef(null);

const addToken = (token) => {
    displayedTokens += token;
    clearTimeout(debounceTimeout.current);
    debounceTimeout.current = setTimeout(() => {
        setDisplayedTokens(displayedTokens);
    }, 50); // Update UI every 50ms max
};
```

### Monitoring Provider Performance
```bash
# Log which provider is being used
docker-compose logs agent | grep "model_used"

# Count provider usage
docker-compose logs agent | grep "model_used" | \
  sed 's/.*model_used: //' | sort | uniq -c

# Find slow requests
docker-compose logs agent | grep "request_time\|duration"
```

### Scaling Auth Routing
Current implementation uses in-memory rate limiting. For production:

```python
# Upgrade to Redis (outlined in code)
# In auth/src/main.py:

# from redis import asyncio as aioredis

# class RateLimitStore:
#     def __init__(self, redis_url: str):
#         self.redis = aioredis.from_url(redis_url)
```

---

## 📚 Documentation Map

| Document | Purpose | Audience |
|----------|---------|----------|
| [PROJECT_STATUS.md](./PROJECT_STATUS.md) | Current phase progress | Everyone |
| [IMPLEMENTATION_2025_REPORT.md](./IMPLEMENTATION_2025_REPORT.md) | What was built | Architects |
| [CHANGELOG.md](../CHANGELOG.md) | Detailed changes | Developers |
| [API_INTEGRATION_SPEC.md](./API_INTEGRATION_SPEC.md) | API endpoints | Frontend |
| [ARCHITECTURE_MICROSERVICE.md](./ARCHITECTURE_MICROSERVICE.md) | System design | Architects |
| This file | Quick reference | Everyone |

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All 6 LLM API keys configured
- [ ] Auth routing service running and healthy
- [ ] Rate limits tested
- [ ] SSL/TLS certificates configured
- [ ] Auth routing backed by Redis (not in-memory)
- [ ] Monitoring alerts set up for:
  - [ ] Provider failures
  - [ ] Rate limit exceeded
  - [ ] Streaming latency > 500ms
  - [ ] Service health
- [ ] Database backups configured
- [ ] Load testing completed (at least 10 concurrent users)
- [ ] E2E tests passing
- [ ] Documentation updated for ops team

---

## 🚨 Emergency Procedures

### Service Goes Down

```bash
# 1. Check overall status
docker-compose ps

# 2. Check logs for errors
docker-compose logs --tail=100

# 3. Restart affected service
docker-compose restart [service-name]

# 4. If that doesn't work, rebuild
docker-compose build [service-name] && docker-compose up -d [service-name]

# 5. Last resort: full reset
docker-compose down -v
docker-compose up --build
```

### Rate Limiting is Too Strict

```bash
# Temporarily disable auth
ENABLE_AUTH=false docker-compose up

# Or increase limits
RATE_LIMIT_TOKENS_PER_DAY=10000 \
RATE_LIMIT_REQUESTS_PER_HOUR=500 \
docker-compose up
```

### LLM Responses Are Gen Broken

```bash
# Try next provider manually
# Check logs for which provider was active
docker-compose logs agent | grep "model_used"

# If DeepSeek failing, check API key
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY"

# Should return model list
```

---

## 🔗 Related Resources

- **Streaming Protocol:** [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- **LangChain Docs:** [LangChain Streaming](https://python.langchain.com/docs/modules/model_io/llms/streaming)
- **FastAPI SSE:** [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/streaming/)
- **DeepSeek API:** [DeepSeek Documentation](https://platform.deepseek.com)

---

## 💬 Quick Questions

**Q: How do I add a new LLM provider?**
A: Add to `PROVIDER_ORDER` list in `backend/src/agent/main.py` and implement provider initialization in `_get_llm_with_tools()`

**Q: Can I use a different rate limit backend?**
A: Yes, replace `RateLimitState` in `auth/src/main.py` with Redis client

**Q: How do I disable auth in development?**
A: Set `ENABLE_AUTH=false` in `.env.local`

**Q: What's the maximum tokens per request?**
A: No hard limit; depends on model. DeepSeek supports 8k context

**Q: Can I monitor token usage per user?**
A: Not built-in yet. Add user ID to auth header; upgrade auth routing to track by user

**Q: How do I debug why a model wasn't selected?**
A: Check `docker-compose logs agent | grep "Trying provider"`

---

## 📞 Support

For issues, check:
1. [Troubleshooting](#-troubleshooting)
2. [PROJECT_STATUS.md](./PROJECT_STATUS.md) - Known issues section
3. GitHub Issues: [Vecinita Repo](https://github.com/VECINA/vecinita)

---

**Last Updated:** 2026-02-08  
**Status:** Pre-Release (6 of 8 phases complete)  
**Next:** Phase 7 (Testing) → Phase 8 (Documentation)
