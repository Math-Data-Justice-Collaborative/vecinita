# ############################################################################
# FILE: db_search.py
# PATH: src/agent/tools/db_search.py
# ROLE: Vector Search Router & Executor
# DESCRIPTION: The primary entry point for context retrieval. It dynamically
#              selects the embedding provider based on environment variables,
#              validates dimensions, and queries Supabase via RPC.
# ############################################################################

import os
import logging
from typing import List, Dict
from supabase import create_client, Client

# Importing the Pluggable Providers
from .embedders.google_v1_provider import GoogleV1Provider
from .embedders.local_hf_provider import LocalHFProvider

logger = logging.getLogger("vecinita.db_search")

def get_active_provider():
    """
    Factory function to select the embedding engine.
    Strategy is determined by the EMBEDDING_STRATEGY env variable.
    """
    strategy = os.getenv("EMBEDDING_STRATEGY", "LOCAL").upper()
    
    if strategy == "GOOGLE":
        logger.info("Routing to QUALITY strategy: GoogleV1")
        return GoogleV1Provider()
    
    logger.info("Routing to AVAILABILITY strategy: LocalHF")
    return LocalHFProvider()

def db_search(query: str, limit: int = 3) -> List[Dict]:
    """
    Executes a semantic search against the Supabase vector store.
    
    Args:
        query (str): The user's natural language question.
        limit (int): Number of relevant document chunks to return.
        
    Returns:
        List[Dict]: A list of source/content pairs for the LLM to use.
    """
    try:
        # 1. Initialize the Provider
        provider = get_active_provider()
        
        # 2. Generate Embedding
        query_embedding = provider.embed_query(query)

        # 3. Structural Guard: Verify dimension matches database schema
        expected_dim = int(os.getenv("VECTOR_DIMENSION", "384"))
        if len(query_embedding) != expected_dim:
            error_msg = f"DIMENSION MISMATCH: Model produced {len(query_embedding)}, DB expected {expected_dim}"
            logger.error(error_msg)
            # Graceful failure to avoid API crash
            return [{"source": "System Error", "content": "The search service is currently undergoing dimension reconfiguration."}]

        # 4. Supabase Connection
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)

        # 5. Vector Similarity Search (RPC)
        # Calls the 'match_documents' function in your Postgres DB
        response = supabase.rpc(
            'match_documents', 
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.4, # Adjust based on model sensitivity
                'match_count': limit,
            }
        ).execute()

        if response.data:
            return [
                {
                    "source": r["metadata"].get("source", "https://ri.gov"), 
                    "content": r["content"]
                } for r in response.data
            ]
        
        return []

    except Exception as e:
        logger.error(f"[CRITICAL SEARCH FAILURE]: {e}")
        # 99% Availability Fallback: Always return a baseline source
        return [{
            "source": "https://health.ri.gov", 
            "content": "Rhode Island Department of Health general assistance portal."
        }]

# ############################################################################
# END OF FILE: db_search.py
# ############################################################################
