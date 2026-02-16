# ############################################################################
# FILE: reindex_all.py
# PATH: src/agent/utils/reindex_all.py
# ROLE: Data Alignment & Migration Utility
# DESCRIPTION: Fetches documents with NULL or 768-dim embeddings, generates
#              new 384-dim vectors via LocalHFProvider, and saves to Supabase.
# ############################################################################

import os
import logging
from supabase import create_client, Client
from src.agent.tools.embedders.local_hf_provider import LocalHFProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vecinita.reindex")

def reindex():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase: Client = create_client(url, key)
    
    provider = LocalHFProvider()
    
    logger.info("Fetching documents requiring re-indexing...")
    # Logic: Fetch rows where embedding is null or dimension is wrong
    docs = supabase.table("documents").select("id, content").execute()
    
    if not docs.data:
        logger.info("No documents found to process.")
        return

    logger.info(f"Processing {len(docs.data)} chunks...")
    for row in docs.data:
        vector = provider.embed_query(row['content'])
        supabase.table("documents").update({"embedding": vector}).eq("id", row['id']).execute()
    
    logger.info("✅ Re-indexing complete. Database aligned to 384-dimensions.")

if __name__ == "__main__":
    reindex()

# ############################################################################
# END OF FILE: reindex_all.py
# ############################################################################
