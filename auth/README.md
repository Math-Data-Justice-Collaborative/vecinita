# Vecinita Auth Proxy

Lightweight Supabase authentication proxy service for Vecinita's frontend and backend.

## Overview

This service provides:
- **API Key Validation**: Validate API keys and check their status
- **Rate Limiting**: Per-API-key rate limiting (tokens/day, requests/hour)
- **Usage Tracking**: Track token and request usage across services
- **Unified Interface**: Single point of auth for frontend and backend

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -e .

# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"

# Run the app
python -m uvicorn src.main:app --reload --port 8003
```

### Docker

```bash
docker build -t vecinita-auth-proxy .
docker run -e SUPABASE_URL="..." -e SUPABASE_KEY="..." -p 8003:8003 vecinita-auth-proxy
```

## API Endpoints

### Health Check
```
GET /health
```

Returns service health status.

### Validate API Key
```
POST /validate-key
Content-Type: application/json

{
  "api_key": "sk_vp_xxxx"
}
```

Validates an API key and returns metadata.

### Get Usage
```
GET /usage
Authorization: Bearer sk_vp_xxxx
```

Returns token and request usage for the API key.

### Track Usage
```
POST /track-usage?tokens=10
Authorization: Bearer sk_vp_xxxx
```

Increment usage tracking for an API key.

### Get Configuration
```
GET /config
```

Returns service configuration and rate limit settings.

## Rate Limiting

Default limits:
- **1000 tokens/day** per API key
- **100 requests/hour** per API key

Limits are enforced at the gateway level.

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run with coverage
pytest --cov=src tests/
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase anon/service key | Yes |
| `ENVIRONMENT` | Environment name (dev/prod) | No |
| `PORT` | Server port | No (default: 8003) |

## Integration with Backend

The gateway service calls this proxy to validate API keys before forwarding requests:

```python
# In gateway authentication middleware
response = requests.post(
    "http://auth-proxy:8003/validate-key",
    json={"api_key": api_key}
)
```

## Future Enhancements

- [ ] Redis integration for distributed rate limiting
- [ ] Email-based API key generation
- [ ] Dashboard for API key management
- [ ] Webhook support for usage alerts
- [ ] OAuth2 integration

## License

MIT
