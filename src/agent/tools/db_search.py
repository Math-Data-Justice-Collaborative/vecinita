# ############################################################################
# FILE: db_search.py
# PATH: src/agent/tools/db_search.py
# ROLE: Production Vector Search Utility for Supabase/PostgreSQL.
# DESCRIPTION: Performs semantic similarity search using Gemini Embeddings
#              and Supabase pgvector 'match_documents' RPC.
# ############################################################################

import os
import logging
from typing import List, Dict
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure logging for production traceability
logger = logging.getLogger("vecinita.db_search")

# --- DATABASE CONFIGURATION ---
# These are injected via Docker Compose / .env
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 

# --- EMBEDDING CONFIGURATION ---
# Initializing the Google Embedding model (768 dimensions)
# This model converts text queries into vectors for semantic matching.
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def db_search(query: str, limit: int = 3) -> List[Dict]:
    """
    Executes a semantic vector search against the Rhode Island resource database.
    
    Args:
        query (str): The user's question (supports English or Spanish).
        limit (int): Number of relevant document chunks to return.
        
    Returns:
        List[Dict]: A list of dictionaries containing 'source' and 'content'.
    """
    try:
        # 1. Generate the semantic vector for the query
        # Note: Even if the query is Spanish, the vector will match English 
        # concepts due to the multilingual nature of embedding-001.
        query_embedding = embeddings_model.embed_query(query)

        # 2. Establish connection to Supabase Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 3. Call the 'match_documents' SQL function (RPC)
        # We pass the embedding and thresholds for relevance.
        response = supabase.rpc(
            'match_documents', 
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5, # Controls how 'close' a match must be
                'match_count': limit,
            }
        ).execute()

        # 4. Parse and Structure the results
        # We ensure the orchestrator gets a clean list of context chunks.
        results = []
        if response.data:
            for row in response.data:
                # Metadata is expected to contain the source URL
                results.append({
                    "source": row.get("metadata", {}).get("source", "https://ri.gov"),
                    "content": row.get("content", "Information not available.")
                })

        # Log a warning if no data was found for a valid query
        if not results:
            logger.warning(f"Semantic search returned 0 results for: {query}")
            return [{"source": "System", "content": "No specific local resources matched your query."}]

        return results

    except Exception as e:
        # Log the full stack trace for debugging without crashing the main app
        logger.error(f"DATABASE SEARCH CRITICAL FAILURE: {e}", exc_info=True)
        return [{"source": "Error", "content": "The search service is currently unavailable."}]

# ############################################################################
# END OF FILE: db_search.py
# ############################################################################
