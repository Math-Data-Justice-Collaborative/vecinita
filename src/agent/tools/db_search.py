# ############################################################################
# FILE: db_search.py
# PATH: src/agent/tools/db_search.py
# ROLE: Production Vector Search with Graceful Fallback (99% Availability)
# ############################################################################

import os
import logging
from typing import List, Dict
from supabase import create_client, Client
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initialize logging for traceability
logger = logging.getLogger("vecinita.db_search")

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# The model name should be the one verified by your environment
# If text-embedding-004 fails, fallback logic handles it.
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="text-embedding-004", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    task_type="retrieval_query"
)

def db_search(query: str, limit: int = 3) -> List[Dict]:
    """
    Executes a vector search against Supabase. 
    If the API or DB fails, it triggers a 'Replacement Action' with static data.
    """
    try:
        # 1. PRIMARY ACTION: Semantic Search
        # Generate embedding for the incoming query
        query_embedding = embeddings_model.embed_query(query)

        # Connect to Supabase Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Call the RPC function in Postgres
        response = supabase.rpc(
            'match_documents', 
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': limit,
            }
        ).execute()

        if response.data and len(response.data) > 0:
            results = []
            for row in response.data:
                results.append({
                    "source": row.get("metadata", {}).get("source", "https://ri.gov"),
                    "content": row.get("content", "")
                })
            return results
        
        # If the search executes but finds nothing, we manually trigger the fallback
        raise ValueError("No relevant documents found in database.")

    except Exception as e:
        # 2. REPLACEMENT ACTION: The Clue for the Watchdog
        # We use a specific tag so the monitor script can alert you.
        logger.error(f"[FALLBACK TRIGGERED] Reason: {str(e)}")

        # 3. GRACEFUL DEGRADATION: High-Value Static Defaults
        # This ensures the GUI 'Sources' section is never empty.
        return [
            {
                "source": "https://health.ri.gov",
                "content": "Portal oficial de salud de Rhode Island. Información sobre vacunas y clínicas locales."
            },
            {
                "source": "https://dhs.ri.gov/programs-and-services/supplemental-nutrition-assistance-program-snap",
                "content": "Asistencia alimentaria para familias de bajos ingresos (SNAP). Contacto: 1-855-MY-RIDHS."
            }
        ]

# ############################################################################
# END OF FILE: db_search.py
# ############################################################################
