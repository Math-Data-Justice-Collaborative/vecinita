"""
Tool Factory Functions Reference

All Vecinita agent tools use the **factory pattern** for proper initialization.
Do NOT call tool functions directly; use their corresponding factory functions instead.

## Pattern

Each tool has:
1. **Placeholder function** decorated with `@tool` (for inspection)
2. **Factory function** `create_*_tool()` that returns a properly configured tool

## Tools

### 1. Static Response Tool (FAQs)

**Placeholder:**
```python
@tool
def static_response_tool(query: str, language: str = "en") -> str | None
```

**Factory:**
```python
from src.services.agent.tools import create_static_response_tool

tool = create_static_response_tool()
```

**Usage:**
```python
result = tool.invoke({"query": "What is climate change?", "language": "en"})
```

**Features:**
- Loads FAQs from markdown files (`backend/src/services/agent/data/faqs/*.md`)
- Returns markdown-formatted answers
- Falls back to English if language not found

---

### 2. Database Search Tool (Vector Similarity)

**Placeholder:**
```python
@tool
def db_search_tool(query: str, match_threshold: float = 0.3) -> str
```

**Factory:**
```python
from src.services.agent.tools import create_db_search_tool
from src.services.db.pool import DatabaseConnectionPool
from langchain_community.embeddings import HuggingFaceEmbeddings

pool = DatabaseConnectionPool()
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

tool = create_db_search_tool(
    db=pool.get_client(),
    embeddings=embeddings,
    match_threshold=0.3,
    match_count=5
)
```

**Usage:**
```python
result = tool.invoke({"query": "climate policy"})
```

**Features:**
- Searches document embeddings stored in Supabase
- Requires RPC function: `search_similar_documents(query_embedding, match_threshold, match_count)`
- Returns JSON with matched documents and relevance scores
- Configurable similarity threshold (0.0-1.0, default 0.3)

---

### 3. Web Search Tool (Tavily + DuckDuckGo)

**Placeholder:**
```python
@tool
def web_search_tool(query: str, max_results: int = 3) -> str
```

**Factory:**
```python
from src.services.agent.tools import create_web_search_tool

# Uses Tavily API (if TAVILY_API_KEY set) or falls back to DuckDuckGo
tool = create_web_search_tool(
    tavily_api_key=os.getenv("TAVILY_API_KEY"),
    max_results=3
)
```

**Usage:**
```python
result = tool.invoke({"query": "latest climate change news"})
```

**Features:**
- Primary: Tavily API (if TAVILY_API_KEY configured)
- Fallback: DuckDuckGo web search (no API key needed)
- Returns JSON with search results and URLs

---

### 4. Clarify Question Tool (Contextual Refinement)

**Placeholder:**
```python
@tool
def clarify_question_tool(query: str, context: str = "") -> str
```

**Factory:**
```python
from src.services.agent.tools import create_clarify_question_tool

tool = create_clarify_question_tool(
    location_context="Providence, RI"  # Optional: location for filtering
)
```

**Usage:**
```python
result = tool.invoke({"query": "office hours", "context": "immigration services"})
# Returns: "You asked: 'office hours' in the context of 'immigration services'. Do you mean: [...options...]"
```

**Features:**
- Assists user in clarifying ambiguous queries
- Can provide location-based context
- Suggests possible interpretations

---

## Architecture

### LangGraph Integration

All tools are bound to the LLM via `.bind_tools()`:

```python
from langchain_core.tools import tool

# In src/services/agent/server.py:
tools = [
    create_static_response_tool(),
    create_db_search_tool(db, embeddings),
    create_web_search_tool(),
    create_clarify_question_tool(),
]

# Bind to model
model_with_tools = model.bind_tools(tools, tool_choice="auto")

# LLM will now automatically select appropriate tool
```

### Error Handling

All tools include:
- Try/catch blocks with detailed logging
- Graceful degradation (returns sensible defaults if external service fails)
- Error messages that guide users to next steps

Example:
```python
try:
    # Tool logic
except Exception as e:
    logger.error(f"Tool failed: {e}")
    return f"Unable to search. Please try a different query."
```

---

## Configuration

### Environment Variables

| Variable | Tool | Purpose | Example |
|----------|------|---------|---------|
| `TAVILY_API_KEY` | web_search_tool | Tavily API key (optional) | `tvly_XXX...` |
| `FAQ_DIR` | static_response_tool | FAQ file directory (optional) | `/path/to/faqs` |
| `SUPABASE_URL` | db_search_tool | Database URL (required) | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | db_search_tool | Database key (required) | `eyJh...` |

---

## Testing Tools

### Unit Test Example

```python
import pytest
from src.services.agent.tools import create_static_response_tool

@pytest.mark.asyncio
async def test_static_response_tool():
    tool = create_static_response_tool()
    
    # This tool is synchronous, but we can test it directly
    result = tool.invoke({
        "query": "What is climate change?",
        "language": "en"
    })
    
    # Should return FAQ answer or None
    assert result is None or isinstance(result, str)
```

### Integration Test Example

```python
@pytest.mark.integration
async def test_db_search_tool_with_real_db():
    from src.services.db.pool import DatabaseConnectionPool
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    pool = DatabaseConnectionPool()
    await pool.initialize()
    
    embeddings = HuggingFaceEmbeddings()
    tool = create_db_search_tool(pool.get_client(), embeddings)
    
    result = tool.invoke({"query": "test query"})
    
    # Result should be JSON string with documents
    assert isinstance(result, str)
    
    await pool.shutdown()
```

---

## Troubleshooting

### "Tool not initialized" Error

**Problem:** Calling tool directly instead of via factory
```python
# ❌ Wrong
result = static_response_tool.invoke({...})

# ✅ Correct
tool = create_static_response_tool()
result = tool.invoke({...})
```

### "RPC function not found" Error (db_search_tool)

**Problem:** Supabase RPC `search_similar_documents` doesn't exist
**Solution:** Create RPC in Supabase SQL Editor:
```sql
CREATE OR REPLACE FUNCTION search_similar_documents(
    query_embedding vector,
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    content text,
    source text,
    similarity float
) AS $$
SELECT
    id,
    content,
    source_url as source,
    (embedding <-> query_embedding) as similarity
FROM document_chunks
WHERE (embedding <-> query_embedding) < (1 - match_threshold)
ORDER BY embedding <-> query_embedding
LIMIT match_count
$$ LANGUAGE SQL;
```

### "API key not configured" Error (web_search_tool)

**Problem:** Tavily API key not set
**Solution:** Either set `TAVILY_API_KEY` env var, or tool will use DuckDuckGo fallback

### "Embedding dimension mismatch" Error

**Problem:** Embeddings are 384-dim but RPC expects different dimension
**Solution:** Verify Supabase vector column is `pgvector(384)`:
```sql
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = 'document_chunks' AND column_name = 'embedding';
-- Should show: vector(384)
```

---

## Additional Resources

- [Agent Architecture](../docs/architecture/ARCHITECTURE_MICROSERVICE.md)
- [Embedding Service](../backend/docs/EMBEDDING_SERVICE_ARCHITECTURE.md)
- [Database Schema](../docs/deployment/SUPABASE_SCHEMA_SETUP.md)
- [Testing Guide](../tests/README.md)
