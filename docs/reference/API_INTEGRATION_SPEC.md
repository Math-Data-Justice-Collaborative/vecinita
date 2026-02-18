# API Integration Specification for New Frontend

## Overview
The new frontend must maintain exact API compatibility with the current backend while implementing real API calls instead of mock responses.

---

## Endpoint 1: GET /config

### Purpose
Discover available LLM providers and models at runtime. Allows backend to dynamically expose different models without frontend changes.

### URL
```
http://localhost:8000/config (dev)
https://vecinita-agent.onrender.com/config (production)
```

### HTTP Method
`GET`

### Query Parameters
None

### Request Headers
No special headers required. May benefit from `Accept: application/json`.

### Response Format
```json
{
  "providers": [
    {
      "key": "deepseek",
      "label": "DeepSeek"
    },
    {
      "key": "llama",
      "label": "Llama"
    },
    {
      "key": "openai",
      "label": "OpenAI"
    }
  ],
  "models": {
    "deepseek": [
      "deepseek-chat",
      "deepseek-reasoner"
    ],
    "llama": [
      "llama3.2"
    ],
    "openai": [
      "gpt-4o-mini"
    ]
  }
}
```

### Response Status Codes
- **200 OK**: Successfully returned provider and model configuration
- **500 Internal Server Error**: Backend configuration error
- **503 Service Unavailable**: Backend service not available

### Error Response
```json
{
  "detail": "Error message describing the issue"
}
```

### Example Implementation (TypeScript)
```typescript
interface Provider {
  key: string;
  label: string;
}

interface Config {
  providers: Provider[];
  models: {
    [key: string]: string[];
  };
}

async function loadConfig(backendUrl: string): Promise<Config | null> {
  try {
    const response = await fetch(`${backendUrl}/config`);
    if (!response.ok) {
      console.error(`Config fetch failed: ${response.status}`);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to load config:', error);
    return null;
  }
}
```

### Caching Strategy
- Call on component mount (once per session)
- Cache result in state
- Optionally: Cache in localStorage with 1-hour TTL
- Fallback to hardcoded defaults if fetch fails

### Current Frontend Implementation
```javascript
// ChatWidget.jsx - Line 122
const res = await fetch(`${base}/config`)
if (!res?.ok) return
const data = await res.json()
const providers = Array.isArray(data?.providers) ? data.providers : null
const models = typeof data?.models === 'object' && data.models ? data.models : null
if (providers && models) {
  setProvidersOptions(providers)
  setModelOptionsMap(models)
  // Auto-select provider with fallback priority: deepseek > llama > openai
  const priority = ['deepseek', 'llama', 'openai']
  let selectedProvider = priority.find(p => providers.some(prov => prov.key === p))
  // ... set provider and model
}
```

---

## Endpoint 2: GET /ask-stream

### Purpose
Primary Q&A endpoint that streams responses using Server-Sent Events (SSE). Supports multi-turn conversations via thread IDs, language detection, and provider/model selection.

### URL
```
http://localhost:8000/ask-stream (dev)
https://vecinita-agent.onrender.com/ask-stream (production)
```

### HTTP Method
`GET`

### Query Parameters

#### Required
| Parameter | Type | Max Length | Description | Example |
|-----------|------|-----------|-------------|---------|
| `query` | string | 2000 | User question (must be URL-encoded) | `query=What%20is%20water%20quality` |
| `provider` | string | - | LLM provider key | `provider=deepseek` |
| `model` | string | - | Model name for the provider | `model=deepseek-chat` |

#### Optional
| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `lang` | string | Auto-detect | Language code ('en' or 'es') | `lang=es` |
| `thread_id` | string | - | Session UUID for context persistence | `thread_id=550e8400-e29b-41d4-a716-446655440000` |

### Full URL Examples

**Minimal Request**:
```
GET /ask-stream?query=Hello&provider=llama&model=llama3.2
```

**Full Request**:
```
GET /ask-stream?query=What%20resources%20help%20with%20water%20quality&provider=deepseek&model=deepseek-chat&lang=es&thread_id=550e8400-e29b-41d4-a716-446655440000
```

### Request Headers
```
Accept: text/event-stream
```

### Response Format
**Content-Type**: `text/event-stream` (Server-Sent Events)

**Format**: Each event is a line starting with `data: ` followed by JSON

```
data: {"type":"thinking","message":"Analyzing water quality concerns..."}
data: {"type":"thinking","message":"Searching for relevant resources..."}
data: {"type":"complete","answer":"Water quality...","sources":[...],"plan":"..."}
```

### Message Types

#### Type: "thinking"
Agent's reasoning process (can occur multiple times)
```json
{
  "type": "thinking",
  "message": "String describing what the agent is thinking"
}
```

#### Type: "complete"
Final answer with sources and planning
```json
{
  "type": "complete",
  "answer": "The answer text with full response",
  "sources": [
    {
      "title": "Water Quality Standards - EPA",
      "url": "https://www.epa.gov/wqs-tech",
      "snippet": "Information about water quality standards and regulations."
    }
  ],
  "plan": "Optional: Agent's planning/reasoning summary"
}
```

#### Type: "clarification"
Agent needs more information from user
```json
{
  "type": "clarification",
  "context": "I need more details to help you better",
  "questions": [
    "What geographic area are you asking about?",
    "Are you concerned about specific water sources?"
  ]
}
```

#### Type: "error"
Error during processing
```json
{
  "type": "error",
  "message": "Error description"
}
```

### Response Status Codes
- **200 OK**: Successfully opened SSE stream
- **400 Bad Request**: Invalid query parameters (e.g., missing required params, invalid provider/model)
- **401 Unauthorized**: Authentication failed (if applicable)
- **500 Internal Server Error**: Backend processing error
- **503 Service Unavailable**: LLM service unavailable

### Error Response (Non-200 Status)
```json
{
  "detail": "Error description"
}
```

### Example Implementation (TypeScript)

```typescript
interface ThinkingMessage {
  type: 'thinking';
  message: string;
}

interface CompleteMessage {
  type: 'complete';
  answer: string;
  sources: Source[];
  plan?: string;
}

interface ClarificationMessage {
  type: 'clarification';
  context: string;
  questions: string[];
}

interface ErrorMessage {
  type: 'error';
  message: string;
}

type StreamMessage = ThinkingMessage | CompleteMessage | ClarificationMessage | ErrorMessage;

interface Source {
  title: string;
  url: string;
  snippet: string;
}

async function askStream(
  backendUrl: string,
  query: string,
  provider: string,
  model: string,
  lang?: string,
  threadId?: string
): Promise<void> {
  const urlBase = backendUrl || '/api';
  const langParam = lang ? `&lang=${lang}` : '';
  const threadParam = threadId ? `&thread_id=${encodeURIComponent(threadId)}` : '';
  
  const streamUrl = `${urlBase}/ask-stream?query=${encodeURIComponent(query)}${langParam}&provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}${threadParam}`;
  
  try {
    const response = await fetch(streamUrl);
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      
      // Keep last incomplete line in buffer
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6); // Remove 'data: ' prefix
            const message: StreamMessage = JSON.parse(jsonStr);
            
            switch (message.type) {
              case 'thinking':
                console.log('Agent thinking:', message.message);
                // Update UI to show thinking process
                break;
              case 'complete':
                console.log('Answer:', message.answer);
                console.log('Sources:', message.sources);
                // Update UI with final answer
                break;
              case 'clarification':
                console.log('Needs clarification:', message.questions);
                // Prompt user for clarification
                break;
              case 'error':
                console.error('Stream error:', message.message);
                throw new Error(message.message);
            }
          } catch (e) {
            if (e instanceof SyntaxError) {
              console.warn('Malformed JSON in stream:', line);
              continue;
            }
            throw e;
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream request failed:', error);
    throw error;
  }
}
```

### Current Frontend Implementation Reference
```javascript
// ChatWidget.jsx - Line 184-240
const streamUrl = `${urlBase}/ask-stream?query=${encodeURIComponent(q)}${langParam}&provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}&thread_id=${encodeURIComponent(thread)}`

const res = await fetch(streamUrl)
if (!res.ok) throw new Error(`Backend error: ${res.status}`)

const reader = res.body.getReader()
const decoder = new TextDecoder()
let assistantMessage = null
let sources = []
let plan = ''

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const chunk = decoder.decode(value, { stream: true })
  const lines = chunk.split('\n')
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        const jsonStr = line.slice(6)
        const update = JSON.parse(jsonStr)
        
        if (update.type === 'thinking') {
          setThinkingMessages(prev => [...prev, { message: update.message, timestamp: Date.now() }])
        } else if (update.type === 'complete') {
          assistantMessage = update.answer
          sources = update.sources || []
          plan = update.plan || ''
          setThinkingMessages([])
        } else if (update.type === 'clarification') {
          // Handle clarification requests
        } else if (update.type === 'error') {
          throw new Error(update.message)
        }
      } catch (e) {
        if (e instanceof SyntaxError) continue
        throw e
      }
    }
  }
}
```

---

## Session Management: Thread IDs

### Purpose
Enable multi-turn conversations with context persistence across requests.

### Thread ID Format
- **Preferred**: UUID v4 (128-bit, RFC 4122)
- **Fallback**: `thread-{timestamp}-{random}` format
  - Example: `thread-1705088400000-567890`

### Storage
**Local Storage Key**: `vecinita_thread_id`

### Lifecycle
1. **Generation**: Create on first message
2. **Persistence**: Store in localStorage
3. **Reuse**: Retrieve and use for subsequent messages
4. **Reset**: Generate new ID for "New Chat" action

### Implementation Example
```typescript
let threadId: string | null = null;

// Initialize or retrieve thread ID
function initializeThread(): void {
  try {
    const stored = localStorage.getItem('vecinita_thread_id');
    threadId = stored || generateThreadId();
    if (!stored) {
      localStorage.setItem('vecinita_thread_id', threadId);
    }
  } catch (e) {
    // Fallback if localStorage unavailable
    threadId = generateThreadId();
  }
}

function generateThreadId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return `thread-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
}

function resetThread(): void {
  threadId = generateThreadId();
  try {
    localStorage.setItem('vecinita_thread_id', threadId);
  } catch (e) {
    // Ignore localStorage errors
  }
}
```

---

## Error Handling Strategy

### Network Errors
```typescript
try {
  const response = await fetch(streamUrl);
  // ...
} catch (error) {
  if (error instanceof TypeError) {
    // Network error
    showError('Unable to reach the server. Check your connection.');
  } else {
    showError('An unexpected error occurred.');
  }
}
```

### HTTP Errors
```typescript
if (!response.ok) {
  const errorData = await response.json().catch(() => ({}));
  const message = errorData.detail || `Server error: ${response.status}`;
  throw new Error(message);
}
```

### Streaming Errors
- **Mid-stream connection loss**: SSE will close reader
- **Malformed JSON**: Skip line and continue
- **Error message type**: Thrown as exception, caught and displayed

### User Feedback
- **Loading state**: Show spinner while waiting
- **Error messages**: Display in chat
- **Retry**: Allow user to resend message
- **Timeout**: Consider 30-second timeout for hanging requests

---

## Development Workflow: Proxy Configuration

### Local Development (Vite Dev Server)
Frontend runs on port 5173, backend on port 8000. Need proxy to avoid CORS issues.

### vite.config.ts Configuration
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    },
    '/config': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

### Usage in Frontend Code
```typescript
// Development: Use /api prefix (proxied to backend)
const baseUrl = import.meta.env.VITE_BACKEND_URL || '/api';

// Production: Use full URL (baked into bundle during build)
const streamUrl = `${baseUrl}/ask-stream?query=...`;
```

### Build-Time Configuration
**Dockerfile**:
```dockerfile
ARG VITE_BACKEND_URL=https://vecinita-agent.onrender.com
RUN VITE_BACKEND_URL=${VITE_BACKEND_URL} npm run build
```

This embeds the backend URL directly into the production JavaScript bundle.

---

## Testing the API Integration

### 1. Test /config Endpoint
```bash
curl http://localhost:8000/config
```

Expected output:
```json
{
  "providers": [...],
  "models": {...}
}
```

### 2. Test /ask-stream Endpoint
```bash
curl "http://localhost:8000/ask-stream?query=Hello&provider=llama&model=llama3.2"
```

Expected output (SSE format):
```
data: {"type":"thinking","message":"..."}
data: {"type":"complete","answer":"...","sources":[...],"plan":""}
```

### 3. Test with Language Parameter
```bash
curl "http://localhost:8000/ask-stream?query=Hola&provider=llama&model=llama3.2&lang=es"
```

### 4. Test with Thread ID
```bash
curl "http://localhost:8000/ask-stream?query=What%20about%20water?&provider=llama&model=llama3.2&thread_id=550e8400-e29b-41d4-a716-446655440000"
```

---

## Performance Considerations

### Streaming Optimization
- Stream enables incremental rendering (thinking messages display as they arrive)
- Prevents long loading waits for large responses
- Better UX than waiting for complete response

### Caching
- **Config endpoint**: Cache result (5 min TTL) to reduce requests
- **Thread IDs**: Persist in localStorage for session continuity
- **Responses**: Don't cache - each query may have different answers

### Timeout Handling
```typescript
// Add timeout to streaming requests
const abortController = new AbortController();
const timeoutId = setTimeout(() => abortController.abort(), 30000); // 30s timeout

try {
  const response = await fetch(streamUrl, { signal: abortController.signal });
  // ...
} catch (error) {
  if (error.name === 'AbortError') {
    showError('Request timed out. Please try again.');
  }
} finally {
  clearTimeout(timeoutId);
}
```

---

## Backward Compatibility

### Current Frontend Uses:
- `/ask-stream` with provider/model parameters ✅
- Thread IDs via `thread_id` parameter ✅
- Language detection via `lang` parameter ✅
- `/config` endpoint for provider discovery ✅
- SSE format with thinking/complete/error messages ✅

### Migration Path
1. **Zero-breaking changes** if backend maintains current API
2. **Deprecate old endpoints** before removing (6+ month notice)
3. **Version endpoints** if major changes needed (`/v2/ask-stream`)
4. **Document breaking changes** clearly

---

## Security Considerations

### Input Validation (Frontend)
```typescript
const MAX_QUERY_LENGTH = 2000;
if (query.length > MAX_QUERY_LENGTH) {
  throw new Error(`Query too long (max ${MAX_QUERY_LENGTH} chars)`);
}

// Ensure provider/model are from /config response
if (!availableProviders.includes(provider)) {
  throw new Error('Invalid provider');
}
```

### CORS Headers (Backend Required)
```python
# FastAPI should include:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### No Authentication Currently
- Endpoints are public
- If auth needed later: Add Authorization header support
- Consider rate limiting on backend

---

## Summary Checklist for New Frontend

- [ ] Remove mock `getMockResponse()` logic
- [ ] Implement real `/config` endpoint call on mount
- [ ] Implement real `/ask-stream` SSE parsing
- [ ] Add dev server proxy configuration
- [ ] Implement thread ID generation and persistence
- [ ] Add input validation (max 2000 chars)
- [ ] Handle all message types (thinking, complete, clarification, error)
- [ ] Add timeout handling for hanging requests
- [ ] Implement error recovery and user feedback
- [ ] Test with real backend responses
- [ ] Verify provider/model selection flow
- [ ] Test language detection and switching
- [ ] Validate streaming with slow/interrupted connections
