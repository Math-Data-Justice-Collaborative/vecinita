# Modal Proxy Authentication Setup

## Overview

The Vecinita Scraper FastAPI endpoint deployed on Modal now uses **Modal Proxy Auth Tokens** to prevent unauthorized clients from triggering web endpoints.

This protects your production endpoints from unauthorized access while allowing legitimate clients with valid tokens to submit scraping jobs.

## How It Works

### Authorization Flow

```
Client Request
    ↓
Modal Proxy Auth Header Check (Modal-Key, Modal-Secret)
    ↓
Endpoint Handler (Only if auth succeeds)
```

### Protected Endpoints

All endpoints **except** the following are protected:
- `GET /health` - Health check (public)
- `GET /docs` - API documentation (public)
- `GET /redoc` - ReDoc documentation (public)
- `GET /openapi.json` - OpenAPI schema (public)

Protected endpoints:
- `POST /jobs` - Submit a scraping job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List jobs
- `POST /jobs/{job_id}/cancel` - Cancel a job

## Setup Steps

### Step 1: Create a Proxy Auth Token

1. Log in to [Modal Dashboard](https://modal.com/)
2. Navigate to Settings → [Proxy Auth Tokens](https://modal.com/settings/proxy-auth-tokens)
3. Click "Create New Token"
4. Copy the Token ID (starts with `wk-`) and Token Secret (starts with `ws-`)

**Important:** Store these securely. You cannot retrieve the secret again.

### Step 2: Use the Token in Requests

Include the token credentials in HTTP headers:

```bash
export TOKEN_ID=wk-1234abcd
export TOKEN_SECRET=ws-1234abcd

curl -X POST https://<your-endpoint>/jobs \
  -H "Content-Type: application/json" \
  -H "Modal-Key: $TOKEN_ID" \
  -H "Modal-Secret: $TOKEN_SECRET" \
  -d '{
    "user_id": "user123",
    "url": "https://example.com",
    "crawl_config": {},
    "chunking_config": {}
  }'
```

## Examples

### Python Client

```python
import httpx

TOKEN_ID = "wk-xxx"
TOKEN_SECRET = "ws-xxx"
API_URL = "https://vecinita-api-endpoint.modal.run"

headers = {
    "Modal-Key": TOKEN_ID,
    "Modal-Secret": TOKEN_SECRET,
}

# Submit a job
response = httpx.post(
    f"{API_URL}/jobs",
    json={
        "user_id": "user123",
        "url": "https://example.com",
        "crawl_config": {},
        "chunking_config": {}
    },
    headers=headers
)

print(response.json())
```

### JavaScript/Node.js Client

```javascript
const TOKEN_ID = "wk-xxx";
const TOKEN_SECRET = "ws-xxx";
const API_URL = "https://vecinita-api-endpoint.modal.run";

const headers = {
  "Modal-Key": TOKEN_ID,
  "Modal-Secret": TOKEN_SECRET,
  "Content-Type": "application/json"
};

const response = await fetch(`${API_URL}/jobs`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    user_id: "user123",
    url: "https://example.com",
    crawl_config: {},
    chunking_config: {}
  })
});

const data = await response.json();
console.log(data);
```

### cURL Examples

```bash
# Store credentials
export TOKEN_ID="wk-xxx"
export TOKEN_SECRET="ws-xxx"
export API_URL="https://vecinita-api-endpoint.modal.run"

# Submit a job
curl -X POST "$API_URL/jobs" \
  -H "Content-Type: application/json" \
  -H "Modal-Key: $TOKEN_ID" \
  -H "Modal-Secret: $TOKEN_SECRET" \
  -d '{
    "user_id": "user123",
    "url": "https://example.com",
    "crawl_config": {},
    "chunking_config": {}
  }'

# Get job status
curl "$API_URL/jobs/job-id-here" \
  -H "Modal-Key: $TOKEN_ID" \
  -H "Modal-Secret: $TOKEN_SECRET"

# Public health check (no auth needed)
curl "$API_URL/health"
```

## Troubleshooting

### 401 Unauthorized Error

```
curl: (22) The requested URL returned error: 401
modal-http: missing credentials for proxy authorization
```

**Solutions:**
- Verify token ID and secret are correct
- Check header names are exactly `Modal-Key` and `Modal-Secret` (case-sensitive in some contexts)
- Ensure token is still active (not revoked)
- Token may have expired - create a new one

### 403 Forbidden Error

**Solution:**
- You may not have permission to manage this token
- Ensure your Modal workspace permissions are correct

### Unknown Host Error

```
curl: (6) Could not resolve host
```

**Solution:**
- Verify the endpoint URL is correct
- Check the Modal app is deployed: `modal app list`

## Token Management

### List All Tokens

In Modal Dashboard Settings → Proxy Auth Tokens, you can see all active tokens.

### Revoke a Token

1. Go to [Proxy Auth Tokens](https://modal.com/settings/proxy-auth-tokens)
2. Click the token to revoke
3. Confirm revocation

**Important:** All clients using this token will immediately lose access.

### Rotate Tokens

To rotate tokens without downtime:
1. Create a new token
2. Update clients to use the new token
3. Revoke the old token once all clients are updated

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** to store tokens
3. **Rotate tokens periodically** (recommended every 90 days)
4. **Use different tokens** for different environments (dev, staging, production)
5. **Monitor token usage** in Modal analytics
6. **Revoke immediately** if token is compromised

## Deployment Notes

### GitHub Actions

If deploying via GitHub Actions, store credentials as repository secrets:

```yaml
- name: Deploy API
  env:
    MODAL_TOKEN_ID: ${{ secrets.MODAL_TOKEN_ID }}
    MODAL_TOKEN_SECRET: ${{ secrets.MODAL_TOKEN_SECRET }}
  run: make deploy
```

### Environment Variables

The FastAPI server also supports optional internal proxy authentication:

```env
MODAL_AUTH_KEY=xxx        # For internal proxy routes (if used)
MODAL_AUTH_SECRET=xxx     # For internal proxy routes (if used)
```

These are separate from the proxy auth tokens used by external clients.

## Additional Resources

- [Modal Proxy Auth Documentation](https://modal.com/docs/guide/webhooks#proxy-auth-tokens)
- [Modal Dashboard](https://modal.com/)
- [API Reference](/docs/)
