# Authentication Proxy & Rate Limiting Guide

**Last Updated:** February 8, 2026  
**Status:** ✅ Complete (Phase 6)  
**Audience:** DevOps engineers, System administrators, Backend developers

## Overview

Vecinita uses a dedicated **Auth Proxy** microservice to manage:
- ✅ API key validation
- ✅ Rate limiting (tokens/day, requests/hour)
- ✅ Usage tracking per API key
- ✅ Daily quota resets
- ✅ Fail-open design (service continues if proxy down)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend / Client                         │
└────────────────────────┬────────────────────────────────────┘
                         │ (1) API Key in header
                         ▼
        ┌────────────────────────────────┐
        │     Gateway (port 8002)         │ ← Authentication layer
        │ - Basic auth validation         │
        │ - Rate limit checks             │
        │ - Request/response headers      │
        └────────┬───────────────────────┘
                 │ (2) Validated request
                 ▼
        ┌────────────────────────────────┐
        │   Auth Proxy (port 8003)        │ ← Rate limiting service
        │ - Key validation                │
        │ - Usage tracking                │
        │ - Quota enforcement             │
        │ - Daily reset logic             │
        └────────┬───────────────────────┘
                 │ (3) Usage update
                 ▼
        ┌────────────────────────────────┐
        │    Redis (optional)             │ ← Distributed cache
        │ - Per-key rate limit state      │
        │ - Shared across instances       │
        └────────────────────────────────┘
```

**Note:** Redis is optional for single-instance deployments. Multi-instance requires Redis for state sharing.

---

## Quick Start

### 1. Configure Environment Variables

```bash
# .env file
AUTH_PROXY_URL=http://localhost:8003
ENABLE_AUTH=true
RATE_LIMIT_TOKENS_PER_DAY=1000
RATE_LIMIT_REQUESTS_PER_HOUR=100
```

### 2. Start Services

```bash
# Using Docker Compose (recommended)
docker-compose up

# Services started:
# - gateway:8002 (main API)
# - auth_proxy:8003 (auth/rate limit)
# - agent:8001 (agent service)
# - redis:6379 (optional, for multi-instance)
```

### 3. Test Authentication

```bash
# Valid API key request
curl -H "X-API-Key: sk_test_abc123" \
  http://localhost:8002/ask \
  -G -d question="What is AI?"

# Missing API key
curl http://localhost:8002/ask \
  -G -d question="What is AI?"
# Response: 401 Unauthorized

# Rate limit exceeded
# (after 100 requests in 1 hour)
# Response: 429 Too Many Requests
```

---

## API Key Setup

### API Key Format

```
sk_test_xxxxxxxxxxxxxxxxxxxx  (for testing)
sk_live_xxxxxxxxxxxxxxxxxxxx  (for production)
```

**Structure:**
- `sk_` = Key prefix (identifies as secret key)
- `test` or `live` = Environment
- `24-32 random characters` = Unique identifier

### Creating API Keys

**For administrators only:**

```python
# In admin dashboard or management script
import secrets
import base64

def generate_api_key(environment="test"):
    random_suffix = secrets.token_hex(16)  # 32 hex chars
    return f"sk_{environment}_{random_suffix}"

# Example:
api_key = generate_api_key()
# Output: sk_test_a3f9e2c1b5d4e8f7a9c2b3d4e5f6a7b8
```

### Storing API Keys

**For end users:**

1. User requests API key from your admin panel
2. System generates unique key
3. User saves key securely (like password)
4. User passes key in request header

```bash
# User stores in .bashrc or .env
export VECINITA_API_KEY="sk_test_abc123"

# User makes requests with key
curl -H "X-API-Key: $VECINITA_API_KEY" \
  http://api.yourdomain.com/ask \
  -G -d question="test"
```

---

## Rate Limiting Configuration

### Rate Limit Tiers

Choose tier based on your use case:

| Tier | Tokens/Day | Requests/Hour | Monthly Cost | Use Case |
|------|-----------|---------------|--------------|----------|
| Free | 1,000 | 10 | $0 | Development |
| Starter | 10,000 | 100 | $20 | Small apps |
| Growth | 50,000 | 500 | $100 | Production |
| Enterprise | 1,000,000 | 10,000 | Custom | Large-scale |

### Configuring Rate Limits

```bash
# .env - Global defaults apply to all API keys
RATE_LIMIT_TOKENS_PER_DAY=10000      # Per API key
RATE_LIMIT_REQUESTS_PER_HOUR=100     # Per API key

# Docker compose override
docker run -e RATE_LIMIT_TOKENS_PER_DAY=50000 vecinita-auth-proxy
```

### Per-Key Rate Limits

**Override for specific customers:**

```python
# In auth proxy database
UPDATE api_keys 
SET 
  daily_token_limit = 50000,      # Override for this customer
  hourly_request_limit = 500
WHERE key = "sk_test_abc123";
```

**Usage tracking:**
```json
{
  "api_key": "sk_test_abc123",
  "tokens_used_today": 5234,
  "tokens_limit": 50000,
  "requests_today": 45,
  "requests_limit": 500
}
```

---

## Usage Tracking

### Token Counting

Tokens counted in POST body at request start:

```python
# Each request tracks:
- Input tokens: Question + context documents
- Output tokens: Generated answer
- Total: Combined count

# Example:
# Question: "What is AI?" (3 tokens)
# Documents: 2000 tokens
# Answer: Generated ~150 tokens
# Total: ~2150 tokens
```

### Tracking Flow

```
1. Client sends request with API key
2. Gateway validates key (calls auth proxy)
3. Auth proxy checks daily token budget
4. If available: Request proceeds, proxy tracks used tokens
5. After response: Used tokens added to daily counter
6. Midnight UTC: Counters reset to 0
```

### Check Usage

**Via API endpoint:**

```bash
# Get current usage for your API key
curl -H "X-API-Key: sk_test_abc123" \
  http://localhost:8003/usage

# Response:
{
  "tokens_today": 2450,
  "tokens_limit": 10000,
  "tokens_remaining": 7550,
  "requests_today": 25,
  "requests_limit": 100,
  "requests_remaining": 75,
  "reset_at": "2026-02-09T00:00:00Z"
}
```

**Via logs:**

```bash
# View auth proxy logs
docker-compose logs auth_proxy | grep "tracking\|usage"

# Output:
# INFO - Tracking usage: key=sk_test_abc123, tokens=2150, daily_total=2450
# INFO - Daily quota check: 2450/10000 tokens used (75% of budget)
```

---

## Rate Limit Behavior

### When Limit Exceeded

**Token limit exceeded:**
```
Request rejected with HTTP 429
Response: {"error": "Daily token limit exceeded"}

Example: Used 10,543 tokens, limit 10,000
```

**Request limit exceeded:**
```
Request rejected with HTTP 429
Response: {"error": "Hourly request limit exceeded"}

Example: Made 101 requests in current hour, limit 100
```

### Quota Reset Timing

**Daily quotas:**
- Reset at **midnight UTC (00:00 UTC)**
- All users reset simultaneously
- Per-customer limits reset independently

**Hourly quotas:**
- Rolling window (last 60 minutes)
- Not synchronized globally

### Handling Rejections

**Strategy 1: Implement client-side batching**

```python
# Client batches requests to stay under rate limit
questions = ["Q1", "Q2", "Q3"]  # 3 questions
batch_size = 20  # Stay under ~30 requests/hour

for i in range(0, len(questions), batch_size):
    batch = questions[i:i+batch_size]
    for q in batch:
        response = send_request(q)
    time.sleep(60)  # Wait 1 minute between batches
```

**Strategy 2: Implement exponential backoff**

```python
import time
import random

def send_with_retry(question, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = send_request(question)
            return response
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.random()
                time.sleep(wait_time)
            else:
                raise
```

**Strategy 3: Request tier upgrade**

```bash
# If rate limited, user can request higher tier
# Contact admin: support@yourdomain.com
# Provide: API key, use case, requested token/request limits
```

---

## Deployment Options

### Option 1: Docker Compose (Single Machine)

**Recommended for development and small production deployments.**

```bash
# docker-compose.yml includes auth proxy
docker-compose up -d

# Verify running
docker-compose ps
# auth_proxy  8003/tcp  ← Should be running

# Check logs
docker-compose logs -f auth_proxy
```

**Storage:** In-memory (rate limits reset on restart)

---

### Option 2: Docker Compose + Redis (Multi-Instance)

**Recommended for high-availability production.**

```yaml
# docker-compose.yml additions
services:
  auth_proxy:
    environment:
      REDIS_URL: redis://redis:6379
      REDIS_ENABLED: "true"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Benefits:**
- ✅ Share rate limit state across multiple instances
- ✅ Survive service restarts
- ✅ Handle concurrent requests to different instances
- ✅ Persist usage data

**Deployment:**

```bash
# Start with Redis
docker-compose up -d

# Verify both services
docker-compose ps
# auth_proxy ✓
# redis ✓

# Check Redis is connected
docker-compose exec auth_proxy redis-cli ping
# Response: PONG
```

---

### Option 3: Kubernetes

**Recommended for enterprise deployments.**

```yaml
# auth-proxy-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-proxy
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: auth-proxy
        image: vecinita:latest
        ports:
        - containerPort: 8003
        env:
        - name: REDIS_URL
          value: cache:6379  # Redis service endpoint
        - name: PORT
          value: "8003"
---
apiVersion: v1
kind: Service
metadata:
  name: auth-proxy
spec:
  type: ClusterIP
  ports:
  - port: 8003
    targetPort: 8003
```

**Deployment:**

```bash
# Apply manifest
kubectl apply -f auth-proxy-deployment.yaml

# Verify
kubectl get pods -l app=auth-proxy
# auth-proxy-xyz 1/1 Running (3 replicas)

# Check logs
kubectl logs -f deployment/auth-proxy
```

---

## Configuration Reference

### Environment Variables

```bash
# Core configuration
AUTH_PROXY_PORT=8003                      # Service port
AUTH_PROXY_HOST=0.0.0.0                   # Bind address

# Data storage
REDIS_ENABLED=false                       # Use Redis for state
REDIS_URL=redis://localhost:6379          # Redis connection
DATABASE_URL=postgresql://...             # PostgreSQL for keys

# Rate limiting defaults
RATE_LIMIT_TOKENS_PER_DAY=10000           # Per key
RATE_LIMIT_REQUESTS_PER_HOUR=100          # Per key
RATE_LIMIT_RESET_UTC_HOUR=0               # Midnight UTC

# API configuration
API_KEY_PREFIX=sk_                        # Key prefix to validate
API_KEY_MIN_LENGTH=28                     # Minimum key length

# Feature flags
ENABLE_USAGE_TRACKING=true                # Track usage stats
ENABLE_RATE_LIMITING=true                 # Enforce limits
FAIL_OPEN_ON_REDIS_DOWN=true              # Continue if Redis down

# Logging
LOG_LEVEL=INFO                            # Log verbosity
LOG_FORMAT=json                           # JSON for aggregation
```

### Example Production Configuration

```bash
# .env.production
AUTH_PROXY_PORT=8003
AUTH_PROXY_HOST=0.0.0.0

# Use Redis for multi-instance setup
REDIS_ENABLED=true
REDIS_URL=redis://redis-cluster:6379

# Store API keys in database
DATABASE_URL=postgresql://user:pass@db:5432/vecinita

# Rate limits for production
RATE_LIMIT_TOKENS_PER_DAY=50000
RATE_LIMIT_REQUESTS_PER_HOUR=500

# Strict logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security
FAIL_OPEN_ON_REDIS_DOWN=false  # Reject if rate-limit state unavailable
```

---

## Monitoring & Debugging

### Health Check

```bash
# Check auth proxy is running
curl http://localhost:8003/health

# Response:
{
  "status": "healthy",
  "timestamp": "2026-02-08T10:30:00Z",
  "redis_connected": true
}
```

### View Active Keys

```bash
# List all API keys and their usage
curl http://localhost:8003/keys

# Response:
[
  {
    "key": "sk_test_abc123",
    "created_at": "2026-01-01T00:00:00Z",
    "tokens_today": 2450,
    "tokens_limit": 10000,
    "requests_today": 25,
    "requests_limit": 100
  },
  ...
]
```

### Real-time Monitoring

```bash
# Watch auth proxy logs
docker-compose logs -f auth_proxy

# Sample output:
# INFO - Validating key: sk_test_abc123
# INFO - Key valid, tokens_available=7550
# INFO - Tracking usage: tokens_used=150
# INFO - Daily total: 2600/10000 tokens (26%)
```

### Debug Rate Limiting

```bash
# Enable debug logging
docker-compose exec auth_proxy \
  curl -X POST http://localhost:8003/debug \
  -d '{"log_level": "DEBUG"}'

# Now logs show detailed rate limit checks:
# DEBUG - Checking token budget: 2600 + 150 <= 10000? YES
# DEBUG - Checking request budget: 25 + 1 <= 100? YES
```

### Metrics Export

```bash
# Get Prometheus metrics (if enabled)
curl http://localhost:8003/metrics

# Sample output:
auth_proxy_requests_total{endpoint="/validate-key"} 1250
auth_proxy_api_keys_active 48
auth_proxy_rate_limit_exceeded_total 3
```

---

## Troubleshooting

### Auth Proxy Not Starting

**Symptom:**
```
docker-compose up
ERROR: Cannot start auth_proxy - port 8003 already in use
```

**Solution:**
```bash
# Check what's using port 8003
lsof -i :8003

# Kill existing process
kill -9 <PID>

# Or use different port
docker-compose override -f - <<EOF
services:
  auth_proxy:
    ports:
      - "8007:8003"
EOF
```

### Rate Limits Not Enforcing

**Symptom:**
```
# Despite hitting rate limit, requests still succeed
curl -H "X-API-Key: sk_test_abc123" http://localhost:8002/ask ...
# Succeeds even after 100 requests in 1 hour
```

**Debug Steps:**

```bash
# 1. Check auth proxy is running
curl http://localhost:8003/health

# 2. Check gateway is calling auth proxy
docker-compose logs gateway | grep "auth_proxy"

# 3. Check ENABLE_AUTH is true
docker-compose exec agent env | grep ENABLE_AUTH

# 4. Check rate limit configuration
curl http://localhost:8003/config | jq '.rate_limits'
```

### Redis Connection Failed

**Symptom:**
```
docker-compose logs auth_proxy | grep "redis"
ERROR - Redis connection failed: Connection refused
```

**Solution:**

```bash
# 1. Verify Redis is running
docker-compose ps | grep redis

# 2. If not running, start it
docker-compose up -d redis

# 3. Test Redis connection
docker-compose exec auth_proxy redis-cli ping
# Should return: PONG

# 4. Check Redis URL in environment
docker-compose exec auth_proxy env | grep REDIS
```

### API Key Invalid

**Symptom:**
```
curl -H "X-API-Key: abc123" http://localhost:8002/ask ...
HTTP/1.1 401 Unauthorized
{"error": "Invalid API key"}
```

**Root Causes:**
1. Key doesn't exist in database
2. Key is revoked/disabled
3. Key format is invalid

**Solution:**

```bash
# 1. Verify key format (should start with sk_)
echo "sk_test_abc123" | grep "^sk_"

# 2. Check key exists in auth proxy
curl -H "X-API-Key: sk_test_abc123" http://localhost:8003/validate-key

# Response should show: "valid": true

# 3. Check key is not disabled
curl http://localhost:8003/keys | jq '.[] | select(.key=="sk_test_abc123")'
# Should not have "disabled": true
```

---

## Best Practices

### Security

✅ **DO:**
- Store API keys in environment variables or secrets manager
- Rotate keys periodically (monthly)
- Use different keys for different applications
- Revoke compromised keys immediately
- Use HTTPS in production (not HTTP)

❌ **DON'T:**
- Hardcode API keys in source code
- Share API keys between users
- Log full API keys (only log masked: `sk_...c123`)
- Use same key across dev/prod
- Store keys in git repositories

### Performance

✅ **DO:**
- Cache rate limit state in Redis for multi-instance
- Batch requests when possible
- Implement client-side request queueing
- Monitor 95th percentile response time

❌ **DON'T:**
- Make auth proxy call for every request if avoidable
- Store unlimited history of all requests
- Query historical data on every health check

### Maintenance

✅ **DO:**
- Monitor Redis disk space if using persistence
- Archive old usage data monthly
- Test failover scenarios (Redis down, etc)
- Review API key usage regularly
- Update documentation when changing limits

❌ **DON'T:**
- Restart auth proxy without notifying users
- Change rate limits without notice
- Ignore Redis out-of-memory errors
- Keep disabled keys forever

---

## FAQ

**Q: What happens if Redis is down?**  
A: If `FAIL_OPEN_ON_REDIS_DOWN=true`, requests continue (rate limits not enforced). If false, requests rejected with 503.

**Q: How many API keys can I manage?**  
A: Unlimited. Storage depends on backend (Redis/Postgres). Performance OK with 10k+ keys.

**Q: Can I use the same key across services?**  
A: Yes, but dangerous. If one service is compromised, all get compromised. Use separate keys per service.

**Q: How do I revoke an API key?**  
A: Set `disabled=true` in database or call `DELETE /keys/{key}`.

**Q: What if user forgets API key?**  
A: User must request new key from admin (old key cannot be recovered).

**Q: How are unused tokens handled?**  
A: Tokens don't roll over. Daily budget resets at midnight UTC.

---

## References

- [Auth Proxy Source Code](../../backend/src/gateway/)
- [Environment Variables](../../.env.example)
- [Rate Limiting Tests](../../backend/tests/integration/test_auth_proxy.py)

---

**Generated:** 2026-02-08  
**Status:** Production Ready  
**Coverage:** Setup, configuration, monitoring, troubleshooting, deployment options
