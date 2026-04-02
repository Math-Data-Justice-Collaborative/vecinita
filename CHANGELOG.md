# Changelog - Vecinita Full-Stack Integration

## Version 2025.02 - Full-Stack Integration Release

**Release Date:** March 29, 2026  
**Status:** Maintenance Update (microservices consolidation and CI hardening)

---

## Summary

Comprehensive integration of frontend components with backend services featuring:
- Token-by-token streaming responses via Server-Sent Events (SSE)
- Multi-model LLM fallback chain (6 providers)
- Unified authentication proxy with rate limiting
- Enhanced gateway with security middleware
- Real-time token and source events in frontend
- Metadata tracking for debugging and analytics

### Added: Localized chat suggestions (March 30, 2026)
- Added backend follow-up suggestion generation for `/ask-stream` complete events.
- Extended SSE complete-event contract with additive field `suggested_questions`.
- Added localized suggestion chips to chat splash state and after assistant responses.
- Added frontend fallback suggestion banks for English and Spanish when backend suggestions are missing.
- Added tests for suggestion parsing, rendering, and click-to-send interaction.

---

## Major Changes

### ✅ PHASE 1: Agent Streaming Refactor

**Modified Files:**
- `backend/src/agent/main.py` (+300 lines, ~15 functions modified)

**Changes:**

1. **New: TokenStreamingCallback class**
```python
class TokenStreamingCallback(BaseCallbackHandler):
    """Tracks token generation from LLM"""
    def __init__(self):
        self.token_count = 0
        self.tokens_list = []
    
    def on_llm_new_token(self, token: str, **kwargs):
        self.token_count += 1
        self.tokens_list.append(token)
```
- Purpose: Real-time token tracking during generation
- Location: ~line 50
- Usage: Passed to LLM during tool execution

2. **New: _extract_model_info() function**
```python
def _extract_model_info(llm) -> tuple[str, str]:
    """Extract (provider, model) from LLM instance"""
    # Returns like ("deepseek", "deepseek-chat")
```
- Purpose: Identify which LLM provider/model was selected
- Location: ~line 80
- Used by: agent_node() to populate metadata

3. **Modified: AgentState TypedDict**
```python
class AgentState(TypedDict):
    # ... existing fields ...
    token_count: int = 0
    model_used: str | None = None
```
- New fields capture metadata during execution
- Purpose: Track tokens and model for debugging

4. **Modified: agent_node() function**
```python
# Now extracts model info and token count from response
state["model_used"] = _extract_model_info(llm)
state["token_count"] = getattr(response.response_metadata, "usage_metadata", {})
```
- Purpose: Populate metadata fields
- Side effect: Can log which model handled request

5. **New: _stream_answer_tokens() generator**
```python
def _stream_answer_tokens(answer: str, batch_size: int = 3):
    """Yield tokens in word batches for responsive UI"""
    words = answer.split()
    for i in range(0, len(words), batch_size):
        batch = " ".join(words[i:i+batch_size])
        yield batch
```
- Purpose: Batch tokens for UI (3-word batches)
- Benefit: Balances streaming responsiveness with network chatter
- Location: ~line 150

6. **Modified: /ask-stream endpoint**
```python
@app.get("/ask-stream")
async def ask_stream(question: str):
    """Stream tokens as they're generated"""
    # Sends SSE events:
    # 1. {"type": "thinking", "message": "..."}
    # 2. {"type": "token", "content": "word_batch", "cumulative": "full_answer"}
    # 3. {"type": "source", "url": "...", "title": "..."}
    # 4. {"type": "complete", ..., "metadata": {...}}
    
    async def event_generator():
        # Run agent and yield events...
        for token_batch in _stream_answer_tokens(answer):
            yield f'data: {{"type": "token", "content": "{token_batch}"}}\n\n'
```
- Purpose: Stream tokens via HTTP Server-Sent Events
- Benefits: Real-time feedback, better perceived performance
- Event types: thinking, token, source, complete, error
- Location: ~line 250

7. **Modified: /ask endpoint**
```python
# Now returns metadata in response
{
    "answer": "...",
    "sources": [...],
    "metadata": {
        "model_used": "deepseek:deepseek-chat",
        "tokens": 245
    }
}
```
- Purpose: Include metadata even in non-streaming responses
- Backward compatible: Old client code still works

**Testing Impact:**
- Need tests for SSE event format
- Need tests for metadata extraction
- Need tests for graceful error handling in streaming

**Breaking Changes:** None (additive)

---

### ✅ PHASE 2: Model Fallback Chain

**Modified Files:**
- `backend/src/agent/main.py` (+150 lines)
- `backend/pyproject.toml` (1 new dependency)

**Changes:**

1. **New Environment Variables**
```bash
# In docker-compose.yml and .env
DEEPSEEK_API_KEY=sk_...       # Primary provider
GEMINI_API_KEY=...             # Fallback 1
GROK_API_KEY=...               # Fallback 2
```

2. **New: _get_llm_with_tools() function with fallback logic**
```python
def _get_llm_with_tools(provider: str = None, model: str = None):
    """Get LLM with tool binding, with fallback chain
    
    Order: DeepSeek → Gemini → Grok → Groq → OpenAI → Ollama
    """
    providers_to_try = PROVIDER_ORDER  # [deepseek, gemini, grok, groq, openai, ollama]
    
    for provider_name in providers_to_try:
        try:
            if provider_name == "deepseek":
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model="deepseek-chat",
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1"
                )
            elif provider_name == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-pro",
                    api_key=os.getenv("GEMINI_API_KEY")
                )
            # ... more providers ...
            return llm.bind_tools(tools)
        except Exception as e:
            logger.warning(f"Provider {provider_name} failed: {e}, trying next...")
            continue
    
    raise RuntimeError("All LLM providers failed")
```
- Purpose: Automatic fallback to next provider if primary fails
- Benefit: Resilient to provider outages
- Transparent: Client doesn't know which provider was used
- Location: ~line 100

3. **Modified: /config endpoint**
```python
@app.get("/config")
def get_config():
    return {
        "providers": [
            {"key": "deepseek", "label": "DeepSeek", "order": 1},
            {"key": "gemini", "label": "Gemini", "order": 2},
            {"key": "grok", "label": "Grok", "order": 3},
            {"key": "groq", "label": "Groq (Llama)", "order": 4},
            {"key": "openai", "label": "OpenAI", "order": 5},
            {"key": "llama", "label": "Llama (Local)", "order": 6},
        ],
        "models": {
            "deepseek": ["deepseek-chat", "deepseek-reasoner"],
            "gemini": ["gemini-pro", "gemini-pro-vision"],
            "grok": ["grok-beta"],
            # ...
        }
    }
```
- Purpose: Let frontend know all available providers
- Benefit: UI can show model options to user
- Location: ~line 350

4. **Updated Dependency: pyproject.toml**
```toml
# Added:
langchain-google-genai = ">= 1.0.0"
```
- Purpose: Support Google Gemini API
- Size: ~5 lines

**Testing Impact:**
- Need unit tests for each provider initialization
- Need tests for fallback order
- Need mock API responses for each provider
- Need negative tests (provider key missing, API down)

**Breaking Changes:** None (additive)

---

### ✅ PHASE 3: Auth Proxy Service (NEW)

**New Files:**
```
auth/
├── Dockerfile
├── pyproject.toml
├── README.md
└── src/
    ├── __init__.py
    └── main.py
```

**Changes:**

1. **New: auth/src/main.py (200 lines)**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime

class RateLimitState:
    """In-memory rate limiting state"""
    def __init__(self, key: str):
        self.key = key
        self.tokens_today = 0
        self.requests_today = 0
        self.last_reset = datetime.now().date()
    
    def is_limit_exceeded(self, tokens: int, requests: int = 1) -> bool:
        """Check if request exceeds daily limits"""
        today = datetime.now().date()
        if today > self.last_reset:
            self.tokens_today = 0
            self.requests_today = 0
            self.last_reset = today
        
        return (
            self.tokens_today + tokens > LIMIT_TOKENS_PER_DAY or
            self.requests_today + requests > LIMIT_REQUESTS_PER_HOUR
        )
    
    def track(self, tokens: int, requests: int = 1):
        """Record usage"""
        self.tokens_today += tokens
        self.requests_today += requests

app = FastAPI()

# CORS middleware
app.add_middleware(CORSMiddleware, ...)

# Rate limit storage (per API key)
rate_limits: dict[str, RateLimitState] = {}

@app.post("/validate-key")
async def validate_key(request: ValidateKeyRequest):
    """Validate API key format and existence"""
    api_key = request.api_key
    
    # Check format
    if not api_key.startswith("sk_"):
        return {"valid": False, "reason": "Invalid format"}
    
    # Could check Supabase database here
    return {"valid": True, "metadata": {...}}

@app.post("/track-usage")
async def track_usage(
    api_key: str = Header(..., alias="X-API-Key"),
    tokens: int = Query(0)
):
    """Track token usage"""
    if api_key not in rate_limits:
        rate_limits[api_key] = RateLimitState(api_key)
    
    state = rate_limits[api_key]
    if state.is_limit_exceeded(tokens):
        return {"status": "rejected", "reason": "Limit exceeded"}
    
    state.track(tokens)
    return {"status": "tracked", "tokens_today": state.tokens_today}

@app.get("/usage")
async def get_usage(api_key: str = Header(..., alias="X-API-Key")):
    """Get current usage statistics"""
    if api_key not in rate_limits:
        return {"tokens_today": 0, "requests_today": 0}
    
    state = rate_limits[api_key]
    return {
        "tokens_today": state.tokens_today,
        "tokens_limit": LIMIT_TOKENS_PER_DAY,
        "requests_today": state.requests_today,
        "requests_limit": LIMIT_REQUESTS_PER_HOUR,
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
```
- Purpose: Centralized API key validation and rate limiting
- Benefit: Decoupled from gateway; can scale independently
- Storage: In-memory (upgrade path: Redis)
- Location: All 200 lines

2. **New: auth/pyproject.toml**
```toml
[project]
name = "vecinita-auth"
version = "0.1.0"
dependencies = [
    "fastapi >= 0.104.0",
    "httpx >= 0.25.0",
    "uvicorn[standard] >= 0.24.0",
    "supabase >= 2.0.0",
]
```
- Purpose: Minimal dependencies (4 packages)
- Benefits: Fast startup, small container

3. **New: auth/Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -q -e .

# Copy source
COPY src/ ./src

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD curl -f http://localhost:8003/health || exit 1

EXPOSE 8003
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```
- Purpose: Production-ready container
- Features: Health check, minimal base image

4. **New: auth/README.md**
- Configuration guide
- API endpoint documentation
- Rate limit defaults
- Deployment instructions

**Testing Impact:**
- Need unit tests for RateLimitState
- Need tests for each endpoint
- Need negative tests (expired keys, limits exceeded)
- Need mock Supabase lookups

**Breaking Changes:** None (new service)

---

### ✅ PHASE 4: Gateway Enhancement

**New Files:**
- `backend/src/gateway/middleware.py` (200 lines)

**Modified Files:**
- `backend/src/gateway/main.py` (+20 lines)

**Changes:**

1. **New: backend/src/gateway/middleware.py**
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import httpx
import time

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Validates API keys via auth proxy"""
    
    def __init__(self, app: ASGIApp, auth_proxy_url: str):
        super().__init__(app)
        self.auth_proxy_url = auth_proxy_url
        self.client = None
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip public endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Extract API key
        auth_header = request.headers.get("authorization", "")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API key"}
            )
        
        api_key = auth_header.replace("Bearer ", "")
        
        # Validate via auth proxy
        try:
            if self.client is None:
                self.client = httpx.AsyncClient()
            
            response = await self.client.post(
                f"{self.auth_proxy_url}/validate-key",
                json={"api_key": api_key}
            )
            
            if not response.json().get("valid"):
                return JSONResponse(status_code=401, content={"error": "Invalid API key"})
        except Exception as e:
            # Fail open: if auth proxy down, continue
            logger.warning(f"Auth check failed: {e}, continuing...")
        
        # Call actual endpoint
        start = time.time()
        response = await call_next(request)
        
        # Add headers
        response.headers["X-API-Key-Masked"] = f"{api_key[:6]}...{api_key[-4:]}"
        response.headers["X-Request-Time"] = str(time.time() - start)
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Enforces rate limits per API key"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip public endpoints
        if request.url.path.startswith(("/health", "/docs")):
            return await call_next(request)
        
        # Get API key from auth header or query
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        
        if api_key:
            # Check rate limit (would call auth proxy or Redis)
            if is_rate_limited(api_key):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
        
        return await call_next(request)
```
- Purpose: Middleware for auth validation and rate limiting
- Location: New file, 200 lines

2. **Modified: backend/src/gateway/main.py**
```python
from .middleware import AuthenticationMiddleware, RateLimitingMiddleware

app = FastAPI()

# Add middleware (in order: auth first, then rate limiting)
app.add_middleware(
    RateLimitingMiddleware,
    tokens_per_day=int(os.getenv("RATE_LIMIT_TOKENS_PER_DAY", "1000"))
)
app.add_middleware(
    AuthenticationMiddleware,
    auth_proxy_url=os.getenv("AUTH_PROXY_URL", "http://localhost:8003")
)
```
- Purpose: Mount middleware on gateway
- Changes: ~10 lines

3. **Environment Variables Added**
```bash
AUTH_PROXY_URL=http://localhost:8003
ENABLE_AUTH=false  # Can disable in development
RATE_LIMIT_TOKENS_PER_DAY=1000
RATE_LIMIT_REQUESTS_PER_HOUR=100
```

**Testing Impact:**
- Need middleware unit tests
- Need integration tests with mock auth proxy
- Need negative tests (missing key, invalid key, rate limited)

**Breaking Changes:** None (feature flag: ENABLE_AUTH=false by default)

---

### ✅ PHASE 5: Frontend Updates

**Modified Files:**
- `frontend/src/app/types/agent.ts` (+30 lines)
- `frontend/src/app/hooks/useAgentChat.ts` (+50 lines)

**Changes:**

1. **Modified: frontend/src/app/types/agent.ts**
```typescript
// New event types for streaming

export interface StreamEventToken {
    type: "token";
    content: string;              // Individual word/subword
    cumulative: string;           // Full answer so far
}

export interface StreamEventSource {
    type: "source";
    url: string;
    title: string;
    source_type: "document" | "link" | "external";
}

export interface StreamEventComplete {
    type: "complete";
    answer: string;
    sources: SourceAttribution[];
    metadata: {
        model_used: string;       // e.g., "deepseek:deepseek-chat"
        tokens: number;           // Total tokens generated
    };
}

export interface StreamEventThinking {
    type: "thinking";
    message: string;              // Tool execution status
}

export interface StreamEventError {
    type: "error";
    message: string;
    error_code?: string;
}

// Updated union type
export type StreamEvent = 
    | StreamEventThinking
    | StreamEventToken
    | StreamEventSource
    | StreamEventComplete
    | StreamEventError;
```
- Purpose: TypeScript types for all SSE event types
- Changes: +30 lines

2. **Modified: frontend/src/app/hooks/useAgentChat.ts**
```typescript
export const useAgentChat = () => {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    
    const sendMessage = async (question: string) => {
        setIsLoading(true);
        let assistantContent = "";
        let sources: SourceAttribution[] = [];
        let metadata: any = null;
        
        try {
            const eventSource = new EventSource(
                `/ask-stream?question=${encodeURIComponent(question)}`
            );
            
            eventSource.addEventListener("message", (event) => {
                const data = JSON.parse(event.data) as StreamEvent;
                
                switch (data.type) {
                    case "thinking":
                        console.debug("Agent thinking:", data.message);
                        break;
                    
                    case "token":
                        // Accumulate tokens into full answer
                        assistantContent += data.content;
                        console.debug("Token received:", data.content);
                        
                        // Update UI with accumulated content
                        setMessages(prev => {
                            const updated = [...prev];
                            const lastMsg = updated[updated.length - 1];
                            if (lastMsg?.role === "assistant") {
                                lastMsg.content = assistantContent;
                            }
                            return updated;
                        });
                        break;
                    
                    case "source":
                        // Add source as discovered
                        sources.push({
                            url: data.url,
                            title: data.title,
                            type: data.source_type || "document"
                        });
                        console.debug("Source found:", data.url);
                        break;
                    
                    case "complete":
                        metadata = data.metadata;
                        console.debug("Streaming complete. Metadata:", metadata);
                        break;
                    
                    case "error":
                        console.error("Streaming error:", data.message);
                        break;
                }
            });
            
            eventSource.onerror = () => {
                eventSource.close();
                setIsLoading(false);
            };
        } catch (error) {
            console.error("Chat error:", error);
            setIsLoading(false);
        }
    };
    
    return { messages, sendMessage, isLoading };
};
```
- Purpose: Handle streaming events in React
- Changes: +50 lines

**Testing Impact:**
- Need React hook tests for token accumulation
- Need EventSource mock tests
- Need tests for metadata handling

**Breaking Changes:** None (additive)

---

### ✅ PHASE 6: RAG Tool Standardization

**Status:** ✅ Verified - No changes needed

**Finding:** All existing tools already use consistent response schema:
```typescript
{
    content: string,              // Document chunk or answer
    source_url: string,           // Where it came from
    similarity?: number,          // Vector similarity (0-1)
    chunk_index?: number,         // Position in doc
    metadata?: {                  // Additional context
        [key: string]: any
    }
}
```

**Existing Tools:**
1. `vector_search_tool` - Database vector similarity search
2. `web_search_tool` - Bing/Google web search
3. `static_response_tool` - Curated FAQ database
4. `clarification_tool` - Ask follow-up questions

All return standardized format with `(Fuente: URL)` attribution.

**No changes required** - Phase 6 validation complete.

---

### ✅ PHASE 7: Testing Strategy (IN PROGRESS)

**Status:** 🔄 Drafted - Implementation in progress

**Test Plan:**
```
tests/
├── conftest.py                      # Shared fixtures
├── integration/
│   ├── test_agent_streaming.py      # SSE format validation
│   ├── test_model_fallback.py       # Provider chain
│   ├── test_gateway_auth.py         # Middleware behavior
│   └── test_streaming_flow.py       # Full request cycle
├── unit/
│   ├── test_token_tracking.py       # Metadata extraction
│   └── test_auth_proxy.py           # Service endpoints
└── e2e/
    ├── test_full_chat.py            # Frontend → Agent
    └── test_streaming_ux.py         # Token accumulation
```

**Estimated:** 40-50 tests, ~3-4 hours to implement

---

### ✅ PHASE 8: Documentation (IN PROGRESS)

**Status:** 🔄 Mostly drafted - Finalizing

**New Documentation:**
1. ✅ This file (CHANGELOG.md)
2. ✅ Project status dashboard (PROJECT_STATUS.md)
3. ✅ Implementation summary (IMPLEMENTATION_2025_REPORT.md)
4. 🔄 Streaming implementation guide (to create)
5. 🔄 Model fallback reference (to create)

**Updated Files:**
- `.env.example` - Added new variables
- `docker-compose.yml` - Documented services
- `docs/API_INTEGRATION_SPEC.md` - New SSE format
- `docs/ARCHITECTURE_MICROSERVICE.md` - Auth proxy role

---

## Docker Compose Changes

**Modified: docker-compose.yml**

**Addition: auth-proxy service**
```yaml
auth-proxy:
  build:
    context: ./auth
    dockerfile: Dockerfile
  container_name: vecinita-auth-proxy
  ports:
    - "8003:8003"
  environment:
    PORT: "8003"
    SUPABASE_URL: "http://postgrest:3000"
    SUPABASE_KEY: "dev-anon-key"
    ENVIRONMENT: "development"
    RATE_LIMIT_TOKENS_PER_DAY: "10000"
    RATE_LIMIT_REQUESTS_PER_HOUR: "100"
  depends_on:
    postgres:
      condition: service_healthy
    postgrest:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
    interval: 30s
    timeout: 3s
    retries: 3
    start_period: 5s
```

**Updates: gateway service**
```yaml
environment:
  # ... existing ...
  AUTH_PROXY_URL: "http://auth-proxy:8003"
  ENABLE_AUTH: "false"
  DEEPSEEK_API_KEY: ""
  GEMINI_API_KEY: ""
  GROK_API_KEY: ""
  RATE_LIMIT_TOKENS_PER_DAY: "10000"
depends_on:
  auth-proxy:
    condition: service_healthy
```

**Updates: agent service**
```yaml
environment:
  # ... existing ...
  DEEPSEEK_API_KEY: ""
  GEMINI_API_KEY: ""
  GROK_API_KEY: ""
```

**No changes to:** PostgreSQL, PostgREST, Embedding service, Redis

---

## Dependencies Added

### Backend (backend/pyproject.toml)
```toml
langchain-google-genai = ">= 1.0.0"  # Google Gemini support
```

### Auth (auth/pyproject.toml)
```toml
# Initial set - no new dependencies within main stack
fastapi >= 0.104.0
httpx >= 0.25.0
uvicorn[standard] >= 0.24.0
```

### Frontend
No new dependencies (EventSource is native JavaScript)

---

## API Endpoints Changed/Added

### GET /ask-stream (MODIFIED)
**Before:** Returned binary streaming  
**After:** Returns Server-Sent Events with 5 event types

**Request:**
```
GET /ask-stream?question=What%20is%20Python%3F
Authorization: Bearer api_key_optional
```

**Response (SSE):**
```
data: {"type": "thinking", "message": "Searching..."}

data: {"type": "token", "content": "Python","cumulative": "Python"}

data: {"type": "token", "content": " is","cumulative": "Python is"}

data: {"type": "source", "url": "https://...", "title": "Python Docs"}

data: {"type": "complete", "answer": "Python is...", "sources": [...], "metadata": {"model_used": "deepseek:deepseek-chat", "tokens": 154}}
```

### GET /ask (MODIFIED)
**Before:**
```json
{
  "answer": "...",
  "sources": [...]
}
```

**After:**
```json
{
  "answer": "...",
  "sources": [...],
  "metadata": {
    "model_used": "deepseek:deepseek-chat",
    "tokens": 154
  }
}
```

### GET /config (MODIFIED)
**Before:** Listed only active providers  
**After:** Lists all 6 providers with ordering

```json
{
  "providers": [
    {"key": "deepseek", "label": "DeepSeek", "order": 1},
    {"key": "gemini", "label": "Gemini", "order": 2},
    ...
  ],
  "models": {...}
}
```

### POST /validate-key (NEW)
**Auth Proxy Service**

```
POST /validate-key
Content-Type: application/json

{"api_key": "sk_..."}

Response:
{"valid": true, "metadata": {...}}
```

### GET /usage (NEW)
**Auth Proxy Service**

```
GET /usage
Authorization: Bearer sk_...

Response:
{
  "tokens_today": 245,
  "tokens_limit": 1000,
  "requests_today": 12,
  "requests_limit": 100
}
```

### POST /track-usage (NEW)
**Auth Proxy Service**

```
POST /track-usage?tokens=50
Authorization: Bearer sk_...

Response:
{"status": "tracked", "tokens_today": 295}
```

---

## Configuration Changes

### New Environment Variables
```bash
# Multi-model support
DEEPSEEK_API_KEY=sk_...           # Primary
GEMINI_API_KEY=...                # Fallback 1
GROK_API_KEY=...                  # Fallback 2

# Auth proxy
AUTH_PROXY_URL=http://localhost:8003
ENABLE_AUTH=false

# Rate limiting (gateway)
RATE_LIMIT_TOKENS_PER_DAY=1000
RATE_LIMIT_REQUESTS_PER_HOUR=100

# Auth proxy service
PORT=8003
```

### Modified Environment Variables
None (all additive)

---

## Breaking Changes

**None** - This release is fully backward compatible.

- Old clients still work with `/ask` endpoint
- New streaming events are optional (client chooses SSE or JSON)
- Existing auth system still works (new auth is feature-gated)
- All new service ports are non-conflicting

---

## Migration Steps

### For Development
```bash
cd /root/GitHub/VECINA/vecinita

# 1. Update environment
cp .env.example .env  # Add new vars

# 2. Build new services
docker-compose build

# 3. Start all services
docker-compose up

# 4. Verify streaming works
curl http://localhost:8002/ask-stream?question=test
```

### For Production
1. Deploy auth-proxy service with Redis backend
2. Enable ENABLE_AUTH=true when ready
3. Add API key management system
4. Update monitoring for new service
5. Document rate limits for users

---

## File Changes Summary

**Files Created:** 7
- `auth/src/main.py` - Auth proxy server (200 lines)
- `auth/pyproject.toml` - Dependencies
- `auth/Dockerfile` - Container definition
- `auth/README.md` - Documentation
- `auth/src/__init__.py` - Package init
- `backend/src/gateway/middleware.py` - Auth + rate-limit middleware
- `docs/IMPLEMENTATION_2025_REPORT.md` - This summary

**Files Modified:** 5
- `backend/src/agent/main.py` - Streaming + fallback chain (+300 lines)
- `backend/src/gateway/main.py` - Middleware integration (+20 lines)
- `backend/pyproject.toml` - New dependency (+1 line)
- `frontend/src/app/types/agent.ts` - Event types (+30 lines)
- `frontend/src/app/hooks/useAgentChat.ts` - Event handling (+50 lines)
- `docker-compose.yml` - Auth proxy service (+50 lines)

**Total Changes:** 12 files, ~2500 lines added/modified

---

## Testing Checklist

Before this PR is considered complete:

- [ ] All Python files pass syntax check: `python3 -m py_compile`
- [ ] Docker compose builds: `docker-compose build`
- [ ] All services start: `docker-compose up`
- [ ] Streaming endpoint works: Manual curl test
- [ ] Auth proxy responds: Health check
- [ ] Model fallback logic: Test with API key missing
- [ ] Frontend builds: `npm run build`
- [ ] No TypeScript errors: `npx tsc --noEmit`
- [ ] Integration tests pass: `pytest tests/integration`
- [ ] E2E test: Full frontend → backend flow

---

## References

- Implementation Report: [IMPLEMENTATION_2025_REPORT.md](./IMPLEMENTATION_2025_REPORT.md)
- Project Status: [PROJECT_STATUS.md](./PROJECT_STATUS.md)
- Architecture Diagram: [ARCHITECTURE_MICROSERVICE.md](./ARCHITECTURE_MICROSERVICE.md)
- API Spec: [API_INTEGRATION_SPEC.md](./API_INTEGRATION_SPEC.md)

---

## Versioning

**Semantic Versioning:** 2025.02.0

- 2025: Year
- 02: Month (February)
- 0: Patch version (full release, not patch)

Next version: 2025.03.0 (March release)

---

**Generated:** 2026-02-08  
**Status:** Pre-Release (6/8 phases complete, ready for testing)
