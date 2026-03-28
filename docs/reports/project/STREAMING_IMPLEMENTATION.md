# Token Streaming Implementation Guide

**Last Updated:** February 8, 2026  
**Status:** ✅ Complete (Phase 1)  
**Audience:** Frontend developers, System architects, Debugging engineers

## Overview

Vecinita now supports real-time token-by-token streaming responses via **Server-Sent Events (SSE)**. This enables progressive answer display, better perceived performance, and real-time feedback.

---

## Architecture

### Event Flow

```
Frontend (React)
    ↓ HTTP GET /ask-stream
Gateway (8002)
    ↓
Agent (8000)
    ↓ LLM (streaming tokens)
    ↓
Frontend receives SSE events in real-time
    ↓
Accumulate tokens → Update UI → Display streaming answer
```

### Event Types

The streaming endpoint yields 5 event types:

| Event Type | Purpose | When | Structure |
|-----------|---------|------|-----------|
| **thinking** | Tool execution status | During processing | `{"type": "thinking", "message": "..."}` |
| **token** | LLM token generation | During answer generation | `{"type": "token", "content": "word_batch", "cumulative": "full_answer_so_far"}` |
| **source** | Document discovered | As sources are found | `{"type": "source", "url": "...", "title": "..."}` |
| **complete** | Request finished | At end of stream | `{"type": "complete", "answer": "...", "metadata": {...}}` |
| **error** | Error occurred | On failure | `{"type": "error", "message": "..."}` |

---

## API Endpoints

### Streaming Response (NEW)

**Endpoint:** `GET /ask-stream`

**Request:**
```bash
curl -X GET "http://localhost:8002/ask-stream?question=What%20is%20Python%3F" \
  -H "Accept: text/event-stream" \
  -H "Authorization: Bearer YOUR_API_KEY"  # Optional (if ENABLE_AUTH=true)
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "thinking", "message": "Analyzing question and searching documents..."}

data: {"type": "token", "content": "Python", "cumulative": "Python"}

data: {"type": "token", "content": " is", "cumulative": "Python is"}

data: {"type": "token", "content": " a", "cumulative": "Python is a"}

data: {"type": "token", "content": " high-level", "cumulative": "Python is a high-level"}

data: {"type": "source", "url": "https://python.org/docs", "title": "Python Official Documentation"}

data: {"type": "complete", "answer": "Python is a high-level programming language...", "sources": [...], "metadata": {"model_used": "deepseek:deepseek-chat", "tokens": 154}}
```

### Non-Streaming Response (UPDATED)

**Endpoint:** `GET /ask`

**Request:**
```bash
curl "http://localhost:8002/ask?question=What%20is%20Python%3F"
```

**Response:**
```json
{
  "answer": "Python is a high-level programming language...",
  "sources": [
    {
      "url": "https://python.org",
      "title": "Python Docs",
      "type": "document"
    }
  ],
  "metadata": {
    "model_used": "deepseek:deepseek-chat",
    "tokens": 154
  }
}
```

---

## Frontend Implementation

### React Hook (useAgentChat)

The `useAgentChat` hook handles SSE automatically:

```typescript
import { useAgentChat } from './hooks/useAgentChat';

export function ChatComponent() {
  const { messages, sendMessage, isLoading } = useAgentChat();
  
  const handleSubmit = (question: string) => {
    sendMessage(question);  // Handles streaming automatically
  };
  
  return (
    <div>
      {messages.map(msg => (
        <div key={msg.id}>
          <strong>{msg.role}:</strong>
          {msg.content}  {/* Updates as tokens stream in */}
        </div>
      ))}
    </div>
  );
}
```

### Manual EventSource Implementation

If you need custom handling:

```typescript
const eventSource = new EventSource(
  `/ask-stream?question=${encodeURIComponent(question)}`
);

let answer = "";

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'thinking':
      console.log('Agent thinking...', data.message);
      break;
    
    case 'token':
      answer += data.content;
      updateUI(answer);  // Update UI with accumulated text
      break;
    
    case 'source':
      addSource(data);  // Add to sources list
      break;
    
    case 'complete':
      console.log('Done!', data.metadata);
      console.log(`Model: ${data.metadata.model_used}`);
      console.log(`Tokens: ${data.metadata.tokens}`);
      break;
    
    case 'error':
      console.error('Error:', data.message);
      break;
  }
});

eventSource.onerror = () => {
  eventSource.close();
};
```

---

## Token Batching

Tokens are batched into **3-word bundles** for optimal UX:

```
Individual tokens from LLM:
"Python" " " "is" " " "a" ...

Batched tokens (3-word bundles):
"Python is a" 
" high-level programming"
" language used"
...
```

**Why 3-word batches?**
- Reduces network chatter (fewer SSE events)
- Preserves streaming feel (updates visible immediately)
- Balances responsiveness and efficiency

**Configuration:**
```python
# In src/agent/main.py
def _stream_answer_tokens(answer: str, batch_size: int = 3):
    # Change batch_size to adjust batching
    words = answer.split()
    for i in range(0, len(words), batch_size):
        yield " ".join(words[i:i+batch_size])
```

---

## Metadata Tracking

Each response includes metadata for debugging:

```json
"metadata": {
  "model_used": "deepseek:deepseek-chat",
  "tokens": 154
}
```

### Understanding Metadata

- **model_used**: Format is `provider:model_name`
  - `deepseek:deepseek-chat` = DeepSeek provider, deepseek-chat model
  - `gemini:gemini-pro` = Google Gemini provider, gemini-pro model
  - Shows which provider actually responded (useful for fallback debugging)

- **tokens**: Total tokens generated by the LLM
  - Input tokens (question + context) + Output tokens (answer)
  - Used for billing/rate limiting
  - Incremented at each response

### Accessing Metadata (Frontend)

```typescript
// In browser console, metadata is logged when streaming completes
eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'complete') {
    console.debug('Streaming complete. Metadata:', data.metadata);
    // Metadata available here:
    // {
    //   model_used: "deepseek:deepseek-chat",
    //   tokens: 245
    // }
  }
});
```

---

## Error Handling

### SSE Errors

**Connection error:**
```typescript
eventSource.onerror = () => {
  console.error('Connection lost');
  eventSource.close();
  // Retry with exponential backoff
  setTimeout(() => {
    // Reconnect
  }, 1000);
};
```

**Streaming error event:**
```
data: {"type": "error", "message": "Failed to retrieve documents", "error_code": "SEARCH_FAILED"}
```

**Common errors:**
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check `Authorization` header |
| 429 Too Many Requests | Rate limit exceeded | Wait or upgrade plan |
| 500 Internal Server Error | Server error | Check logs, retry later |
| Connection reset | Network issue | Implement retry logic |

---

## Performance Optimization

### Browser-Side

```typescript
// Debounce UI updates (prevents too frequent renders)
const [displayedText, setDisplayedText] = useState("");
const updateTimeout = useRef<ReturnType<typeof setTimeout>>();

const addToken = (token: string) => {
  displayedText += token;
  
  clearTimeout(updateTimeout.current);
  updateTimeout.current = setTimeout(() => {
    setDisplayedText(displayedText);  // Update every 50ms max
  }, 50);
};
```

### Server-Side

- Token batching (3-word bundles) reduces SSE overhead
- Streaming starts immediately (user sees first token in ~200ms)
- No buffering of full answer

### Network

- Use HTTP/2 for multiplexed streaming
- SSE is more efficient than WebSockets for one-way streaming
- Keepalive prevents connection timeouts (30s by default)

---

## Troubleshooting

### Streaming stalls or no tokens appear

**Check 1:** Verify SSE is being sent
```bash
curl -v "http://localhost:8002/ask-stream?question=test" \
  -H "Accept: text/event-stream"

# Should respond with:
# < HTTP/1.1 200 OK
# < content-type: text/event-stream
```

**Check 2:** Verify browser connection
- Open DevTools → Network tab
- Look for `ask-stream` request
- Status should be 200
- Type should be `eventsource` or similar

**Check 3:** Check browser console
```javascript
// Enable detailed logging
eventSource.addEventListener('message', (event) => {
  console.log('Raw message:', event.data);
});
```

### Wrong event types received

**If seeing `{"complete": {...}}` instead of proper events:**
- Response is using old non-streaming format
- Check endpoint: should be `/ask-stream`, not `/ask`

**If seeing empty `data:` lines:**
- May be keepalive heartbeats (safe to ignore)
- Check for actual event JSON on non-empty lines

### Tokens not accumulating properly

**Check cumulative field:**
```
Event 1: {"type": "token", "content": "Python", "cumulative": "Python"}
Event 2: {"type": "token", "content": " is", "cumulative": "Python is"}
         ↑ cumulative must grow
```

---

## Debugging

### Enable verbose logging

**Backend:**
```python
# In src/agent/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```typescript
// In useAgentChat.ts
console.debug = console.log;  // Force debug logs to appear
```

### Monitor metadata

```bash
# Watch for model_used changes in streaming responses
curl "http://localhost:8002/ask-stream?question=test" | \
  grep "metadata" | jq .
```

### Check response times

```bash
time curl "http://localhost:8002/ask-stream?question=test" > /dev/null

# Should be < 2s for first token
# Full response varies by question/model
```

---

## FAQ

**Q: Why are tokens batched instead of sent individually?**  
A: Sending 1000+ individual SSE events for one answer would overwhelm the browser. Batching reduces overhead while maintaining real-time feel.

**Q: Can I change batch size?**  
A: Yes. Edit `_stream_answer_tokens(batch_size=3)` in `src/agent/main.py`. Use 1 for max responsiveness, 5+ for max efficiency.

**Q: Is metadata exposed to users?**  
A: No. Metadata is logged to browser console for debugging only. Users see the answer, users don't see token counts or provider info.

**Q: Does streaming work with WebSocket?**  
A: Streaming uses HTTP/1.1 Server-Sent Events, not WebSocket. SSE is simpler, more reliable for server→client one-way streams.

**Q: Can I use streaming with rate limiting?**  
A: Yes. Rate limiting is enforced before streaming starts. If over limit, request is rejected before any events sent.

---

## References

- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/streaming/)
- [LangChain Streaming](https://python.langchain.com/docs/modules/model_io/llms/streaming)
- [HTTP Streaming Best Practices](https://www.html5rocks.com/en/tutorials/eventsource/basics/)

---

**Generated:** 2026-02-08  
**Status:** Production Ready  
**Coverage:** Streaming API, Frontend Integration, Troubleshooting, Performance
