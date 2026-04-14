# Model Fallback Chain Implementation Guide

**Last Updated:** February 8, 2026  
**Status:** ✅ Complete (Phase 2)  
**Audience:** Ops engineers, System architects, Developers

## Overview

Vecinita implements **automatic multi-model fallback** to ensure resilience. If one LLM provider is unavailable, the system automatically tries the next in the priority chain.

---

## Fallback Chain Priority

The system tries providers in this order. First available provider is used.

```
1️⃣  DeepSeek (Primary)
    ↓ If DeepSeek API key missing or down
2️⃣  Gemini (Fallback 1)
    ↓ If Gemini API key missing or down
3️⃣  Grok (Fallback 2)
    ↓ If Grok API key missing or down
4️⃣  Groq/Llama (Fallback 3)
    ↓ If Groq API key missing or down
5️⃣  OpenAI (Fallback 4)
    ↓ If OpenAI API key missing or down
6️⃣  Ollama (Fallback 5 - Local, Always Available)
```

---

## Provider Configuration

### Environment Variables

Each provider requires one environment variable:

| Provider | Environment Variable | API Key Format | Get Key From |
|----------|----------------------|-----------------|--------------|
| DeepSeek | `DEEPSEEK_API_KEY` | `sk_...` | https://platform.deepseek.com |
| Gemini | `GEMINI_API_KEY` | `AIzaSy...` | https://ai.google.dev |
| Grok | `GROK_API_KEY` | `xai_...` | https://api.x.ai |
| Groq | `GROQ_API_KEY` | `gsk_...` | https://console.groq.com |
| OpenAI | `OPENAI_API_KEY` | `sk-...` | https://platform.openai.com |
| Ollama | `OLLAMA_BASE_URL` | (local) | http://localhost:11434 (self-hosted) |

### Example .env Configuration

```bash
# Full fallback chain configured
DEEPSEEK_API_KEY=sk_xxxxxxxxxxx          # Try first
GEMINI_API_KEY=AIzaSy_xxxxxxxxxxx        # Try second
GROK_API_KEY=xai_xxxxxxxxxxx             # Try third
GROQ_API_KEY=gsk_xxxxxxxxxxx             # Try fourth
OPENAI_API_KEY=sk-xxxxxxxxxxx            # Try fifth
OLLAMA_BASE_URL=http://localhost:11434   # Try sixth (local)
```

### Minimal Configuration

If budget-conscious, you can use just free/cheap providers:

```bash
# Free tier setup (Groq only)
GROQ_API_KEY=gsk_free_tier_key           # Free with rate limits
OLLAMA_BASE_URL=http://localhost:11434   # Local fallback (free)
```

---

## Models Supported by Each Provider

### DeepSeek
- `deepseek-chat` (primary)
- `deepseek-reasoner` (extended thinking)

### Google Gemini
- `gemini-pro` (text generation)
- `gemini-pro-vision` (image understanding)

### xAI Grok
- `grok-beta` (latest version)

### Groq (Llama)
- `llama-3.1-8b` (free, fast)
- `llama-3.1-70b` (higher quality, slower)
- `mixtral-8x7b` (mixture of experts)

### OpenAI
- `gpt-4o-mini` (fallback choice - economical)
- `gpt-4o` (high quality, expensive)
- `gpt-3.5-turbo` (legacy, very fast)

### Ollama (Local)
- `gemma3` (Vecinita default when `OLLAMA_MODEL` is unset; Gemma 3 via Ollama)
- `llama3.2` (fast alternative)
- `mistral` (high quality)
- `neural-chat` (specialized for chat)

---

## How Fallback Works

### Automatic Selection

When the agent processes a question:

```python
# In src/agent/main.py - _get_llm_with_tools()

# Try in order
for provider in ["deepseek", "gemini", "grok", "groq", "openai", "ollama"]:
    try:
        llm = initialize_provider(provider)  # Try to create client
        return llm.bind_tools(tools)         # If successful, return
    except Exception as e:
        logger.warning(f"Provider {provider} failed: {e}")
        continue  # Try next
```

### Selection Logging

Track which provider is used:

```bash
# Watch logs to see provider selection
docker-compose logs agent | grep "model_used\|Trying provider"

# Examples:
# INFO - Trying provider: deepseek
# INFO - DeepSeek initialized successfully
# INFO - model_used: deepseek:deepseek-chat
```

### Metadata in Response

Response includes which provider was used:

```json
{
  "answer": "...",
  "metadata": {
    "model_used": "deepseek:deepseek-chat",  ← Which provider
    "tokens": 245
  }
}
```

---

## Configuration Scenarios

### Scenario 1: Full Resilience (Recommended for Production)

**Goal:** Maximum uptime, try all providers

```bash
# .env configuration
DEEPSEEK_API_KEY=sk_...      # Primary (cheapest)
GEMINI_API_KEY=AIzaSy_...    # Fallback (Google)
GROK_API_KEY=xai_...         # Fallback (xAI)
GROQ_API_KEY=gsk_...         # Fallback (free tier)
OPENAI_API_KEY=sk_...        # Fallback (premium)
OLLAMA_BASE_URL=...          # Always available locally
```

**Effects:**
- ✅ If DeepSeek down → automatic switch to Gemini
- ✅ If multiple providers down → keeps trying until finds one
- ✅ If all cloud providers down → falls back to local Ollama
- ✅ Users experience uninterrupted service

---

### Scenario 2: Cost-Optimized (Small Budget)

**Goal:** Minimize API costs

```bash
# .env configuration
GROQ_API_KEY=gsk_...         # Free tier (rate-limited)
OLLAMA_BASE_URL=...          # Local fallback (free)

# NOT SET (skipped, cheaper):
# DEEPSEEK_API_KEY
# GEMINI_API_KEY
# GROK_API_KEY
# OPENAI_API_KEY
```

**Effects:**
- ✅ Uses free Groq API until rate limit hit
- ✅ Falls back to local Ollama when rate limited
- ✅ Zero cloud costs if Ollama is available
- ⚠️ Lower quality if Groq rate limit exceeded

---

### Scenario 3: Quality-First (Premium)

**Goal:** Best possible answer quality

```bash
# .env configuration - Set models in _get_llm_with_tools()
DEEPSEEK_API_KEY=sk_...         # DeepSeek Reasoner (best thinking)
OPENAI_API_KEY=sk_...           # GPT-4o (high quality)
GROQ_API_KEY=gsk_...            # Llama 70b (good quality)

# Priority order (code):
providers_to_try = [
    "deepseek",  # Try reasoning first
    "openai",    # Try GPT-4o
    "groq"       # Try Llama 70b
]
```

**Effects:**
- ✅ Primary answers from best reasoning (Deepseek Reasoner)
- ✅ Falls back to world's top LLM (GPT-4o) if needed
- ✅ Never degrades to cheap models
- ⚠️ Significantly higher costs

---

## Monitoring & Debugging

### Check Available Providers

**Request to /config endpoint:**

```bash
curl http://localhost:8002/config | jq '.providers'

# Response showing all available providers:
[
  {
    "key": "deepseek",
    "label": "DeepSeek",
    "order": 1
  },
  {
    "key": "gemini",
    "label": "Gemini",
    "order": 2
  },
  ...
]
```

### See Which Provider Was Used

**In response metadata:**

```bash
curl "http://localhost:8002/ask?question=test" | jq '.metadata.model_used'

# Output: "deepseek:deepseek-chat"
# Or: "groq:llama-3.1-8b" (if deepseek was down)
```

### Monitor Provider Changes

**Watch logs for fallback events:**

```bash
# Watch real-time logs
docker-compose logs -f agent | grep "provider\|fallback\|initialized"

# Sample output:
# INFO - Trying provider: deepseek
# INFO - DeepSeek initialized successfully
# (Next request after DeepSeek goes down)
# INFO - Trying provider: deepseek
# WARNING - DeepSeek failed: connection timeout
# INFO - Trying provider: gemini
# INFO - Gemini initialized successfully
```

### Test Provider Fallback

**Simulate DeepSeek failure:**

```bash
# Unset DeepSeek key to trigger fallback
unset DEEPSEEK_API_KEY
docker-compose restart agent

# Next request should use Gemini
curl "http://localhost:8002/ask?question=test" | jq '.metadata.model_used'
# Output: "gemini:gemini-pro"
```

---

## Performance Characteristics

### Response Times by Provider

| Provider | Time to First Token | Quality | Cost |
|----------|-------------------|---------|------|
| DeepSeek | ~400ms | Very Good | $ |
| Gemini | ~300ms | Good | $/mo |
| Grok | ~500ms | Good | $ |
| Groq | ~200ms | Good (8B) | Free |
| OpenAI | ~600ms | Excellent | $$$ |
| Ollama | ~100ms | Fair | Free (self-hosted) |

**Note:** Times vary by question length and token count. Streaming masks latency by showing first token ASAP.

---

## Cost Analysis

### Monthly Cost Estimates (100k questions)

| Configuration | Provider | Avg Tokens | Est. Cost |
|---------------|----------|-----------|-----------|
| Full Fallback | Mostly DeepSeek | 250 | $25 |
| Cost-Optimized | Groq (free tier) | 100 | $0 (rate limited) |
| Quality | GPT-4o | 300 | $150+ |
| Hybrid | DeepSeek + Ollama | 200 | $15-20 |

**Cost factors:**
- DeepSeek: ~$0.0014 per 1k tokens
- Gemini: Free tier + paid
- Grok: Variable (xAI pricing)
- Groq: Free (rate limited) / Paid (unlimited)
- OpenAI: ~$0.0015-0.02 per 1k tokens
- Ollama: Free (but requires self-hosted hardware)

---

## Troubleshooting

### All providers failing

**Symptoms:**
```
curl "http://localhost:8002/ask?question=test"
# Returns: 500 Internal Server Error
# Logs: "All LLM providers failed"
```

**Causes & Solutions:**
1. **No API keys set:** Set at least `GROQ_API_KEY` or `DEEPSEEK_API_KEY`
   ```bash
   export GROQ_API_KEY="gsk_..."
   docker-compose up
   ```

2. **Invalid API keys:** Verify keys are correct
   ```bash
   curl -X POST "https://api.deepseek.com/v1/models" \
     -H "Authorization: Bearer $DEEPSEEK_API_KEY"
   ```

3. **Network blocked:** Check firewall
   ```bash
   ping api.deepseek.com
   curl https://api.deepseek.com  # Should not timeout
   ```

4. **Ollama not running:** If all cloud providers down, Ollama is last resort
   ```bash
   docker-compose logs ollama
   # Ollama service must be running
   ```

### Sticking to one provider when others available

**Symptoms:**
```json
{
  "metadata": {
    "model_used": "groq:llama-3.1-8b"
  }
}
// But DEEPSEEK_API_KEY is set
```

**Cause:** DeepSeek might have initialization error silently caught

**Solution:** Check logs for warnings
```bash
docker-compose logs agent | grep -i "deepseek\|fallback"
```

### High latency fallback

**Problem:** If primary provider is slow, users experience delays

**Solutions:**
1. Increase timeout threshold in code
2. Monitor response times and adjust provider order
3. For high traffic, consider geographic deployment

---

## Advanced Configuration

### Change Fallback Order

Edit `_get_llm_with_tools()` in `src/agent/main.py`:

```python
# Current order:
PROVIDER_ORDER = ["deepseek", "gemini", "grok", "groq", "openai", "ollama"]

# Custom order (prefer Somethingelse):
PROVIDER_ORDER = ["openai", "deepseek", "groq", "gemini", "grok", "ollama"]
```

### Use Specific Model

Force a specific model:

```python
# In src/agent/main.py
# Instead of default deepseek-chat, use reasoner:
if provider_name == "deepseek":
    llm = ChatOpenAI(
        model="deepseek-reasoner",  # Extended thinking for complex queries
        ...
    )
```

### Health Checks

Implement provider health checks:

```python
async def check_provider_health(provider: str):
    try:
        llm = initialize_provider(provider)
        # Test with simple query
        llm.invoke("Hi")  # Quick test
        return True
    except:
        return False
```

---

## Troubleshooting

### Error: "Connection refused on port 11434"

**Symptom:** Backend logs show `Connection refused (errno 111)` when trying to connect to localhost:11434

**Root Causes:**
1. Ollama is not running locally
2. `OLLAMA_BASE_URL` is set in `.env` but system is cloud-only
3. Stale provider selection from previous session

**Solutions:**

```bash
# Option 1: Ensure Ollama is running
ollama serve

# Option 2: Cloud-only setup (recommended)
# In .env:
DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key-here
# Comment out these lines:
# OLLAMA_BASE_URL=http://localhost:11434

# Option 3: If stale provider selection, delete cached selection
rm -f backend/src/agent/data/model_selection.json
```

### Error: "No LLM provider configured"

**Symptom:** Backend fails to start with this error

**Root Cause:** No API keys are configured for any provider

**Solution:** Set at least one API key:

```bash
# Minimal setup (FREE)
GROQ_API_KEY=your-groq-free-key

# Recommended setup
DEEPSEEK_API_KEY=your-deepseek-key
GROQ_API_KEY=your-groq-key
```

### Provider Not Available (Silent Fallback)

**Symptom:** Backend logs show different provider being used than what you set in `DEFAULT_PROVIDER`

**Root Cause:** Selected provider's API key is not configured

**Solution:** 

```bash
# Check which providers have API keys:
grep -E "API_KEY|OLLAMA_BASE_URL" .env

# Ensure DEFAULT_PROVIDER has a corresponding API key:
DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key  # Must be set!

# OR set the provider that HAS an API key:
DEFAULT_PROVIDER=groq
GROQ_API_KEY=your-groq-key-here
```

### Slow Response Times

**Root Cause:** May be falling back through multiple providers

**Solution:** 

1. Check backend logs to see which provider is actually being used:
   ```bash
   docker-compose logs vecinita-agent | grep -E "Initializing|Provider"
   ```

2. Set `DEFAULT_PROVIDER` to your fastest/preferred provider:
   ```bash
   # Set to specific fast provider
   DEFAULT_PROVIDER=deepseek  # Typically fastest
   ```

3. Reduce fallback chain by removing unused provider keys:
   ```bash
   # Don't set API keys for providers you're not using
   # Remove or leave blank:
   # OLLAMA_BASE_URL=...
   # GEMINI_API_KEY=...
   ```

### Model Selection Not Persisting

**Symptom:** You set a provider via API but it reverts on restart

**Cause:** `model_selection.json` only persists within a session; full restart resets to `DEFAULT_PROVIDER`

**Solution:** Use `DEFAULT_PROVIDER` in `.env` for permanent provider preference:

```bash
# This persists across restarts:
DEFAULT_PROVIDER=deepseek
```

### Testing Provider Availability

Check which providers are available on startup:

```bash
# View startup logs
docker-compose logs vecinita-agent | grep "Provider"

# Expected output when configured:
# Provider validation: DEFAULT_PROVIDER=deepseek, has_api_key=True, using=deepseek
# Provider availability: ['deepseek', 'groq', ...]
# Initializing ChatOpenAI with DeepSeek (primary)...
```

### Debugging Provider Selection

Enable detailed logging:

```bash
# In backend/src/agent/main.py, look for logs with pattern:
# - "Provider validation:"
# - "Provider availability:"
# - "Initializing Chat*"
# - "Using provider:"

# These logs help identify which provider is actually selected
```

---

## FAQ

**Q: What happens if primary provider is slow?**  
A: The agent will still wait for it. Consider adjusting timeout or reordering providers.

**Q: Can I lock to one provider?**  
A: Yes, set `LOCK_MODEL_SELECTION=true` and `DEFAULT_PROVIDER=deepseek` to always use DeepSeek (if key is set).

**Q: How long does fallback take?**  
A: Typically <1 second to detect failure and switch. Network timeouts can extend this.

**Q: Does fallback happen mid-response?**  
A: No. Provider is selected BEFORE generating answer. If it fails during generation, error is returned.

**Q: Can I use custom models?**  
A: Yes, fork the repo and modify `_get_llm_with_tools()` to add your provider.

---

## References

- [DeepSeek API](https://platform.deepseek.com)
- [Google Gemini API](https://ai.google.dev)
- [Groq Console](https://console.groq.com)  
- [OpenAI API](https://platform.openai.com)
- [Ollama](https://ollama.ai)

---

**Generated:** 2026-02-08  
**Status:** Production Ready  
**Coverage:** Provider configuration, monitoring, troubleshooting, cost analysis
