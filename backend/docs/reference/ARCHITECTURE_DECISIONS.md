# Refactoring Decisions & Architecture

## Key Architectural Decisions Made

### 1. **Service Naming Convention**
**Decision:** Rename `main.py` → `server.py` in services  
**Rationale:** 
- Clarifies that FastAPI servers are HTTP wrappers, not the primary entry point
- `api/main.py` remains as the true "main" entry point for the backend
- Creates clear distinction: `server.py` = HTTP interface, `core.py` would be pure logic

**Alternative Considered:** Extract pure Python `core.py` from FastAPI servers
- Could be done in future Phase 2 if needed for better testing/reusability
- Currently FastAPI is deeply integrated; refactoring now would be high effort/risk

### 2. **Services Directory Structure**
**Decision:** `src/services/{agent,embedding,scraper}` grouping  
**Rationale:**
- Cleaner organization than top-level folders
- Signals that these are services (as opposed to API layer)
- Easier to add new services in future
- Mirrors microservice architecture pattern

**API Location:** `src/api/` (formerly `src/gateway/`)
**Rationale:**
- More conventional naming
- `api/` clearly indicates HTTP/FastAPI interface
- Single entry point for all requests

### 3. **Pydantic Models Strategy**
**Decision:** Per-service models + API-only models in `api/models.py`  
**Rationale:**
```
API Models (api/models.py)
  ↓
External Contracts (request/response)
  ↓
Never should change without API versioning

Service Models (services/*/models.py)
  ↓
Internal Data Structures
  ↓
Can evolve independently
```

**Implementation:**
- `api/models.py` = AskRequest, AskResponse, ScrapeRequest, etc.
- `services/agent/models.py` = ModelSelection, ProviderConfig, SearchResult, etc.
- `services/embedding/models.py` = EmbeddingModel, BatchEmbeddingResult, etc.
- `services/scraper/models.py` = ScraperJob, ScraperResult, etc.

### 4. **Utils Consolidation**
**Decision:** Single `src/utils/` for shared functions  
**Rationale:**
- Supabase utilities should be accessible to all services
- Reduces duplication
- Service-specific utils (agent/utils, scraper/utils) remain local
- Clear distinction: src/utils = shared, service/utils = local

**Example:**
- SHARED: `src/utils/supabase_embeddings.py`
- LOCAL: `src/services/agent/utils/vector_loader.py`
- LOCAL: `src/services/scraper/utils.py`

### 5. **Data Files Location**
**Decision:** Keep `data/` in workspace root  
**Rationale:**
```
Workspace Root (data/)
  ↑
  ├─ Backend scripts (cron_scraper.sh, clean_and_load.py)
  ├─ Frontend (doesn't directly use data files)
  └─ Shared across backend services

Benefits:
- Simpler to manage shared configuration
- Scripts already set up for this location
- Less disruptive than moving (no git history issues)
- Clear separation: data files stay with project, not service
```

**File Structure:**
```
workspace/
├── data/                    # Shared data directory
│   ├── urls.txt            # URLs to scrape
│   ├── config/             # Scraper configuration
│   ├── input/              # Input files
│   └── output/             # Generated outputs
├── backend/                # Backend services
│   ├── src/api/            # API layer
│   ├── src/services/       # Services
│   ├── scripts/            # Scripts reference ../data/
│   └── ...
└── frontend/               # Frontend
```

**Note:** Originally considered moving to `backend/data/` but determined:
- Simpler to keep in root (already working)
- Scripts already reference paths correctly
- Data files are project-level, not backend-specific

### 6. **Test Organization**
**Decision:** Mirror source structure exactly  
**Benefits:**
- Easy to find corresponding tests
- Obvious where new tests belong
- PyTest discovery works naturally
- Logical organization

**Structure:**
```
tests/
├── test_api/               # ← tests for src/api/
├── test_services/          # ← tests for src/services/
│   ├── agent/
│   ├── embedding/
│   └── scraper/
├── test_utils/             # ← tests for src/utils/
├── integration/           # ← cross-service tests
└── e2e/                   # ← end-to-end flows
```

### 7. **Server vs Core Split**
**Current Status:** Services have `server.py` (FastAPI wrapper)  
**Rationale for NOT splitting further now:**
- Would require significant refactoring of large files (agent/server.py is 1987 lines)
- FastAPI decorators heavily integrated into logic
- HTTP concerns mixed with business logic
- Would add complexity (import cycles, testing overhead)

**Future Consideration (Phase 2):**
```python
# If needed later:
src/services/agent/
├── server.py     # FastAPI HTTP interface
├── core.py       # Pure Python business logic
├── models.py     # Pydantic schemas
└── ...
```
Could extract:
- Query execution into pure functions
- Tool definitions into data structures
- Response building into serializers

### 8. **Import Paths**
**Decision:** Full module paths from `src/`  
**Examples:**
```python
# ✓ Correct
from src.api.main import app
from src.services.agent.models import ModelSelection
from src.utils.supabase_embeddings import SupabaseEmbeddings

# ✗ Avoid
from .api import app              # Too relative
import api                         # Unclear scope
```

**Rationale:**
- Explicit and unambiguous
- Works from any directory
- PyCharm/IDE friendly
- Matches entry points in Dockerfile/pyproject.toml

### 9. **API Gateway Responsibilities**
**What API Does:**
- Routes requests to appropriate endpoints
- Handles CORS, authentication, rate limiting
- Proxies to services via HTTP (when running separately)
- Could import services directly when deployed together

**What API Does NOT Do:**
- Business logic (Q&A, embeddings, scraping)
- Direct database access (goes through services)
- Model training/inference
- Document processing

### 10. **Service Independence**
**Design Principle:** Services are loosely coupled
- Communicate via HTTP
- No direct Python imports between services
- Can be deployed on separate servers
- Gateway is the only integration point

**Current Reality:** All services run together in development
- Agent: http://localhost:8000
- Embedding: http://localhost:8001
- API Gateway: http://localhost:8002
- Scraper: CLI-triggered or cron job

**Future Scaling:**
- Deploy each service independently
- Use service discovery (Consul, Kubernetes, etc.)
- Add load balancing if needed

---

## Trade-offs & Considerations

### Trade-off #1: FastAPI in Services
**Pro:**
- Easy to run services standalone
- Can be deployed as individual Docker containers
- Easy testing with client libraries

**Con:**
- "Pure Python" ideally means no HTTP framework
- Could extract core to reusable library

**Decision:** Keep for now (phase 2 optimization)

### Trade-off #2: Main.py → Server.py Naming
**Pro:**
- Clear that gateway is the "main" entry point
- Signals these are HTTP servers

**Con:**
- Breaks from Python convention (main = entry point)
- Requires updating import statements

**Decision:** More benefits than costs for clarity

### Trade-off #3: Data Files in Backend
**Pro:**
- Organized with backend code
- Simpler Docker COPY
- Backend-specific config

**Con:**
- Moving files in git history
- Scripts need updating
- Different from original structure

**Decision:** Better organization outweighs transition cost

---

## What Was NOT Changed (And Why)

### 1. API Endpoints
All `/api/*` routes remain unchanged. Frontend needs zero changes.

### 2. Database Schema
No changes to Supabase structure or tables.

### 3. Dependencies
No new packages added. Same versions maintained.

### 4. Service Logic
No business logic changed. Only moved/reorganized.

### 5. Deployment Strategy
Services still meant to run separately. Only structure changed.

### 6. Environment Variables
All same .env variables work. No new requirements.

---

## Team Guidance

### Onboarding to New Structure
1. **API Development:** Work in `src/api/`
2. **Agent Development:** Work in `src/services/agent/`
3. **Embedding Development:** Work in `src/services/embedding/`
4. **Scraper Development:** Work in `src/services/scraper/`
5. **Shared Code:** Put in `src/utils/`, document why it's shared

### Adding New Service
```
1. Create src/services/newservice/
2. Add __init__.py, server.py, models.py
3. Create corresponding test directory
4. Update pyproject.toml if needed
5. Update Docker setup
```

### Import Pattern
```python
# When in source:
from src.api.models import AskRequest
from src.services.agent.models import ModelSelection

# When in tests:
from src.api import app
from src.services.agent.server import app as agent_app
```

---

## Performance Implications

### Startup Time
- No change (all services same as before)

### Request Latency
- Services talk via HTTP: +1-2ms roundtrip
- Already the case (API proxies to services)
- Negligible impact

### Memory Usage
- No change (same code, same imports)

### Development Experience
- Better: Clearer organization
- Better: Easier to find code
- Neutral: Same running process

---

## Rollback Plan (If Needed)

If refactoring caused issues:

```bash
# Identify breaking change
git log --oneline  # See what changed

# Check specific change
git show <commit>

# Revert if severe issues
git revert <commit>

# Or restore from backup branch
git checkout <original-branch>
```

**No database changes**, so rollback is clean.

---

## Success Metrics

✅ **Code Organization**
- Clear separation: API vs Services vs Utils
- Tests mirror source structure
- New developers can find code easily

✅ **Version Control**
- All imports updated
- No broken references
- Clean git history

✅ **Maintainability**
- Services independent
- Easy to add features
- Easy to add new services
- Easy to test in isolation

✅ **Documentation**
- Architecture clear
- Decision rationale documented
- Team can onboard quickly

---

## Questions This Answers

**Q: Where do I put database code?**  
A: In service that uses it, OR in `src/utils/supabase_*.py` if shared

**Q: Can services import from each other?**  
A: No. They should communicate via HTTP (or gateway proxies)

**Q: Where do I put a new utility function?**  
A: In `src/utils/` if shared by 2+ services, otherwise keep local

**Q: How do I write tests for a service?**  
A: In `tests/test_services/<service>/test_*.py` mirroring source structure

**Q: Can I add a new service?**  
A: Yes! Create `src/services/newname/` with same structure

---

**Document Version:** 1.0  
**Last Updated:** February 8, 2026  
**Status:** Reference Document - Use for onboarding and future development decisions
