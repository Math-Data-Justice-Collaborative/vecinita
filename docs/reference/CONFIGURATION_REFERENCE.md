"""
Vecinita Configuration Guide (Phase 8)

Complete reference for all configurable settings in Vecinita.
Multiple configuration methods are supported: environment variables, .env file, Docker environment.
"""

# ============================================================================
# SECTION 1: API Gateway & Services (Port Configuration)
# ============================================================================

"""
Port Configuration:
  - API Gateway (main entry): 8002 (http://localhost:8002)
  - Agent Service: 8000 (http://localhost:8000)
  - Embedding Service: 8001 (http://localhost:8001)
  - Auth Routing: 8003 (http://localhost:8003)

Environment:
  AGENT_SERVICE_URL=http://localhost:8000
  EMBEDDING_SERVICE_URL=http://localhost:8001
  AUTH_SERVICE_URL=http://localhost:8003
"""

# ============================================================================
# SECTION 2: Authentication (Phase 7 - Security Hardening)
# ============================================================================

"""
Authentication Configuration:

1. ENABLE_AUTH (default: false)
   - Enable API key validation
   - Set to 'true' in production
   
   ENABLE_AUTH=false    # Development
   ENABLE_AUTH=true     # Production

2. AUTH_FAIL_CLOSED (default: true) ⭐ Secure Default
   - Fail-closed pattern: deny on auth service unavailability
   - Set to 'false' only for development
   
   AUTH_FAIL_CLOSED=true    # Production (secure)
   AUTH_FAIL_CLOSED=false   # Development (permissive)

3. ADMIN_API_KEYS (comma-separated list)
   - Required when ENABLE_AUTH=true
   - Grants access to /admin/* endpoints
   
   ADMIN_API_KEYS=admin-key-1,admin-key-2,admin-key-3

4. AUTH_SERVICE_URL
   - URL of authentication service
   - Default: http://localhost:8003
   
   AUTH_SERVICE_URL=http://localhost:8003

Usage:
  curl -X GET http://localhost:8002/api/v1/ask \\
    -H "Content-Type: application/json" \\
    -H "Authorization: Bearer YOUR_API_KEY" \\
    -d '{"query":"What is Vecinita?"}'
"""

# ============================================================================
# SECTION 3: Rate Limiting (Phase 7 - Per-Endpoint)
# ============================================================================

"""
Rate Limiting Configuration:

Global Defaults:
  RATE_LIMIT_TOKENS_PER_DAY=1000
  RATE_LIMIT_REQUESTS_PER_HOUR=100

Per-Endpoint Limits (in code):
  /api/v1/ask → 60 requests/hour, 1000 tokens/day
  /api/v1/scrape → 10 requests/hour, 5000 tokens/day
  /api/v1/admin → 5 requests/hour, 100 tokens/day
  /api/v1/embed → 100 requests/hour, 10000 tokens/day

Response Format (429 Too Many Requests):
  HTTP/1.1 429 Too Many Requests
  Retry-After: 3600
  X-RateLimit-Limit: 60
  X-RateLimit-Remaining: 0
  X-RateLimit-Reset: 2025-02-13T18:30:00
  
  {
    "error": "Rate limit exceeded",
    "detail": "Hourly request limit (60 req/hr) exceeded for /api/v1/ask",
    "limit_type": "requests_per_hour",
    "limit": 60,
    "remaining": 0,
    "reset_at": "2025-02-13T18:30:00"
  }

TODO for Multi-Instance Deployment:
  - Configure Redis backend for distributed rate limiting
  - Add metrics/monitoring via Prometheus
"""

# ============================================================================
# SECTION 4: Database Configuration
# ============================================================================

"""
Supabase Database Configuration:

Required:
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Optional:
  DATABASE_URL=postgresql://user:password@host:5432/vecinita
  (Used only for direct PostgreSQL operations, not required for Supabase)

Pool Configuration (Phase 7):
  POOL_MIN_SIZE=5              # Minimum connections (default)
  POOL_MAX_SIZE=20             # Maximum connections (default)
  POOL_TIMEOUT_SECONDS=10      # Connection timeout
  POOL_RECYCLE_SECONDS=3600    # Connection recycle interval
  
  Query Configuration:
  QUERY_TIMEOUT_SECONDS=30     # Query timeout
  QUERY_RETRY_MAX_ATTEMPTS=3   # Retry failed queries
  QUERY_RETRY_BACKOFF_SECONDS=1  # Exponential backoff

Health Checks:
  POOL_HEALTH_CHECK_INTERVAL_SECONDS=300  # Run every 5 minutes

Schema:
  Tables:
    - documents (content chunks)
    - chunks (processed chunks with embeddings)
    - sessions (conversation sessions)
  
  Required Extensions:
    - pgvector (for vector similarity search)
"""

# ============================================================================
# SECTION 5: Embeddings Configuration
# ============================================================================

"""
Embedding Model Configuration:

Default:
  EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

Supported Models:
  - all-MiniLM-L6-v2 (384 dimensions, fast)
  - all-mpnet-base-v2 (768 dimensions, better quality)
  - all-roberta-large-v1 (1024 dimensions, best quality)

Embedding Service:
  EMBEDDING_SERVICE_URL=http://localhost:8001

Local Embeddings:
  By default, embeddings are generated locally using HuggingFace transformers.
  No configuration needed - model downloads automatically on first use.

Remote Embeddings:
  Use embedding microservice for distributed setup:
  - Deploy embedding service separately (Port 8001)
  - Configure EMBEDDING_SERVICE_URL
  - Service handles model caching and GPU acceleration
"""

# ============================================================================
# SECTION 6: Scraper Configuration  
# ============================================================================

"""
Web Scraper Configuration:

Configuration Directory (flexible!):
  Default: backend/data/config/
  Override: SCRAPER_CONFIG_DIR=/custom/path
  
  Environment variable takes precedence over default path.

Configuration Files:
  recursive_sites.txt
    Format: <url> <depth>
    Example: https://example.com 2
    
  playwright_sites.txt
    Format: One domain per line
    Example: javascript-heavy.com
    
  skip_sites.txt
    Format: One domain per line (skip entirely)
    Example: blocked-domain.com

Data Input:
  URLs to scrape: backend/data/urls.txt
  Format: One URL per line, comments start with #
  
  Example:
    # Blog posts
    https://example.com/blog/post1
    https://example.com/blog/post2
    
    # Documentation
    https://docs.example.com

Scraper Settings (in code):
  RATE_LIMIT_DELAY=2        # 2-second delay between requests
  CHUNK_SIZE=1000           # Text chunk size
  CHUNK_OVERLAP=200         # Overlap between chunks

Loaders:
  - Unstructured: Default for most content types
  - PyPDF: For PDF files
  - Playwright: For JavaScript-heavy sites
  - Recursive: For structured hierarchies

Stream Mode:
  True: Upload chunks immediately to database (recommended)
  False: Save to file, upload in batch later

Run Scraper:
  bash backend/scripts/data_scrape_load.sh         # Add data
  bash backend/scripts/data_scrape_load.sh --clean # Replace all data
"""

# ============================================================================
# SECTION 7: Agent Configuration
# ============================================================================

"""
Agent Service Configuration:

FAQ Configuration:
  FAQ Directory: backend/src/services/agent/data/faqs/
  Files:
    - en.md (English FAQs)
    - es.md (Spanish FAQs)
  
  Format (Markdown):
    ## Question text here?
    
    Answer paragraph here. Can have multiple paragraphs.
    
    ## Another question?
    
    Another answer.
  
  Auto-reload: Every 5 minutes
  Language Detection: Automatic from query

Tools:
  1. static_response (FAQ lookup)
     - Exact match
     - Cleaned match (punctuation removed)
     - Partial match (for longer queries)
  
  2. db_search (Database search)
     - Vector similarity search
     - Session isolation
     - Session-filtered results
  
  3. web_search (Web search)
     - Tavily (premium, requires API key)
     - DuckDuckGo (fallback, free)
  
  4. clarify_question (Ask for clarification)
     - When query is ambiguous

Web Search Configuration:
  TAVILY_API_KEY=tvly_XXX       # Optional (uses DuckDuckGo if not set)
  TVLY_API_KEY=tvly_XXX         # Alternative name
  TAVILY_API_AI_KEY=tvly_XXX    # Alternative name

Language Support:
  - English (en)
  - Spanish (es)
  - Extensible: add language specific prompts/FAQs
"""

# ============================================================================
# SECTION 8: CORS & Frontend Configuration
# ============================================================================

"""
CORS (Cross-Origin Resource Sharing):

Default Allowed Origins:
  - http://localhost:5173  (Vite dev server)
  - http://localhost:5174  (Frontend dev)
  - http://localhost:4173  (Built frontend)

Configuration:
  ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://example.com
  Comma-separated list of allowed origins

Production:
  ALLOWED_ORIGINS=https://app.example.com,https://www.example.com

Credentials:
  Enabled by default (allow cookies, auth headers)
  
Methods & Headers:
  Methods: GET, POST, PUT, DELETE, OPTIONS
  Headers: Content-Type, Authorization, Accept
"""

# ============================================================================
# SECTION 9: Logging Configuration
# ============================================================================

"""
Logging Configuration:

Default Level: INFO

Configure via Python logging (recommended):
  [logging]
  disable_existing_loggers = false
  
  [loggers]
  vecinita = INFO
  vecinita.slow_queries = WARNING
  vecinita.agent = DEBUG

Slow Query Logging:
  Logger: vecinita.slow_queries
  Threshold: 5 seconds (configurable)
  Pattern: SLOW QUERY: <query_type> <table> took <duration>s

Enable Debug Logging:
  In code or logging config:
  logging.getLogger("vecinita").setLevel(logging.DEBUG)

Structured Logging:
  Consider adding JSON logging for production:
  - python-json-logger library
  - Structured JSON output for log aggregation services
"""

# ============================================================================
# SECTION 10: Environment Variables - Complete Reference
# ============================================================================

"""
COMPLETE LIST OF ENVIRONMENT VARIABLES:

API Gateway:
  AGENT_SERVICE_URL=http://localhost:8000
  EMBEDDING_SERVICE_URL=http://localhost:8001
  DATABASE_URL=postgresql://...
  ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174

Authentication & Security (Phase 7):
  ENABLE_AUTH=false                    # Set to true in production
  AUTH_FAIL_CLOSED=true                # Secure default
  AUTH_SERVICE_URL=http://localhost:8003
  ADMIN_API_KEYS=key1,key2,key3

Rate Limiting:
  RATE_LIMIT_TOKENS_PER_DAY=1000
  RATE_LIMIT_REQUESTS_PER_HOUR=100

Database:
  SUPABASE_URL=https://project.supabase.co
  SUPABASE_KEY=eyJ...
  DATABASE_URL=postgresql://user:pass@host/db

Connection Pooling:
  POOL_MIN_SIZE=5
  POOL_MAX_SIZE=20
  POOL_TIMEOUT_SECONDS=10
  POOL_RECYCLE_SECONDS=3600
  POOL_HEALTH_CHECK_INTERVAL_SECONDS=300

Query Configuration:
  QUERY_TIMEOUT_SECONDS=30
  QUERY_RETRY_MAX_ATTEMPTS=3
  QUERY_RETRY_BACKOFF_SECONDS=1

Embeddings:
  EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
  EMBEDDING_SERVICE_URL=http://localhost:8001

Scraper:
  SCRAPER_CONFIG_DIR=/path/to/config  # Flexible path!
  MAX_URLS_PER_REQUEST=100
  JOB_RETENTION_HOURS=24

Web Search:
  TAVILY_API_KEY=tvly_XXX
  TVLY_API_KEY=tvly_XXX
  TAVILY_API_AI_KEY=tvly_XXX
"""

# ============================================================================
# SECTION 11: Configuration Methods
# ============================================================================

"""
Three ways to configure Vecinita:

1. Environment Variables (highest priority):
   export SUPABASE_URL=https://...
   export SUPABASE_KEY=eyJ...
   python -m uvicorn backend.src.main:app

2. .env File (second priority):
   Create backend/.env:
     SUPABASE_URL=https://...
     SUPABASE_KEY=eyJ...
   
   File is auto-loaded by python-dotenv

3. Docker Environment (third priority):
   In docker-compose.yml:
     environment:
       - SUPABASE_URL=https://...
       - SUPABASE_KEY=eyJ...

Priority Order (first match wins):
  1. Environment variable
  2. .env file
  3. Code default
  4. Error/warning if required

Development (.env.example):
  Copy backend/.env.example to backend/.env
  Update with your development credentials

Production:
  Set environment variables via:
  - Docker: YAML environment section
  - Kubernetes: ConfigMaps + Secrets
  - Cloud platform: Environment settings (Render, Heroku, etc.)
"""

# ============================================================================
# SECTION 12: Default Configuration Values
# ============================================================================

"""
Safe defaults for development:

API & Services:
  AGENT_SERVICE_URL=http://localhost:8000
  EMBEDDING_SERVICE_URL=http://localhost:8001
  AUTH_SERVICE_URL=http://localhost:8003
  ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:4173

Authentication:
  ENABLE_AUTH=false  # Development
  AUTH_FAIL_CLOSED=true  # Secure default

Rate Limiting:
  RATE_LIMIT_TOKENS_PER_DAY=1000
  RATE_LIMIT_REQUESTS_PER_HOUR=100

Connection Pool:
  POOL_MIN_SIZE=5
  POOL_MAX_SIZE=20
  POOL_TIMEOUT_SECONDS=10

Queries:
  QUERY_TIMEOUT_SECONDS=30
  QUERY_RETRY_MAX_ATTEMPTS=3

Embeddings:
  EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

Scraper:
  MAX_URLS_PER_REQUEST=100
  JOB_RETENTION_HOURS=24
"""

# ============================================================================
# SECTION 13: Configuration Validation Checklist
# ============================================================================

"""
Before Production Deployment:

Authentication:
  [ ] ENABLE_AUTH=true
  [ ] AUTH_FAIL_CLOSED=true (verify it's default)
  [ ] ADMIN_API_KEYS set with multiple keys
  [ ] Auth routing service running and healthy

Database:
  [ ] SUPABASE_URL configured
  [ ] SUPABASE_KEY configured (not in git!)
  [ ] Database connection pool sized for workload
  [ ] Slow query logging enabled
  [ ] Regular backups configured

Security:
  [ ] Rate limits set appropriately
  [ ] CORS only allows production domains
  [ ] No debug logging in production
  [ ] Secrets not logged anywhere
  [ ] TLS/HTTPS enforced

Performance:
  [ ] Connection pool tested under load
  [ ] Embedding service responsive
  [ ] Query timeouts appropriate
  [ ] Slow query log reviewed weekly

Monitoring:
  [ ] Logging system configured
  [ ] Health check endpoints monitored
  [ ] Database pool metrics tracked
  [ ] Rate limit violations tracked

Documentation:
  [ ] .env.example updated with all vars
  [ ] Admin users have access guide
  [ ] Operations team has runbooks
  [ ] Emergency procedures documented
"""

# ============================================================================
# SECTION 14: Troubleshooting Configuration Issues
# ============================================================================

"""
Problem: "SUPABASE_URL not configured"
  Solution: Set SUPABASE_URL and SUPABASE_KEY environment variables
  Check: echo $SUPABASE_URL
  File: backend/.env (create if missing)

Problem: "Configuration directory does not exist"
  Solution: Create the directory or set SCRAPER_CONFIG_DIR
  Default: backend/data/config/
  Fix: mkdir -p backend/data/config or SCRAPER_CONFIG_DIR=/path

Problem: "Auth routing unreachable"
  Solution: Ensure AUTH_SERVICE_URL is correct and service is running
  Check: curl http://localhost:8003/health
  Fix: docker-compose up auth

Problem: "Rate limit exceeded"
  Solution: Wait for reset time or use different API key
  Response includes: Retry-After header with seconds to wait
  Check: X-RateLimit-Remaining header

Problem: "Query timeout"
  Solution: Increase QUERY_TIMEOUT_SECONDS
  Default: 30 seconds
  Increase to: 60 or more for large datasets

Problem: "Connection pool exhausted"
  Solution: Increase POOL_MAX_SIZE
  Check: Monitor connection pool statistics
  Endpoint: GET /api/v1/admin/health/pool (with admin key)

Problem: "Embedding model not found"
  Solution: Model auto-downloads on first use
  Location: ~/.cache/huggingface/transformers/
  Wait: First run may take 1-2 minutes
  Fix: Pre-download model in Docker image
"""
